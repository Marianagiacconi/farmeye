from celery import shared_task
import time
import random
from collections import Counter
from contextlib import contextmanager
from utils.database import SessionLocal
from server.models import Prediction, Image
import logging
from tasks.celery_config import celery
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@celery.task
def process_image_task(image_path: str, user_id: str):
    """Simula el procesamiento de imágenes."""
    num_repeats = 5
    labels = {0: "Sano", 1: "Posible Enfermedad", 2: "Enfermo"}
    results = []

    for _ in range(num_repeats):
        time.sleep(1)  # Simula procesamiento
        prediction = random.choice([0, 1, 2])
        results.append(prediction)

    final_prediction = Counter(results).most_common(1)[0][0]
    result = {
        "user_id": user_id,
        "image": image_path,
        "final_result": labels[final_prediction],
        "details": results
    }

    with get_db_session() as db:
        try:
            image = db.query(Image).filter_by(image_path=image_path).first()
            if image:
                new_prediction = Prediction(image_id=image.id, result=labels[final_prediction], confidence=90)
                db.add(new_prediction)
                db.commit()
            else:
                logger.error(f"No se encontró la imagen en la base de datos: {image_path}")
        except Exception as e:
            logger.error(f"Ocurrió un error al guardar la predicción: {e}")

    return result
