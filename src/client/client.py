import random
import socket
import json
import argparse
import os
import redis
from dotenv import load_dotenv
import select
# Cargar configuraciones desde .env
load_dotenv()

# Configuración del sistema
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 5000))
BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", 65536))
REDIS_HOST = os.getenv("REDIS_URL", "127.0.0.1").split("//")[-1].split(":")[0]
REDIS_PORT = int(os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0").split(":")[-1].split("/")[0])
REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "resultados")

def send_images(image_paths, host=None, port=None):
    """Envía imágenes al servidor y maneja la conexión de manera segura."""
    user_id = random.randint(1, 2**31 - 1)
    tasks = {}

    host = host or HOST
    port = port or PORT

    try:
        family, type_, proto, _, sockaddr = socket.getaddrinfo(host, port, socket.AF_UNSPEC, socket.SOCK_STREAM)[0]
    except Exception as e:
        print(f"Error resolviendo la dirección {host}:{port} - {e}")
        return user_id, []

    client = socket.socket(family, type_, proto)
    
    try:
        client.connect(sockaddr)
        print(f"Conectado al servidor en {host}:{port}")

        for image_path in image_paths:
            if not os.path.exists(image_path):
                print(f"La imagen {image_path} no existe.")
                continue

            file_size = os.path.getsize(image_path)
            filename = os.path.basename(image_path)

            metadata = json.dumps({
                "action": "send_image",
                "user_id": user_id,
                "image_name": filename,
                "file_size": file_size
            })
            metadata_bytes = metadata.encode()

            print(f"Enviando metadata ({len(metadata_bytes)} bytes)")
            client.sendall(len(metadata_bytes).to_bytes(4, "big"))
            client.sendall(metadata_bytes)

            print(f"Enviando imagen {filename} ({file_size} bytes)...")
            with open(image_path, "rb") as f:
                while chunk := f.read(BUFFER_SIZE):
                    try:
                        client.sendall(chunk)
                        ack = client.recv(3)  # Esperar confirmación del servidor
                        if ack != b"ACK":
                            raise Exception("No se recibió ACK correctamente.")
                    except BrokenPipeError:
                        print("Error: El servidor cerró la conexión antes de terminar el envío.")
                        return user_id, []

            response_data = client.recv(BUFFER_SIZE).decode()
            if not response_data:
                raise Exception("No se recibió respuesta del servidor.")

            response = json.loads(response_data)

            if "task_id" in response:
                print(f"Imagen {filename} enviada correctamente. Task ID: {response['task_id']}")
                tasks[response["task_id"]] = {"image": filename, "prediction": None}
            else:
                print(f"Error en respuesta del servidor: {response}")

            print(f"Esperando predicción del servidor para {filename}...")

            client.settimeout(60)
            ready, _, _ = select.select([client], [], [], 60)
            if ready:
                prediction_data = client.recv(BUFFER_SIZE).decode()
                if prediction_data:
                    prediction = json.loads(prediction_data)
                    print(f"Predicción recibida para {filename}: {prediction}")
            else:
                print(f"No se recibió predicción para {filename} a tiempo.")

        print("Todas las imágenes fueron enviadas y sus predicciones recibidas.")

    except ConnectionResetError:
        print("El servidor cerró la conexión inesperadamente.")
    except BrokenPipeError:
        print("El servidor cerró la conexión antes de completar el envío.")
    except Exception as e:
        print(f"Error inesperado: {e}")
    finally:
        if client.fileno() != -1: 
            client.close()

    return user_id, list(tasks.keys())  # lista de task_ids


def wait_for_prediction(user_id, timeout=10):
    """Escucha en Redis hasta recibir la predicción o que pase el timeout."""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        pubsub = r.pubsub()
        channel = f"resultados:{user_id}"
        pubsub.subscribe(channel)
        print(f"Esperando resultado en {channel} (máximo {timeout}s)...")

        for message in pubsub.listen():
            if message["type"] == "message":
                result_data = json.loads(message["data"])
                print(f"Predicción recibida: {result_data}")
                break
    except Exception as e:
        print(f"Error al escuchar en Redis: {e}")

def get_history(user_id):
    """Consulta el historial de predicciones de un usuario."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((HOST, PORT))
            request = json.dumps({"action": "get_history", "user_id": user_id}).encode()
            client.sendall(len(request).to_bytes(4, "big"))
            client.sendall(request)
            response_data = client.recv(BUFFER_SIZE).decode()
            if response_data:
                response = json.loads(response_data)
                print("Historial de predicciones:")
                for entry in response.get("historial", []):
                    print(f"Imagen ID: {entry['image_id']}, Resultado: {entry['result']}, Confianza: {entry['confidence']}%")
            else:
                print("No se recibió respuesta del servidor.")
    except Exception as e:
        print(f"Error al obtener el historial: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente para enviar imágenes o consultar historial de predicciones")
    parser.add_argument("--images", nargs='+', help="Lista de imágenes a enviar")
    parser.add_argument("--historial", type=int, help="Consultar historial de predicciones de un usuario")
    parser.add_argument("--host", type=str, default=None, help="Dirección del servidor (IPv4 o IPv6)")
    parser.add_argument("--port", type=int, default=None, help="Puerto del servidor")

    args = parser.parse_args()

    if args.historial:
        get_history(args.historial)
    elif args.images:
        user_id, task_ids = send_images(args.images, args.host, args.port)
        print(f"\nUsuario: {user_id}")
        print(f"Tareas creadas: {task_ids if task_ids else 'Ninguna'}")
    else:
        print("Debe especificar --images para enviar imágenes o --historial para ver historial.")
