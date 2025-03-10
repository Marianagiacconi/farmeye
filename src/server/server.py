import socket
import threading
import json
import os
from dotenv import load_dotenv
import redis
import multiprocessing
from multiprocessing import Lock, Queue
from sqlalchemy.exc import OperationalError
from tasks.celery_config import celery
from tasks.image_processing import process_image_task
import logging
from utils.database import SessionLocal
from server.models import Image, User, Prediction

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cargar variables desde .env
load_dotenv()

# Configuración del servidor
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))
BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", 65536))
IMAGE_FOLDER = os.getenv("IMAGE_FOLDER", "server/uploads/")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_HOST = REDIS_URL.split("//")[-1].split(":")[0]
REDIS_PORT = int(REDIS_URL.split(":")[-1].split("/")[0])

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

#Colas
prediction_queue = Queue()  # Para guardar predicciones en la BD
history_queue = Queue()  # Para consultas de historial

# Lock para evitar conflictos en la BD
db_lock = Lock()

def prediction_worker(queue):
    """Proceso que guarda predicciones en la BD."""
    db = SessionLocal()
    logger.info("Proceso de guardado de predicciones iniciado...")

    while True:
        try:
            task = queue.get()
            if task is None:
                logger.info("Cerrando proceso de predicciones...")
                break

            image_id, result, confidence = task
            logger.info(f"Guardando predicción: {result} ({confidence}%) para imagen {image_id}")

            image = db.query(Image).filter(Image.id == image_id).first()
            if not image:
                logger.error(f"Imagen {image_id} no encontrada.")
                continue

            prediction = Prediction(image_id=image_id, result=result, confidence=confidence)
            db.add(prediction)
            db.commit()
            logger.info(f"Predicción guardada en la BD.")

        except Exception as e:
            db.rollback()
            logger.error(f"Error al guardar predicción: {e}")

    db.close()


def history_worker(queue):
    """Proceso que maneja solicitudes de historial."""
    db = SessionLocal()
    logger.info("Proceso de historial iniciado...")

    while True:
        try:
            task = queue.get()
            if task is None:
                logger.info("Cerrando proceso de historial...")
                break

            user_id, client_conn = task
            logger.info(f"Procesando historial para usuario {user_id}")

            predictions = (
                db.query(Prediction)
                .join(Image, Prediction.image_id == Image.id)
                .filter(Image.user_id == user_id)
                .all()
            )

            if not predictions:
                response = {"status": "success", "historial": [], "message": "No hay predicciones registradas."}
            else:
                history = [
                    {"image_id": p.image_id, "result": p.result, "confidence": p.confidence}
                    for p in predictions
                ]
                response = {"status": "success", "historial": history}

            client_conn.sendall(json.dumps(response).encode())
            client_conn.close()
            logger.info(f"Historial enviado al cliente {user_id}")

        except Exception as e:
            logger.error(f"Error en historial: {e}")

    db.close()


class ImageServer:
    def __init__(self):
        self.server = None
        os.makedirs(IMAGE_FOLDER, exist_ok=True)

    def listen_for_result(self, conn, user_id, image_id, task_id):
        """Escucha el canal en Redis y envía el resultado al cliente sin cerrar la conexión antes de tiempo."""
        channel = f"resultados:{user_id}"
        pubsub = redis_client.pubsub()
        pubsub.subscribe(channel)
        logger.info(f"Cliente {user_id} suscrito a {channel}")

        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    result_data = json.loads(message["data"])
                    logger.info(f"Resultado recibido para {user_id}: {result_data}")

                    # Encolar la predicción para que el worker la guarde en la BD
                    prediction_queue.put((image_id, result_data["final_result"], result_data["confidence"]))
                    logger.info(f"Predicción encolada para guardar.")

                    # **Verificar si la conexión sigue activa antes de enviar datos**
                    if conn.fileno() != -1:  
                        try:
                            conn.sendall(json.dumps(result_data).encode())
                            logger.info(f"Resultado enviado a {user_id}")
                        except (BrokenPipeError, ConnectionResetError):
                            logger.error(f"El cliente {user_id} cerró la conexión antes de recibir el resultado.")
                    else:
                        logger.warning(f"Conexión con {user_id} ya estaba cerrada.")

                    break  # Termina la escucha una vez que se recibe el resultado

        except Exception as e:
            logger.error(f"Error en listen_for_result para {user_id}: {e}")
        finally:
            pubsub.close()

    def process_image_request(self, metadata, conn, db):
        """Procesa una solicitud de imagen."""
        user_id = int(metadata["user_id"])
        filename = metadata["image_name"]
        file_size = metadata["file_size"]

        logger.debug(f"Recibiendo imagen {filename} ({file_size} bytes)...")

        user = db.query(User).filter_by(id=user_id).first()
        if not user:
            logger.info(f"Creando usuario {user_id}...")
            new_user = User(id=user_id)
            db.add(new_user)
            db.commit()

        image_path = os.path.join(IMAGE_FOLDER, filename)
        received_size = 0
        with open(image_path, "wb") as f:
            while received_size < file_size:
                chunk = conn.recv(min(BUFFER_SIZE, file_size - received_size))
                if not chunk:
                    raise Exception("Conexión interrumpida")
                f.write(chunk)
                received_size += len(chunk)
                conn.sendall(b"ACK")

        logger.info(f"Imagen guardada en {image_path}")

        new_image = Image(image_path=image_path, user_id=user_id)
        db.add(new_image)
        db.commit()

        try:
            task = process_image_task.delay(image_path, user_id)
            response = {"status": "success", "task_id": task.id, "message": "Imagen recibida y procesamiento iniciado"}
            conn.sendall(json.dumps(response).encode())

            listener_thread = threading.Thread(target=self.listen_for_result, args=(conn, user_id, new_image.id, task.id))
            listener_thread.daemon = True
            listener_thread.start()
        except Exception as e:
            logger.error(f"Error al procesar imagen: {e}")
            conn.sendall(json.dumps({"status": "error", "message": str(e)}).encode())

    def send_history(self, metadata, conn):
        """Encola la solicitud de historial para ser procesada en segundo plano."""
        user_id = int(metadata["user_id"])
        logger.info(f"Encolando historial para usuario {user_id}...")
        history_queue.put((user_id, conn))

    def handle_client(self, conn, addr):
        """Maneja la conexión con un cliente."""
        logger.info(f"Conectado con {addr}")
        db = SessionLocal()
    
        try:
            while True:
                size_data = conn.recv(4)
                if not size_data:
                    logger.info(f"Cliente {addr} cerró la conexión.")
                    break
                
                metadata_size = int.from_bytes(size_data, "big")
                metadata_bytes = conn.recv(metadata_size)
                if not metadata_bytes:
                    break  
                
                metadata = json.loads(metadata_bytes.decode())
                action = metadata.get("action", "send_image")
    
                if action == "send_image":
                    # Procesar la imagen y esperar a que se envíe la predicción antes de cerrar la conexión
                    listener_thread = threading.Thread(
                        target=self.process_image_request,
                        args=(metadata, conn, db),
                        daemon=True
                    )
                    listener_thread.start()
                    listener_thread.join()  # Esperar a que el hilo termine antes de cerrar la conexión
    
                elif action == "get_history":
                    self.send_history(metadata, conn, db)
                else:
                    conn.sendall(json.dumps({"status": "error", "message": "Acción no reconocida"}).encode())
    
        except Exception as e:
            logger.error(f"Error general en handle_client: {e}")
        finally:
            db.close()
            conn.close()  
    

    def start(self):
        self.server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.server.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)  # Permite IPv4 e IPv6
        self.server.bind(("::", PORT))  # Escucha en todas las interfaces
        self.server.listen(5)
        logger.info(f"🚀 Servidor TCP iniciado en {HOST}:{PORT}")
    
        while True:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    multiprocessing.Process(target=prediction_worker, args=(prediction_queue,), daemon=True).start()
    multiprocessing.Process(target=history_worker, args=(history_queue,), daemon=True).start()

    server = ImageServer()
    server.start()
