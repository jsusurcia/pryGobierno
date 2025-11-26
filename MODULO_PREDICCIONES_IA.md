# 🤖 Módulo de Predicciones con Inteligencia Artificial

## 📋 Descripción General

El **Módulo de Predicciones con IA** es un sistema avanzado de análisis predictivo que utiliza algoritmos de Machine Learning para ayudar en la gestión proactiva de incidentes de TI. Este módulo analiza datos históricos de incidentes para identificar patrones, detectar anomalías y generar predicciones que permiten una mejor planificación de recursos.

---

## 🎯 Funcionalidades Principales

### 1. **Predicción de Incidentes por Categoría**
- 📊 **Algoritmo**: Promedio móvil ponderado con análisis de tendencia
- 🎯 **Objetivo**: Predecir la cantidad de incidentes que se esperan en cada categoría
- 📈 **Métricas**:
  - Predicción para el próximo período
  - Comparación con el mes anterior
  - Tendencia (Alza/Baja/Estable)
  - Nivel de confianza basado en variabilidad histórica
  - Datos históricos utilizados

**Cómo funciona**:
1. Agrupa incidentes por categoría y mes
2. Aplica pesos mayores a datos más recientes
3. Calcula la tendencia de cambio
4. Genera predicción = promedio ponderado + tendencia
5. Calcula nivel de confianza basado en la desviación estándar

**Casos de uso**:
- Identificar categorías con crecimiento de incidentes
- Asignar recursos preventivos a áreas críticas
- Planificar capacitación específica por categoría

---

### 2. **Predicción de Tiempo de Resolución (MTTR)**
- ⏱️ **Algoritmo**: Análisis estadístico de tiempos históricos
- 🎯 **Objetivo**: Estimar el tiempo que tomará resolver un incidente
- 📊 **Parámetros**: Categoría del incidente y nivel de prioridad
- 📈 **Métricas**:
  - Tiempo estimado en horas
  - Rango mínimo y máximo (intervalo de confianza)
  - Mejor y peor caso histórico
  - Nivel de confianza
  - Casos históricos analizados

**Cómo funciona**:
1. Filtra incidentes resueltos por categoría y prioridad
2. Calcula promedio, mínimo, máximo y desviación estándar
3. Genera intervalo de confianza (±1 desviación estándar)
4. Calcula nivel de confianza basado en cantidad de casos

**Casos de uso**:
- Establecer SLAs realistas
- Planificar capacidad de recursos
- Informar tiempos esperados a usuarios

---

### 3. **Análisis de Patrones Temporales**
- 📅 **Algoritmo**: Análisis de frecuencia y distribución temporal
- 🎯 **Objetivo**: Identificar días y horarios con mayor actividad de incidentes
- 📈 **Análisis**:
  - **Días críticos**: Días de la semana con más incidentes
  - **Horarios pico**: Rangos horarios con mayor actividad
  - **Categorías de riesgo**: Tipos de incidentes más frecuentes
  - Porcentajes de distribución

**Cómo funciona**:
1. Extrae día de la semana y hora de cada incidente
2. Cuenta frecuencias por día y hora
3. Identifica los 3 días más críticos
4. Identifica las 3 horas más críticas
5. Calcula porcentajes de distribución

**Casos de uso**:
- Reforzar equipos técnicos en días/horarios críticos
- Planificar mantenimientos preventivos fuera de horarios pico
- Identificar patrones de uso del sistema

---

### 4. **Detección de Anomalías**
- 🚨 **Algoritmo**: Análisis de desviación estándar (Z-score)
- 🎯 **Objetivo**: Detectar picos o caídas inusuales en el volumen de incidentes
- 📊 **Parámetros**: Threshold de desviación (por defecto 2.0)
- 📈 **Métricas**:
  - Fecha de la anomalía
  - Cantidad de incidentes vs promedio
  - Desviación en unidades de desviación estándar
  - Tipo (Pico inusual / Baja inusual)
  - Categorías afectadas
  - Severidad (Alta/Media/Baja)

**Cómo funciona**:
1. Calcula promedio y desviación estándar de incidentes diarios
2. Define umbral superior: promedio + (threshold × desviación)
3. Define umbral inferior: promedio - (threshold × desviación)
4. Identifica días que exceden los umbrales
5. Clasifica severidad según distancia del promedio

**Casos de uso**:
- Detectar problemas sistémicos tempranamente
- Investigar causas de picos inusuales
- Validar efectividad de mejoras implementadas

---

### 5. **Predicción de Carga de Trabajo de Técnicos**
- 👥 **Algoritmo**: Proyección basada en promedios históricos
- 🎯 **Objetivo**: Estimar la carga de trabajo futura de cada técnico
- 📊 **Parámetros**: Días hacia adelante (por defecto 7)
- 📈 **Métricas**:
  - Incidentes actuales asignados
  - Promedio de incidentes diarios
  - Predicción para los próximos N días
  - Nivel de carga (Muy Alta/Alta/Media/Baja)
  - Promedio de horas de resolución
  - Código de color para visualización

**Cómo funciona**:
1. Obtiene historial de incidentes por técnico
2. Calcula promedio de incidentes por día trabajado
3. Proyecta: predicción = promedio diario × días adelante
4. Clasifica nivel de carga:
   - Muy Alta: ≥ 15 incidentes proyectados
   - Alta: ≥ 10 incidentes
   - Media: ≥ 5 incidentes
   - Baja: < 5 incidentes

**Casos de uso**:
- Redistribuir carga entre técnicos
- Identificar necesidad de contratar personal
- Planificar vacaciones y capacitaciones

---

### 6. **Recomendaciones Inteligentes**
- 💡 **Algoritmo**: Sistema de reglas basado en análisis combinado
- 🎯 **Objetivo**: Generar sugerencias accionables basadas en los datos
- 📊 **Tipos de recomendaciones**:
  1. **Categoría en Riesgo**: Cuando se prevé aumento significativo
  2. **Patrón Temporal**: Días/horas que concentran incidentes
  3. **Anomalía Detectada**: Picos inusuales recientes
  4. **Carga de Trabajo**: Técnicos sobrecargados
- 📈 **Componentes**:
  - Tipo de recomendación
  - Nivel de severidad (Alta/Media/Baja)
  - Mensaje descriptivo
  - Acción sugerida

**Cómo funciona**:
1. Ejecuta todos los análisis predictivos
2. Aplica reglas de negocio para generar recomendaciones:
   - Si categoría con predicción > mes anterior → Recomendar más recursos
   - Si días críticos concentran > 30% → Reforzar equipo esos días
   - Si hay anomalías de alta severidad → Investigar causas raíz
   - Si técnicos con carga alta → Redistribuir o contratar
3. Prioriza recomendaciones por severidad

**Casos de uso**:
- Guiar decisiones estratégicas del Jefe de TI
- Identificar áreas de mejora prioritarias
- Planificación proactiva de recursos

---

## 🏗️ Arquitectura Técnica

### Archivos del Módulo

```
app/
├── controllers/
│   └── control_predicciones.py       # Controlador con toda la lógica de IA
├── templates/
│   └── predicciones_ia.html          # Interfaz visual con gráficos
└── run.py                             # Rutas Flask para APIs

MODULO_PREDICCIONES_IA.md             # Esta documentación
requirements.txt                       # Dependencias actualizadas
```

### Dependencias de ML

```python
numpy>=1.24.0          # Ya incluido para biometría
pandas>=2.0.0          # Manipulación de datos (NUEVA)
scikit-learn>=1.3.0    # Algoritmos ML (NUEVA)
scipy>=1.11.0          # Cálculos científicos (NUEVA)
```

Para instalar las nuevas dependencias:
```bash
pip install pandas scikit-learn scipy
```

O instalar todo:
```bash
pip install -r requirements.txt
```

---

## 🔌 APIs Disponibles

### 1. Vista Principal
```
GET /predicciones_ia
```
- **Descripción**: Página principal del módulo con dashboard interactivo
- **Requiere**: Rol de Jefe de TI
- **Respuesta**: Render de plantilla HTML

### 2. Predicciones por Categoría
```
GET /api/predicciones/categorias?meses=3
```
- **Parámetros**:
  - `meses` (opcional, default=3): Meses de historial a analizar
- **Respuesta**:
```json
{
  "success": true,
  "predicciones": [
    {
      "categoria": "Hardware",
      "prediccion": 25.5,
      "historico_promedio": 22.3,
      "mes_anterior": 24,
      "tendencia": "Alza",
      "confianza": 87.5,
      "datos_historicos": 3
    }
  ]
}
```

### 3. Predicción de Tiempo de Resolución
```
GET /api/predicciones/tiempo-resolucion?categoria=1&nivel=A
```
- **Parámetros**:
  - `categoria` (opcional): ID de categoría
  - `nivel` (opcional, default='M'): Prioridad (A/M/B)
- **Respuesta**:
```json
{
  "success": true,
  "prediccion": {
    "estimado_horas": 8.5,
    "rango_min": 6.2,
    "rango_max": 10.8,
    "mejor_caso": 2.5,
    "peor_caso": 24.0,
    "confianza": 85.0,
    "basado_en_casos": 45
  }
}
```

### 4. Patrones Temporales
```
GET /api/predicciones/patrones-temporales?meses=3
```
- **Parámetros**:
  - `meses` (opcional, default=3): Período de análisis
- **Respuesta**:
```json
{
  "success": true,
  "patrones": {
    "dias_criticos": [
      {"dia": "Lunes", "cantidad": 45, "porcentaje": 25.5}
    ],
    "horas_criticas": [
      {"hora": "09:00 - 09:59", "cantidad": 32, "porcentaje": 18.1}
    ],
    "categorias_riesgo": [
      {"categoria": "Hardware", "cantidad": 67, "porcentaje": 38.0}
    ],
    "total_incidentes": 176,
    "periodo_analisis": "Últimos 3 meses"
  }
}
```

### 5. Detección de Anomalías
```
GET /api/predicciones/anomalias?threshold=2.0
```
- **Parámetros**:
  - `threshold` (opcional, default=2.0): Sensibilidad de detección
- **Respuesta**:
```json
{
  "success": true,
  "anomalias": [
    {
      "fecha": "2025-11-20",
      "cantidad": 35,
      "promedio": 18.5,
      "desviacion": 2.8,
      "tipo": "Pico inusual",
      "categorias_afectadas": "Hardware, Software",
      "severidad": "Alta"
    }
  ]
}
```

### 6. Carga de Técnicos
```
GET /api/predicciones/carga-tecnicos?dias=7
```
- **Parámetros**:
  - `dias` (opcional, default=7): Días hacia adelante para predicción
- **Respuesta**:
```json
{
  "success": true,
  "predicciones": [
    {
      "id_tecnico": 5,
      "nombre": "Juan Pérez",
      "incidentes_actuales": 8,
      "promedio_diario": 2.1,
      "prediccion_proximos_dias": 14.7,
      "nivel_carga": "Alta",
      "color": "orange",
      "promedio_horas_resolucion": 6.5
    }
  ]
}
```

### 7. Recomendaciones
```
GET /api/predicciones/recomendaciones
```
- **Sin parámetros**
- **Respuesta**:
```json
{
  "success": true,
  "recomendaciones": [
    {
      "tipo": "Categoría en Riesgo",
      "severidad": "Alta",
      "mensaje": "Se prevé un aumento de incidentes en 'Hardware'. Predicción: 28.5 incidentes (vs 24 del mes anterior).",
      "accion": "Considerar asignar más recursos preventivos a esta categoría."
    }
  ]
}
```

---

## 🎨 Interfaz de Usuario

### Características Visuales

1. **Dashboard Moderno**:
   - Diseño tipo tarjetas con animaciones
   - Gradientes y efectos visuales
   - Iconos descriptivos para cada sección
   - Diseño responsive (móvil y desktop)

2. **Gráficos Interactivos**:
   - Gráficos de barras comparativos (Chart.js)
   - Código de colores intuitivo
   - Leyendas y etiquetas claras

3. **Filtros Dinámicos**:
   - Selector de meses históricos (1, 3, 6, 12)
   - Selector de días para predicción (7, 14, 30)
   - Botón de actualización manual

4. **Tarjetas de Información**:
   - **Predicciones**: Gráfico + top 5 categorías
   - **Patrones**: Días y horas críticas
   - **Anomalías**: Lista scrolleable de eventos inusuales
   - **Carga**: Grid de técnicos con código de colores
   - **Recomendaciones**: Lista priorizada con acciones

5. **Estados Visuales**:
   - Loading spinner durante carga
   - Empty states para sin datos
   - Mensajes de error amigables

---

## 🚀 Cómo Usar el Módulo

### Acceso al Módulo

1. **Iniciar sesión** como **Jefe de TI** (id_rol = 1)
2. En el **menú lateral**, hacer clic en **"Predicciones IA"**
3. El dashboard cargará automáticamente todas las predicciones

### Interpretación de Datos

#### Predicciones por Categoría
- **Verde (Baja)**: Tendencia a la baja, situación bajo control
- **Amarillo (Estable)**: Sin cambios significativos
- **Rojo (Alza)**: Aumento previsto, requiere atención

**Ejemplo**:
```
Categoría: Hardware
Predicción: 28.5 incidentes
Mes anterior: 24 incidentes
Tendencia: Alza (🔺)
Confianza: 87.5%

→ Acción: Asignar más técnicos a soporte de hardware
```

#### Carga de Técnicos
- **Verde (Baja)**: < 5 incidentes proyectados
- **Amarillo (Media)**: 5-9 incidentes
- **Naranja (Alta)**: 10-14 incidentes
- **Rojo (Muy Alta)**: ≥ 15 incidentes

**Ejemplo**:
```
Técnico: Juan Pérez
Predicción 7 días: 14.7 incidentes
Nivel: Alta (🟠)

→ Acción: Redistribuir carga o asignar apoyo
```

#### Anomalías
- **Alta Severidad**: > 3 desviaciones del promedio
- **Media Severidad**: 2-3 desviaciones

**Ejemplo**:
```
Fecha: 2025-11-20
Incidentes: 35 (promedio: 18.5)
Tipo: Pico inusual
Severidad: Alta (🚨)

→ Acción: Investigar causa raíz del pico
```

---

## 📊 Casos de Uso Reales

### Caso 1: Planificación de Recursos
**Situación**: Se aproxima el inicio de clases en la universidad

**Análisis**:
1. Revisar predicciones por categoría
2. Identificar aumento en "Redes" y "Software"
3. Ver patrones temporales → Lunes y Martes críticos

**Decisiones**:
- Asignar 2 técnicos adicionales de redes los lunes
- Programar mantenimiento preventivo el fin de semana anterior
- Preparar respuestas rápidas para problemas comunes

---

### Caso 2: Optimización de Equipo
**Situación**: Presupuesto limitado, necesidad de priorizar contrataciones

**Análisis**:
1. Revisar carga de técnicos
2. Identificar 3 técnicos con carga "Muy Alta" constante
3. Ver categorías más afectadas

**Decisiones**:
- Contratar técnico especializado en categoría más crítica
- Redistribuir incidentes de baja prioridad
- Implementar soluciones de autoservicio para problemas comunes

---

### Caso 3: Detección de Problemas Sistémicos
**Situación**: Pico inusual de incidentes detectado

**Análisis**:
1. Revisar anomalías → Pico de 35 incidentes (promedio: 18)
2. Ver categorías afectadas → Mayoría en "Software - ERP"
3. Revisar fecha → Coincide con actualización del sistema

**Decisiones**:
- Rollback de la actualización problemática
- Comunicar problema a usuarios
- Mejorar proceso de testing antes de actualizaciones

---

## 🔧 Configuración Avanzada

### Ajustar Sensibilidad de Anomalías

En el código `control_predicciones.py`, método `detectar_anomalias`:

```python
# Más sensible (detecta más anomalías)
threshold = 1.5  

# Menos sensible (solo anomalías muy evidentes)
threshold = 3.0  

# Por defecto (equilibrado)
threshold = 2.0
```

### Modificar Clasificación de Carga

En `predecir_carga_tecnicos`:

```python
# Ajustar umbrales según necesidad del equipo
if prediccion_semanal >= 15:
    nivel_carga = 'Muy Alta'
elif prediccion_semanal >= 10:
    nivel_carga = 'Alta'
elif prediccion_semanal >= 5:
    nivel_carga = 'Media'
else:
    nivel_carga = 'Baja'
```

### Personalizar Recomendaciones

En `obtener_recomendaciones`, agregar nuevas reglas:

```python
# Ejemplo: Detectar si un área tiene tiempos de resolución muy altos
if promedio_mttr > 24:  # Más de 24 horas
    recomendaciones.append({
        'tipo': 'MTTR Elevado',
        'severidad': 'Alta',
        'mensaje': 'El tiempo promedio de resolución excede las 24 horas.',
        'accion': 'Revisar procesos y capacitar al equipo.'
    })
```

---

## 🧪 Testing y Validación

### Verificar Datos Históricos

```python
from controllers.control_predicciones import ControlPredicciones

# Obtener datos de los últimos 3 meses
datos = ControlPredicciones.obtener_datos_historicos(3)
print(f"Total de incidentes analizados: {len(datos)}")
```

### Probar Predicciones

```python
# Predicciones por categoría
predicciones = ControlPredicciones.predecir_incidentes_por_categoria(3, 1)
for pred in predicciones[:3]:
    print(f"{pred['categoria']}: {pred['prediccion']} incidentes esperados")
```

### Validar Anomalías

```python
# Detectar anomalías
anomalias = ControlPredicciones.detectar_anomalias(2.0)
print(f"Anomalías detectadas: {len(anomalias)}")
```

---

## 📈 Métricas de Éxito

### KPIs del Módulo

1. **Precisión de Predicciones**:
   - Comparar predicciones vs realidad mensualmente
   - Meta: ±15% de precisión

2. **Reducción de Sobrecarga**:
   - Medir distribución de carga antes y después
   - Meta: Ningún técnico con carga "Muy Alta" > 2 semanas

3. **Detección Temprana**:
   - Contar problemas sistémicos detectados antes de que escalen
   - Meta: 80% de detección proactiva

4. **Adopción**:
   - Frecuencia de uso por el Jefe de TI
   - Meta: Revisión semanal mínima

---

## 🐛 Solución de Problemas

### Error: "No hay suficientes datos históricos"

**Causa**: Menos de 2 meses de datos en la base de datos

**Solución**:
1. Esperar a acumular más datos históricos
2. Reducir período de análisis a 1 mes
3. Verificar que hay incidentes registrados con fechas correctas

### Gráficos no se muestran

**Causa**: Chart.js no cargó correctamente

**Solución**:
1. Verificar conexión a internet (CDN de Chart.js)
2. Revisar consola del navegador (F12) para errores
3. Limpiar caché del navegador

### Predicciones con baja confianza

**Causa**: Alta variabilidad en datos históricos

**Solución**:
1. Aumentar período de análisis (más meses)
2. Revisar si hay estacionalidad (ej: período de clases vs vacaciones)
3. Considerar segmentar análisis por temporada

### API retorna error 403

**Causa**: Usuario sin permisos de Jefe de TI

**Solución**:
1. Verificar rol del usuario en sesión
2. Confirmar que `es_jefe_ti()` retorna `True`
3. Revisar tabla `ROL` y `USUARIO` en la base de datos

---

## 🔮 Futuras Mejoras

### Corto Plazo
- [ ] Exportar reportes de predicciones a PDF
- [ ] Notificaciones automáticas cuando se detectan anomalías
- [ ] Dashboard personalizable (arrastrar y soltar widgets)
- [ ] Comparación de predicción vs realidad mensual

### Mediano Plazo
- [ ] Modelos de ML más avanzados (Random Forest, Gradient Boosting)
- [ ] Predicción de categoría de nuevos incidentes basada en descripción
- [ ] Análisis de sentimiento en descripciones de incidentes
- [ ] Predicción de recurrencia de incidentes

### Largo Plazo
- [ ] Sistema de recomendación de soluciones basado en casos similares
- [ ] Chatbot con IA para consultas sobre predicciones
- [ ] Integración con sistemas externos (calendario, ERP, etc.)
- [ ] Análisis predictivo en tiempo real

---

## 📚 Referencias y Recursos

### Documentación Técnica
- [NumPy Documentation](https://numpy.org/doc/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Scikit-learn Documentation](https://scikit-learn.org/stable/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)

### Conceptos de ML Utilizados
- **Promedio Móvil Ponderado**: Técnica de suavizado que da más peso a observaciones recientes
- **Desviación Estándar**: Medida de variabilidad de los datos
- **Z-Score**: Número de desviaciones estándar que un valor está del promedio
- **Intervalo de Confianza**: Rango en el que se espera que caiga un valor

### Algoritmos Futuros
- **Random Forest**: Ensemble de árboles de decisión para predicciones más robustas
- **Gradient Boosting**: Método iterativo que mejora predicciones sucesivamente
- **LSTM (Long Short-Term Memory)**: Red neuronal para series temporales
- **K-Means Clustering**: Agrupación de incidentes similares

---

## 👥 Soporte y Contacto

### Reportar Problemas
Si encuentras algún error o tienes sugerencias:

1. **Logs**: Revisar consola de Python para mensajes de error
2. **Datos**: Verificar integridad de datos en base de datos
3. **Versiones**: Confirmar que todas las dependencias están instaladas

### Contribuciones
Para agregar nuevas funcionalidades:

1. **Crear nuevo método** en `ControlPredicciones`
2. **Agregar nueva API** en `run.py`
3. **Actualizar interfaz** en `predicciones_ia.html`
4. **Documentar** en este archivo

---

## 📝 Changelog

### Versión 1.0.0 (2025-11-25)
- ✅ Implementación inicial del módulo
- ✅ Predicción de incidentes por categoría
- ✅ Predicción de tiempo de resolución
- ✅ Análisis de patrones temporales
- ✅ Detección de anomalías
- ✅ Predicción de carga de técnicos
- ✅ Sistema de recomendaciones inteligentes
- ✅ Interfaz web con gráficos interactivos
- ✅ Integración con menú lateral
- ✅ APIs RESTful completas
- ✅ Documentación completa

---

## ✅ Resumen Ejecutivo

El **Módulo de Predicciones con IA** transforma la gestión reactiva de incidentes en una gestión **proactiva y basada en datos**. Mediante el análisis de patrones históricos y la aplicación de algoritmos de Machine Learning, el sistema:

✨ **Anticipa problemas** antes de que escalen
✨ **Optimiza recursos** distribuyendo carga eficientemente
✨ **Reduce tiempos** mediante planificación informada
✨ **Mejora decisiones** con recomendaciones basadas en datos
✨ **Detecta anomalías** para respuesta rápida

Este módulo convierte los datos históricos de incidentes en **inteligencia accionable**, permitiendo al Jefe de TI tomar decisiones estratégicas que mejoran la eficiencia operativa y la satisfacción de usuarios.

---

**Documentación creada**: 25 de Noviembre, 2025
**Autor**: Sistema de Gestión de Incidentes TI - Módulo de IA
**Versión**: 1.0.0


