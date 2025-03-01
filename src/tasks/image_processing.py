import json
from celery import shared_task
import time
import random
from collections import Counter
from contextlib import contextmanager
from utils.database import SessionLocal
from server.models import Prediction, Image
import logging
import redis
from tasks.celery_config import celery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Redis
REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379
REDIS_CHANNEL = "resultados"

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@celery.task
def process_image_task(image_path: str, client_ip: str):
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
        "client_ip": client_ip
    }

    with get_db_session() as db:
        try:
            image = db.query(Image).filter_by(image_path=image_path).first()
            if image:
                new_prediction = Prediction(
                    image_id=image.id, 
                    result=labels[final_prediction], 
                    confidence=round(confidence, 2)
                )
                db.add(new_prediction)
                db.commit()
                logger.info(f"Predicción guardada en la BD: {new_prediction.result} ({new_prediction.confidence}%)")
            else:
                logger.error(f"⚠️ No se encontró la imagen en la BD: {image_path}. Asegúrate de guardarla antes de procesarla.")
        except Exception as e:
            logger.error(f"Error al guardar la predicción: {e}")

    # Publicar el resultado en un canal único para cada cliente
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        client_channel = f"resultados:{client_ip}"  # Canal específico del cliente
        r.publish(client_channel, json.dumps(result))
        logger.info(f"Resultado publicado en Redis en {client_channel}: {result}")
    except Exception as e:
        logger.error(f"No se pudo publicar el resultado en Redis: {e}")
    
    