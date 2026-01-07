import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import faiss
import numpy as np
import json
from src.features.embeddings_store import get_db


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / 'faiss'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Workaround for Windows path encoding issues with special characters
# Use a temp location if needed, then move
import tempfile
import shutil
TEMP_DIR = Path(tempfile.gettempdir()) / 'faiss_build'
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def build_index(collection_name='embeddings_text', index_name='text'):
    db = get_db()
    coll = db[collection_name]
    docs = list(coll.find())
    if not docs:
        print(f'No docs in {collection_name}')
        return

    vectors = np.array([d['vector'] for d in docs], dtype='float32')
    # Ensure normalized
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    vectors = vectors / norms

    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    # Use temp directory for FAISS write due to path encoding issues on Windows
    temp_index_path = TEMP_DIR / f'{index_name}.index'
    faiss.write_index(index, str(temp_index_path))
    
    # Move to final location
    final_index_path = OUT_DIR / f'{index_name}.index'
    shutil.copy(str(temp_index_path), str(final_index_path))
    
    mapping = {i: str(docs[i].get('product_id') or docs[i].get('product_id') or docs[i].get('product_id')) for i in range(len(docs))}
    with open(OUT_DIR / f'{index_name}_mapping.json', 'w', encoding='utf8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f'Built index {final_index_path} with {len(docs)} vectors (dim={dim})')


if __name__ == '__main__':
    build_index('embeddings_text', 'text')
    build_index('embeddings_image', 'image')
