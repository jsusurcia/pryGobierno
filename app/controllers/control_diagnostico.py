from ConexionBD import get_connection

class ControlDiagnosticos:
    @staticmethod
    def insertar_diagnostico(id_incidente, descripcion, causa_raiz, solucion, comentario, usuario_id):
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            sql = """
                INSERT INTO diagnosticos (id_incidente, descripcion, causa_raiz, solucion_propuesta, comentario_usuario, id_usuario)
                VALUES (%s, %s, %s, %s, %s, %s);
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_incidente, descripcion, causa_raiz, solucion, comentario, usuario_id))
                conexion.commit()

            conexion.close()
            return True  # Éxito

        except Exception as e:
            print(f"Error en insertar_diagnostico => {e}")
            return False
    
    def buscar_por_IDDiagnostico(id_diagnosticos):
        try:
            sql = """
                SELECT * FROM diagnosticos WHERE id_diagnosticos = %s
            """
            atributos = [
                'id_diagnosticos', 'id_incidente', 'id_usuario', 
                'descripcion', 'causa_raiz', 'solucion_propuesta', 
                'comentario_usuario', 'fecha_diagnostico', 'fecha_actualizacion'
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
    
    def listar_diagnosticos():
        try:
            sql = "SELECT * FROM diagnosticos ORDER BY id_diagnosticos DESC"
            atributos = [
                'id_diagnosticos', 'id_incidente', 'id_usuario', 
                'descripcion', 'causa_raiz', 'solucion_propuesta', 
                'comentario_usuario', 'fecha_diagnostico', 'fecha_actualizacion'
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
            print(f"⚠️ Error en buscar_todos => {e}")
            return None
    
    def actualizar_diagnostico(id_diagnosticos, descripcion, causa_raiz, solucion_propuesta, comentario_usuario):
        try:
            sql = """
                UPDATE diagnosticos
                SET descripcion = %s,
                    causa_raiz = %s,
                    solucion_propuesta = %s,
                    comentario_usuario = %s,
                    fecha_actualizacion = NOW()
                WHERE id_diagnosticos = %s;
            """
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            with conexion.cursor() as cursor:
                cursor.execute(sql, (descripcion, causa_raiz, solucion_propuesta, comentario_usuario, id_diagnosticos))
                conexion.commit()

            conexion.close()
            return 0 

        except Exception as e:
            print(f"Error en actualizar => {e}")
            return -1
