from pathlib import Path
import numpy as np
from pymongo import MongoClient
from datetime import datetime


def get_db(uri="mongodb://localhost:27017/", db_name="SmartSearch"):
    client = MongoClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
    return client[db_name]


def l2_normalize(vec: np.ndarray) -> np.ndarray:
    vec = np.array(vec, dtype=float)
    n = np.linalg.norm(vec)
    if n == 0:
        return vec
    return vec / n


def save_embedding(collection, product_id: str, vector: np.ndarray, model: str, extra: dict = None):
    doc = {
        'product_id': product_id,
        'vector': vector.astype(float).tolist(),
        'model': model,
        'created_at': datetime.utcnow(),
    }
    if extra:
        doc.update(extra)
    collection.replace_one({'product_id': product_id}, doc, upsert=True)
