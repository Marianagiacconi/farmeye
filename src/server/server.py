import socket
import threading
import json
import os
from tasks.celery_config import celery
from tasks.image_processing import process_image_task
from celery.exceptions import OperationalError
import logging

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuración del servidor
HOST = '0.0.0.0'
PORT = 5000
IMAGE_FOLDER = "server/uploads/"
BUFFER_SIZE = 65536  

class ImageServer:
    def __init__(self):
        self.server = None
        os.makedirs(IMAGE_FOLDER, exist_ok=True)

    def handle_client(self, conn, addr):
        """Maneja la conexión con un cliente."""
        logger.info(f"Conectado con {addr}")

        try:
            metadata_size = int.from_bytes(conn.recv(4), "big")
            metadata = json.loads(conn.recv(metadata_size).decode())

            user_id = metadata["user_id"]
            filename = metadata["image_name"]
            file_size = metadata["file_size"]

            logger.debug(f"Recibiendo imagen {filename} de {file_size} bytes...")

            # Guardar imagen
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

            logger.debug(f"Imagen {filename} guardada en {image_path}")

            # Procesar imagen con Celery
            try:
                task = process_image_task.delay(image_path, user_id)
                logger.debug(f"Tarea enviada a Celery con ID: {task.id}")
                response = {
                    "status": "success",
                    "task_id": task.id,
                    "image_path": image_path,
                    "message": "Imagen recibida y procesamiento iniciado"
                }
            except OperationalError as e:
                logger.error(f"Error de conexión con Celery/Redis: {e}")
                response = {
                    "status": "error",
                    "error": "Error de conexión con el sistema de procesamiento",
                    "details": str(e)
                }
            except Exception as e:
                logger.error(f"Error inesperado al procesar imagen: {e}")
                response = {
                    "status": "error",
                    "error": "Error interno del servidor",
                    "details": str(e)
                }

        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar metadata: {e}")
            response = {
                "status": "error",
                "error": "Error en formato de metadata",
                "details": str(e)
            }
        except Exception as e:
            logger.error(f"Error general en handle_client: {e}")
            response = {
                "status": "error",
                "error": str(e)
            }
        
        finally:
            try:
                # Enviar respuesta final al cliente
                conn.sendall(json.dumps(response).encode())
            except Exception as e:
                logger.error(f"Error al enviar respuesta: {e}")
            finally:
                conn.close()

    def start(self):
        """Inicia el servidor TCP y maneja múltiples clientes con threads."""
        try:
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server.bind((HOST, PORT))
            self.server.listen(5)
            logger.info(f"Servidor TCP iniciado en {HOST}:{PORT}")

            while True:
                try:
                    conn, addr = self.server.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(conn, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except Exception as e:
                    logger.error(f"Error al aceptar conexión: {e}")

        except Exception as e:
            logger.error(f"Error al iniciar servidor: {e}")
        finally:
            if self.server:
                self.server.close()

    def stop(self):
        """Detiene el servidor."""
        if self.server:
            self.server.close()
            logger.info("Servidor detenido")

if __name__ == "__main__":
    server = ImageServer()
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Deteniendo servidor por interrupción del usuario...")
        server.stop()
