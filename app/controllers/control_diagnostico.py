from ConexionBD import get_connection

class ControlDiagnosticos:
    @staticmethod
    def insertar_diagnostico(id_incidente, descripcion, causa_raiz, solucion, comentario=None, usuario_id=None):
        """
        Inserta un diagnóstico. El parámetro comentario se mantiene por compatibilidad pero no se usa.
        """
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            sql = """
                INSERT INTO DIAGNOSTICO (id_incidente, descripcion, causa_raiz, solucion_propuesta, id_usuario)
                VALUES (%s, %s, %s, %s, %s);
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_incidente, descripcion, causa_raiz, solucion, usuario_id))
                conexion.commit()

            conexion.close()
            return True  # Éxito

        except Exception as e:
            print(f"Error en insertar_diagnostico => {e}")
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
        Lista todos los diagnósticos con su incidente asociado,
        para la vista de revisión de diagnósticos.
        """
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return []

            sql = """
                SELECT d.id_diagnosticos, 
                    d.id_incidente,
                    i.titulo AS titulo_incidente,
                    d.descripcion, 
                    d.causa_raiz, 
                    d.solucion_propuesta,
                    d.fecha_diagnostico,
                    d.fecha_actualizacion
                FROM DIAGNOSTICO d
                LEFT JOIN INCIDENTE i ON d.id_incidente = i.id_incidente
                where i.estado = 'P'
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
            return []


    
    def actualizar_diagnostico(id_diagnosticos, descripcion, causa_raiz, solucion_propuesta):
        try:
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
            return 0 

        except Exception as e:
            print(f"Error en actualizar => {e}")
            return -1
    
    def aceptar_revision(id_diagnostico, id_incidente):
    
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False

            sql = """
                UPDATE INCIDENTE
                SET estado = 'A'
                WHERE id_incidente = %s;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_diagnostico, id_incidente))
                conexion.commit()

            conexion.close()
            return True

        except Exception as e:
            print(f"Error en actualizar_revision => {e}")
            return False
        
    def cancelar_revision(id_diagnostico, id_incidente):
    
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return False

            sql = """
                UPDATE INCIDENTE
                SET estado = 'C'
                WHERE id_incidente = %s;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_incidente,))
                conexion.commit()

            conexion.close()
            return True

        except Exception as e:
            print(f"Error en actualizar_revision => {e}")
            return False
        
    def obtener_diagnosticos_filtrados(self, id_usuario, titulo='', causa=''):
        conexion = get_connection()
        cursor = conexion.cursor()

        query = """
            SELECT d.id_diagnosticos, d.id_incidente, i.descripcion, 
                d.fecha_diagnostico, d.fecha_actualizacion, 
                d.causa_raiz, d.solucion_propuesta
            FROM DIAGNOSTICO d
            JOIN INCIDENTE i ON d.id_incidente = i.id_incidente
            WHERE (%s = '' OR i.descripcion ILIKE %s)
            AND (%s = '' OR d.causa_raiz ILIKE %s)
            AND d.id_usuario = %s
            ORDER BY d.fecha_diagnostico DESC;
        """
        valores = (titulo, f"%{titulo}%", causa, f"%{causa}%", id_usuario)
        cursor.execute(query, valores)
        diagnosticos = cursor.fetchall()

        conexion.close()

        lista = []
        for d in diagnosticos:
            lista.append({
                "id_diagnosticos": d[0],
                "id_incidente": d[1],
                "descripcion": d[2],
                # 🔹 formatear fechas para no mostrar horas
                "fecha_diagnostico": d[3].strftime('%Y-%m-%d') if d[3] else '',
                "fecha_actualizacion": d[4].strftime('%Y-%m-%d') if d[4] else '',
                "causa_raiz": d[5],
                "solucion_propuesta": d[6]
            })
        return lista

