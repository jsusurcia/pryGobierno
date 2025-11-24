from ConexionBD import get_connection
class ControlIncidentes:
    @staticmethod

    def insertar_incidentes(titulo, descripcion, id_categoria, id_usuario, nivel='M'):
        try:
            sql = """
                INSERT INTO INCIDENTE (titulo, descripcion, id_categoria, id_usuario, nivel, estado)
                VALUES (%s, %s, %s, %s, %s, 'P');
            """
            conexion = get_connection()
            if not conexion:
                print("No se pudo conectar a la base de datos.")
                return -2

            with conexion.cursor() as cursor:
                cursor.execute(sql, (titulo, descripcion, id_categoria, id_usuario, nivel))
                conexion.commit()

            conexion.close()
            return 0  
        except Exception as e:
            print(f"Error en insertar => {e}")
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
                    i.nivel,
                    i.fecha_reporte,
                    i.fecha_resolucion,
                    i.tiempo_reparacion
                FROM INCIDENTE i
                LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                ORDER BY i.id_incidente DESC;
            """

            with conexion.cursor() as cursor:
                cursor.execute(sql)
                filas = cursor.fetchall()

            atributos = [
                'id_incidente', 'titulo', 'descripcion',
                'categoria', 'estado', 'nivel', 'fecha_reporte',
                'fecha_resolucion', 'tiempo_reparacion'
            ]

            incidentes = [dict(zip(atributos, fila)) for fila in filas]

            # 🔹 Traducir estado corto a texto completo
            estado_map = {
                'P': 'pendiente',
                'A': 'abierto',
                'T': 'en_tratamiento',
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
            sql = """
                UPDATE INCIDENTE
                SET estado = %s,
                    fecha_resolucion = CASE
                        WHEN %s IN ('C') THEN NOW()
                        ELSE fecha_resolucion
                    END,
                    tiempo_reparacion = CASE
                        WHEN %s IN ('C') THEN NOW() - fecha_reporte
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
                FROM INCIDENTE
                WHERE estado NOT IN ('C');
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

    def obtener_mttr_por_categoria(self):
        """Calcula el MTTR (Mean Time To Repair) por categoría SOLO con datos reales"""
        try:
            conexion = get_connection()
            if not conexion:
                print("❌ No se pudo conectar a la base de datos.")
                return []

            # Consulta que calcula MTTR usando el campo tiempo_reparacion o calculándolo
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
                    incidentes i
                LEFT JOIN 
                    categorias c ON i.id_categoria = c.id_categoria
                WHERE 
                    i.estado IN ('R', 'C', 'resuelto', 'cerrado')
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
                    WHERE estado IN ('C');
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
                    WHERE i.estado IN ('C')
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
                    WHERE i.estado IN ('C')
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
                    i.estado IN ('C')
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
                    estado IN ('C')
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
            where_conditions = ["i.estado IN ('C')"]
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