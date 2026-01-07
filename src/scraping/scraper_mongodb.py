from pathlib import Path
import os
import time
import requests
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
from pymongo import MongoClient
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATASET_IMG = ROOT / "dataset" / "ImagesTech"
DATASET_IMG.mkdir(parents=True, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def get_db(uri="mongodb://localhost:27017/", db_name="SmartSearch"):
    client = MongoClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
    db = client[db_name]
    return db


def save_image(src_url, product_url):
    p_url = urlparse(urljoin(product_url, src_url))
    enc_url = f"{p_url.scheme}://{p_url.netloc}{quote(p_url.path)}"
    fname = os.path.basename(p_url.path).replace('\u2011', '-')
    fname = fname.encode('ascii', 'ignore').decode('ascii')
    out_path = DATASET_IMG / fname
    try:
        r_img = requests.get(enc_url, headers=HEADERS, timeout=10)
        r_img.raise_for_status()
        with open(out_path, 'wb') as f:
            f.write(r_img.content)
        return str(out_path.relative_to(ROOT))
    except Exception:
        return None


def scrape_site(url_base, max_pages=50, mongo_uri=None, db_name='SmartSearch'):
    db = get_db(uri=mongo_uri or "mongodb://localhost:27017/", db_name=db_name)
    produits_col = db['produits']
    produits_col.create_index('url', unique=True)

    page = 1
    while page <= max_pages:
        url_page = f"{url_base}page/{page}/"
        print(f"\n==> Page {page} --> {url_page}")
        try:
            response = requests.get(url_page, headers=HEADERS, timeout=15)
            if response.status_code not in [200, 301, 302]:
                print(f"Erreur d'accès : {response.status_code}")
                break
        except Exception as e:
            print(f"Erreur requête page: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        links = list(dict.fromkeys([a.get("href") for a in soup.select("a.woocommerce-LoopProduct-link") if a.get('href')]))
        print(f"Nombre de produits trouvés sur cette page : {len(links)}")
        if not links:
            print("Aucun lien trouvé — arrêt.")
            break

        for product_url in links:
            if produits_col.find_one({"url": product_url}):
                print(f"Déjà en base : {product_url}")
                continue

            print(f"Extraction : {product_url}")
            try:
                prod_resp = requests.get(product_url, headers=HEADERS, timeout=15)
                ps = BeautifulSoup(prod_resp.text, "html.parser")

                nom = ps.find('h1').get_text(strip=True) if ps.find('h1') else "Inconnu"
                prix_avant = ps.find("del").find("bdi").get_text(strip=True) if ps.find("del") else None
                p_ins = ps.find("ins")
                if p_ins:
                    prix_apres = p_ins.find("bdi").get_text(strip=True)
                else:
                    p_tag = ps.find("p", class_="price")
                    prix_apres = p_tag.find("bdi").get_text(strip=True) if p_tag and p_tag.find("bdi") else None

                reduction = ps.find("span", class_="onsale").get_text(strip=True) if ps.find("span", class_="onsale") else None

                meta = ps.find('div', class_='product_meta')
                categorie = None
                if meta:
                    posted_in = meta.find('span', class_='posted_in')
                    if posted_in and posted_in.find('a'):
                        categorie = posted_in.find('a').get_text(strip=True)

                bread = ps.find("nav", class_="woocommerce-breadcrumb")
                sous_categorie = None
                if bread:
                    links_b = bread.find_all("a")
                    if len(links_b) > 0:
                        dernier_lien = links_b[-1].get_text(strip=True)
                        if dernier_lien.lower() not in ['accueil', 'home', 'boutique', 'shop']:
                            sous_categorie = dernier_lien

                description = ps.find("div", class_="electro-description").get_text(strip=True) if ps.find("div", class_="electro-description") else None

                imgs = ps.select(".woocommerce-product-gallery__wrapper img")
                img_files = []
                seen = set()
                for img in imgs:
                    src = img.get('src')
                    if not src or src in seen:
                        continue
                    seen.add(src)
                    saved = save_image(src, product_url)
                    if saved:
                        img_files.append(saved)

                nouveau_produit = {
                    "nom": nom,
                    "url": product_url,
                    "prix_avant": prix_avant,
                    "prix_apres": prix_apres,
                    "reduction": reduction,
                    "categorie": categorie,
                    "sous_categorie": sous_categorie,
                    "description": description,
                    "images": img_files,
                    "date_scraping": time.strftime("%d-%m-%Y")
                }

                produits_col.insert_one(nouveau_produit)
                print(f"Sauvegardé dans MongoDB : {nom}")
            except Exception as e:
                print(f"Erreur produit : {e}")
                time.sleep(2)

        page += 1


def export_csv(db_name='SmartSearch', mongo_uri=None, out_file='newtech_mongodb_final.csv'):
    db = get_db(uri=mongo_uri or "mongodb://localhost:27017/", db_name=db_name)
    produits_col = db['produits']
    data = list(produits_col.find())
    if not data:
        print("Aucun produit trouvé pour export CSV.")
        return
    df = pd.DataFrame(data)
    if '_id' in df.columns:
        df = df.drop(columns=['_id'])
    out_path = Path(out_file)
    df.to_csv(out_path, index=False)
    print(f"CSV exporté : {out_path}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='https://nowtechcenter.com/boutique/', help='Base shop url')
    parser.add_argument('--pages', type=int, default=150)
    parser.add_argument('--db', default='SmartSearch')
    args = parser.parse_args()
    scrape_site(args.base, max_pages=args.pages, db_name=args.db)
    export_csv(db_name=args.db)
