"""
Controlador de Predicciones con IA
Utiliza Machine Learning para predecir patrones y tendencias de incidentes
"""
from ConexionBD import get_connection
import numpy as np
from datetime import datetime, timedelta
from collections import Counter

class ControlPredicciones:
    
    @staticmethod
    def obtener_datos_historicos(meses=6):
        """Obtiene datos históricos de incidentes para análisis"""
        try:
            conexion = get_connection()
            if not conexion:
                return None
            
            sql = """
                SELECT 
                    i.id_incidente,
                    i.id_categoria,
                    c.nombre as categoria,
                    i.nivel,
                    i.estado,
                    i.fecha_reporte,
                    i.fecha_resolucion,
                    EXTRACT(EPOCH FROM i.tiempo_reparacion) / 3600 as horas_resolucion,
                    EXTRACT(DOW FROM i.fecha_reporte) as dia_semana,
                    EXTRACT(HOUR FROM i.fecha_reporte) as hora_dia,
                    u.id_rol,
                    r.id_area
                FROM INCIDENTE i
                LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                LEFT JOIN USUARIO u ON i.id_usuario = u.id_usuario
                LEFT JOIN ROL r ON u.id_rol = r.id_rol
                WHERE i.fecha_reporte >= CURRENT_DATE - INTERVAL '%s months'
                ORDER BY i.fecha_reporte DESC;
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (meses,))
                resultados = cursor.fetchall()
            
            conexion.close()
            
            datos = []
            for r in resultados:
                datos.append({
                    'id_incidente': r[0],
                    'id_categoria': r[1],
                    'categoria': r[2] or 'Sin categoría',
                    'nivel': r[3],
                    'estado': r[4],
                    'fecha_reporte': r[5],
                    'fecha_resolucion': r[6],
                    'horas_resolucion': float(r[7]) if r[7] else None,
                    'dia_semana': int(r[8]) if r[8] is not None else None,
                    'hora_dia': int(r[9]) if r[9] is not None else None,
                    'id_rol': r[10],
                    'id_area': r[11]
                })
            
            return datos
            
        except Exception as e:
            print(f"Error al obtener datos históricos => {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def predecir_incidentes_por_categoria(meses_historico=3, meses_prediccion=1):
        """
        Predice la cantidad de incidentes por categoría para el próximo período
        Usa promedio móvil ponderado con tendencia
        """
        try:
            datos = ControlPredicciones.obtener_datos_historicos(meses_historico)
            if not datos:
                return []
            
            # Agrupar por categoría y mes
            incidentes_por_mes = {}
            
            for incidente in datos:
                fecha = incidente['fecha_reporte']
                categoria = incidente['categoria']
                mes_key = f"{fecha.year}-{fecha.month:02d}"
                
                if categoria not in incidentes_por_mes:
                    incidentes_por_mes[categoria] = {}
                
                if mes_key not in incidentes_por_mes[categoria]:
                    incidentes_por_mes[categoria][mes_key] = 0
                
                incidentes_por_mes[categoria][mes_key] += 1
            
            # Calcular predicciones
            predicciones = []
            
            for categoria, meses_data in incidentes_por_mes.items():
                valores = list(meses_data.values())
                
                # Inicializar variables
                tendencia = 0
                
                if len(valores) < 2:
                    # No hay suficientes datos para predecir
                    prediccion = valores[0] if valores else 0
                    tendencia = 0
                else:
                    # Promedio móvil ponderado (más peso a datos recientes)
                    pesos = [i+1 for i in range(len(valores))]
                    promedio_ponderado = sum(v * w for v, w in zip(valores, pesos)) / sum(pesos)
                    
                    # Calcular tendencia
                    tendencia = (valores[-1] - valores[0]) / len(valores)
                    
                    # Predicción = promedio ponderado + tendencia
                    prediccion = promedio_ponderado + tendencia
                
                # Calcular nivel de confianza basado en variabilidad
                if len(valores) >= 2:
                    desviacion = np.std(valores)
                    promedio = np.mean(valores)
                    coef_variacion = (desviacion / promedio * 100) if promedio > 0 else 100
                    confianza = max(0, min(100, 100 - coef_variacion))
                else:
                    confianza = 50
                
                predicciones.append({
                    'categoria': categoria,
                    'prediccion': round(prediccion, 1),
                    'historico_promedio': round(np.mean(valores), 1) if valores else 0,
                    'mes_anterior': valores[-1] if valores else 0,
                    'tendencia': 'Alza' if tendencia > 0.5 else 'Baja' if tendencia < -0.5 else 'Estable',
                    'confianza': round(confianza, 1),
                    'datos_historicos': len(valores)
                })
            
            # Ordenar por predicción descendente
            predicciones.sort(key=lambda x: x['prediccion'], reverse=True)
            
            return predicciones
            
        except Exception as e:
            print(f"Error en predecir_incidentes_por_categoria => {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def predecir_tiempo_resolucion(id_categoria=None, nivel='M'):
        """
        Predice el tiempo estimado de resolución basado en categoría y prioridad
        """
        try:
            conexion = get_connection()
            if not conexion:
                return None
            
            # Consulta con filtros opcionales
            where_conditions = ["i.estado IN ('T', 'C')", "i.tiempo_reparacion IS NOT NULL"]
            params = []
            
            if id_categoria:
                where_conditions.append("i.id_categoria = %s")
                params.append(id_categoria)
            
            if nivel:
                where_conditions.append("i.nivel = %s")
                params.append(nivel)
            
            where_clause = " AND ".join(where_conditions)
            
            sql = f"""
                SELECT 
                    ROUND(AVG(EXTRACT(EPOCH FROM tiempo_reparacion) / 3600), 2) as promedio_horas,
                    ROUND(MIN(EXTRACT(EPOCH FROM tiempo_reparacion) / 3600), 2) as min_horas,
                    ROUND(MAX(EXTRACT(EPOCH FROM tiempo_reparacion) / 3600), 2) as max_horas,
                    ROUND(STDDEV(EXTRACT(EPOCH FROM tiempo_reparacion) / 3600), 2) as desviacion,
                    COUNT(*) as total_casos
                FROM INCIDENTE i
                WHERE {where_clause}
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, params)
                resultado = cursor.fetchone()
            
            conexion.close()
            
            if resultado and resultado[0]:
                promedio = float(resultado[0])
                minimo = float(resultado[1]) if resultado[1] else promedio
                maximo = float(resultado[2]) if resultado[2] else promedio
                desviacion = float(resultado[3]) if resultado[3] else 0
                casos = int(resultado[4])
                
                # Calcular intervalo de confianza (±1 desviación estándar)
                estimado_min = max(0, promedio - desviacion)
                estimado_max = promedio + desviacion
                
                return {
                    'estimado_horas': round(promedio, 1),
                    'rango_min': round(estimado_min, 1),
                    'rango_max': round(estimado_max, 1),
                    'mejor_caso': round(minimo, 1),
                    'peor_caso': round(maximo, 1),
                    'confianza': round(min(100, (casos / 10) * 100), 1),  # Más casos = más confianza
                    'basado_en_casos': casos
                }
            
            return {
                'estimado_horas': 0,
                'rango_min': 0,
                'rango_max': 0,
                'mejor_caso': 0,
                'peor_caso': 0,
                'confianza': 0,
                'basado_en_casos': 0
            }
            
        except Exception as e:
            print(f"Error en predecir_tiempo_resolucion => {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def analizar_patrones_temporales(meses=3):
        """
        Analiza patrones temporales de incidentes (día de semana, hora del día)
        """
        try:
            datos = ControlPredicciones.obtener_datos_historicos(meses)
            if not datos:
                return None
            
            # Análisis por día de semana (0=Domingo, 6=Sábado en PostgreSQL)
            dias_semana = {
                0: 'Domingo', 1: 'Lunes', 2: 'Martes', 
                3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado'
            }
            
            contador_dias = Counter()
            contador_horas = Counter()
            
            for incidente in datos:
                if incidente['dia_semana'] is not None:
                    contador_dias[incidente['dia_semana']] += 1
                if incidente['hora_dia'] is not None:
                    contador_horas[incidente['hora_dia']] += 1
            
            # Top 3 días con más incidentes
            dias_criticos = []
            for dia, cantidad in contador_dias.most_common(3):
                dias_criticos.append({
                    'dia': dias_semana.get(dia, 'Desconocido'),
                    'cantidad': cantidad,
                    'porcentaje': round((cantidad / len(datos)) * 100, 1)
                })
            
            # Top 3 horas con más incidentes
            horas_criticas = []
            for hora, cantidad in contador_horas.most_common(3):
                horas_criticas.append({
                    'hora': f"{hora:02d}:00 - {hora:02d}:59",
                    'cantidad': cantidad,
                    'porcentaje': round((cantidad / len(datos)) * 100, 1)
                })
            
            # Análisis por categoría
            contador_categorias = Counter()
            for incidente in datos:
                contador_categorias[incidente['categoria']] += 1
            
            categorias_riesgo = []
            for categoria, cantidad in contador_categorias.most_common(5):
                categorias_riesgo.append({
                    'categoria': categoria,
                    'cantidad': cantidad,
                    'porcentaje': round((cantidad / len(datos)) * 100, 1)
                })
            
            return {
                'dias_criticos': dias_criticos,
                'horas_criticas': horas_criticas,
                'categorias_riesgo': categorias_riesgo,
                'total_incidentes': len(datos),
                'periodo_analisis': f'Últimos {meses} meses'
            }
            
        except Exception as e:
            print(f"Error en analizar_patrones_temporales => {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def detectar_anomalias(threshold=2.0):
        """
        Detecta anomalías en el volumen de incidentes
        Usa desviación estándar para identificar picos inusuales
        """
        try:
            conexion = get_connection()
            if not conexion:
                return []
            
            # Obtener conteo de incidentes por día en los últimos 3 meses
            sql = """
                SELECT 
                    DATE(fecha_reporte) as fecha,
                    COUNT(*) as cantidad,
                    STRING_AGG(DISTINCT c.nombre, ', ') as categorias
                FROM INCIDENTE i
                LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
                WHERE fecha_reporte >= CURRENT_DATE - INTERVAL '3 months'
                GROUP BY DATE(fecha_reporte)
                ORDER BY fecha DESC;
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultados = cursor.fetchall()
            
            conexion.close()
            
            if not resultados or len(resultados) < 7:
                return []
            
            # Calcular estadísticas
            cantidades = [r[1] for r in resultados]
            promedio = np.mean(cantidades)
            desviacion = np.std(cantidades)
            
            # Detectar anomalías (días con cantidad > promedio + threshold * desviación)
            anomalias = []
            umbral_superior = promedio + (threshold * desviacion)
            umbral_inferior = max(0, promedio - (threshold * desviacion))
            
            for resultado in resultados[:30]:  # Solo últimos 30 días
                fecha = resultado[0]
                cantidad = resultado[1]
                categorias = resultado[2] or 'Sin categoría'
                
                if cantidad > umbral_superior:
                    anomalias.append({
                        'fecha': fecha.strftime('%Y-%m-%d'),
                        'cantidad': cantidad,
                        'promedio': round(promedio, 1),
                        'desviacion': round((cantidad - promedio) / desviacion, 2),
                        'tipo': 'Pico inusual',
                        'categorias_afectadas': categorias,
                        'severidad': 'Alta' if cantidad > promedio + (3 * desviacion) else 'Media'
                    })
                elif cantidad < umbral_inferior and cantidad > 0:
                    anomalias.append({
                        'fecha': fecha.strftime('%Y-%m-%d'),
                        'cantidad': cantidad,
                        'promedio': round(promedio, 1),
                        'desviacion': round((cantidad - promedio) / desviacion, 2),
                        'tipo': 'Baja inusual',
                        'categorias_afectadas': categorias,
                        'severidad': 'Baja'
                    })
            
            return anomalias
            
        except Exception as e:
            print(f"Error en detectar_anomalias => {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def predecir_carga_tecnicos(dias_adelante=7):
        """
        Predice la carga de trabajo de los técnicos basada en patrones históricos
        """
        try:
            conexion = get_connection()
            if not conexion:
                return []
            
            # Obtener promedio de incidentes asignados por técnico por día
            sql = """
                SELECT 
                    u.id_usuario,
                    u.nombre || ' ' || u.ape_pat as nombre_tecnico,
                    COUNT(DISTINCT DATE(i.fecha_reporte)) as dias_trabajados,
                    COUNT(*) as total_incidentes,
                    ROUND(COUNT(*) * 1.0 / NULLIF(COUNT(DISTINCT DATE(i.fecha_reporte)), 0), 2) as incidentes_por_dia,
                    ROUND(AVG(EXTRACT(EPOCH FROM i.tiempo_reparacion) / 3600), 2) as promedio_horas_resolucion
                FROM USUARIO u
                JOIN ROL r ON u.id_rol = r.id_rol
                LEFT JOIN INCIDENTE i ON (i.id_tecnico_asignado = u.id_usuario OR 
                                          EXISTS (SELECT 1 FROM EQUIPO_TECNICO et 
                                                  WHERE et.id_incidente = i.id_incidente 
                                                  AND et.id_usuario = u.id_usuario))
                    AND i.fecha_reporte >= CURRENT_DATE - INTERVAL '1 month'
                WHERE r.tipo = 'T' AND u.estado = TRUE
                GROUP BY u.id_usuario, nombre_tecnico
                ORDER BY incidentes_por_dia DESC;
            """
            
            with conexion.cursor() as cursor:
                cursor.execute(sql)
                resultados = cursor.fetchall()
            
            conexion.close()
            
            predicciones_tecnicos = []
            
            for r in resultados:
                incidentes_por_dia = float(r[4]) if r[4] else 0
                prediccion_semanal = round(incidentes_por_dia * dias_adelante, 1)
                
                # Determinar nivel de carga
                if prediccion_semanal >= 15:
                    nivel_carga = 'Muy Alta'
                    color = 'red'
                elif prediccion_semanal >= 10:
                    nivel_carga = 'Alta'
                    color = 'orange'
                elif prediccion_semanal >= 5:
                    nivel_carga = 'Media'
                    color = 'yellow'
                else:
                    nivel_carga = 'Baja'
                    color = 'green'
                
                predicciones_tecnicos.append({
                    'id_tecnico': r[0],
                    'nombre': r[1],
                    'incidentes_actuales': r[3],
                    'promedio_diario': float(r[4]) if r[4] else 0,
                    'prediccion_proximos_dias': prediccion_semanal,
                    'nivel_carga': nivel_carga,
                    'color': color,
                    'promedio_horas_resolucion': float(r[5]) if r[5] else 0
                })
            
            return predicciones_tecnicos
            
        except Exception as e:
            print(f"Error en predecir_carga_tecnicos => {e}")
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def obtener_recomendaciones():
        """
        Genera recomendaciones basadas en análisis predictivo
        """
        try:
            recomendaciones = []
            
            # 1. Análisis de categorías con predicción alta
            predicciones = ControlPredicciones.predecir_incidentes_por_categoria()
            if predicciones:
                top_categoria = predicciones[0]
                if top_categoria['prediccion'] > top_categoria['mes_anterior']:
                    recomendaciones.append({
                        'tipo': 'Categoría en Riesgo',
                        'severidad': 'Alta',
                        'mensaje': f"Se prevé un aumento de incidentes en '{top_categoria['categoria']}'. "
                                   f"Predicción: {top_categoria['prediccion']} incidentes (vs {top_categoria['mes_anterior']} del mes anterior).",
                        'accion': 'Considerar asignar más recursos preventivos a esta categoría.'
                    })
            
            # 2. Análisis de patrones temporales
            patrones = ControlPredicciones.analizar_patrones_temporales()
            if patrones and patrones['dias_criticos']:
                dia_critico = patrones['dias_criticos'][0]
                recomendaciones.append({
                    'tipo': 'Patrón Temporal',
                    'severidad': 'Media',
                    'mensaje': f"Los {dia_critico['dia']}s concentran el {dia_critico['porcentaje']}% de los incidentes.",
                    'accion': 'Reforzar el equipo técnico en días críticos.'
                })
            
            # 3. Análisis de anomalías
            anomalias = ControlPredicciones.detectar_anomalias()
            anomalias_altas = [a for a in anomalias if a['severidad'] == 'Alta']
            if anomalias_altas:
                recomendaciones.append({
                    'tipo': 'Anomalía Detectada',
                    'severidad': 'Alta',
                    'mensaje': f"Se detectaron {len(anomalias_altas)} picos inusuales de incidentes en los últimos 30 días.",
                    'accion': 'Investigar causas raíz de los picos de incidentes.'
                })
            
            # 4. Análisis de carga de técnicos
            carga_tecnicos = ControlPredicciones.predecir_carga_tecnicos()
            tecnicos_sobrecargados = [t for t in carga_tecnicos if t['nivel_carga'] in ['Alta', 'Muy Alta']]
            if tecnicos_sobrecargados:
                nombres = ', '.join([t['nombre'] for t in tecnicos_sobrecargados[:2]])
                recomendaciones.append({
                    'tipo': 'Carga de Trabajo',
                    'severidad': 'Media',
                    'mensaje': f"{len(tecnicos_sobrecargados)} técnico(s) con carga alta prevista: {nombres}",
                    'accion': 'Considerar redistribución de carga o incorporar más personal.'
                })
            
            return recomendaciones
            
        except Exception as e:
            print(f"Error en obtener_recomendaciones => {e}")
            return []

