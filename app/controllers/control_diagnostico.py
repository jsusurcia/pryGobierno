from ConexionBD import get_connection

class ControlDiagnosticos:
    @staticmethod
    def insertar_historial_diagnostico(id_diagnostico, id_incidente, id_usuario, descripcion, causa_raiz=None, solucion_propuesta=None):
        """Inserta un registro en el historial de diagnósticos"""
        try:
            conexion = get_connection()
            if not conexion:
                return False
            
            sql = """
                INSERT INTO HISTORIAL_DIAGNOSTICO 
                (id_diagnostico, id_incidente, id_usuario, descripcion, causa_raiz, solucion_propuesta, fecha)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (
                    id_diagnostico, id_incidente, id_usuario, descripcion, 
                    causa_raiz, solucion_propuesta
                ))
                conexion.commit()
            
            conexion.close()
            return True
        except Exception as e:
            print(f"Error en insertar_historial_diagnostico => {e}")
            return False
    
    @staticmethod
    def tiene_diagnostico_pendiente(id_incidente, id_usuario):
        """
        Verifica si el usuario ya tiene un diagnóstico pendiente para este incidente.
        Retorna True si tiene diagnóstico pendiente, False si no tiene o fue rechazado sin actualizar.
        """
        try:
            conexion = get_connection()
            if not conexion:
                return False
            
            sql = """
                SELECT COUNT(*) 
                FROM DIAGNOSTICO d
                LEFT JOIN REVISION_DIAGNOSTICO rd ON d.id_diagnosticos = rd.id_diagnostico
                WHERE d.id_incidente = %s
                AND d.id_usuario = %s
                AND (
                    -- No tiene revisión (pendiente)
                    rd.id_revision IS NULL
                    OR (
                        -- Tiene revisión rechazada PERO el diagnóstico fue actualizado después del rechazo (pendiente de nuevo)
                        rd.id_revision IS NOT NULL 
                        AND d.fecha_actualizacion IS NOT NULL
                        AND d.fecha_actualizacion > rd.fecha_rechazo
                    )
                )
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_incidente, id_usuario))
                resultado = cursor.fetchone()[0]
            
            conexion.close()
            
            return resultado > 0
            
        except Exception as e:
            print(f"Error en tiene_diagnostico_pendiente => {e}")
            return False
    
    @staticmethod
    def insertar_diagnostico(id_incidente, descripcion, causa_raiz, solucion, comentario=None, usuario_id=None):
        """
        Inserta un diagnóstico. El parámetro comentario se mantiene por compatibilidad pero no se usa.
        Verifica primero que el usuario no tenga un diagnóstico pendiente para este incidente.
        """
        try:
            # Verificar si el usuario ya tiene un diagnóstico pendiente para este incidente
            if usuario_id and ControlDiagnosticos.tiene_diagnostico_pendiente(id_incidente, usuario_id):
                print(f"⚠️ El usuario {usuario_id} ya tiene un diagnóstico pendiente para el incidente {id_incidente}")
                return False
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            sql = """
                INSERT INTO DIAGNOSTICO (id_incidente, descripcion, causa_raiz, solucion_propuesta, id_usuario)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id_diagnosticos;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_incidente, descripcion, causa_raiz, solucion, usuario_id))
                id_diagnostico = cursor.fetchone()[0]
                conexion.commit()

            conexion.close()
            
            # Registrar en historial de diagnósticos
            if id_diagnostico and usuario_id:
                ControlDiagnosticos.insertar_historial_diagnostico(
                    id_diagnostico=id_diagnostico,
                    id_incidente=id_incidente,
                    id_usuario=usuario_id,
                    descripcion=descripcion,
                    causa_raiz=causa_raiz,
                    solucion_propuesta=solucion
                )
            
            # Obtener nombre del técnico que registró el diagnóstico
            from controllers.control_Usuarios import controlUsuarios
            usuario_diagnostico = controlUsuarios.buscar_por_ID(usuario_id) if usuario_id else None
            nombre_tecnico = "Técnico desconocido"
            if usuario_diagnostico:
                nombre_tecnico = f"{usuario_diagnostico.get('nombre', '')} {usuario_diagnostico.get('ape_pat', '')}"
            
            # Obtener el estado actual del incidente
            from controllers.control_incidentes import ControlIncidentes
            incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            estado_actual = incidente.get('estado') if incidente else None
            
            # Registrar en el historial del incidente que se agregó un diagnóstico pendiente de revisión
            if id_diagnostico:
                ControlIncidentes.insertar_historial(
                    id_incidente=id_incidente,
                    estado_anterior=estado_actual,
                    estado_nuevo=estado_actual,  # El estado no cambia al agregar diagnóstico
                    observacion=f"Diagnóstico D{id_diagnostico} registrado y pendiente de revisión. Realizado por: {nombre_tecnico}"
                )
            
            # Notificar al Jefe de TI que hay un nuevo diagnóstico para revisar
            from controllers.control_notificaciones import ControlNotificaciones
            titulo_incidente = incidente.get('titulo', f'Incidente #{id_incidente}')
            
            # Obtener ID del jefe de TI
            from controllers.control_Usuarios import controlUsuarios
            id_jefe_ti_rol = controlUsuarios.obtener_id_jefe_ti()
            
            if id_jefe_ti_rol:
                # Obtener usuarios con ese rol
                conexion = get_connection()
                if conexion:
                    sql_usuarios = """
                        SELECT id_usuario FROM USUARIO
                        WHERE id_rol = %s AND estado = TRUE
                    """
                    with conexion.cursor() as cursor:
                        cursor.execute(sql_usuarios, (id_jefe_ti_rol,))
                        jefes_ti = cursor.fetchall()
                    
                    conexion.close()
                    
                    # Notificar a cada jefe de TI
                    for jefe_ti in jefes_ti:
                        ControlNotificaciones.crear_notificacion(
                            id_usuario=jefe_ti[0],
                            titulo=f"Nuevo Diagnóstico para Revisar - Incidente #{id_incidente}",
                            mensaje=f"{nombre_tecnico} ha enviado un diagnóstico para el incidente '{titulo_incidente}'. Requiere tu revisión.",
                            tipo="diagnostico",
                            id_referencia=id_incidente
                        )
                    
                    print(f"✅ Notificación enviada al Jefe de TI sobre nuevo diagnóstico de {nombre_tecnico}")
            
            return True  # Éxito

        except Exception as e:
            print(f"Error en insertar_diagnostico => {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def buscar_por_IDDiagnostico(id_diagnosticos):
        try:
            sql = """
                SELECT * FROM DIAGNOSTICO WHERE id_diagnosticos = %s
            """
            atributos = [
                'id_diagnosticos', 'id_incidente', 'id_usuario', 
                'descripcion', 'causa_raiz', 'solucion_propuesta', 
                'fecha_diagnostico', 'fecha_actualizacion'
            ]

            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_diagnosticos,))
                diagnostico = cursor.fetchone()

            conexion.close()
            diagnostico_dict = dict(zip(atributos, diagnostico)) if diagnostico else None
            return diagnostico_dict

        except Exception as e:
            print(f"Error en buscar_por_ID => {e}")
            return None
    
    def listar_diagnosticos(self):
        try:
            sql = "SELECT * FROM DIAGNOSTICO ORDER BY id_diagnosticos DESC"
            atributos = [
                'id_diagnosticos', 'id_incidente', 'id_usuario', 
                'descripcion', 'causa_raiz', 'solucion_propuesta', 
                'fecha_diagnostico', 'fecha_actualizacion'
            ]

            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            with conexion.cursor() as cursor:
                cursor.execute(sql)
                diagnosticos = cursor.fetchall()

            conexion.close()
            diagnosticos_list = [dict(zip(atributos, diag)) for diag in diagnosticos] if diagnosticos else []
            return diagnosticos_list

        except Exception as e:
            print(f"⚠️ Error en listar_diagnosticos => {e}")
            return None
        
    @staticmethod
    def listar_diagnosticos_usuario(id_usuario):
        """
        Lista todos los diagnósticos realizados por un usuario específico.
        """
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return []

            sql = """
                SELECT * FROM DIAGNOSTICO
                WHERE id_usuario = %s
                ORDER BY id_diagnosticos DESC;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                diagnosticos = cursor.fetchall()

            conexion.close()

            columnas = [
                'id_diagnosticos', 'id_incidente', 'id_usuario',
                'descripcion', 'causa_raiz', 'solucion_propuesta',
                'fecha_diagnostico', 'fecha_actualizacion'
            ]

            return [dict(zip(columnas, fila)) for fila in diagnosticos]

        except Exception as e:
            print(f"Error en listar_diagnosticos_usuario => {e}")
            return []
    
    @staticmethod
    def listado_diagnosticos_revision():
        """
        Lista diagnósticos con solución propuesta que están pendientes de revisión.
        Solo muestra diagnósticos que:
        - Tienen solucion_propuesta (no NULL)
        - El incidente está en estado 'A' (Activo) o 'P' (Pendiente)
        - Si fueron rechazados, solo se muestran si fueron actualizados después del rechazo
        """
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return []

            # Primero, crear la tabla REVISION_DIAGNOSTICO si no existe
            sql_create_table = """
                CREATE TABLE IF NOT EXISTS REVISION_DIAGNOSTICO (
                    id_revision SERIAL PRIMARY KEY,
                    id_diagnostico INTEGER NOT NULL,
                    fecha_rechazo TIMESTAMP DEFAULT NOW(),
                    id_usuario INTEGER,
                    FOREIGN KEY (id_diagnostico) REFERENCES DIAGNOSTICO(id_diagnosticos),
                    FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
                );
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql_create_table)
                conexion.commit()

            # Consulta para obtener diagnósticos pendientes de revisión
            sql = """
                SELECT DISTINCT d.id_diagnosticos, 
                    d.id_incidente,
                    i.titulo AS titulo_incidente,
                    d.descripcion, 
                    d.causa_raiz, 
                    d.solucion_propuesta,
                    d.fecha_diagnostico,
                    d.fecha_actualizacion
                FROM DIAGNOSTICO d
                LEFT JOIN INCIDENTE i ON d.id_incidente = i.id_incidente
                LEFT JOIN REVISION_DIAGNOSTICO rd ON d.id_diagnosticos = rd.id_diagnostico
                WHERE d.solucion_propuesta IS NOT NULL 
                    AND d.solucion_propuesta != ''
                    AND i.estado IN ('P', 'A')
                    AND (
                        rd.id_revision IS NULL  -- Nunca fue rechazado
                        OR (
                            rd.id_revision IS NOT NULL 
                            AND d.fecha_actualizacion IS NOT NULL
                            AND d.fecha_actualizacion > rd.fecha_rechazo  -- Fue actualizado después del rechazo
                        )
                    )
                ORDER BY d.id_diagnosticos DESC;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql)
                diagnosticos = cursor.fetchall()

            conexion.close()

            columnas = [
                'id_diagnosticos', 'id_incidente', 'titulo_incidente',
                'descripcion', 'causa_raiz', 'solucion_propuesta',
                'fecha_diagnostico', 'fecha_actualizacion'
            ]

            return [dict(zip(columnas, fila)) for fila in diagnosticos]

        except Exception as e:
            print(f"Error en listado_diagnosticos_revision => {e}")
            import traceback
            traceback.print_exc()
            return []


    
    @staticmethod
    def actualizar_diagnostico(id_diagnosticos, descripcion, causa_raiz, solucion_propuesta, id_usuario=None):
        try:
            # Obtener información del diagnóstico antes de actualizar
            diagnostico_anterior = ControlDiagnosticos.buscar_por_IDDiagnostico(id_diagnosticos)
            if not diagnostico_anterior:
                return -1
            
            id_incidente = diagnostico_anterior.get('id_incidente')
            
            sql = """
                UPDATE DIAGNOSTICO
                SET descripcion = %s,
                    causa_raiz = %s,
                    solucion_propuesta = %s,
                    fecha_actualizacion = NOW()
                WHERE id_diagnosticos = %s;
            """
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            with conexion.cursor() as cursor:
                cursor.execute(sql, (descripcion, causa_raiz, solucion_propuesta, id_diagnosticos))
                conexion.commit()

            conexion.close()
            
            # Registrar en historial si se proporciona id_usuario
            if id_usuario and id_incidente:
                ControlDiagnosticos.insertar_historial_diagnostico(
                    id_diagnostico=id_diagnosticos,
                    id_incidente=id_incidente,
                    id_usuario=id_usuario,
                    descripcion=descripcion,
                    causa_raiz=causa_raiz,
                    solucion_propuesta=solucion_propuesta
                )
            
            # Notificar al Jefe de TI que el diagnóstico fue actualizado
            # (esto aplica cuando fue rechazado y el técnico lo actualizó)
            from controllers.control_notificaciones import ControlNotificaciones
            from controllers.control_incidentes import ControlIncidentes
            from controllers.control_Usuarios import controlUsuarios
            
            # Obtener información del incidente y técnico
            incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            titulo_incidente = incidente.get('titulo', f'Incidente #{id_incidente}') if incidente else f'Incidente #{id_incidente}'
            
            usuario_tecnico = controlUsuarios.buscar_por_ID(id_usuario) if id_usuario else None
            nombre_tecnico = "Técnico desconocido"
            if usuario_tecnico:
                nombre_tecnico = f"{usuario_tecnico.get('nombre', '')} {usuario_tecnico.get('ape_pat', '')}"
            
            # Obtener ID del jefe de TI
            id_jefe_ti_rol = controlUsuarios.obtener_id_jefe_ti()
            
            if id_jefe_ti_rol:
                # Obtener usuarios con ese rol
                conexion_notif = get_connection()
                if conexion_notif:
                    sql_usuarios = """
                        SELECT id_usuario FROM USUARIO
                        WHERE id_rol = %s AND estado = TRUE
                    """
                    with conexion_notif.cursor() as cursor:
                        cursor.execute(sql_usuarios, (id_jefe_ti_rol,))
                        jefes_ti = cursor.fetchall()
                    
                    conexion_notif.close()
                    
                    # Notificar a cada jefe de TI
                    for jefe_ti in jefes_ti:
                        ControlNotificaciones.crear_notificacion(
                            id_usuario=jefe_ti[0],
                            titulo=f"Diagnóstico Actualizado - Incidente #{id_incidente}",
                            mensaje=f"{nombre_tecnico} ha actualizado el diagnóstico del incidente '{titulo_incidente}'. Por favor, revísalo nuevamente.",
                            tipo="diagnostico",
                            id_referencia=id_incidente
                        )
                    
                    print(f"✅ Notificación enviada al Jefe de TI sobre actualización de diagnóstico por {nombre_tecnico}")
            
            return 0 

        except Exception as e:
            print(f"Error en actualizar => {e}")
            import traceback
            traceback.print_exc()
            return -1
    
    @staticmethod
    def aceptar_revision(id_diagnostico, id_incidente):
        from controllers.control_incidentes import ControlIncidentes
        from controllers.control_notificaciones import ControlNotificaciones
        
        try:
            # Obtener información del incidente antes de actualizar
            incidente_anterior = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            if not incidente_anterior:
                print(f"Incidente {id_incidente} no encontrado")
                return False
                
            estado_anterior = incidente_anterior.get('estado')
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False

            # Cambiar estado del incidente a 'T' (Terminado)
            sql = """
                UPDATE INCIDENTE
                SET estado = 'T', fecha_resolucion = NOW()
                WHERE id_incidente = %s;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_incidente,))
                conexion.commit()
                afectadas = cursor.rowcount

            conexion.close()
            
            # Obtener información completa del diagnóstico aceptado
            diagnostico = ControlDiagnosticos.buscar_por_IDDiagnostico(id_diagnostico)
            nombre_tecnico = "Técnico desconocido"
            descripcion_diag = ""
            causa_raiz_diag = ""
            solucion_diag = ""
            
            if diagnostico:
                from controllers.control_Usuarios import controlUsuarios
                usuario_diagnostico = controlUsuarios.buscar_por_ID(diagnostico.get('id_usuario'))
                if usuario_diagnostico:
                    nombre_tecnico = f"{usuario_diagnostico.get('nombre', '')} {usuario_diagnostico.get('ape_pat', '')}"
                
                descripcion_diag = diagnostico.get('descripcion', '')[:200] if diagnostico.get('descripcion') else 'No especificada'
                causa_raiz_diag = diagnostico.get('causa_raiz', '')[:200] if diagnostico.get('causa_raiz') else 'No especificada'
                solucion_diag = diagnostico.get('solucion_propuesta', '')[:200] if diagnostico.get('solucion_propuesta') else 'No especificada'
            
            # Construir mensaje detallado para el historial
            mensaje_historial = f"Diagnóstico D{id_diagnostico} aceptado por el Jefe de TI - Incidente terminado.\n"
            mensaje_historial += f"Realizado por: {nombre_tecnico}\n"
            mensaje_historial += f"Descripción: {descripcion_diag}\n"
            mensaje_historial += f"Causa raíz: {causa_raiz_diag}\n"
            if solucion_diag and solucion_diag != 'No especificada':
                mensaje_historial += f"Solución propuesta: {solucion_diag}"
            
            # Registrar en historial si se actualizó correctamente
            if afectadas > 0 and estado_anterior != 'T':
                ControlIncidentes.insertar_historial(
                    id_incidente=id_incidente,
                    estado_anterior=estado_anterior,
                    estado_nuevo='T',
                    observacion=mensaje_historial
                )
                
                # Notificar a todos los involucrados
                titulo_incidente = incidente_anterior.get('titulo', f'Incidente #{id_incidente}')
                id_tecnico_diagnostico = diagnostico.get('id_usuario') if diagnostico else None
                
                # Notificar al usuario que reportó el incidente
                ControlNotificaciones.notificar_estado_incidente(id_incidente, 'T', incidente_anterior['id_usuario'])
                
                # Notificar PRIMERO al técnico que hizo el diagnóstico con mensaje personalizado
                if id_tecnico_diagnostico:
                    ControlNotificaciones.crear_notificacion(
                        id_usuario=id_tecnico_diagnostico,
                        titulo=f"✅ Tu Diagnóstico fue Aceptado - Incidente #{id_incidente}",
                        mensaje=f"¡Excelente trabajo! Tu diagnóstico para el incidente '{titulo_incidente}' ha sido aceptado por el Jefe de TI. El incidente está terminado.",
                        tipo="diagnostico",
                        id_referencia=id_incidente
                    )
                    print(f"✅ Notificación de aceptación enviada al técnico {nombre_tecnico}")
                
                # Notificar a otros técnicos en el equipo técnico
                equipo = ControlIncidentes.obtener_equipo_tecnico(id_incidente)
                for miembro in equipo:
                    # No duplicar notificación si es el mismo técnico que hizo el diagnóstico
                    if miembro['id_usuario'] != id_tecnico_diagnostico:
                        ControlNotificaciones.crear_notificacion(
                            id_usuario=miembro['id_usuario'],
                            titulo=f"Incidente #{id_incidente} Terminado",
                            mensaje=f"El incidente '{titulo_incidente}' ha sido terminado. El diagnóstico fue aceptado.",
                            tipo="incidente",
                            id_referencia=id_incidente
                        )
                
                # Si hay técnico asignado directamente (y no es el que hizo el diagnóstico)
                if incidente_anterior.get('id_tecnico_asignado') and incidente_anterior.get('id_tecnico_asignado') != id_tecnico_diagnostico:
                    ControlNotificaciones.crear_notificacion(
                        id_usuario=incidente_anterior['id_tecnico_asignado'],
                        titulo=f"Incidente #{id_incidente} Terminado",
                        mensaje=f"El incidente '{titulo_incidente}' ha sido terminado. El diagnóstico fue aceptado.",
                        tipo="incidente",
                        id_referencia=id_incidente
                    )
            
            return True

        except Exception as e:
            print(f"Error en aceptar_revision => {e}")
            import traceback
            traceback.print_exc()
            return False
        
    @staticmethod
    def cancelar_revision(id_diagnostico, id_incidente, id_usuario_rechazo=None):
        """
        Rechaza un diagnóstico. Registra el rechazo en REVISION_DIAGNOSTICO.
        También registra en el historial del incidente que el diagnóstico fue rechazado.
        No cambia el estado del incidente, solo marca el diagnóstico como rechazado.
        """
        from controllers.control_incidentes import ControlIncidentes
        
        try:
            # Obtener información completa del diagnóstico antes de rechazarlo
            diagnostico = ControlDiagnosticos.buscar_por_IDDiagnostico(id_diagnostico)
            if not diagnostico:
                print(f"Diagnóstico {id_diagnostico} no encontrado")
                return False
            
            # Obtener nombre del técnico que hizo el diagnóstico
            from controllers.control_Usuarios import controlUsuarios
            usuario_diagnostico = controlUsuarios.buscar_por_ID(diagnostico.get('id_usuario'))
            nombre_tecnico = "Técnico desconocido"
            if usuario_diagnostico:
                nombre_tecnico = f"{usuario_diagnostico.get('nombre', '')} {usuario_diagnostico.get('ape_pat', '')}"
            
            # Obtener detalles del diagnóstico
            descripcion_diag = diagnostico.get('descripcion', '')[:200] if diagnostico.get('descripcion') else 'No especificada'
            causa_raiz_diag = diagnostico.get('causa_raiz', '')[:200] if diagnostico.get('causa_raiz') else 'No especificada'
            solucion_diag = diagnostico.get('solucion_propuesta', '')[:200] if diagnostico.get('solucion_propuesta') else 'No especificada'
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False

            # Crear la tabla si no existe
            sql_create_table = """
                CREATE TABLE IF NOT EXISTS REVISION_DIAGNOSTICO (
                    id_revision SERIAL PRIMARY KEY,
                    id_diagnostico INTEGER NOT NULL,
                    fecha_rechazo TIMESTAMP DEFAULT NOW(),
                    id_usuario INTEGER,
                    FOREIGN KEY (id_diagnostico) REFERENCES DIAGNOSTICO(id_diagnosticos),
                    FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
                );
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql_create_table)
                conexion.commit()
                
                # Verificar si ya existe un rechazo para este diagnóstico
                sql_check = """
                    SELECT id_revision FROM REVISION_DIAGNOSTICO 
                    WHERE id_diagnostico = %s;
                """
                cursor.execute(sql_check, (id_diagnostico,))
                existe = cursor.fetchone()
                
                fue_nuevo_rechazo = False
                if existe:
                    # Actualizar fecha de rechazo (ya estaba rechazado antes)
                    sql_update = """
                        UPDATE REVISION_DIAGNOSTICO
                        SET fecha_rechazo = NOW(), id_usuario = %s
                        WHERE id_diagnostico = %s;
                    """
                    cursor.execute(sql_update, (id_usuario_rechazo, id_diagnostico))
                else:
                    # Insertar nuevo rechazo
                    fue_nuevo_rechazo = True
                    sql_insert = """
                        INSERT INTO REVISION_DIAGNOSTICO (id_diagnostico, id_usuario, fecha_rechazo)
                        VALUES (%s, %s, NOW());
                    """
                    cursor.execute(sql_insert, (id_diagnostico, id_usuario_rechazo))
                
                conexion.commit()

            conexion.close()
            
            # Obtener el estado actual del incidente
            incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            estado_actual = incidente.get('estado') if incidente else None
            
            # Construir mensaje detallado para el historial
            mensaje = f"Diagnóstico D{id_diagnostico} rechazado por el Jefe de TI.\n"
            if not fue_nuevo_rechazo:
                mensaje = f"Diagnóstico D{id_diagnostico} rechazado nuevamente por el Jefe de TI.\n"
            mensaje += f"Realizado por: {nombre_tecnico}\n"
            mensaje += f"Descripción: {descripcion_diag}\n"
            mensaje += f"Causa raíz: {causa_raiz_diag}\n"
            if solucion_diag and solucion_diag != 'No especificada':
                mensaje += f"Solución propuesta: {solucion_diag}"
            
            # Registrar en el historial del incidente que el diagnóstico fue rechazado
            # Registrar siempre, incluso si ya estaba rechazado antes (para mantener el historial completo)
            ControlIncidentes.insertar_historial(
                id_incidente=id_incidente,
                estado_anterior=estado_actual,
                estado_nuevo=estado_actual,  # El estado no cambia
                observacion=mensaje
            )
            
            # Notificar al técnico que hizo el diagnóstico
            from controllers.control_notificaciones import ControlNotificaciones
            titulo_incidente = incidente.get('titulo', f'Incidente #{id_incidente}')
            id_tecnico = diagnostico.get('id_usuario')
            
            if id_tecnico:
                ControlNotificaciones.crear_notificacion(
                    id_usuario=id_tecnico,
                    titulo=f"Diagnóstico Rechazado - Incidente #{id_incidente}",
                    mensaje=f"Tu diagnóstico para el incidente '{titulo_incidente}' ha sido rechazado por el Jefe de TI. Por favor, revísalo y actualízalo.",
                    tipo="diagnostico",
                    id_referencia=id_incidente
                )
                print(f"✅ Notificación enviada al técnico {nombre_tecnico} sobre rechazo del diagnóstico")
            
            return True

        except Exception as e:
            print(f"Error en cancelar_revision => {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def obtener_diagnosticos_filtrados(self, id_usuario, titulo='', causa=''):
        conexion = None
        try:
            # Asegurar que los parámetros sean strings
            titulo = str(titulo) if titulo else ''
            causa = str(causa) if causa else ''
            
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return []
            
            cursor = conexion.cursor()

            query = """
                SELECT 
                    d.id_diagnosticos, 
                    d.id_incidente, 
                    i.titulo as titulo_incidente,
                    i.descripcion as descripcion_incidente,
                    d.fecha_diagnostico, 
                    d.fecha_actualizacion, 
                    d.causa_raiz, 
                    d.solucion_propuesta,
                    d.descripcion as descripcion_diagnostico,
                    COALESCE(u.nombre, '') || ' ' || COALESCE(u.ape_pat, '') || ' ' || COALESCE(u.ape_mat, '') as creado_por
                FROM DIAGNOSTICO d
                JOIN INCIDENTE i ON d.id_incidente = i.id_incidente
                JOIN USUARIO u ON d.id_usuario = u.id_usuario
                WHERE (%s = '' OR i.titulo ILIKE %s OR i.descripcion ILIKE %s)
                AND (%s = '' OR d.causa_raiz ILIKE %s)
                AND d.id_usuario = %s
                AND i.estado = 'A'
                ORDER BY d.fecha_diagnostico DESC;
            """
            valores = (titulo, f"%{titulo}%", f"%{titulo}%", causa, f"%{causa}%", id_usuario)
            cursor.execute(query, valores)
            diagnosticos = cursor.fetchall()

            lista = []
            for d in diagnosticos:
                lista.append({
                    "id_diagnosticos": d[0],
                    "id_incidente": d[1],
                    "titulo_incidente": d[2] if d[2] else f"INC-{d[1]}",
                    "descripcion_incidente": d[3] if d[3] else '',
                    "descripcion": d[8] if d[8] else '',  # descripcion del diagnóstico
                    "fecha_diagnostico": d[4].strftime('%Y-%m-%d %H:%M:%S') if d[4] else '',
                    "fecha_actualizacion": d[5].strftime('%Y-%m-%d %H:%M:%S') if d[5] else '',
                    "causa_raiz": d[6] if d[6] else '',
                    "solucion_propuesta": d[7] if d[7] else '',
                    "creado_por": d[9] if d[9] else 'N/A'
                })
            
            return lista
        except Exception as e:
            print(f"Error en obtener_diagnosticos_filtrados => {e}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            if conexion:
                conexion.close()

