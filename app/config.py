import os
API_BASE_URL=os.getenv('API_BASE_URL','http://127.0.0.1:8000')
API_TOKEN=os.getenv('API_TOKEN','local-demo-token')
DATABASE_PATH=os.getenv('DATABASE_PATH','data/ingestion.db')
PAGE_SIZE=int(os.getenv('PAGE_SIZE','100'))
MAX_RETRIES=int(os.getenv('MAX_RETRIES','4'))
LOOKBACK_SECONDS=int(os.getenv('LOOKBACK_SECONDS','3600'))
