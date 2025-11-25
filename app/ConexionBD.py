import psycopg2
import os

def get_connection():
    try:
        # Forzar encoding para evitar problemas con rutas que tienen tildes
        os.environ['PGCLIENTENCODING'] = 'LATIN1'
        
        conexion = psycopg2.connect(
            host="localhost",
            database="Gobierno2",
            user="postgres",
            password="SMAILLIW"
        )
        
        # Después de conectar, cambiar a UTF8 para queries
        cursor = conexion.cursor()
        cursor.execute("SET CLIENT_ENCODING TO 'UTF8';")
        conexion.commit()
        cursor.close()
        
        return conexion
    except UnicodeDecodeError:
        # Si falla con encoding, intentar sin configurar
        try:
            conexion = psycopg2.connect(
                host="localhost",
                database="Gobierno2",
                user="postgres",
                password="SMAILLIW"
            )
            return conexion
        except Exception as e2:
            print("Error al conectar con PostgreSQL:", e2)
            return None
    except Exception as e:
        print("Error al conectar con PostgreSQL:", e)
        return None
