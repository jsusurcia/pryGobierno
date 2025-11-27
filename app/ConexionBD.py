import psycopg2
import psycopg2.extensions

def get_connection():
    try:
        # Configurar conexión con UTF-8 explícitamente
        conexion = psycopg2.connect(
            host="localhost",
            database="Gobierno2",
            user="postgres",
            password="070905",
            client_encoding='UTF8'
        )
        
        # Establecer el encoding del cliente explícitamente
        conexion.set_client_encoding('UTF8')
        
        # Obtener el cursor y asegurar que use UTF-8
        cursor = conexion.cursor()
        cursor.execute("SET CLIENT_ENCODING TO 'UTF8';")
        cursor.execute("SET NAMES 'UTF8';")
        conexion.commit()
        cursor.close()
        
        return conexion
    except Exception as e:
        print(f"Error al conectar con PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return None
