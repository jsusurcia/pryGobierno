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
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return []

            sql = """
                SELECT 
                    i.id_incidente,
                    i.titulo,
                    i.descripcion,
                    COALESCE(c.nombre, 'Sin categoría') AS categoria,
                    i.estado,
                    i.fecha_reporte,
                    i.fecha_resolucion,
                    i.tiempo_reparacion
                FROM incidentes i
                LEFT JOIN categorias c ON i.id_categoria = c.id_categoria
                ORDER BY i.id_incidente DESC;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql)
                filas = cursor.fetchall()

            atributos = [
                'id_incidente', 'titulo', 'descripcion',
                'categoria', 'estado', 'fecha_reporte',
                'fecha_resolucion', 'tiempo_reparacion'
            ]

            incidentes = [dict(zip(atributos, fila)) for fila in filas]

            # 🔹 Traducir estado corto a texto completo
            estado_map = {
                'A': 'abierto',
                'P': 'en_proceso',
                'R': 'resuelto',
                'C': 'cerrado'
            }

            for inc in incidentes:
                if inc.get('estado'):
                    inc['estado'] = estado_map.get(inc['estado'].upper(), inc['estado'])
                if inc.get('fecha_reporte'):
                    inc['fecha_reporte'] = inc['fecha_reporte'].strftime('%Y-%m-%d')

            
            

            conexion.close()
            return incidentes

        except Exception as e:
            print(f"Error en listar_incidentes => {e}")
            return []

        
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
            return 0  

        except Exception as e:
            print(f"Error en actualizar_estado => {e}")
            return -1
        
    @staticmethod
    def obtener_incidentes_sin_diagnostico():
        try:
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return []

            sql = """
                SELECT id_incidente, titulo
                FROM incidentes
                WHERE estado != 'Diagnosticado';
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultado = cursor.fetchall()

            incidentes = [
                {'id_incidente': row[0], 'titulo': row[1]} for row in resultado
            ]

            conexion.close()
            return incidentes

        except Exception as e:
            print("Error al obtener incidentes =>", e)
            return []
