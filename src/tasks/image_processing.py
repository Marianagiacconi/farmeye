import json
import os
import time
import random
from collections import Counter
import logging
from dotenv import load_dotenv
import redis
from tasks.celery_config import celery

# Cargar variables desde el .env
load_dotenv()

# Configuración de Redis desde .env
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_HOST = REDIS_URL.split("//")[-1].split(":")[0]
REDIS_PORT = int(REDIS_URL.split(":")[-1].split("/")[0])
REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "resultados")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery.task
def process_image_task(image_path: str, user_id: int):
    """Simula el procesamiento de imágenes y publica el resultado en Redis."""
    num_repeats = 5
    labels = {0: "Sano", 1: "Posible Enfermedad", 2: "Enfermo"}
    results = []

    for _ in range(num_repeats):
        time.sleep(1)  # Simula procesamiento
        prediction = random.choice([0, 1, 2])
        results.append(prediction)

    # Determinar la predicción final y su confianza
    final_prediction, count = Counter(results).most_common(1)[0]
    confidence = (count / num_repeats) * 100
    result = {
        "image": image_path,
        "final_result": labels[final_prediction],
        "confidence": round(confidence, 2),
        "details": results,
        "user_id": user_id
    }

    # Publicar el resultado en un canal único para cada usuario
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        user_channel = f"resultados:{user_id}"  # Canal basado en user_id
        r.publish(user_channel, json.dumps(result))
        logger.info(f"Resultado publicado en Redis en {user_channel}: {result}")
    except Exception as e:
        logger.error(f"No se pudo publicar el resultado en Redis: {e}")
