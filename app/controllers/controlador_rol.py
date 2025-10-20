from app.database.db import get_connection

class ControlRol:
    @staticmethod

    def buscar_por_IDROL(id_rol):
        try:
            sql = """
                SELECT * FROM roles WHERE id_rol = %s
            """
            atributos = ['id_rol', 'nombre', 'descripcion']

            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            rol = None
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_rol,))
                rol = cursor.fetchone()

            conexion.close()
            rol_dict = dict(zip(atributos, rol)) if rol else None
            return rol_dict

        except Exception as e:
            print(f" Error en buscar_por_IDROL => {e}")
            return None
        
    def insertar_rol(nombre, descripcion):
        try:
            sql = """
                INSERT INTO roles (nombre, descripcion)
                VALUES (%s, %s)
                RETURNING id_rol;
            """
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False

            with conexion.cursor() as cursor:
                cursor.execute(sql, (nombre, descripcion))
                id_nuevo = cursor.fetchone()[0]
                conexion.commit()

            conexion.close()
            return True

        except Exception as e:
            return False
        
