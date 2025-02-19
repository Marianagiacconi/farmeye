import socket
import json
import argparse
import os
import uuid

HOST = "127.0.0.1"
PORT = 5000
BUFFER_SIZE = 65536  

def send_images(image_paths):
    user_id = str(uuid.uuid4())  
    tasks = []

    for image_path in image_paths:
        if not os.path.exists(image_path):
            print(f"La imagen {image_path} no existe.")
            continue

        file_size = os.path.getsize(image_path)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((HOST, PORT))

            filename = os.path.basename(image_path)
            metadata = json.dumps({"user_id": user_id, "image_name": filename, "file_size": file_size})
            metadata_bytes = metadata.encode()

            print(f"[DEBUG] Enviando metadata ({len(metadata_bytes)} bytes)")
            client.send(len(metadata_bytes).to_bytes(4, "big"))
            client.send(metadata_bytes)

            print(f"[DEBUG] Enviando imagen {filename} ({file_size} bytes)...")
            with open(image_path, "rb") as f:
                while chunk := f.read(BUFFER_SIZE):
                    client.send(chunk)
                    client.recv(3)  # Esperar confirmación de recepción

            response = json.loads(client.recv(BUFFER_SIZE).decode())

            if "status" in response and response["status"] == "OK":
                print(f"Imagen {filename} enviada correctamente.")
            else:
                print(f"Error en respuesta del servidor: {response}")

    return user_id, tasks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente para enviar imágenes")
    parser.add_argument("--images", nargs='+', required=True, help="Lista de imágenes a enviar")
    args = parser.parse_args()

    user_id, task_ids = send_images(args.images)
    print(f"\nImágenes enviadas para usuario {user_id}")
    print(f"Tareas creadas: {task_ids}")
