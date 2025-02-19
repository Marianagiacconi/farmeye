import time
import random
from collections import Counter
from src.tasks.celery_config import celery
from src.utils.database import SessionLocal
from src.server.models import Prediction, Image

@celery.task
def process_image_task(image_path: str, user_id: str, num_repeats=5):
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

    # Guarda en la BD
    db = SessionLocal()
    image = db.query(Image).filter_by(image_path=image_path).first()
    new_prediction = Prediction(image_id=image.id, result=labels[final_prediction], confidence=90)
    db.add(new_prediction)
    db.commit()
    db.close()

    return result
