# 🍺 Brewery Data Capture Pipeline

Pipeline de engenharia de dados construído para consumir, transformar e disponibilizar dados da Open Brewery DB API (https://www.openbrewerydb.org/), utilizando uma arquitetura em camadas (Medallion Architecture).

------------------------------------------------------------

## 🧱 Arquitetura Utilizada: Medallion (Bronze → Silver → Gold)

Este pipeline foi estruturado com base em boas práticas modernas de engenharia de dados, separando os dados em 3 camadas:

🥉 Bronze Layer:
- Armazena os dados brutos extraídos da API.
- Formato: JSON.
- Exemplo de arquivo: bronze/breweries_raw_2025-03-22.json

🥈 Silver Layer:
- Dados curados (limpos, estruturados e otimizados).
- Particionado por estado (state).
- Formato: Parquet, com compressão snappy.
- Exemplo de path: silver/state=texas/breweries.parquet

🥇 Gold Layer:
- Dados agregados prontos para consumo analítico.
- Métrica gerada: quantidade de cervejarias por tipo e estado.
- Exemplo de path: gold/breweries_summary_2025-03-22.parquet

------------------------------------------------------------

## 🛠️ Tecnologias Utilizadas

Ferramenta           | Papel
---------------------|---------------------------------------------------
Apache Airflow       | Orquestração das etapas da pipeline
Docker               | Isolamento e portabilidade do ambiente
AWS S3               | Armazenamento de dados em camadas
Pandas / PyArrow     | Manipulação e formatação dos dados
Parquet              | Formato colunar e eficiente para análise
Requests             | Consumo da API pública de cervejarias

------------------------------------------------------------

## 🚀 Como Rodar o Projeto

✅ Pré-requisitos:
- Docker e Docker Compose instalados
- Conta na AWS com acesso ao S3

Crie um bucket e configure as credenciais no arquivo .env:

AWS_ACCESS_KEY_ID=SUAS_CREDENCIAIS  
AWS_SECRET_ACCESS_KEY=SUA_SENHA  
AWS_DEFAULT_REGION=us-east-1  
S3_BUCKET_NAME=nome-do-seu-bucket  

▶️ Passos para execução:

1. Subir os serviços:
   docker compose up

2. Acessar o Airflow:
   Interface: http://localhost:8080  
   Usuário: admin  
   Senha: admin

3. Executar o pipeline:
   - Ative o DAG: brewery_etl_pipeline  
   - Clique em “Trigger DAG” para iniciar a execução

------------------------------------------------------------

## 🧪 Validações Implementadas

✅ Verificação de variáveis de ambiente  
✅ Tratamento de falhas de rede/API  
✅ Reprocessamento a partir dos dados da camada Bronze  
✅ Logs de sucesso e erro salvos no S3 para cada etapa
