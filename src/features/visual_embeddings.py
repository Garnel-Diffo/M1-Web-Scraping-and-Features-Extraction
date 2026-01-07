import numpy as np
from pathlib import Path
from PIL import Image
import tensorflow as tf
from tensorflow.keras.applications.xception import Xception, preprocess_input
from tensorflow.keras.layers import Dense
from features.embeddings_store import get_db, l2_normalize, save_embedding


ROOT = Path(__file__).resolve().parents[2]
IMG_ROOT = ROOT / 'dataset'


def load_models():
    base = Xception(include_top=False, pooling='avg', weights='imagenet')
    proj = tf.keras.Sequential([Dense(4096, activation=None, input_shape=(base.output_shape[1],))])
    return base, proj


def image_to_array(path: Path):
    img = Image.open(path).convert('RGB')
    img = img.resize((299, 299))
    arr = np.array(img)
    arr = preprocess_input(arr.astype('float32'))
    return arr


def build_visual_embeddings(mongo_uri=None, db_name='SmartSearch', batch_size=16):
    db = get_db(uri=mongo_uri or "mongodb://localhost:27017/", db_name=db_name)
    produits = list(db['produits'].find())
    if not produits:
        print('Aucun produit trouvé dans produits.')
        return

    base, proj = load_models()
    coll_out = db['embeddings_image']

    imgs = []
    ids = []
    for p in produits:
        pid = p.get('url') or p.get('_id')
        images = p.get('images') or []
        if not images:
            continue
        # Use first available image
        first = images[0]
        img_path = ROOT / first if not Path(first).is_absolute() else Path(first)
        if not img_path.exists():
            # try relative to project root dataset
            img_path = IMG_ROOT / first
            if not img_path.exists():
                continue
        ids.append(str(pid))
        imgs.append(img_path)

    for i in range(0, len(imgs), batch_size):
        batch_paths = imgs[i:i+batch_size]
        arrs = np.stack([image_to_array(p) for p in batch_paths])
        feats = base.predict(arrs, verbose=0)
        proj_feats = proj.predict(feats)
        for j, vec in enumerate(proj_feats):
            pid = ids[i+j]
            vecn = l2_normalize(vec)
            save_embedding(coll_out, pid, vecn, model='Xception-4096')
        print(f'Processed image batch {i//batch_size + 1} / {((len(imgs)-1)//batch_size)+1}')


if __name__ == '__main__':
    build_visual_embeddings()
