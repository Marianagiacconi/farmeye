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

# 🔹 Cola de predicciones compartida
prediction_queue = Queue()

# Lock para evitar conflictos en la BD
db_lock = Lock()

def save_prediction_worker(queue):
    """Proceso que escucha la cola de predicciones y las guarda en la BD."""
    db = SessionLocal()
    logger.info("🛠️ Proceso de guardado de predicciones iniciado...")

    while True:
        try:
            image_id, result, confidence = queue.get()
            if image_id is None:
                logger.info("Cerrando proceso de guardado de predicciones...")
                break

            logger.info(f"Guardando predicción: {result} ({confidence}%) para imagen {image_id}")

            image = db.query(Image).filter(Image.id == image_id).first()
            if not image:
                logger.error(f"No se encontró la imagen {image_id}. No se puede guardar la predicción.")
                continue

            prediction = Prediction(image_id=image_id, result=result, confidence=confidence)
            db.add(prediction)
            db.commit()
            logger.info(f"Predicción guardada en la BD: {result} ({confidence}%) para imagen {image_id}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error al guardar predicción en la BD: {e}")

    db.close()

class ImageServer:
    def __init__(self):
        self.server = None
        os.makedirs(IMAGE_FOLDER, exist_ok=True)

    def listen_for_result(self, conn, user_id, image_id, task_id):
        """Escucha el canal en Redis y envía el resultado al cliente sin cerrar la conexión."""
        channel = f"resultados:{user_id}"
        pubsub = redis_client.pubsub()
        pubsub.subscribe(channel)
        logger.info(f"Cliente {user_id} suscrito a {channel}")

        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    result_data = json.loads(message["data"])
                    logger.info(f"Resultado recibido para {user_id}: {result_data}")

                    result_data["task_id"] = task_id

                    prediction_queue.put((image_id, result_data["final_result"], result_data["confidence"]))
                    logger.info(f"Predicción encolada para guardar en la BD.")

                    if conn.fileno() != -1:
                        try:
                            conn.sendall(json.dumps(result_data).encode())
                            logger.info(f"Resultado enviado a {user_id}")
                        except (BrokenPipeError, ConnectionResetError):
                            logger.error(f"El cliente {user_id} cerró la conexión antes de recibir el resultado.")
                    else:
                        logger.error(f"Conexión con {user_id} ya estaba cerrada.")

                    break  
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
            logger.info(f"Usuario {user_id} no encontrado. Creándolo...")
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
        logger.debug(f"Imagen registrada en BD con ID: {new_image.id}")
    
        try:
            task = process_image_task.delay(image_path, user_id)
            logger.debug(f"Tarea enviada a Celery con ID: {task.id}")
            response = {
                "status": "success",
                "task_id": task.id,
                "image_path": image_path,
                "message": "Imagen recibida y procesamiento iniciado"
            }
            conn.sendall(json.dumps(response).encode())
    
            listener_thread = threading.Thread(
                target=self.listen_for_result,
                args=(conn, user_id, new_image.id, task.id)
            )
            listener_thread.daemon = True
            listener_thread.start()
        except OperationalError as e:
            logger.error(f"Error con Celery/Redis: {e}")
            conn.sendall(json.dumps({
                "status": "error",
                "error": "Error de conexión con el sistema de procesamiento",
                "details": str(e)
            }).encode())
        except Exception as e:
            logger.error(f"Error inesperado al procesar imagen: {e}")
            conn.sendall(json.dumps({
                "status": "error",
                "error": "Error interno del servidor",
                "details": str(e)
            }).encode())
    def send_history(self, metadata, conn, db):
        """Consulta el historial de predicciones de un usuario y lo envía al cliente."""
        user_id = int(metadata["user_id"])
        logger.info(f"Buscando historial de predicciones para el usuario {user_id}...")

        try:
            predictions = (
                db.query(Prediction)
                .join(Image, Prediction.image_id == Image.id)  
                .filter(Image.user_id == user_id)
                .all()
            )

            if not predictions:
                response = {"status": "success", "historial": [], "message": "No hay predicciones registradas para este usuario."}
                logger.info(f"No se encontraron predicciones para {user_id}.")
            else:
                history = [
                    {"image_id": p.image_id, "result": p.result, "confidence": p.confidence}
                    for p in predictions
                ]
                response = {"status": "success", "historial": history}
                logger.info(f"Historial de {user_id} recuperado con {len(history)} registros.")

            conn.sendall(json.dumps(response).encode())
        except Exception as e:
            logger.error(f"Error al obtener historial para {user_id}: {e}")
            conn.sendall(json.dumps({"status": "error", "message": str(e)}).encode())

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
                    self.process_image_request(metadata, conn, db)
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
        self.server.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        self.server.bind(("::", PORT))
        self.server.listen(5)
        logger.info(f"Servidor TCP iniciado en {HOST}:{PORT}")

        while True:
            conn, addr = self.server.accept()
            client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()

if __name__ == "__main__":
    process = multiprocessing.Process(target=save_prediction_worker, args=(prediction_queue,), daemon=True)
    process.start()

    server = ImageServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Deteniendo servidor...")
        prediction_queue.put((None, None, None))
        process.join()
        server.server.close()
