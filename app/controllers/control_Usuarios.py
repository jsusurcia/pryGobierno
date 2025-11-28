from ConexionBD import get_connection

class controlUsuarios:
    
    @staticmethod
    def insertar(nombre, ape_pat, ape_mat, correo, contrasena, id_rol, estado):
        """
        Inserta un nuevo usuario en la base de datos.
        """
        try:
            sql = """
                INSERT INTO USUARIO (nombre, ape_pat, ape_mat, correo, contrasena, id_rol, estado, fecha_creacion)
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
                SELECT * FROM USUARIO WHERE id_usuario = %s
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
                SELECT * FROM USUARIO
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
                UPDATE USUARIO
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
                SELECT * FROM USUARIO WHERE correo = %s AND contrasena = %s
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
                FROM USUARIO
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

    @staticmethod
    def es_jefe(id_usuario):
        """Verifica si un usuario es jefe (tipo 'J')"""
        try:
            sql = """
                SELECT r.tipo
                FROM USUARIO u
                JOIN ROL r ON u.id_rol = r.id_rol
                WHERE u.id_usuario = %s AND r.tipo = 'J'
            """
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                resultado = cursor.fetchone()
            
            conexion.close()
            return resultado is not None
        except Exception as e:
            print(f"Error en es_jefe => {e}")
            return False

    @staticmethod
    def es_jefe_ti(id_usuario):
        """Verifica si un usuario es el Jefe de Tecnología de la Información y Comunicaciones"""
        try:
            sql = """
                SELECT r.id_rol
                FROM USUARIO u
                JOIN ROL r ON u.id_rol = r.id_rol
                WHERE u.id_usuario = %s 
                AND r.tipo = 'J' 
                AND r.id_area = 1
                AND r.nombre = 'Jefe de Tecnología de la Información y Comunicaciones'
            """
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                resultado = cursor.fetchone()
            
            conexion.close()
            return resultado is not None
        except Exception as e:
            print(f"Error en es_jefe_ti => {e}")
            return False

    @staticmethod
    def obtener_id_jefe_ti():
        """Obtiene el ID del rol del Jefe de TI"""
        try:
            sql = """
                SELECT id_rol FROM ROL
                WHERE tipo = 'J' 
                AND id_area = 1
                AND nombre = 'Jefe de Tecnología de la Información y Comunicaciones'
                LIMIT 1
            """
            conexion = get_connection()
            if not conexion:
                return None
            
            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultado = cursor.fetchone()
            
            conexion.close()
            return resultado[0] if resultado else None
        except Exception as e:
            print(f"Error en obtener_id_jefe_ti => {e}")
            return None

    @staticmethod
    def es_tecnico_area_1(id_usuario):
        """Verifica si un usuario es técnico del área 1 (Desarrollo y Control de Gestión)"""
        try:
            sql = """
                SELECT r.id_rol
                FROM USUARIO u
                JOIN ROL r ON u.id_rol = r.id_rol
                WHERE u.id_usuario = %s 
                AND r.tipo = 'T' 
                AND r.id_area = 1
            """
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                resultado = cursor.fetchone()
            
            conexion.close()
            return resultado is not None
        except Exception as e:
            print(f"Error en es_tecnico_area_1 => {e}")
            return False

    @staticmethod
    def es_jefe_ti_rol_1(id_usuario):
        """Verifica si un usuario es el jefe de TI con id_rol = 1"""
        try:
            sql = """
                SELECT r.id_rol
                FROM USUARIO u
                JOIN ROL r ON u.id_rol = r.id_rol
                WHERE u.id_usuario = %s 
                AND r.id_rol = 1
                AND r.tipo = 'J' 
                AND r.id_area = 1
            """
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                resultado = cursor.fetchone()
            
            conexion.close()
            return resultado is not None
        except Exception as e:
            print(f"Error en es_jefe_ti_rol_1 => {e}")
            return False

    @staticmethod
    def obtener_tecnicos():
        """Obtiene todos los técnicos (tipo 'T')"""
        try:
            sql = """
                SELECT u.id_usuario, u.nombre, u.ape_pat, u.ape_mat, r.nombre as rol_nombre
                FROM USUARIO u
                JOIN ROL r ON u.id_rol = r.id_rol
                WHERE r.tipo = 'T' AND u.estado = TRUE
                ORDER BY u.nombre, u.ape_pat
            """
            conexion = get_connection()
            if not conexion:
                return []
            
            with conexion.cursor() as cursor:
                cursor.execute(sql)
                tecnicos = cursor.fetchall()
            
            conexion.close()
            return [
                {
                    'id_usuario': t[0],
                    'nombre_completo': f"{t[1]} {t[2]} {t[3]}",
                    'rol_nombre': t[4]
                }
                for t in tecnicos
            ]
        except Exception as e:
            print(f"Error en obtener_tecnicos => {e}")
            return []

    @staticmethod
    def contar_tickets_activos(id_usuario):
        """Cuenta los tickets activos asignados directamente a un usuario (estados P y A, excluyendo Terminados)"""
        try:
            sql = """
                SELECT COUNT(*)
                FROM INCIDENTE
                WHERE id_tecnico_asignado = %s
                AND estado IN ('P', 'A')
            """
            conexion = get_connection()
            if not conexion:
                return 0
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                resultado = cursor.fetchone()
            
            conexion.close()
            return resultado[0] if resultado else 0
        except Exception as e:
            print(f"Error en contar_tickets_activos => {e}")
            return 0

    @staticmethod
    def contar_tickets_en_equipo(id_usuario):
        """Cuenta los tickets activos donde el usuario está en el equipo técnico (excluyendo Terminados)"""
        try:
            sql = """
                SELECT COUNT(DISTINCT et.id_incidente)
                FROM EQUIPO_TECNICO et
                JOIN INCIDENTE i ON et.id_incidente = i.id_incidente
                WHERE et.id_usuario = %s
                AND i.estado IN ('P', 'A')
            """
            conexion = get_connection()
            if not conexion:
                return 0
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                resultado = cursor.fetchone()
            
            conexion.close()
            return resultado[0] if resultado else 0
        except Exception as e:
            print(f"Error en contar_tickets_en_equipo => {e}")
            return 0
    
    @staticmethod
    def obtener_jefes_por_area():
        """
        Obtiene todos los usuarios con rol de tipo 'J' (Jefe) agrupados por área
        
        Returns:
            list: Lista de usuarios jefes con información de su rol y área
        """
        try:
            sql = """
                SELECT 
                    u.id_usuario,
                    u.nombre,
                    u.ape_pat,
                    u.ape_mat,
                    u.correo,
                    r.nombre as nombre_rol,
                    a.nombre as nombre_area,
                    r.id_rol,
                    r.id_area
                FROM USUARIO u
                INNER JOIN ROL r ON u.id_rol = r.id_rol
                INNER JOIN AREA a ON r.id_area = a.id_area
                WHERE r.tipo = 'J' AND u.estado = TRUE
                ORDER BY a.nombre, u.nombre
            """
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return []
            
            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultados = cursor.fetchall()
            
            conexion.close()
            
            jefes = []
            for row in resultados:
                jefes.append({
                    'id_usuario': row[0],
                    'nombre': row[1],
                    'ape_pat': row[2],
                    'ape_mat': row[3],
                    'nombre_completo': f"{row[1]} {row[2]} {row[3]}",
                    'correo': row[4],
                    'nombre_rol': row[5],
                    'nombre_area': row[6],
                    'id_rol': row[7],
                    'id_area': row[8]
                })
            
            return jefes
            
        except Exception as e:
            print(f"Error en obtener_jefes_por_area => {e}")
            return []
    
    @staticmethod
    def es_rol_firmante(id_usuario):
        """
        Verifica si un usuario tiene un rol de firmante de contratos
        Roles de firmantes: 8, 10, 11, 9, 12
        
        Returns:
            bool: True si el usuario es firmante
        """
        try:
            usuario = controlUsuarios.buscar_por_ID(id_usuario)
            if not usuario:
                return False
            
            roles_firmantes = [8, 10, 11, 9, 12]
            return usuario.get('id_rol') in roles_firmantes
            
        except Exception as e:
            print(f"Error en es_rol_firmante => {e}")
            return False
    
    @staticmethod
    def puede_crear_contratos(id_usuario):
        """
        Verifica si un usuario puede crear contratos
        Puede crear: Jefes (tipo 'J') que NO sean firmantes (roles 8, 10, 11, 9, 12)
        
        Returns:
            bool: True si puede crear contratos
        """
        try:
            usuario = controlUsuarios.buscar_por_ID(id_usuario)
            if not usuario:
                return False
            
            from controllers.controlador_rol import ControlRol
            rol = ControlRol.buscar_por_IDRol(usuario['id_rol'])
            if not rol:
                return False
            
            # Debe ser tipo 'J' (Jefe)
            es_jefe = rol.get('tipo') == 'J'
            
            # NO debe ser rol firmante
            roles_firmantes = [8, 10, 11, 9, 12]
            es_firmante = usuario.get('id_rol') in roles_firmantes
            
            # Puede crear contratos si es jefe Y NO es firmante
            return es_jefe and not es_firmante
            
        except Exception as e:
            print(f"Error en puede_crear_contratos => {e}")
            return False
    
    @staticmethod
    def obtener_usuarios_por_rol(id_rol):
        """
        Obtiene todos los usuarios con un rol específico
        
        Args:
            id_rol: ID del rol a buscar
            
        Returns:
            list: Lista de usuarios con ese rol
        """
        try:
            sql = """
                SELECT 
                    id_usuario,
                    nombre,
                    ape_pat,
                    ape_mat,
                    correo,
                    id_rol,
                    estado
                FROM USUARIO
                WHERE id_rol = %s AND estado = TRUE
                ORDER BY nombre, ape_pat
            """
            
            conexion = get_connection()
            if not conexion:
                return []
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_rol,))
                resultados = cursor.fetchall()
            
            conexion.close()
            
            usuarios = []
            for row in resultados:
                usuarios.append({
                    'id_usuario': row[0],
                    'nombre': row[1],
                    'ape_pat': row[2],
                    'ape_mat': row[3],
                    'nombre_completo': f"{row[1]} {row[2]} {row[3]}",
                    'correo': row[4],
                    'id_rol': row[5],
                    'estado': row[6]
                })
            
            return usuarios
            
        except Exception as e:
            print(f"Error en obtener_usuarios_por_rol => {e}")
            return []
    
    @staticmethod
    def obtener_usuarios_por_area(id_area):
        """
        Obtiene todos los usuarios de un área específica
        
        Args:
            id_area: ID del área a buscar
            
        Returns:
            list: Lista de usuarios con información del rol
        """
        try:
            sql = """
                SELECT 
                    u.id_usuario,
                    u.nombre,
                    u.ape_pat,
                    u.ape_mat,
                    u.correo,
                    u.id_rol,
                    r.nombre as nombre_rol,
                    r.tipo as tipo_rol
                FROM USUARIO u
                INNER JOIN ROL r ON u.id_rol = r.id_rol
                WHERE r.id_area = %s AND u.estado = TRUE
                ORDER BY r.tipo, u.nombre, u.ape_pat
            """
            
            conexion = get_connection()
            if not conexion:
                return []
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_area,))
                resultados = cursor.fetchall()
            
            conexion.close()
            
            usuarios = []
            for row in resultados:
                usuarios.append({
                    'id_usuario': row[0],
                    'nombre': row[1],
                    'ape_pat': row[2],
                    'ape_mat': row[3],
                    'nombre_completo': f"{row[1]} {row[2]} {row[3]}",
                    'correo': row[4],
                    'id_rol': row[5],
                    'nombre_rol': row[6],
                    'tipo_rol': row[7]
                })
            
            return usuarios
            
        except Exception as e:
            print(f"Error en obtener_usuarios_por_area => {e}")
            return []
    
    @staticmethod
    def obtener_todas_areas():
        """
        Obtiene todas las áreas de la organización
        
        Returns:
            list: Lista de áreas
        """
        try:
            sql = """
                SELECT id_area, nombre
                FROM AREA
                ORDER BY nombre
            """
            
            conexion = get_connection()
            if not conexion:
                return []
            
            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultados = cursor.fetchall()
            
            conexion.close()
            
            areas = []
            for row in resultados:
                areas.append({
                    'id_area': row[0],
                    'nombre': row[1]
                })
            
            return areas
            
        except Exception as e:
            print(f"Error en obtener_todas_areas => {e}")
            return []

         
