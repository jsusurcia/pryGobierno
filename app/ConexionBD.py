import psycopg2

def get_connection():
    try:
        conexion = psycopg2.connect(
            host="localhost",
            database="gobierno",
            user="postgres",
            password="200605"
        )
        return conexion
    except Exception as e:
        print("Error al conectar con PostgreSQL:", e)
        return None
