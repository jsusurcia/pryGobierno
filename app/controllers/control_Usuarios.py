from ConexionBD import get_connection

class controlUsuarios:
    
    @staticmethod
    def insertar(nombre, ape_pat, ape_mat, correo, contrasena, id_rol, estado):
        """
        Inserta un nuevo usuario en la base de datos.
        """
        try:
            sql = """
                INSERT INTO usuarios (nombre, ape_pat, ape_mat, correo, contrasena, id_rol, estado, fecha_creacion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (nombre, ape_pat, ape_mat, correo, contrasena, id_rol, estado))
                conexion.commit()
            
            conexion.close()
            print(f"Usuario '{nombre} {ape_pat}' agregado correctamente.")
            return True
        
        except Exception as e:
            print(f"Error al insertar usuario => {e}")
            return False
    @staticmethod
    def buscar_por_ID(id_usuario):
        try:
            sql = """
                SELECT * FROM USUARIOS WHERE id_usuario = %s
            """
            atributos = ['id_usuario', 'nombre', 'ape_pat', 'ape_mat', 'correo', 'contrasena', 'id_rol', 'estado', 'fecha_creacion']
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            producto = None
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                usuario = cursor.fetchone()

            conexion.close()
            usuario_dict = dict(zip(atributos, usuario)) if usuario else None
            return usuario_dict

        except Exception as e:
            print(f"Error al buscar_por_ID => {e}")
            return None
        
    @staticmethod
    def buscar_todos():
        try:
            sql = """
                SELECT * FROM USUARIOS
            """
            atributos = ['idProducto', 'nombre', 'descripcion', 'precio', 'stock', 'activo', 'categoria', 'fechaCreacion', 'imagenURL']
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            usuarios = []
            with conexion.cursor() as cursor:
                cursor.execute(sql)
                usuarios = cursor.fetchall()

            conexion.close()
            usuarios_list = [dict(zip(atributos, usuario)) for usuario in usuarios] if usuarios else []
            return usuarios_list

        except Exception as e:
            print(f"Error al buscar_todos => {e}")
            return None
    @staticmethod
    def editar_usuario(id_usuario, nombre, ape_pat, ape_mat, correo, contrasena, id_rol, estado):
        try:
            sql = """
                UPDATE USUARIOS
                SET nombre = %s,
                    ape_pat = %s,
                    ape_mat = %s,
                    correo = %s,
                    contrasena = %s,
                    id_rol = %s,
                    estado = %s
                WHERE id_usuario = %s
            """

            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False

            with conexion.cursor() as cursor:
                cursor.execute(sql, (nombre, ape_pat, ape_mat, correo, contrasena, id_rol, estado, id_usuario))
                conexion.commit()

            conexion.close()
            print(f"Usuario {id_usuario} actualizado correctamente.")
            return True

        except Exception as e:
            print(f"Error al editar_usuario => {e}")
            return False
    @staticmethod
    def buscar_por_correo(correo, contrasena):
        try:
            sql = """
                SELECT * FROM usuarios WHERE correo = %s AND contrasena = %s
            """
            atributos = [
                'id_usuario', 'nombre', 'ape_pat', 'ape_mat', 
                'correo', 'contrasena', 'id_rol', 'estado', 'fecha_creacion'
            ]
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            usuario_dict = None
            with conexion.cursor() as cursor:
                cursor.execute(sql, (correo, contrasena))  # ✅ usar los parámetros correctos
                usuario = cursor.fetchone()

            if usuario:
                usuario_dict = dict(zip(atributos, usuario))

            conexion.close()
            return usuario_dict

        except Exception as e:
            print(f"Error al buscar_por_correo => {e}")
        return None
    @staticmethod
    def verificar_contrasena(correo, contrasena):
        try:
            sql = """
                SELECT id_usuario, nombre, ape_pat, ape_mat, correo, id_rol, estado
                FROM usuarios
                WHERE correo = %s AND contrasena = %s
            """

            conexion = get_connection()
            if not conexion:
                print("❌ No se pudo conectar a la base de datos.")
                return None

            with conexion.cursor() as cursor:
                cursor.execute(sql, (correo, contrasena))
                usuario = cursor.fetchone()

            conexion.close()

            if usuario:
                atributos = ['id_usuario', 'nombre', 'ape_pat', 'ape_mat', 'correo', 'id_rol', 'estado']
                usuario_dict = dict(zip(atributos, usuario))
                print("✅ Usuario verificado correctamente.")
                return usuario_dict
            else:
                print("⚠️ Correo o contraseña incorrectos.")
                return None

        except Exception as e:
            print(f"❌ Error en verificar_contrasena => {e}")
            return None

        
         
