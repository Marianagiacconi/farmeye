import random
import socket
import json
import argparse
import os

HOST = "127.0.0.1"
PORT = 5000
BUFFER_SIZE = 65536  

def send_images(image_paths):
    user_id = random.randint(1, 2**31 - 1)
    tasks = []  # Lista para almacenar los task_id recibidos

    for image_path in image_paths:
        if not os.path.exists(image_path):
            print(f"La imagen {image_path} no existe.")
            continue

        file_size = os.path.getsize(image_path)

        # Resolver dirección para IPv4/IPv6
        try:
            family, type_, proto, canonname, sockaddr = socket.getaddrinfo(
                HOST, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM
            )[0]
        except Exception as e:
            print(f"Error resolviendo la dirección: {e}")
            continue

        with socket.socket(family, type_, proto) as client:
            try:
                client.connect(sockaddr)

                filename = os.path.basename(image_path)
                metadata = json.dumps({
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
                        client.sendall(chunk)
                        ack = client.recv(3)  # Esperar confirmación del servidor
                        if ack != b"ACK":
                            raise Exception("⚠️ No se recibió ACK correctamente.")

                # Recibir respuesta inicial del servidor
                response_data = client.recv(BUFFER_SIZE).decode()
                if not response_data:
                    raise Exception("⚠️ No se recibió respuesta del servidor.")

                response = json.loads(response_data)

                if "task_id" in response:
                    print(f"Imagen {filename} enviada correctamente. Task ID: {response['task_id']}")
                    tasks.append(response["task_id"])
                    
                    # Esperar resultado final del procesamiento
                    print(f"Esperando resultado final para la tarea {response['task_id']}...")
                    final_response_data = client.recv(BUFFER_SIZE).decode()
                    if not final_response_data:
                        raise Exception("⚠️ No se recibió resultado final del servidor.")

                    final_response = json.loads(final_response_data)
                    print(f"Resultado final recibido: {final_response}")

                else:
                    print(f"⚠️ Error en respuesta del servidor: {response}")

            except ConnectionRefusedError:
                print("No se pudo conectar con el servidor. Asegúrate de que está en ejecución.")
            except json.JSONDecodeError:
                print("Error al decodificar la respuesta del servidor.")
            except Exception as e:
                print(f"Error inesperado: {e}")

    return user_id, tasks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente para enviar imágenes")
    parser.add_argument("--images", nargs='+', required=True, help="Lista de imágenes a enviar")
    args = parser.parse_args()

    user_id, task_ids = send_images(args.images)
    print(f"\nUsuario: {user_id}")
    print(f"Tareas creadas: {task_ids if task_ids else 'Ninguna'}")
