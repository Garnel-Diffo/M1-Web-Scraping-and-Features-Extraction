from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PY = 'python'

default_args = {
    'owner': 'smartsearch',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='smartsearch_scraping_and_features',
    default_args=default_args,
    description='Scrape site, extract text and image features, build FAISS index',
    schedule_interval='@daily',
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:

    scrape = BashOperator(
        task_id='scrape_site',
        bash_command=f"{PY} {ROOT}/src/scraping/scraper_mongodb.py --pages 50",
    )

    text_emb = BashOperator(
        task_id='text_embeddings',
        bash_command=f"{PY} {ROOT}/src/features/text_embeddings.py",
    )

    visual_emb = BashOperator(
        task_id='visual_embeddings',
        bash_command=f"{PY} {ROOT}/src/features/visual_embeddings.py",
    )

    build_faiss = BashOperator(
        task_id='build_faiss',
        bash_command=f"{PY} {ROOT}/src/faiss/build_index.py",
    )

    scrape >> text_emb >> visual_emb >> build_faiss
