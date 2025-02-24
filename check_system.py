import redis
import socket
import logging
from celery import Celery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_redis():
    try:
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        logger.info("Redis está funcionando")
        return True
    except Exception as e:
        logger.error(f"Error en Redis: {e}")
        return False

def check_server(host='127.0.0.1', port=5000):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
        logger.info("Servidor está funcionando")
        return True
    except Exception as e:
        logger.error(f" Error en servidor: {e}")
        return False

def check_celery():
    try:
        app = Celery('tasks', broker='redis://localhost:6379/0')
        with app.connection() as conn:
            conn.ensure_connection(max_retries=3)
        logger.info("Celery está funcionando")
        return True
    except Exception as e:
        logger.error(f"Error en Celery: {e}")
        return False

if __name__ == "__main__":
    print("Verificando sistema...")
    redis_ok = check_redis()
    server_ok = check_server()
    celery_ok = check_celery()
    
    if all([redis_ok, server_ok, celery_ok]):
        print("Todo el sistema está funcionando correctamente")
    else:
        print("Hay problemas en el sistema")
