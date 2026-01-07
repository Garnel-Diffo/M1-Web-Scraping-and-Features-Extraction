import csv, ast
from pathlib import Path
from pymongo import MongoClient

ROOT = Path.cwd()
CSV = ROOT / 'src' / 'scraping' / 'newtech_mongodb_final.csv'

with open(CSV, encoding='utf8') as f:
    r = csv.DictReader(f)
    row = next(r)
    url = row['url']
    imgs = ast.literal_eval(row['images'])
    print('url:', url)
    print('imgs sample:', imgs[:3])
    db = MongoClient('mongodb://localhost:27017/')['SmartSearch']
    res = db['produits'].update_one({'url': url}, {'$set': {'images': ['dataset/ImagesTech/' + imgs[0]]}})
    print('matched_count', res.matched_count, 'modified_count', res.modified_count)
