import psycopg2

def get_connection():
    try:
        conexion = psycopg2.connect(
            host="localhost",
            database="Gobierno2",
            user="postgres",
            password="070905"
        )
        return conexion
    except Exception as e:
        print("Error al conectar con PostgreSQL:", e)
        return None
