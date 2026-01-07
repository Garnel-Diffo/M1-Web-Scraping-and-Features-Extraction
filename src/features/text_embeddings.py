import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import numpy as np
from datetime import datetime
import tensorflow_hub as hub
from src.features.embeddings_store import get_db, l2_normalize, save_embedding


def load_use():
    return hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")


def build_text_embeddings(mongo_uri=None, db_name='SmartSearch', batch_size=64):
    db = get_db(uri=mongo_uri or "mongodb://localhost:27017/", db_name=db_name)
    produits = list(db['produits'].find())
    if not produits:
        print('Aucun produit trouvé dans produits.')
        return

    model = load_use()
    coll_out = db['embeddings_text']

    texts = []
    ids = []
    for p in produits:
        pid = p.get('url') or p.get('_id')
        name = p.get('nom', '') or ''
        desc = p.get('description', '') or ''
        txt = (name + '\n' + desc).strip()
        texts.append(txt)
        ids.append(pid)

    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        emb = model(batch_texts).numpy()
        for j, vec in enumerate(emb):
            pid = ids[i+j]
            vecn = l2_normalize(vec)
            save_embedding(coll_out, str(pid), vecn, model='USE-4')
        print(f'Processed batch {i//batch_size + 1} / {((len(texts)-1)//batch_size)+1}')


if __name__ == '__main__':
    build_text_embeddings()
