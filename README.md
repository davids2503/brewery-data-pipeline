# 🍺 Brewery Data Capture Pipeline

Data engineering pipeline built to consume, transform, and make data available from the Open Brewery DB API (https://www.openbrewerydb.org/), using a layered architecture (Medallion Architecture).

------------------------------------------------------------

## 🧱 Architecture Used: Medallion (Bronze → Silver → Gold)

This pipeline is structured based on modern data engineering best practices, separating the data into 3 layers:

🥉 Bronze Layer:
- Stores raw data extracted from the API.
- Format: JSON.
- Example file: bronze/breweries_raw_2025-03-22.json

🥈 Silver Layer:
- Curated data (cleaned, structured, and optimized).
- Partitioned by state.
- Format: Parquet with Snappy compression.
- Example path: silver/state=texas/breweries.parquet

🥇 Gold Layer:
- Aggregated data ready for analytical consumption.
- Generated metric: number of breweries by type and state.
- Example path: gold/breweries_summary_2025-03-22.parquet

------------------------------------------------------------

## 🛠️ Technologies Used

Tool                | Role
--------------------|---------------------------------------------------
Apache Airflow      | Orchestration of pipeline stages
Docker              | Environment isolation and portability
AWS S3              | Layered data storage
Pandas / PyArrow    | Data manipulation and formatting
Parquet             | Columnar and efficient format for analysis
Requests            | Consumption of the public brewery API

------------------------------------------------------------

## 🚀 How to Run the Project

✅ Prerequisites:
- Docker and Docker Compose installed
- AWS account with access to S3

Create a bucket and configure credentials in the .env file:

AWS_ACCESS_KEY_ID=YOUR_CREDENTIALS  
AWS_SECRET_ACCESS_KEY=YOUR_SECRET  
AWS_DEFAULT_REGION=us-east-1  
S3_BUCKET_NAME=your-bucket-name  

▶️ Execution steps:

1. Start the services:
   docker compose up

2. Access Airflow:
   Interface: http://localhost:8080  
   User: admin  
   Password: admin

3. Run the pipeline:
   - Enable the DAG: brewery_etl_pipeline  
   - Click “Trigger DAG” to start execution

------------------------------------------------------------

## 🧪 Implemented Validations

✅ Environment variable check  
✅ Network/API failure handling  
✅ Reprocessing from Bronze layer data  
✅ Success and error logs saved to S3 for each step