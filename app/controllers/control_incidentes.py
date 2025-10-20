from ConexionBD import get_connection
class ControlIncidentes:
    @staticmethod

    def insertar_incidentes(titulo, descripcion, id_categoria, id_usuario):
        try:
            sql = """
                INSERT INTO incidentes (titulo, descripcion, id_categoria, id_usuario)
                VALUES (%s, %s, %s, %s);
            """
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            with conexion.cursor() as cursor:
                cursor.execute(sql, (titulo, descripcion, id_categoria, id_usuario))
                conexion.commit()

            conexion.close()
            return 0  
        except Exception as e:
            print(f"Error en insertar => {e}")
            return -1
        
    def buscar_por_IDIncidente(id_incidente):
        try:
            sql = "SELECT * FROM incidentes WHERE id_incidente = %s"
            atributos = [
                'id_incidente', 'titulo', 'descripcion', 'id_categoria',
                'id_usuario', 'estado', 'fecha_reporte', 'fecha_resolucion', 'tiempo_reparacion'
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
        
    def listar_incidentes():
        try:
            sql = "SELECT * FROM incidentes ORDER BY id_incidente DESC"
            atributos = [
                'id_incidente', 'titulo', 'descripcion', 'id_categoria',
                'id_usuario', 'estado', 'fecha_reporte', 'fecha_resolucion', 'tiempo_reparacion'
            ]

            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return None

            with conexion.cursor() as cursor:
                cursor.execute(sql)
                incidentes = cursor.fetchall()

            conexion.close()
            incidentes_list = [dict(zip(atributos, i)) for i in incidentes] if incidentes else []
            return incidentes_list
        except Exception as e:
            print(f"Error en buscar_todos => {e}")
            return None
        
    def actualizar_incidentes(id_incidente, titulo, descripcion, id_categoria, id_usuario, estado):
        try:
            sql = """
                UPDATE incidentes
                SET titulo = %s,
                    descripcion = %s,
                    id_categoria = %s,
                    id_usuario = %s,
                    estado = %s,
                WHERE id_incidente = %s;
            """
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            with conexion.cursor() as cursor:
                cursor.execute(sql, (
                    titulo, descripcion, id_categoria, id_usuario,
                    estado, id_incidente
                ))
                conexion.commit()

            conexion.close()
            return 0  
        except Exception as e:
            print(f"Error en actualizar => {e}")
            return -1
        
    def actualizar_estado(id_incidente, nuevo_estado):
        try:
            sql = """
                UPDATE incidentes
                SET estado = %s,
                    fecha_resolucion = CASE
                        WHEN %s IN ('R', 'C') THEN NOW()
                        ELSE fecha_resolucion
                    END,
                    tiempo_reparacion = CASE
                        WHEN %s IN ('R', 'C') THEN NOW() - fecha_reporte
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
            return 0  # ✅ Éxito

        except Exception as e:
            print(f"Error en actualizar_estado => {e}")
            return -1