import socket
import threading
import json
import os

HOST = '0.0.0.0'  
PORT = 5000  
IMAGE_FOLDER = "src/server/uploads/"
BUFFER_SIZE = 65536  # Aumentamos el buffer a 64KB

def handle_client(conn, addr):
    """Maneja la conexión con un cliente."""
    print(f"Conectado con {addr}")

    try:
        # Recibir tamaño del JSON primero
        metadata_size = int.from_bytes(conn.recv(4), "big")
        metadata = json.loads(conn.recv(metadata_size).decode())

        user_id = metadata["user_id"]
        filename = metadata["image_name"]
        file_size = metadata["file_size"]

        print(f"[DEBUG] Recibiendo imagen {filename} de {file_size} bytes...")

        os.makedirs(IMAGE_FOLDER, exist_ok=True)
        image_path = os.path.join(IMAGE_FOLDER, filename)

        received_size = 0
        with open(image_path, "wb") as f:
            while received_size < file_size:
                chunk = conn.recv(BUFFER_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                received_size += len(chunk)
                conn.sendall(b"ACK")  # Confirmación de recepción

        print(f"Imagen {filename} guardada en {image_path}")

        response = {"status": "OK", "image_path": image_path}
        conn.send(json.dumps(response).encode())

    except Exception as e:
        print(f"[-] Error en handle_client: {str(e)}")
        conn.send(json.dumps({"error": str(e)}).encode())

    finally:
        conn.close()

def start_server():
    """Inicia el servidor TCP y maneja múltiples clientes con threads."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Servidor TCP en {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()
