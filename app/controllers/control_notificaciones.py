from ConexionBD import get_connection

class ControlNotificaciones:
    
    @staticmethod
    def crear_notificacion(id_usuario, titulo, mensaje, tipo=None, id_referencia=None):
        """Crea una nueva notificación"""
        try:
            sql = """
                INSERT INTO NOTIFICACION (id_usuario, titulo, mensaje, tipo, id_referencia, fecha, leida)
                VALUES (%s, %s, %s, %s, %s, NOW(), FALSE)
            """
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario, titulo, mensaje, tipo, id_referencia))
                conexion.commit()
            
            conexion.close()
            return True
        except Exception as e:
            print(f"Error al crear notificación => {e}")
            return False
    
    @staticmethod
    def obtener_notificaciones_usuario(id_usuario, no_leidas=False):
        """Obtiene las notificaciones de un usuario"""
        try:
            if no_leidas:
                sql = """
                    SELECT id_notificacion, titulo, mensaje, tipo, id_referencia, fecha, leida
                    FROM NOTIFICACION
                    WHERE id_usuario = %s AND leida = FALSE
                    ORDER BY fecha DESC
                """
            else:
                sql = """
                    SELECT id_notificacion, titulo, mensaje, tipo, id_referencia, fecha, leida
                    FROM NOTIFICACION
                    WHERE id_usuario = %s
                    ORDER BY fecha DESC
                    LIMIT 50
                """
            
            conexion = get_connection()
            if not conexion:
                return []
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                notificaciones = cursor.fetchall()
            
            conexion.close()
            
            atributos = ['id_notificacion', 'titulo', 'mensaje', 'tipo', 'id_referencia', 'fecha', 'leida']
            return [dict(zip(atributos, n)) for n in notificaciones]
        except Exception as e:
            print(f"Error al obtener notificaciones => {e}")
            return []
    
    @staticmethod
    def contar_no_leidas(id_usuario):
        """Cuenta las notificaciones no leídas de un usuario"""
        try:
            sql = """
                SELECT COUNT(*) FROM NOTIFICACION
                WHERE id_usuario = %s AND leida = FALSE
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
            print(f"Error al contar notificaciones => {e}")
            return 0
    
    @staticmethod
    def marcar_como_leida(id_notificacion, id_usuario):
        """Marca una notificación como leída"""
        try:
            sql = """
                UPDATE NOTIFICACION
                SET leida = TRUE
                WHERE id_notificacion = %s AND id_usuario = %s
            """
            
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_notificacion, id_usuario))
                conexion.commit()
            
            conexion.close()
            return True
        except Exception as e:
            print(f"Error al marcar notificación como leída => {e}")
            return False
    
    @staticmethod
    def marcar_todas_como_leidas(id_usuario):
        """Marca todas las notificaciones de un usuario como leídas"""
        try:
            sql = """
                UPDATE NOTIFICACION
                SET leida = TRUE
                WHERE id_usuario = %s AND leida = FALSE
            """
            
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                conexion.commit()
            
            conexion.close()
            return True
        except Exception as e:
            print(f"Error al marcar todas como leídas => {e}")
            return False
    
    @staticmethod
    def notificar_incidente_creado(id_incidente, id_jefe_reporta):
        """Notifica al jefe de TI cuando se crea un incidente"""
        try:
            from controllers.control_Usuarios import controlUsuarios
            
            # Obtener ID del jefe de TI
            id_jefe_ti_rol = controlUsuarios.obtener_id_jefe_ti()
            if not id_jefe_ti_rol:
                return False
            
            # Obtener usuarios con ese rol
            sql_usuarios = """
                SELECT id_usuario FROM USUARIO
                WHERE id_rol = %s AND estado = TRUE
            """
            
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql_usuarios, (id_jefe_ti_rol,))
                jefes_ti = cursor.fetchall()
            
            # Obtener información del jefe que reporta
            jefe_reporta = controlUsuarios.buscar_por_ID(id_jefe_reporta)
            nombre_jefe = f"{jefe_reporta['nombre']} {jefe_reporta['ape_pat']}" if jefe_reporta else "Un jefe"
            
            # Crear notificación para cada jefe de TI
            for jefe_ti in jefes_ti:
                ControlNotificaciones.crear_notificacion(
                    id_usuario=jefe_ti[0],
                    titulo="Nuevo Incidente Reportado",
                    mensaje=f"{nombre_jefe} ha reportado un nuevo incidente (#{id_incidente})",
                    tipo="incidente",
                    id_referencia=id_incidente
                )
            
            conexion.close()
            return True
        except Exception as e:
            print(f"Error al notificar incidente creado => {e}")
            return False
    
    @staticmethod
    def notificar_estado_incidente(id_incidente, estado, id_jefe_reporta):
        """Notifica al jefe que reportó cuando se cambia el estado del incidente"""
        try:
            from controllers.control_incidentes import ControlIncidentes
            
            incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            if not incidente:
                return False
            
            estado_texto = {
                'A': 'aceptado',
                'C': 'cancelado',
                'T': 'terminado'
            }.get(estado, estado)
            
            ControlNotificaciones.crear_notificacion(
                id_usuario=incidente['id_usuario'],
                titulo=f"Incidente #{id_incidente} {estado_texto.capitalize()}",
                mensaje=f"Tu incidente ha sido {estado_texto} por el Jefe de TI",
                tipo="incidente",
                id_referencia=id_incidente
            )
            
            return True
        except Exception as e:
            print(f"Error al notificar estado incidente => {e}")
            return False
    
    @staticmethod
    def notificar_asignacion_tecnico(id_incidente, id_tecnico, es_grupo=False):
        """Notifica a un técnico cuando es asignado a un incidente"""
        try:
            from controllers.control_incidentes import ControlIncidentes
            
            incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            if not incidente:
                return False
            
            tipo_mensaje = "asignado al equipo técnico" if es_grupo else "asignado como responsable"
            
            ControlNotificaciones.crear_notificacion(
                id_usuario=id_tecnico,
                titulo=f"Asignación a Incidente #{id_incidente}",
                mensaje=f"Has sido {tipo_mensaje} del incidente: {incidente['titulo']}",
                tipo="incidente",
                id_referencia=id_incidente
            )
            
            return True
        except Exception as e:
            print(f"Error al notificar asignación => {e}")
            return False
    
    @staticmethod
    def notificar_asignacion_a_reportante(id_incidente, id_tecnico, nombre_tecnico, es_grupo=False):
        """Notifica al usuario que reportó el incidente cuando se le asigna un técnico"""
        try:
            from controllers.control_incidentes import ControlIncidentes
            
            incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            if not incidente:
                return False
            
            # Notificar al usuario que reportó
            tipo_asignacion = "un equipo técnico" if es_grupo else f"el técnico {nombre_tecnico}"
            
            ControlNotificaciones.crear_notificacion(
                id_usuario=incidente['id_usuario'],
                titulo=f"Técnico Asignado a tu Incidente #{id_incidente}",
                mensaje=f"Se ha asignado {tipo_asignacion} para atender tu incidente: {incidente['titulo']}",
                tipo="incidente",
                id_referencia=id_incidente
            )
            
            return True
        except Exception as e:
            print(f"Error al notificar asignación a reportante => {e}")
            return False

