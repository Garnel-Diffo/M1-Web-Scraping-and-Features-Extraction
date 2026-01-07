import ast
from pathlib import Path
from pymongo import MongoClient
import csv


ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / 'src' / 'scraping' / 'newtech_mongodb_final.csv'
IMG_DIR = ROOT / 'dataset' / 'ImagesTech'


def get_db(uri='mongodb://localhost:27017/', db_name='SmartSearch'):
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return client[db_name]


def parse_images_field(val):
    # CSV stores images as Python list string like "['a.jpg', 'b.jpg']"
    try:
        imgs = ast.literal_eval(val)
        if isinstance(imgs, list):
            return [str(x) for x in imgs]
    except Exception:
        pass
    return []


def main():
    db = get_db()
    produits = db['produits']
    updated = 0
    missing = 0
    if not CSV_PATH.exists():
        print('CSV not found:', CSV_PATH)
        return

    # Build fast lookup of available image filenames
    available = {p.name for p in IMG_DIR.iterdir()}

    from pymongo import UpdateOne
    batch_ops = []
    BATCH_SIZE = 500
    with open(CSV_PATH, newline='', encoding='utf8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            url = row.get('url')
            imgs_raw = row.get('images')
            if not url or not imgs_raw:
                continue
            imgs = parse_images_field(imgs_raw)
            rel_paths = []
            for name in imgs:
                if name in available:
                    p = IMG_DIR / name
                    rel_paths.append(str(p.relative_to(ROOT)))
                else:
                    missing += 1

            if rel_paths:
                batch_ops.append(UpdateOne({'url': url}, {'$set': {'images': rel_paths}}))

            if i % BATCH_SIZE == 0:
                if batch_ops:
                    try:
                        res = produits.bulk_write(batch_ops, ordered=False)
                        updated += res.matched_count
                    except Exception as e:
                        print('Bulk write error:', e)
                    batch_ops = []
                print(f'Processed rows: {i} -- updated: {updated} -- missing images so far: {missing}')

    # flush remaining
    if batch_ops:
        try:
            res = produits.bulk_write(batch_ops, ordered=False)
            updated += res.matched_count
        except Exception as e:
            print('Final bulk write error:', e)

    print(f'Finished. Updated products: {updated}, missing image files: {missing}')

    print(f'Updated products: {updated}, missing image files: {missing}')


if __name__ == '__main__':
    main()
