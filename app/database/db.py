import psycopg2

DB_CONFIG = {
    'host':'localhost',
    'port':5432,
    'user':'postgres',
    'password':'200605',
    'database':'products'
}

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(e)
        return None