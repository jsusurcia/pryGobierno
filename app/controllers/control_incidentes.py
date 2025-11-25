from ConexionBD import get_connection
class ControlIncidentes:
    @staticmethod

    def insertar_incidentes(titulo, descripcion, id_categoria, id_usuario, nivel=None):
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            # Asegurar que los strings estén correctamente codificados en UTF-8
            if isinstance(titulo, bytes):
                titulo = titulo.decode('utf-8', errors='ignore')
            if isinstance(descripcion, bytes):
                descripcion = descripcion.decode('utf-8', errors='ignore')
            
            # Convertir a string si no lo es
            titulo = str(titulo) if titulo else ''
            descripcion = str(descripcion) if descripcion else ''
            
            # Limpiar y normalizar strings
            titulo = titulo.strip()
            descripcion = descripcion.strip()

            # Si no se proporciona nivel, usar 'B' (Bajo) como valor por defecto
            # El jefe de TI puede cambiarlo después cuando acepte el incidente
            if nivel is None:
                nivel = 'B'  # Valor por defecto: Bajo
                print(f"ℹ️ Asignando nivel por defecto 'B' (Bajo). El jefe de TI puede cambiarlo después.")
            
            # Validar que el nivel sea válido
            if nivel not in ['B', 'M', 'A', 'C']:
                print(f"⚠️ Nivel '{nivel}' no es válido, usando 'B' por defecto")
                nivel = 'B'
            
            # Insertar incidente con nivel
            sql = """
                INSERT INTO INCIDENTE (titulo, descripcion, id_categoria, id_usuario, nivel, estado)
                VALUES (%s, %s, %s, %s, %s, 'P')
                RETURNING id_incidente;
            """
            with conexion.cursor() as cursor:
                # Asegurar encoding UTF-8 antes de ejecutar
                cursor.execute("SET CLIENT_ENCODING TO 'UTF8';")
                cursor.execute(sql, (titulo, descripcion, id_categoria, id_usuario, nivel))
                id_incidente = cursor.fetchone()[0]
                conexion.commit()
            conexion.close()
            print(f"✅ Incidente creado con nivel '{nivel}' (ID: {id_incidente})")
            return id_incidente
                
        except Exception as e:
            print(f"❌ Error en insertar => {e}")
            import traceback
            traceback.print_exc()
            return -1
        
    def buscar_por_IDIncidente(id_incidente):
        try:
            sql = "SELECT * FROM INCIDENTE WHERE id_incidente = %s"
            atributos = [
                'id_incidente', 'titulo', 'descripcion', 'id_categoria',
                'id_usuario', 'id_tecnico_asignado', 'estado', 'nivel', 
                'fecha_reporte', 'fecha_resolucion', 'tiempo_reparacion'
            ]

            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_incidente,))
                incidente = cursor.fetchone()

            conexion.close()
            incidente_dict = dict(zip(atributos, incidente)) if incidente else None
            return incidente_dict
        except Exception as e:
            print(f"Error en buscar_por_ID => {e}")
            return None
        
    def listar_incidentes(id_usuario=None, id_rol=None):
        """
        Lista incidentes según el usuario y rol.
        - Si id_rol == 1 (Jefe de TI): todos los incidentes
        - Si es jefe (tipo J): solo los que creó (id_usuario)
        - Si es técnico (tipo T): solo los asignados (id_tecnico_asignado) o en equipo técnico
        """
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return []

            # Construir la consulta según el rol
            if id_rol == 1:
                # Jefe de TI: ver todos los incidentes
                sql = """
                    SELECT 
                        i.id_incidente,
                        i.titulo,
                        i.descripcion,
                        COALESCE(c.nombre, 'Sin categoría') AS categoria,
                        i.estado,
                        i.nivel,
                        i.fecha_reporte,
                        i.fecha_resolucion,
                        i.tiempo_reparacion,
                        i.id_usuario,
                        i.id_tecnico_asignado
                    FROM INCIDENTE i
                    LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                    ORDER BY i.id_incidente DESC;
                """
                params = ()
            elif id_usuario:
                # Para jefes o técnicos: filtrar según corresponda
                # Primero verificamos si es jefe o técnico consultando el rol
                from controllers.controlador_rol import ControlRol
                if id_rol:
                    rol = ControlRol.buscar_por_IDRol(id_rol)
                    tipo_rol = rol.get('tipo') if rol else None
                    
                    if tipo_rol == 'J':
                        # Jefe: solo los que creó
                        sql = """
                            SELECT 
                                i.id_incidente,
                                i.titulo,
                                i.descripcion,
                                COALESCE(c.nombre, 'Sin categoría') AS categoria,
                                i.estado,
                                i.nivel,
                                i.fecha_reporte,
                                i.fecha_resolucion,
                                i.tiempo_reparacion,
                                i.id_usuario,
                                i.id_tecnico_asignado
                            FROM INCIDENTE i
                            LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                            WHERE i.id_usuario = %s
                            ORDER BY i.id_incidente DESC;
                        """
                        params = (id_usuario,)
                    elif tipo_rol == 'T':
                        # Técnico: los asignados directamente o en equipo técnico
                        sql = """
                            SELECT DISTINCT
                                i.id_incidente,
                                i.titulo,
                                i.descripcion,
                                COALESCE(c.nombre, 'Sin categoría') AS categoria,
                                i.estado,
                                i.nivel,
                                i.fecha_reporte,
                                i.fecha_resolucion,
                                i.tiempo_reparacion,
                                i.id_usuario,
                                i.id_tecnico_asignado
                            FROM INCIDENTE i
                            LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                            LEFT JOIN EQUIPO_TECNICO et ON i.id_incidente = et.id_incidente
                            WHERE i.id_tecnico_asignado = %s OR et.id_usuario = %s
                            ORDER BY i.id_incidente DESC;
                        """
                        params = (id_usuario, id_usuario)
                    else:
                        # Otro tipo de rol: sin incidentes
                        return []
                else:
                    # Sin rol definido: sin incidentes
                    return []
            else:
                # Sin usuario: sin incidentes
                return []

            with conexion.cursor() as cursor:
                cursor.execute(sql, params)
                filas = cursor.fetchall()

            atributos = [
                'id_incidente', 'titulo', 'descripcion',
                'categoria', 'estado', 'nivel', 'fecha_reporte',
                'fecha_resolucion', 'tiempo_reparacion', 'id_usuario', 'id_tecnico_asignado'
            ]

            incidentes = [dict(zip(atributos, fila)) for fila in filas]

            # Traducir estado corto a texto completo
            estado_map = {
                'P': 'Pendiente',
                'A': 'Activo',
                'T': 'Terminado',
                'C': 'Cancelado'
            }

            for inc in incidentes:
                if inc.get('estado'):
                    estado_corto = inc['estado'].upper()
                    inc['estado'] = estado_map.get(estado_corto, inc['estado'])
                    inc['estado_corto'] = estado_corto  # Guardar también el código corto
                if inc.get('fecha_reporte'):
                    inc['fecha_reporte'] = inc['fecha_reporte'].strftime('%Y-%m-%d')

            conexion.close()
            return incidentes

        except Exception as e:
            print(f"Error en listar_incidentes => {e}")
            import traceback
            traceback.print_exc()
            return []

        
    def actualizar_incidentes(id_incidente, titulo, descripcion, id_categoria, id_usuario, estado, nivel=None):
        try:
            if nivel:
                sql = """
                    UPDATE INCIDENTE
                    SET titulo = %s,
                        descripcion = %s,
                        id_categoria = %s,
                        id_usuario = %s,
                        estado = %s,
                        nivel = %s
                    WHERE id_incidente = %s;
                """
                params = (titulo, descripcion, id_categoria, id_usuario, estado, nivel, id_incidente)
            else:
                sql = """
                    UPDATE INCIDENTE
                    SET titulo = %s,
                        descripcion = %s,
                        id_categoria = %s,
                        id_usuario = %s,
                        estado = %s
                    WHERE id_incidente = %s;
                """
                params = (titulo, descripcion, id_categoria, id_usuario, estado, id_incidente)
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            with conexion.cursor() as cursor:
                cursor.execute(sql, params)
                conexion.commit()

            conexion.close()
            return 0  
        except Exception as e:
            print(f"Error en actualizar => {e}")
            return -1
        
    def actualizar_estado(id_incidente, nuevo_estado):
        try:
            # Obtener estado anterior antes de actualizar
            incidente_anterior = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            estado_anterior = incidente_anterior.get('estado') if incidente_anterior else None
            
            sql = """
                UPDATE INCIDENTE
                SET estado = %s,
                    fecha_resolucion = CASE
                        WHEN %s IN ('C', 'T') THEN NOW()
                        ELSE fecha_resolucion
                    END,
                    tiempo_reparacion = CASE
                        WHEN %s IN ('C', 'T') THEN NOW() - fecha_reporte
                        ELSE tiempo_reparacion
                    END
                WHERE id_incidente = %s;
            """

            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            with conexion.cursor() as cursor:
                cursor.execute(sql, (nuevo_estado, nuevo_estado, nuevo_estado, id_incidente))
                conexion.commit()

            conexion.close()
            
            # Registrar en historial si cambió el estado
            if estado_anterior != nuevo_estado:
                ControlIncidentes.insertar_historial(
                    id_incidente=id_incidente,
                    estado_anterior=estado_anterior,
                    estado_nuevo=nuevo_estado,
                    observacion=f"Estado cambiado de {estado_anterior} a {nuevo_estado}"
                )
            
            return 0  

        except Exception as e:
            print(f"Error en actualizar_estado => {e}")
            return -1

    @staticmethod
    def cambiar_estado_jefe_ti(id_incidente, nuevo_estado):
        """Cambia el estado de un incidente (A o C) por el jefe de TI"""
        try:
            # Obtener estado anterior antes de actualizar
            incidente_anterior = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            estado_anterior = incidente_anterior.get('estado') if incidente_anterior else None
            
            # Si se cancela (C), también calcular tiempo_reparacion y fecha_resolucion
            sql = """
                UPDATE INCIDENTE
                SET estado = %s,
                    fecha_resolucion = CASE
                        WHEN %s = 'C' THEN NOW()
                        ELSE fecha_resolucion
                    END,
                    tiempo_reparacion = CASE
                        WHEN %s = 'C' THEN NOW() - fecha_reporte
                        ELSE tiempo_reparacion
                    END
                WHERE id_incidente = %s AND estado = 'P'
            """
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (nuevo_estado, nuevo_estado, nuevo_estado, id_incidente))
                conexion.commit()
                afectadas = cursor.rowcount
            
            conexion.close()
            
            # Registrar en historial si se actualizó correctamente
            if afectadas > 0 and estado_anterior != nuevo_estado:
                estado_texto = "Aceptado" if nuevo_estado == 'A' else "Cancelado"
                ControlIncidentes.insertar_historial(
                    id_incidente=id_incidente,
                    estado_anterior=estado_anterior,
                    estado_nuevo=nuevo_estado,
                    observacion=f"Incidente {estado_texto} por el Jefe de TI"
                )
            
            return afectadas > 0
        except Exception as e:
            print(f"Error en cambiar_estado_jefe_ti => {e}")
            return False

    @staticmethod
    def asignar_nivel_prioridad(id_incidente, nivel):
        """Asigna nivel de prioridad a un incidente aceptado"""
        try:
            # Obtener prioridad anterior antes de actualizar
            incidente_anterior = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            prioridad_anterior = incidente_anterior.get('nivel') if incidente_anterior else None
            
            sql = """
                UPDATE INCIDENTE
                SET nivel = %s
                WHERE id_incidente = %s AND estado = 'A'
            """
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (nivel, id_incidente))
                conexion.commit()
                afectadas = cursor.rowcount
            
            conexion.close()
            
            # Registrar en historial si se actualizó correctamente
            if afectadas > 0 and prioridad_anterior != nivel:
                nivel_map = {'B': 'Bajo', 'M': 'Medio', 'A': 'Alto', 'C': 'Crítico'}
                nivel_anterior_texto = nivel_map.get(prioridad_anterior, prioridad_anterior) if prioridad_anterior else 'Sin prioridad'
                nivel_nuevo_texto = nivel_map.get(nivel, nivel)
                ControlIncidentes.insertar_historial(
                    id_incidente=id_incidente,
                    prioridad_anterior=prioridad_anterior,
                    prioridad_nueva=nivel,
                    observacion=f"Prioridad cambiada de {nivel_anterior_texto} a {nivel_nuevo_texto}"
                )
            
            return afectadas > 0
        except Exception as e:
            print(f"Error en asignar_nivel_prioridad => {e}")
            return False

    @staticmethod
    def asignar_tecnico_individual(id_incidente, id_tecnico):
        """Asigna un técnico individual como responsable"""
        try:
            # Obtener técnico anterior antes de actualizar
            incidente_anterior = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            tecnico_anterior = incidente_anterior.get('id_tecnico_asignado') if incidente_anterior else None
            
            sql = """
                UPDATE INCIDENTE
                SET id_tecnico_asignado = %s
                WHERE id_incidente = %s AND estado = 'A'
            """
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_tecnico, id_incidente))
                conexion.commit()
                afectadas = cursor.rowcount
            
            conexion.close()
            
            # Registrar en historial si se actualizó correctamente
            if afectadas > 0 and tecnico_anterior != id_tecnico:
                ControlIncidentes.insertar_historial(
                    id_incidente=id_incidente,
                    tecnico_anterior=tecnico_anterior,
                    tecnico_nuevo=id_tecnico,
                    observacion="Técnico asignado al incidente"
                )
            
            return True
        except Exception as e:
            print(f"Error en asignar_tecnico_individual => {e}")
            return False

    @staticmethod
    def agregar_a_equipo_tecnico(id_incidente, id_usuario, es_responsable=False):
        """Agrega un usuario al equipo técnico de un incidente"""
        try:
            from controllers.control_Usuarios import controlUsuarios
            
            # Verificar si ya está en el equipo
            sql_check = """
                SELECT id_equipo FROM EQUIPO_TECNICO
                WHERE id_incidente = %s AND id_usuario = %s
            """
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql_check, (id_incidente, id_usuario))
                existe = cursor.fetchone()
                
                if existe:
                    conexion.close()
                    return True  # Ya está en el equipo
                
                # Si es responsable, también asignarlo como técnico principal
                if es_responsable:
                    sql_principal = """
                        UPDATE INCIDENTE
                        SET id_tecnico_asignado = %s
                        WHERE id_incidente = %s
                    """
                    cursor.execute(sql_principal, (id_usuario, id_incidente))
                
                # Agregar al equipo
                sql_insert = """
                    INSERT INTO EQUIPO_TECNICO (id_incidente, id_usuario, fecha_asignacion)
                    VALUES (%s, %s, NOW())
                """
                cursor.execute(sql_insert, (id_incidente, id_usuario))
                conexion.commit()
            
            conexion.close()
            
            # Registrar en historial
            tecnico = controlUsuarios.buscar_por_ID(id_usuario)
            nombre_tecnico = f"{tecnico['nombre']} {tecnico['ape_pat']}" if tecnico else "Técnico desconocido"
            tipo_asignacion = "responsable" if es_responsable else "miembro del equipo técnico"
            
            ControlIncidentes.insertar_historial(
                id_incidente=id_incidente,
                tecnico_nuevo=id_usuario,
                observacion=f"{nombre_tecnico} agregado como {tipo_asignacion}"
            )
            
            return True
        except Exception as e:
            print(f"Error en agregar_a_equipo_tecnico => {e}")
            return False

    @staticmethod
    def obtener_incidentes_disponibles_tecnicos(id_usuario=None):
        """Obtiene incidentes disponibles para técnicos (Bajo/Medio, estado A, sin límite alcanzado)
        Si se proporciona id_usuario, incluye información sobre si el usuario ya está trabajando en cada incidente
        y excluye incidentes donde el usuario ya tiene un diagnóstico pendiente de revisión"""
        try:
            conexion = get_connection()
            if not conexion:
                return []
            
            # Construir la consulta con o sin verificación de usuario
            if id_usuario:
                sql = """
                    SELECT 
                        i.id_incidente,
                        i.titulo,
                        i.descripcion,
                        c.nombre as categoria,
                        i.nivel,
                        i.fecha_reporte,
                        COUNT(et.id_usuario) as personas_trabajando,
                        CASE WHEN EXISTS (
                            SELECT 1 FROM EQUIPO_TECNICO et2 
                            WHERE et2.id_incidente = i.id_incidente 
                            AND et2.id_usuario = %s
                        ) THEN TRUE ELSE FALSE END as ya_esta_trabajando
                    FROM INCIDENTE i
                    LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                    LEFT JOIN EQUIPO_TECNICO et ON i.id_incidente = et.id_incidente
                    WHERE i.estado = 'A'
                    AND i.nivel IN ('B', 'M')
                    AND (i.id_tecnico_asignado IS NULL OR i.nivel IN ('B', 'M'))
                    -- Excluir incidentes donde el usuario ya tiene un diagnóstico pendiente
                    -- Si el diagnóstico fue rechazado y no fue actualizado después, el incidente puede aparecer para agregar otro diagnóstico
                    AND NOT EXISTS (
                        SELECT 1 
                        FROM DIAGNOSTICO d
                        LEFT JOIN REVISION_DIAGNOSTICO rd ON d.id_diagnosticos = rd.id_diagnostico
                        WHERE d.id_incidente = i.id_incidente
                        AND d.id_usuario = %s
                        AND (
                            -- Si no tiene revisión, está pendiente (excluir)
                            rd.id_revision IS NULL
                            OR (
                                -- Si tiene revisión rechazada PERO el diagnóstico fue actualizado después del rechazo, está pendiente de nuevo (excluir)
                                rd.id_revision IS NOT NULL 
                                AND d.fecha_actualizacion IS NOT NULL
                                AND d.fecha_actualizacion > rd.fecha_rechazo
                            )
                        )
                    )
                    GROUP BY i.id_incidente, i.titulo, i.descripcion, c.nombre, i.nivel, i.fecha_reporte
                    HAVING 
                        (i.nivel = 'B' AND COUNT(et.id_usuario) < 3)
                        OR (i.nivel = 'M' AND COUNT(et.id_usuario) < 5)
                    ORDER BY 
                        CASE i.nivel 
                            WHEN 'M' THEN 1 
                            WHEN 'B' THEN 2 
                        END,
                        i.fecha_reporte ASC
                """
                params = (id_usuario, id_usuario)
            else:
                sql = """
                    SELECT 
                        i.id_incidente,
                        i.titulo,
                        i.descripcion,
                        c.nombre as categoria,
                        i.nivel,
                        i.fecha_reporte,
                        COUNT(et.id_usuario) as personas_trabajando,
                        FALSE as ya_esta_trabajando
                    FROM INCIDENTE i
                    LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                    LEFT JOIN EQUIPO_TECNICO et ON i.id_incidente = et.id_incidente
                    WHERE i.estado = 'A'
                    AND i.nivel IN ('B', 'M')
                    AND (i.id_tecnico_asignado IS NULL OR i.nivel IN ('B', 'M'))
                    GROUP BY i.id_incidente, i.titulo, i.descripcion, c.nombre, i.nivel, i.fecha_reporte
                    HAVING 
                        (i.nivel = 'B' AND COUNT(et.id_usuario) < 3)
                        OR (i.nivel = 'M' AND COUNT(et.id_usuario) < 5)
                    ORDER BY 
                        CASE i.nivel 
                            WHEN 'M' THEN 1 
                            WHEN 'B' THEN 2 
                        END,
                        i.fecha_reporte ASC
                """
                params = ()
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, params)
                resultados = cursor.fetchall()
            
            conexion.close()
            
            return [
                {
                    'id_incidente': r[0],
                    'titulo': r[1],
                    'descripcion': r[2],
                    'categoria': r[3],
                    'nivel': r[4],
                    'fecha_reporte': r[5],
                    'personas_trabajando': r[6],
                    'ya_esta_trabajando': r[7] if len(r) > 7 else False
                }
                for r in resultados
            ]
        except Exception as e:
            print(f"Error en obtener_incidentes_disponibles_tecnicos => {e}")
            import traceback
            traceback.print_exc()
            return []

    @staticmethod
    def tomar_incidente_disponible(id_incidente, id_usuario):
        """Permite a un técnico tomar un incidente disponible"""
        try:
            from controllers.control_Usuarios import controlUsuarios
            from controllers.control_notificaciones import ControlNotificaciones
            
            # Verificar límite de tickets activos
            tickets_activos = controlUsuarios.contar_tickets_activos(id_usuario)
            tickets_equipo = controlUsuarios.contar_tickets_en_equipo(id_usuario)
            total_tickets = tickets_activos + tickets_equipo
            
            # Obtener información del incidente
            incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            if not incidente:
                return {'exito': False, 'mensaje': 'Incidente no encontrado'}
            
            # Verificar si es crítico o alto asignado
            es_critico = incidente.get('nivel') == 'C'
            es_alto_asignado = incidente.get('nivel') == 'A' and incidente.get('id_tecnico_asignado') == id_usuario
            
            # Verificar límite (máximo 3, excepto si es crítico o alto asignado)
            if total_tickets >= 3 and not es_critico and not es_alto_asignado:
                return {'exito': False, 'mensaje': f'Ya tienes {total_tickets} tickets activos. Máximo permitido: 3'}
            
            # Verificar que el incidente esté disponible
            if incidente.get('estado') != 'A' or incidente.get('nivel') not in ['B', 'M']:
                return {'exito': False, 'mensaje': 'Este incidente no está disponible para tomar'}
            
            # Verificar límite de personas trabajando
            conexion = get_connection()
            if not conexion:
                return {'exito': False, 'mensaje': 'Error de conexión'}
            
            with conexion.cursor() as cursor:
                # Verificar si el usuario ya está trabajando en este incidente
                sql_verificar_usuario = """
                    SELECT COUNT(*) FROM EQUIPO_TECNICO
                    WHERE id_incidente = %s AND id_usuario = %s
                """
                cursor.execute(sql_verificar_usuario, (id_incidente, id_usuario))
                ya_esta_en_equipo = cursor.fetchone()[0] > 0
                
                if ya_esta_en_equipo:
                    conexion.close()
                    return {'exito': False, 'mensaje': 'Ya estás trabajando en este incidente'}
                
                # Verificar límite de personas trabajando
                sql_count = """
                    SELECT COUNT(*) FROM EQUIPO_TECNICO
                    WHERE id_incidente = %s
                """
                cursor.execute(sql_count, (id_incidente,))
                count = cursor.fetchone()[0]
                
                max_personas = 3 if incidente.get('nivel') == 'B' else 5
                if count >= max_personas:
                    conexion.close()
                    return {'exito': False, 'mensaje': f'Ya hay {count} personas trabajando en este incidente (máximo: {max_personas})'}
                
                # Agregar al equipo
                sql_insert = """
                    INSERT INTO EQUIPO_TECNICO (id_incidente, id_usuario, fecha_asignacion)
                    VALUES (%s, %s, NOW())
                """
                cursor.execute(sql_insert, (id_incidente, id_usuario))
                conexion.commit()
            
            conexion.close()
            
            # Obtener información del técnico
            tecnico = controlUsuarios.buscar_por_ID(id_usuario)
            nombre_tecnico = f"{tecnico['nombre']} {tecnico['ape_pat']}" if tecnico else "un técnico"
            
            # Registrar en historial
            ControlIncidentes.insertar_historial(
                id_incidente=id_incidente,
                tecnico_nuevo=id_usuario,
                observacion=f"{nombre_tecnico} tomó el incidente y se unió al equipo técnico"
            )
            
            # Si es el primer técnico en el equipo, notificar al usuario reportante
            if count == 0:
                ControlNotificaciones.notificar_asignacion_a_reportante(id_incidente, id_usuario, nombre_tecnico, True)
            
            return {'exito': True, 'mensaje': 'Incidente tomado correctamente'}
        except Exception as e:
            print(f"Error en tomar_incidente_disponible => {e}")
            return {'exito': False, 'mensaje': f'Error: {str(e)}'}

    @staticmethod
    def obtener_incidentes_pendientes_jefe_ti():
        """Obtiene incidentes pendientes para el jefe de TI con información del área"""
        try:
            conexion = get_connection()
            if not conexion:
                return []
            
            sql = """
                SELECT 
                    i.id_incidente,
                    i.titulo,
                    i.descripcion,
                    c.nombre as categoria,
                    u.nombre || ' ' || u.ape_pat || ' ' || u.ape_mat as reportado_por,
                    a.nombre as area,
                    i.fecha_reporte,
                    i.nivel
                FROM INCIDENTE i
                LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                LEFT JOIN USUARIO u ON i.id_usuario = u.id_usuario
                LEFT JOIN ROL r ON u.id_rol = r.id_rol
                LEFT JOIN AREA a ON r.id_area = a.id_area
                WHERE i.estado = 'P'
                ORDER BY i.fecha_reporte ASC
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultados = cursor.fetchall()
            
            conexion.close()
            
            return [
                {
                    'id_incidente': r[0],
                    'titulo': r[1],
                    'descripcion': r[2],
                    'categoria': r[3],
                    'reportado_por': r[4],
                    'area': r[5],
                    'fecha_reporte': r[6],
                    'nivel': r[7]
                }
                for r in resultados
            ]
        except Exception as e:
            print(f"Error en obtener_incidentes_pendientes_jefe_ti => {e}")
            return []
    
    @staticmethod
    def obtener_evidencias_incidente(id_incidente):
        """Obtiene las evidencias de un incidente"""
        try:
            from controllers.control_evidencias import controlEvidencias
            conexion = get_connection()
            if not conexion:
                return []
            
            sql = """
                SELECT id_evidencias, url_archivo, fecha_subida
                FROM EVIDENCIAS
                WHERE id_incidente = %s
                ORDER BY fecha_subida DESC
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_incidente,))
                resultados = cursor.fetchall()
            
            conexion.close()
            
            return [
                {
                    'id_evidencias': r[0],
                    'url_archivo': r[1],
                    'fecha_subida': r[2]
                }
                for r in resultados
            ]
        except Exception as e:
            print(f"Error en obtener_evidencias_incidente => {e}")
            return []
    
    @staticmethod
    def insertar_historial(id_incidente, estado_anterior=None, estado_nuevo=None, 
                          tecnico_anterior=None, tecnico_nuevo=None,
                          prioridad_anterior=None, prioridad_nueva=None, 
                          observacion=None):
        """Inserta un registro en el historial de incidentes"""
        try:
            conexion = get_connection()
            if not conexion:
                return False
            
            sql = """
                INSERT INTO HISTORIAL_INCIDENTE 
                (id_incidente, estado_anterior, estado_nuevo, tecnico_anterior, tecnico_nuevo,
                 prioridad_anterior, prioridad_nueva, observacion, fecha)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (
                    id_incidente, estado_anterior, estado_nuevo,
                    tecnico_anterior, tecnico_nuevo,
                    prioridad_anterior, prioridad_nueva, observacion
                ))
                conexion.commit()
            
            conexion.close()
            return True
        except Exception as e:
            print(f"Error en insertar_historial => {e}")
            return False
    
    @staticmethod
    def obtener_historial_incidente(id_incidente):
        """Obtiene el historial de cambios de un incidente"""
        try:
            conexion = get_connection()
            if not conexion:
                return []
            
            sql = """
                SELECT 
                    h.id_historial,
                    h.estado_anterior,
                    h.estado_nuevo,
                    h.prioridad_anterior,
                    h.prioridad_nueva,
                    h.fecha,
                    h.observacion,
                    u_anterior.nombre || ' ' || u_anterior.ape_pat as tecnico_anterior_nombre,
                    u_nuevo.nombre || ' ' || u_nuevo.ape_pat as tecnico_nuevo_nombre
                FROM HISTORIAL_INCIDENTE h
                LEFT JOIN USUARIO u_anterior ON h.tecnico_anterior = u_anterior.id_usuario
                LEFT JOIN USUARIO u_nuevo ON h.tecnico_nuevo = u_nuevo.id_usuario
                WHERE h.id_incidente = %s
                ORDER BY h.fecha DESC
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_incidente,))
                resultados = cursor.fetchall()
            
            conexion.close()
            
            # Mapear estados
            estado_map = {
                'P': 'Pendiente',
                'A': 'Activo',
                'T': 'Terminado',
                'C': 'Cancelado'
            }
            
            historial = []
            for r in resultados:
                historial.append({
                    'id_historial': r[0],
                    'estado_anterior': estado_map.get(r[1], r[1]) if r[1] else None,
                    'estado_nuevo': estado_map.get(r[2], r[2]) if r[2] else None,
                    'prioridad_anterior': r[3],
                    'prioridad_nueva': r[4],
                    'fecha': r[5],
                    'observacion': r[6],
                    'tecnico_anterior_nombre': r[7],
                    'tecnico_nuevo_nombre': r[8]
                })
            
            return historial
        except Exception as e:
            print(f"Error en obtener_historial_incidente => {e}")
            return []

    @staticmethod
    def obtener_equipo_tecnico(id_incidente):
        """Obtiene el equipo técnico asignado a un incidente"""
        try:
            conexion = get_connection()
            if not conexion:
                return []
            
            sql = """
                SELECT 
                    et.id_equipo,
                    et.id_usuario,
                    u.nombre || ' ' || u.ape_pat || ' ' || u.ape_mat as nombre_completo,
                    et.fecha_asignacion,
                    CASE WHEN i.id_tecnico_asignado = et.id_usuario THEN TRUE ELSE FALSE END as es_responsable
                FROM EQUIPO_TECNICO et
                JOIN USUARIO u ON et.id_usuario = u.id_usuario
                JOIN INCIDENTE i ON et.id_incidente = i.id_incidente
                WHERE et.id_incidente = %s
                ORDER BY es_responsable DESC, et.fecha_asignacion ASC
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_incidente,))
                resultados = cursor.fetchall()
            
            conexion.close()
            
            return [
                {
                    'id_equipo': r[0],
                    'id_usuario': r[1],
                    'nombre_completo': r[2],
                    'fecha_asignacion': r[3],
                    'es_responsable': r[4]
                }
                for r in resultados
            ]
        except Exception as e:
            print(f"Error en obtener_equipo_tecnico => {e}")
            return []
        
    @staticmethod
    def obtener_incidentes_sin_diagnostico(id_usuario=None):
        """
        Obtiene incidentes sin diagnóstico que están en estado 'A' (Activo)
        y que fueron asignados al técnico (id_tecnico_asignado) o que el técnico está en EQUIPO_TECNICO.
        Excluye incidentes donde el usuario ya tiene un diagnóstico pendiente de revisión.
        """
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return []

            if id_usuario:
                # Consulta que verifica ambas condiciones:
                # 1. Incidentes asignados directamente (id_tecnico_asignado)
                # 2. Incidentes donde el técnico está en EQUIPO_TECNICO
                # SOLO estado 'A' (Activo) y sin diagnóstico pendiente de revisión del usuario
                # Excluir incidentes donde el usuario ya tiene un diagnóstico pendiente (sin rechazo)
                # Pero incluir incidentes con diagnóstico rechazado para que pueda agregar otro
                sql = """
                    SELECT DISTINCT
                        i.id_incidente, 
                        i.titulo
                    FROM INCIDENTE i
                    WHERE i.estado = 'A'
                        AND i.id_tecnico_asignado = %s
                        -- Excluir si el usuario tiene un diagnóstico pendiente para este incidente
                        AND NOT EXISTS (
                            SELECT 1 
                            FROM DIAGNOSTICO d
                            LEFT JOIN REVISION_DIAGNOSTICO rd ON d.id_diagnosticos = rd.id_diagnostico
                            WHERE d.id_incidente = i.id_incidente
                            AND d.id_usuario = %s
                            AND (
                                -- Si no tiene revisión, está pendiente (excluir)
                                rd.id_revision IS NULL
                                OR (
                                    -- Si tiene revisión rechazada PERO el diagnóstico fue actualizado después del rechazo, está pendiente de nuevo (excluir)
                                    rd.id_revision IS NOT NULL 
                                    AND d.fecha_actualizacion IS NOT NULL
                                    AND d.fecha_actualizacion > rd.fecha_rechazo
                                )
                            )
                        )
                    
                    UNION
                    
                    SELECT DISTINCT
                        i.id_incidente, 
                        i.titulo
                    FROM EQUIPO_TECNICO et
                    INNER JOIN INCIDENTE i ON et.id_incidente = i.id_incidente
                    WHERE et.id_usuario = %s
                        AND i.estado = 'A'
                        -- Excluir si el usuario tiene un diagnóstico pendiente para este incidente
                        AND NOT EXISTS (
                            SELECT 1 
                            FROM DIAGNOSTICO d
                            LEFT JOIN REVISION_DIAGNOSTICO rd ON d.id_diagnosticos = rd.id_diagnostico
                            WHERE d.id_incidente = i.id_incidente
                            AND d.id_usuario = %s
                            AND (
                                -- Si no tiene revisión, está pendiente (excluir)
                                rd.id_revision IS NULL
                                OR (
                                    -- Si tiene revisión rechazada PERO el diagnóstico fue actualizado después del rechazo, está pendiente de nuevo (excluir)
                                    rd.id_revision IS NOT NULL 
                                    AND d.fecha_actualizacion IS NOT NULL
                                    AND d.fecha_actualizacion > rd.fecha_rechazo
                                )
                            )
                        )
                    
                    ORDER BY id_incidente DESC;
                """
                params = (id_usuario, id_usuario, id_usuario, id_usuario)
            else:
                # Sin usuario: sin incidentes
                return []

            with conexion.cursor() as cursor:
                cursor.execute(sql, params)
                resultado = cursor.fetchall()

            incidentes = [
                {'id_incidente': row[0], 'titulo': row[1]} for row in resultado
            ]

            conexion.close()
            return incidentes

        except Exception as e:
            print("Error al obtener incidentes =>", e)
            import traceback
            traceback.print_exc()
            return []

    def obtener_mttr_por_categoria(self):
        """Calcula el MTTR (Mean Time To Repair) por categoría SOLO con datos reales"""
        try:
            conexion = get_connection()
            if not conexion:
                print("❌ No se pudo conectar a la base de datos.")
                return []

            # Consulta que calcula MTTR usando el campo tiempo_reparacion o calculándolo
            # Solo considera incidentes Terminados ('T') o Cancelados ('C')
            sql = """
                SELECT 
                    COALESCE(c.nombre, 'Sin categoría') AS categoria,
                    CASE 
                        WHEN COUNT(CASE WHEN i.tiempo_reparacion IS NOT NULL THEN 1 END) > 0 THEN
                            ROUND(AVG(EXTRACT(EPOCH FROM i.tiempo_reparacion) / 3600), 2)
                        WHEN COUNT(CASE WHEN i.fecha_resolucion IS NOT NULL AND i.fecha_reporte IS NOT NULL THEN 1 END) > 0 THEN
                            ROUND(AVG(EXTRACT(EPOCH FROM (i.fecha_resolucion - i.fecha_reporte)) / 3600), 2)
                        ELSE 0
                    END AS mttr_horas,
                    COUNT(i.id_incidente) AS total_incidentes
                FROM 
                    INCIDENTE i
                LEFT JOIN 
                    CATEGORIA c ON i.id_categoria = c.id_categoria
                WHERE 
                    i.estado IN ('T', 'C')
                GROUP BY 
                    c.nombre
                ORDER BY 
                    mttr_horas ASC;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultados = cursor.fetchall()

            conexion.close()

            mttr_list = []
            for fila in resultados:
                mttr_list.append({
                    'categoria': fila[0] or 'Sin categoría',
                    'mttr_horas': float(fila[1]) if fila[1] else 0.0,
                    'total_incidentes': int(fila[2]) if fila[2] else 0
                })
            
            return mttr_list

        except Exception as e:
            print(f"⚠️ Error al calcular MTTR => {e}")
            import traceback
            traceback.print_exc()
            return []

    def obtener_estadisticas_mttr(self):
        """Obtiene las métricas de MTTR global y por categoría SOLO con datos reales"""
        try:
            conexion = get_connection()
            if not conexion:
                print("❌ No se pudo conectar a la base de datos.")
                return self._estadisticas_vacias()

            with conexion.cursor() as cursor:
                # MTTR Global usando tiempo_reparacion o calculando
                # Solo incidentes Terminados ('T') o Cancelados ('C')
                cursor.execute("""
                    SELECT 
                        CASE 
                            WHEN COUNT(CASE WHEN tiempo_reparacion IS NOT NULL THEN 1 END) > 0 THEN
                                ROUND(AVG(EXTRACT(EPOCH FROM tiempo_reparacion) / 3600), 2)
                            WHEN COUNT(CASE WHEN fecha_resolucion IS NOT NULL AND fecha_reporte IS NOT NULL THEN 1 END) > 0 THEN
                                ROUND(AVG(EXTRACT(EPOCH FROM (fecha_resolucion - fecha_reporte)) / 3600), 2)
                            ELSE 0
                        END AS mttr_global
                    FROM INCIDENTE
                    WHERE estado IN ('T', 'C');
                """)
                resultado = cursor.fetchone()
                mttr_global = float(resultado[0]) if resultado and resultado[0] else 0.0

                # Total de incidentes
                cursor.execute("SELECT COUNT(*) FROM INCIDENTE;")
                total_incidentes = cursor.fetchone()[0] or 0

                # Mejor categoría (menor MTTR) con datos reales
                cursor.execute("""
                    SELECT 
                        COALESCE(c.nombre, 'Sin categoría') AS nombre, 
                        CASE 
                            WHEN COUNT(CASE WHEN i.tiempo_reparacion IS NOT NULL THEN 1 END) > 0 THEN
                                ROUND(AVG(EXTRACT(EPOCH FROM i.tiempo_reparacion) / 3600), 2)
                            WHEN COUNT(CASE WHEN i.fecha_resolucion IS NOT NULL AND i.fecha_reporte IS NOT NULL THEN 1 END) > 0 THEN
                                ROUND(AVG(EXTRACT(EPOCH FROM (i.fecha_resolucion - i.fecha_reporte)) / 3600), 2)
                            ELSE 999999
                        END AS mttr
                    FROM INCIDENTE i
                    LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                    WHERE i.estado IN ('T', 'C')
                    GROUP BY c.nombre
                    HAVING COUNT(i.id_incidente) > 0
                    ORDER BY mttr ASC
                    LIMIT 1;
                """)
                mejor_categoria = cursor.fetchone()
                mejor_nombre = mejor_categoria[0] if mejor_categoria else "N/A"
                mejor_mttr = float(mejor_categoria[1]) if mejor_categoria and mejor_categoria[1] < 999999 else 0.0

                # Categoría crítica (mayor MTTR) con datos reales
                cursor.execute("""
                    SELECT 
                        COALESCE(c.nombre, 'Sin categoría') AS nombre, 
                        CASE 
                            WHEN COUNT(CASE WHEN i.tiempo_reparacion IS NOT NULL THEN 1 END) > 0 THEN
                                ROUND(AVG(EXTRACT(EPOCH FROM i.tiempo_reparacion) / 3600), 2)
                            WHEN COUNT(CASE WHEN i.fecha_resolucion IS NOT NULL AND i.fecha_reporte IS NOT NULL THEN 1 END) > 0 THEN
                                ROUND(AVG(EXTRACT(EPOCH FROM (i.fecha_resolucion - i.fecha_reporte)) / 3600), 2)
                            ELSE 0
                        END AS mttr
                    FROM INCIDENTE i
                    LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                    WHERE i.estado IN ('T', 'C')
                    GROUP BY c.nombre
                    HAVING COUNT(i.id_incidente) > 0
                    ORDER BY mttr DESC
                    LIMIT 1;
                """)
                categoria_critica = cursor.fetchone()
                crit_nombre = categoria_critica[0] if categoria_critica else "N/A"
                crit_mttr = float(categoria_critica[1]) if categoria_critica and categoria_critica[1] else 0.0

            conexion.close()

            return {
                "mttr_global": mttr_global,
                "total_incidentes": total_incidentes,
                "mejor_categoria": mejor_nombre,
                "mejor_mttr": mejor_mttr,
                "categoria_critica": crit_nombre,
                "crit_mttr": crit_mttr
            }

        except Exception as e:
            print(f"⚠️ Error al obtener estadísticas MTTR => {e}")
            return self._estadisticas_vacias()

    def obtener_mttr_completo_por_categoria(self):
        """Obtiene MTTR y conteo de incidentes por categoría SOLO con datos reales"""
        try:
            conexion = get_connection()
            if not conexion:
                print("❌ No se pudo conectar a la base de datos.")
                return []

            sql = """
                SELECT 
                    COALESCE(c.nombre, 'Sin categoría') AS categoria,
                    CASE 
                        WHEN COUNT(CASE WHEN i.tiempo_reparacion IS NOT NULL THEN 1 END) > 0 THEN
                            ROUND(AVG(EXTRACT(EPOCH FROM i.tiempo_reparacion) / 3600), 2)
                        WHEN COUNT(CASE WHEN i.fecha_resolucion IS NOT NULL AND i.fecha_reporte IS NOT NULL THEN 1 END) > 0 THEN
                            ROUND(AVG(EXTRACT(EPOCH FROM (i.fecha_resolucion - i.fecha_reporte)) / 3600), 2)
                        ELSE 0
                    END AS mttr_horas,
                    COUNT(i.id_incidente) AS total_incidentes
                FROM 
                    INCIDENTE i
                LEFT JOIN 
                    CATEGORIA c ON i.id_categoria = c.id_categoria
                WHERE 
                    i.estado IN ('T', 'C')
                GROUP BY 
                    c.nombre
                ORDER BY 
                    mttr_horas ASC;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultados = cursor.fetchall()

            conexion.close()

            mttr_list = [{
                'categoria': fila[0] or 'Sin categoría', 
                'mttr_horas': float(fila[1]) if fila[1] else 0.0, 
                'total_incidentes': int(fila[2]) if fila[2] else 0
            } for fila in resultados]
            
            return mttr_list

        except Exception as e:
            print(f"⚠️ Error al calcular MTTR completo => {e}")
            return []

    def obtener_tendencia_mttr(self, meses=6):
        """Obtiene la tendencia de MTTR por mes SOLO con datos reales"""
        try:
            conexion = get_connection()
            if not conexion:
                print("❌ No se pudo conectar a la base de datos.")
                return []

            sql = """
                SELECT 
                    TO_CHAR(COALESCE(fecha_resolucion, fecha_reporte), 'YYYY-MM') AS mes,
                    CASE 
                        WHEN COUNT(CASE WHEN tiempo_reparacion IS NOT NULL THEN 1 END) > 0 THEN
                            ROUND(AVG(EXTRACT(EPOCH FROM tiempo_reparacion) / 3600), 2)
                        WHEN COUNT(CASE WHEN fecha_resolucion IS NOT NULL AND fecha_reporte IS NOT NULL THEN 1 END) > 0 THEN
                            ROUND(AVG(EXTRACT(EPOCH FROM (fecha_resolucion - fecha_reporte)) / 3600), 2)
                        ELSE 0
                    END AS mttr_horas
                FROM 
                    INCIDENTE
                WHERE 
                    estado IN ('T', 'C')
                    AND COALESCE(fecha_resolucion, fecha_reporte) >= CURRENT_DATE - INTERVAL '%s months'
                GROUP BY 
                    TO_CHAR(COALESCE(fecha_resolucion, fecha_reporte), 'YYYY-MM')
                ORDER BY 
                    mes;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql, (meses,))
                resultados = cursor.fetchall()

            conexion.close()

            tendencia = [{
                'mes': fila[0], 
                'mttr_horas': float(fila[1]) if fila[1] else 0.0
            } for fila in resultados]
            
            return tendencia

        except Exception as e:
            print(f"⚠️ Error al obtener tendencia MTTR => {e}")
            return []

    def obtener_distribucion_incidentes(self):
        """Obtiene la distribución de incidentes por categoría SOLO con datos reales"""
        try:
            conexion = get_connection()
            if not conexion:
                print("❌ No se pudo conectar a la base de datos.")
                return []

            sql = """
                SELECT 
                    COALESCE(c.nombre, 'Sin categoría') AS categoria,
                    COUNT(i.id_incidente) AS cantidad,
                    ROUND((COUNT(i.id_incidente) * 100.0 / (SELECT COUNT(*) FROM INCIDENTE)), 2) AS porcentaje
                FROM 
                    INCIDENTE i
                LEFT JOIN 
                    CATEGORIA c ON i.id_categoria = c.id_categoria
                GROUP BY 
                    c.nombre
                ORDER BY 
                    cantidad DESC;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultados = cursor.fetchall()

            conexion.close()

            distribucion = [{
                'categoria': fila[0] or 'Sin categoría', 
                'cantidad': int(fila[1]) if fila[1] else 0,
                'porcentaje': float(fila[2]) if fila[2] else 0.0
            } for fila in resultados]
            
            return distribucion

        except Exception as e:
            print(f"⚠️ Error al obtener distribución => {e}")
            return []

    def obtener_mttr_filtrado(self, categoria=None, periodo_meses=6):
        """Obtiene MTTR filtrado por categoría y período SOLO con datos reales"""
        try:
            conexion = get_connection()
            if not conexion:
                print("❌ No se pudo conectar a la base de datos.")
                return []

            # Construir query dinámicamente
            # Solo considerar incidentes Terminados ('T') o Cancelados ('C')
            where_conditions = ["i.estado IN ('T', 'C')"]
            params = []

            if categoria and categoria.strip() and categoria.lower() != 'todas':
                where_conditions.append("c.nombre = %s")
                params.append(categoria)

            if periodo_meses:
                where_conditions.append("COALESCE(i.fecha_resolucion, i.fecha_reporte) >= CURRENT_DATE - INTERVAL '%s months'")
                params.append(periodo_meses)

            where_clause = " AND ".join(where_conditions)

            sql = f"""
                SELECT 
                    COALESCE(c.nombre, 'Sin categoría') AS categoria,
                    CASE 
                        WHEN COUNT(CASE WHEN i.tiempo_reparacion IS NOT NULL THEN 1 END) > 0 THEN
                            ROUND(AVG(EXTRACT(EPOCH FROM i.tiempo_reparacion) / 3600), 2)
                        WHEN COUNT(CASE WHEN i.fecha_resolucion IS NOT NULL AND i.fecha_reporte IS NOT NULL THEN 1 END) > 0 THEN
                            ROUND(AVG(EXTRACT(EPOCH FROM (i.fecha_resolucion - i.fecha_reporte)) / 3600), 2)
                        ELSE 0
                    END AS mttr_horas,
                    COUNT(i.id_incidente) AS total_incidentes
                FROM 
                    INCIDENTE i
                LEFT JOIN 
                    CATEGORIA c ON i.id_categoria = c.id_categoria
                WHERE 
                    {where_clause}
                GROUP BY 
                    c.nombre
                ORDER BY 
                    mttr_horas ASC;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql, params)
                resultados = cursor.fetchall()

            conexion.close()

            mttr_list = [{
                'categoria': fila[0] or 'Sin categoría', 
                'mttr_horas': float(fila[1]) if fila[1] else 0.0, 
                'total_incidentes': int(fila[2]) if fila[2] else 0
            } for fila in resultados]
            
            return mttr_list

        except Exception as e:
            print(f"⚠️ Error al obtener MTTR filtrado => {e}")
            return []

    def _estadisticas_vacias(self):
        """Retorna estadísticas vacías cuando no hay conexión"""
        return {
            "mttr_global": 0,
            "total_incidentes": 0,
            "mejor_categoria": "N/A",
            "mejor_mttr": 0,
            "categoria_critica": "N/A",
            "crit_mttr": 0
        }

    def obtener_categorias_disponibles(self):
        """Obtiene lista de categorías disponibles en la BD"""
        try:
            conexion = get_connection()
            if not conexion:
                return []

            sql = """
                SELECT DISTINCT COALESCE(c.nombre, 'Sin categoría') AS categoria
                FROM INCIDENTE i
                LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                WHERE c.nombre IS NOT NULL
                ORDER BY categoria;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultados = cursor.fetchall()

            conexion.close()
            return [fila[0] for fila in resultados]

        except Exception as e:
            print(f"⚠️ Error al obtener categorías => {e}")
            return []