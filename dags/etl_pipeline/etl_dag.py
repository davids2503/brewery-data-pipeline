from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from etl_pipeline.utils import functions
import pandas as pd  # não esquecer!

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    dag_id='brewery_etl_pipeline',
    default_args=default_args,
    start_date=datetime(2023, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['brewery', 'bronze', 'silver', 'gold']
) as dag:

    def bronze_step(**context):
        try:
            data = functions.fetch_brewery_data()
            key = functions.save_bronze_to_s3(data)
            context['ti'].xcom_push(key='bronze_key', value=key)
        except Exception as e:
            functions.log_error_to_s3("bronze_step", e, layer="bronze")
            raise

    def silver_step(**context):
        try:
            bronze_key = context['ti'].xcom_pull(key='bronze_key', task_ids='bronze_step')
            df = functions.transform_bronze_to_silver(bronze_key)

            if df.empty:
                raise ValueError("❌ Dados curados (silver) estão vazios!")

            if 'state' not in df.columns or df['state'].isnull().all():
                raise ValueError("❌ Coluna 'state' ausente ou totalmente nula!")

            context['ti'].xcom_push(key='silver_df', value=df.to_json())
        except Exception as e:
            functions.log_error_to_s3("silver_step", e, layer="silver")
            raise


    def gold_step(**context):
        try:
            df_json = context['ti'].xcom_pull(key='silver_df', task_ids='silver_step')
            df = pd.read_json(df_json)

            if df.empty:
                raise ValueError("❌ DataFrame de entrada para gold está vazio!")

            functions.save_gold_layer(df)
        except Exception as e:
            functions.log_error_to_s3("gold_step", e, layer="gold")
            raise


    bronze = PythonOperator(
        task_id='bronze_step',
        python_callable=bronze_step,
        provide_context=True
    )

    silver = PythonOperator(
        task_id='silver_step',
        python_callable=silver_step,
        provide_context=True
    )

    gold = PythonOperator(
        task_id='gold_step',
        python_callable=gold_step,
        provide_context=True
    )

    bronze >> silver >> gold
