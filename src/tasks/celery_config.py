from celery import Celery
import logging
import redis
from redis.exceptions import ConnectionError
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_redis(max_retries=5, retry_delay=2):
    """Espera hasta que Redis esté disponible"""
    for attempt in range(max_retries):
        try:
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            redis_client.ping()
            logger.info("Conexión exitosa con Redis")
            return True
        except ConnectionError as e:
            logger.warning(f"Intento {attempt + 1}/{max_retries}: No se puede conectar a Redis. Reintentando en {retry_delay} segundos...")
            time.sleep(retry_delay)
    return False
if not wait_for_redis():
    logger.error("No se pudo establecer conexión con Redis después de varios intentos")
    raise ConnectionError("No se pudo conectar a Redis")

# Configuración de Celery
celery = Celery(
    'tasks',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['tasks.image_processing']
)

# Configuración específica
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    broker_connection_timeout=5
)
