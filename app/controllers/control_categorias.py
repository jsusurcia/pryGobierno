from ConexionBD import get_connection

class controlCategorias:
    @staticmethod
    def agregar(nombre, descripcion):
        """
        Inserta una nueva categoría en la base de datos.
        """
        try:
            sql = """
                INSERT INTO categorias (nombre, descripcion)
                VALUES (%s, %s)
            """
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (nombre, descripcion))
                conexion.commit()
            
            conexion.close()
            print(f"Categoría '{nombre}' agregada correctamente.")
            return True

        except Exception as e:
            print(f"Error al agregar categoría => {e}")
            return False


    @staticmethod
    def buscar_por_ID(id_categoria):
        """
        Busca una categoría por su ID.
        """
        try:
            sql = """
                SELECT * FROM categorias WHERE id_categoria = %s
            """
            atributos = ['id_categoria', 'nombre', 'descripcion']
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            categoria = None
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_categoria,))
                categoria = cursor.fetchone()

            conexion.close()
            categoria_dict = dict(zip(atributos, categoria)) if categoria else None
            return categoria_dict

        except Exception as e:
            print(f"Error al buscar_por_ID => {e}")
            return None


    @staticmethod
    def buscar_todos():
        """
        Retorna todas las categorías registradas en la base de datos.
        """
        try:
            sql = """
                SELECT * FROM categorias
            """
            atributos = ['id_categoria', 'nombre', 'descripcion']
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            categorias = []
            with conexion.cursor() as cursor:
                cursor.execute(sql)
                categorias = cursor.fetchall()

            conexion.close()
            categorias_list = [dict(zip(atributos, c)) for c in categorias] if categorias else []
            return categorias_list

        except Exception as e:
            print(f"Error al buscar_todos => {e}")
            return None

    @staticmethod
    def editar(id_categoria, nombre, descripcion):
        """
        Actualiza el nombre y la descripción de una categoría existente.
        """
        try:
            sql = """
                UPDATE categorias
                SET nombre = %s, descripcion = %s
                WHERE id_categoria = %s
            """
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (nombre, descripcion, id_categoria))
                conexion.commit()
            
            conexion.close()
            print(f"Categoría con ID {id_categoria} actualizada correctamente.")
            return True
        
        except Exception as e:
            print(f"Error al editar categoría => {e}")
            return False

    @staticmethod
    def eliminar(id_categoria):
        """
        Elimina una categoría por su ID.
        """
        try:
            sql = """
                DELETE FROM categorias
                WHERE id_categoria = %s
            """
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_categoria,))
                conexion.commit()
            
            conexion.close()
            print(f"Categoría con ID {id_categoria} eliminada correctamente.")
            return True
        
        except Exception as e:
            print(f"Error al eliminar categoría => {e}")
            return False