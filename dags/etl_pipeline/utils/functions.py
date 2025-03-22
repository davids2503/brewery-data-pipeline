import os
import json
import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests
import traceback
from io import BytesIO
from datetime import datetime

# -------------------------------
# 🔐 Verificação das variáveis de ambiente
# -------------------------------

required_envs = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "S3_BUCKET_NAME"]
missing_envs = [var for var in required_envs if not os.getenv(var)]

if missing_envs:
    raise EnvironmentError(f"❌ Variáveis de ambiente ausentes: {', '.join(missing_envs)}")

# ENV VARS
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

# S3 client
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# -------------------------------
# 🥉 BRONZE
# -------------------------------

def fetch_brewery_data():
    all_data = []
    page = 1
    per_page = 100

    while True:
        url = f"https://api.openbrewerydb.org/breweries?page={page}&per_page={per_page}"
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f"Erro na requisição: {response.status_code}")

        page_data = response.json()
        if not page_data:
            break

        all_data.extend(page_data)
        page += 1

    return all_data

def save_bronze_to_s3(data):
    today = datetime.today().strftime("%Y-%m-%d")
    key = f"bronze/breweries_raw_{today}.json"

    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=json.dumps(data)
    )

    print(f"✅ Bronze salvo: s3://{S3_BUCKET_NAME}/{key}")
    log_success("bronze_step", f"Bronze layer salva com {len(data)} registros.")
    return key

# -------------------------------
# 🥈 SILVER
# -------------------------------

def transform_bronze_to_silver(bronze_key):
    response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=bronze_key)
    raw_data = response['Body'].read().decode('utf-8')
    df = pd.read_json(raw_data)

    # Limpeza e padronização
    df = df.drop(columns=["website_url", "updated_at", "created_at"], errors='ignore')
    df = df[df['state'].notnull()]
    df['state'] = df['state'].str.strip().str.lower()

    for state, group in df.groupby('state'):
        table = pa.Table.from_pandas(group)
        buffer = BytesIO()
        pq.write_table(table, buffer, compression='snappy')
        buffer.seek(0)

        key = f"silver/state={state.replace(' ', '_')}/breweries.parquet"
        s3.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=buffer.getvalue())
        print(f"✅ Silver salvo: {key}")

    log_success("silver_step", f"Silver layer gerada com {len(df)} registros e {df['state'].nunique()} estados.")
    return df

# -------------------------------
# 🥇 GOLD
# -------------------------------

def save_gold_layer(df):
    agg_df = df.groupby(['state', 'brewery_type']).size().reset_index(name='brewery_count')

    table = pa.Table.from_pandas(agg_df)
    buffer = BytesIO()
    pq.write_table(table, buffer, compression='snappy')
    buffer.seek(0)

    key = f"gold/breweries_summary_{datetime.today().strftime('%Y-%m-%d')}.parquet"
    s3.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=buffer.getvalue())

    print(f"✅ Gold salvo: {key}")
    log_success("gold_step", f"Gold layer criada com {len(agg_df)} registros.")

# -------------------------------
# 📉 Logging de Erros no S3
# -------------------------------

def log_error_to_s3(task_id, error, layer="generic"):
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    folder = timestamp[:10]
    log_key = f"logs/{layer}/{folder}/{task_id}_{timestamp}.txt"
    error_message = f"[{timestamp}] Task: {task_id}\nError: {str(error)}\n\nTraceback:\n{traceback.format_exc()}"

    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=log_key,
        Body=error_message.encode('utf-8')
    )

    print(f"🚨 Erro registrado no S3: s3://{S3_BUCKET_NAME}/{log_key}")

# -------------------------------
# ✅ Logging de Sucesso no S3
# -------------------------------

def log_success(task_id, message, layer="generic"):
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    folder = timestamp[:10]
    log_key = f"logs/{layer}/{folder}/{task_id}_SUCCESS_{timestamp}.txt"

    s3.put_object(
        Bucket=S3_BUCKET_NAME,
        Key=log_key,
        Body=message.encode('utf-8')
    )

    print(f"📄 Log de sucesso salvo em: s3://{S3_BUCKET_NAME}/{log_key}")
