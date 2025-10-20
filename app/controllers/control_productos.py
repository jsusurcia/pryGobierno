from app.database.db import get_connection

class ControlProducto:
    @staticmethod
    def buscar_por_ID(id_producto):
        try:
            sql = """
                SELECT * FROM productos WHERE idProducto = %s
            """
            atributos = ['idProducto', 'nombre', 'descripcion', 'precio', 'stock', 'activo', 'categoria', 'fechaCreacion', 'imagenURL']
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            producto = None
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_producto,))
                producto = cursor.fetchone()

            conexion.close()
            producto_dict = dict(zip(atributos, producto)) if producto else None
            return producto_dict

        except Exception as e:
            print(f"Error al buscar_por_ID => {e}")
            return None
        
    @staticmethod
    def buscar_todos():
        try:
            sql = """
                SELECT * FROM productos
            """
            atributos = ['idProducto', 'nombre', 'descripcion', 'precio', 'stock', 'activo', 'categoria', 'fechaCreacion', 'imagenURL']
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            productos = []
            with conexion.cursor() as cursor:
                cursor.execute(sql)
                productos = cursor.fetchall()

            conexion.close()
            productos_list = [dict(zip(atributos, producto)) for producto in productos] if productos else []
            return productos_list

        except Exception as e:
            print(f"Error al buscar_todos => {e}")
            return None