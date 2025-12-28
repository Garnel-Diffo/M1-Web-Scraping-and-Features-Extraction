
# Module 1 (M1) – Collecte automatisée des données & Feature Extraction
## Projet Smart Search – Recherche multimodale (Texte + Image)

---

## 1. Présentation générale

Le **Module 1 (M1)** est responsable de la **chaîne amont du pipeline Smart Search**.  
Il couvre deux volets fondamentaux du projet :

1. **Collecte automatisée des données (Web Scraping)**  
2. **Extraction des caractéristiques (Feature Extraction) textuelles et visuelles**

Les données produites par ce module sont utilisées par le **Module 2 (M2)** pour la construction de l’index FAISS et le calcul de similarité, puis par le **Module 3 (M3)** pour l’interface utilisateur et l’expérience de recherche.

Ce module est conçu pour être :
- reproductible,
- scalable,
- conforme aux bonnes pratiques de scraping,
- facilement containerisable (Docker),
- compatible CPU/GPU.

---

## 2. Objectifs du Module 1

### 2.1 Collecte automatisée (Web Scraping)

- Scraper automatiquement les données produits depuis une plateforme de vente en ligne.
- Extraire les champs suivants :
  - Identifiant produit
  - Nom du produit
  - Description textuelle
  - Prix
  - Réduction (le cas échéant)
  - Catégorie
  - sous-catégorie
  - Note / popularité (si disponible)
  - URL de l’image principale
- Télécharger et stocker les images localement.
- Nettoyer, valider et structurer les données.
- Stocker les données dans **MongoDB** et en **CSV**.

### 2.2 Feature Extraction (Textuelle & Visuelle)

- Générer des **représentations vectorielles normalisées** pour chaque produit :
  - **Texte** : Universal Sentence Encoder (512 dimensions)
  - **Image** : Xception avec projection vers 4096 dimensions
- Appliquer une **normalisation L2** systématique.
- Préparer les vecteurs pour une indexation FAISS (cosine similarity).
- Sauvegarder les embeddings et métadonnées dans MongoDB.

---

## 3. Architecture globale du Module 1

```
Scraping (Selenium)
        ↓
Validation & Nettoyage
        ↓
Stockage (MongoDB + CSV + Images locales)
        ↓
Feature Extraction (USE + Xception)
        ↓
Normalisation L2
        ↓
Préparation FAISS (Index prêt pour M2)
```

---

## 4. Stack technologique

### Langage
- Python 3.10

### Scraping
- Selenium (Chrome headless)
- BeautifulSoup (parsing HTML)
- Requests (téléchargement images)

### Stockage
- MongoDB
- CSV (export complémentaire)

### Feature Extraction
- TensorFlow
- TensorFlow Hub (Universal Sentence Encoder)
- Keras Applications (Xception)

### Recherche vectorielle
- FAISS (CPU ou GPU)

### Environnement & orchestration
- Anaconda (conda)
- Docker / Docker Compose
- Airflow (optionnel, recommandé)

### Prérequis - Installations

#### Git
```bash
git --version
```

#### Anaconda / Miniconda
- https://www.anaconda.com/products/distribution
- Vérification :
```bash
conda --version
```

#### Google Chrome + ChromeDriver
- Chrome : https://www.google.com/chrome/
- ChromeDriver : https://chromedriver.chromium.org/downloads
- Ajouter `chromedriver` au PATH système

#### MongoDB (local)
- https://www.mongodb.com/try/download/community
- Lancer le service MongoDB
```bash
mongod
```
- Vérification :
```bash
mongosh
```

*(Alternative simple via Docker si MongoDB local non disponible)*
```bash
docker run -d -p 27017:27017 --name mongo mongo:6
```

---

## 5. Arborescence du projet

```
smartsearch-m1/
├── environment.yml
├── Dockerfile
├── README.md
├── src/
│   ├── scraping/
│   │   ├── selenium_scraper.py
│   │   ├── parsers/
│   │   └── utils_download.py
│   ├── images/
│   │   ├── validate_images.py
│   │   └── img_utils.py
│   ├── features/
│   │   ├── text_embeddings.py
│   │   ├── visual_embeddings.py
│   │   └── embeddings_store.py
│   ├── faiss/
│   │   └── build_index.py
│   └── config.py
├── dataset/
│   └── images/
│       └── id_<product_id>.jpg
├── tests/
└── dags/
```

---

## 6. Environnement Anaconda

Création de l’environnement :

```bash
conda env create -f environment.yml
conda activate smartsearch
```

Principales dépendances :
- selenium
- pymongo
- tensorflow
- tensorflow-hub
- faiss-cpu / faiss-gpu
- pillow
- opencv-python
- apache-airflow (optionnel)

---

## 7. Collecte automatisée des données (Scraping)

### 7.1 Règles et bonnes pratiques

- Respect strict du `robots.txt`
- User-Agent explicite
- Rate limiting et backoff exponentiel
- Logs détaillés (succès / échec)
- Pas de contournement illégal de captcha
- Parsers robustes et modulaires

### 7.2 Processus de scraping

1. Chargement de la page via Selenium
2. Parsing du DOM avec BeautifulSoup
3. Extraction des champs requis
4. Téléchargement de l’image produit
5. Stockage MongoDB + CSV
6. Log du statut du produit

---

## 8. Gestion et validation des images

Les images sont stockées localement dans :

```
dataset/images/id_<product_id>.jpg
```

### Validations appliquées :
- Format valide (JPEG / PNG)
- Taille minimale (ex : ≥ 200×200 px)
- Image non corrompue
- Suppression ou marquage des images invalides en base

---

## 9. Feature Extraction – Texte

### Modèle utilisé
- **Universal Sentence Encoder (USE)**

### Détails techniques
- Entrée : concaténation `nom + description`
- Dimension : **512**
- Normalisation : **L2**

### Stockage
- Collection MongoDB : `embeddings_text`
- Métadonnées : modèle, date, norme L2

---

## 10. Feature Extraction – Image

### Modèle utilisé
- **Xception (ImageNet)**
- Couche de projection vers **4096 dimensions**

### Processus
1. Chargement et prétraitement de l’image
2. Extraction des features via Xception
3. Projection Dense → 4096 dimensions
4. Normalisation L2

### Stockage
- Collection MongoDB : `embeddings_image`

---

## 11. Normalisation et Similarité

- Tous les vecteurs sont normalisés L2
- Similarité cosinus utilisée via FAISS
- Index recommandé :
  - `IndexFlatIP` (Inner Product)

---

## 12. MongoDB – Schéma de données

### Collections principales
- `products`
- `embeddings_text`
- `embeddings_image`
- `scrape_logs`

Chaque embedding est lié à un `product_id`.

### Exemple de document `products`
```json
{
  "product_id": "string",
  "name": "string",
  "description": "string",
  "price": number,
  "discount": number,
  "category": "string",
  "subcategory": "string",
  "rating": number,
  "image_url": "string",
  "image_local_path": "/dataset/images/id_<product_id>.jpg",
  "source_url": "string",
  "scraped_at": "ISODate",
  "status": "valid | invalid_image | incomplete"
}

```

---

## 13. Préparation FAISS

Le module fournit un script de construction d’index FAISS :

- Chargement des embeddings depuis MongoDB
- Construction de l’index
- Sauvegarde sur disque
- Export mapping `index_id ↔ product_id`

Ces fichiers sont consommés directement par le Module 2.

---

## 14. Orchestration (optionnelle)

- Airflow recommandé pour :
  - Scraping planifié
  - Validation images
  - Extraction des features
  - Reconstruction périodique de l’index FAISS

---

## 15. Tests et qualité

- Tests unitaires (parsers, embeddings)
- Tests d’intégration (pipeline complet)
- Vérification :
  - dimensions des embeddings
  - norme L2 ≈ 1
  - cohérence produit ↔ image ↔ embedding

---

## 16. Dockerisation

Module prêt pour être containerisé :

- Image scraping (CPU)
- Image feature extraction (GPU possible)
- Volumes montés pour :
  - dataset
  - modèles
  - index FAISS

---

## 17. Livrables du Module 1

- Scripts de scraping robustes
- Base MongoDB structurée
- Dataset d’images validées
- Embeddings texte (512D) et image (4096D)
- Index FAISS prêt pour M2
- Documentation complète
- Environnement reproductible

---

## 18. Responsabilités

Le Module 1 garantit que **les données fournies au moteur de recherche sont propres, normalisées, exploitables et conformes aux exigences du projet**.

Tout le pipeline Smart Search repose sur la qualité et la rigueur de ce module.

---
