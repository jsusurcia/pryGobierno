# 📊 Corrección de Reportes MTTR - Base de Datos

## 🎯 Problema Identificado

El código de reportes MTTR tenía varios errores que impedían su correcto funcionamiento con el esquema de base de datos:

### ❌ **Errores Encontrados:**

1. **Nombres de tablas incorrectos** (minúsculas vs mayúsculas)
   - Usaba: `incidentes`, `categorias`
   - Correcto: `INCIDENTE`, `CATEGORIA`

2. **Estados de incidente incorrectos**
   - Usaba: `'R', 'C', 'resuelto', 'cerrado'`
   - Correcto según BD: `'T'` (Terminado), `'C'` (Cancelado)

3. **Campo `tiempo_reparacion` no se calculaba en todos los casos**
   - No se calculaba al cancelar incidente
   - No se calculaba al aceptar diagnóstico

---

## ✅ Solución Implementada

### **1. Corrección de Nombres de Tablas**

**Antes:**
```sql
FROM incidentes i
LEFT JOIN categorias c ON...
```

**Ahora:**
```sql
FROM INCIDENTE i
LEFT JOIN CATEGORIA c ON...
```

---

### **2. Corrección de Estados**

**Según el esquema de BD:**
```sql
estado CHAR(1) NOT NULL CHECK (estado IN ('P','A','T','C')) DEFAULT 'P'

-- P = Pendiente
-- A = Activo
-- T = Terminado
-- C = Cancelado
```

**Todos los reportes MTTR ahora filtran correctamente:**
```sql
WHERE i.estado IN ('T', 'C')  -- Solo incidentes finalizados
```

---

### **3. Cálculo Correcto de `tiempo_reparacion`**

El campo `tiempo_reparacion` es de tipo `INTERVAL` y se calcula como:
```sql
tiempo_reparacion = NOW() - fecha_reporte
```

#### **Métodos actualizados:**

**a) `actualizar_estado()` - Ya estaba correcto ✅**
```python
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
```

**b) `cambiar_estado_jefe_ti()` - CORREGIDO ✨**

**Antes:**
```python
sql = """
    UPDATE INCIDENTE
    SET estado = %s
    WHERE id_incidente = %s AND estado = 'P'
"""
```

**Ahora:**
```python
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
```

**c) `aceptar_revision()` en control_diagnostico.py - CORREGIDO ✨**

**Antes:**
```python
sql = """
    UPDATE INCIDENTE
    SET estado = 'T', fecha_resolucion = NOW()
    WHERE id_incidente = %s;
"""
```

**Ahora:**
```python
sql = """
    UPDATE INCIDENTE
    SET estado = 'T', 
        fecha_resolucion = NOW(),
        tiempo_reparacion = NOW() - fecha_reporte
    WHERE id_incidente = %s;
"""
```

---

### **4. Uso Correcto de `tiempo_reparacion` en Reportes**

Todos los métodos de MTTR ahora usan esta lógica:

```sql
CASE 
    -- Prioridad 1: Si existe tiempo_reparacion (calculado por el sistema)
    WHEN COUNT(CASE WHEN i.tiempo_reparacion IS NOT NULL THEN 1 END) > 0 THEN
        ROUND(AVG(EXTRACT(EPOCH FROM i.tiempo_reparacion) / 3600), 2)
    
    -- Prioridad 2: Calcular manualmente si no existe (fallback)
    WHEN COUNT(CASE WHEN i.fecha_resolucion IS NOT NULL AND i.fecha_reporte IS NOT NULL THEN 1 END) > 0 THEN
        ROUND(AVG(EXTRACT(EPOCH FROM (i.fecha_resolucion - fecha_reporte)) / 3600), 2)
    
    -- Default: 0 horas
    ELSE 0
END AS mttr_horas
```

**¿Cómo funciona `EXTRACT(EPOCH FROM ...)`?**
- `EXTRACT(EPOCH FROM interval)` convierte un INTERVAL a segundos totales
- Dividir entre 3600 convierte segundos a horas
- `ROUND(..., 2)` redondea a 2 decimales

---

## 📋 Métodos Corregidos

| Método | Archivo | Corrección |
|--------|---------|------------|
| `obtener_mttr_por_categoria()` | control_incidentes.py | ✅ Nombres de tablas + Estados |
| `obtener_estadisticas_mttr()` | control_incidentes.py | ✅ Estados ('T', 'C') |
| `obtener_mttr_completo_por_categoria()` | control_incidentes.py | ✅ Estados ('T', 'C') |
| `obtener_tendencia_mttr()` | control_incidentes.py | ✅ Estados ('T', 'C') |
| `obtener_mttr_filtrado()` | control_incidentes.py | ✅ Estados ('T', 'C') |
| `cambiar_estado_jefe_ti()` | control_incidentes.py | ✅ Calcula tiempo_reparacion |
| `aceptar_revision()` | control_diagnostico.py | ✅ Calcula tiempo_reparacion |

---

## 🔍 Ejemplo de Cálculo MTTR

### **Escenario:**
- **Incidente reportado:** 2025-11-25 10:00:00
- **Incidente terminado:** 2025-11-25 14:30:00

### **Cálculo:**
```sql
tiempo_reparacion = NOW() - fecha_reporte
                 = 2025-11-25 14:30:00 - 2025-11-25 10:00:00
                 = INTERVAL '4 hours 30 minutes'
```

### **Conversión a horas:**
```sql
EXTRACT(EPOCH FROM '4 hours 30 minutes')  -- = 16200 segundos
16200 / 3600  -- = 4.5 horas
ROUND(4.5, 2)  -- = 4.5
```

**Resultado:** MTTR = **4.5 horas**

---

## 📊 Estructura de Base de Datos Verificada

### **Tabla INCIDENTE:**
```sql
CREATE TABLE INCIDENTE (
    id_incidente SERIAL PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT NOT NULL,
    id_categoria INTEGER NOT NULL,
    id_usuario INTEGER NOT NULL,
    id_tecnico_asignado INTEGER,
    estado CHAR(1) NOT NULL CHECK (estado IN ('P','A','T','C')) DEFAULT 'P',
    nivel CHAR(1) NOT NULL CHECK (nivel IN ('B','M','A','C')),
    fecha_reporte TIMESTAMP DEFAULT NOW(),
    fecha_resolucion TIMESTAMP,
    tiempo_reparacion INTERVAL,  -- ✅ Campo usado para MTTR
    ...
);
```

### **Estados válidos:**
- **'P'** = Pendiente (recién creado, esperando aceptación)
- **'A'** = Activo (aceptado por Jefe TI, en proceso)
- **'T'** = Terminado (diagnóstico aceptado, finalizado)
- **'C'** = Cancelado (rechazado por Jefe TI)

### **Para MTTR:**
Solo se consideran incidentes en estados **'T'** o **'C'** porque son estados finales.

---

## 🧪 Cómo Verificar que Funciona

### **Prueba 1: Crear y Terminar Incidente**
1. Jefe crea incidente → Estado: 'P'
2. Jefe TI acepta → Estado: 'A'
3. Técnico envía diagnóstico
4. Jefe TI acepta diagnóstico → Estado: 'T'
5. **Verificar en BD:**
   ```sql
   SELECT titulo, estado, fecha_reporte, fecha_resolucion, tiempo_reparacion
   FROM INCIDENTE WHERE id_incidente = X;
   ```
6. **Resultado esperado:**
   - estado = 'T'
   - fecha_resolucion = timestamp actual
   - tiempo_reparacion = INTERVAL (ej: '02:30:00' para 2.5 horas)

### **Prueba 2: Verificar MTTR en Reportes**
1. Ir a la ruta `/gestion_mttr`
2. **Verificar:**
   - ✅ Se muestran datos de incidentes reales
   - ✅ MTTR se calcula en horas
   - ✅ No hay errores en consola
   - ✅ Las categorías se muestran correctamente

### **Prueba 3: Verificar en Base de Datos**
```sql
-- Ver incidentes con tiempo_reparacion calculado
SELECT 
    id_incidente,
    titulo,
    estado,
    tiempo_reparacion,
    EXTRACT(EPOCH FROM tiempo_reparacion) / 3600 AS horas
FROM INCIDENTE
WHERE estado IN ('T', 'C')
AND tiempo_reparacion IS NOT NULL
ORDER BY id_incidente DESC;
```

### **Prueba 4: Verificar MTTR por Categoría**
```sql
-- Consulta manual de MTTR por categoría
SELECT 
    COALESCE(c.nombre, 'Sin categoría') AS categoria,
    ROUND(AVG(EXTRACT(EPOCH FROM i.tiempo_reparacion) / 3600), 2) AS mttr_horas,
    COUNT(i.id_incidente) AS total_incidentes
FROM INCIDENTE i
LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
WHERE i.estado IN ('T', 'C')
AND i.tiempo_reparacion IS NOT NULL
GROUP BY c.nombre
ORDER BY mttr_horas ASC;
```

---

## ✅ Estado: COMPLETADO

**Funcionalidades corregidas:**
- ✅ Nombres de tablas corregidos (INCIDENTE, CATEGORIA)
- ✅ Estados correctos para MTTR ('T', 'C')
- ✅ Cálculo de tiempo_reparacion en todos los escenarios
- ✅ Uso correcto del campo INTERVAL
- ✅ Conversión correcta a horas
- ✅ Fallback si tiempo_reparacion es NULL
- ✅ Sin errores de linting
- ✅ 7 métodos corregidos

**Archivos modificados:**
- `app/controllers/control_incidentes.py` (6 métodos)
- `app/controllers/control_diagnostico.py` (1 método)

---

## 📚 Documentación Relacionada

- `CAMBIOS_NOTIFICACIONES.md` - Sistema de notificaciones
- `MEJORAS_VISUALES_HISTORIAL.md` - Línea de tiempo
- `NOTIFICACIONES_DIAGNOSTICOS.md` - Notificaciones de diagnósticos

---

## 📈 Beneficios

1. ✅ **Reportes MTTR funcionales** con datos reales de la BD
2. ✅ **Métricas precisas** basadas en tiempo_reparacion
3. ✅ **Compatibilidad total** con el esquema de BD proporcionado
4. ✅ **Cálculo automático** del INTERVAL en todos los escenarios
5. ✅ **Fallback robusto** si el campo no está calculado

**Fecha:** 25 de noviembre de 2025

---

**¡Reportes MTTR completamente funcionales!** 📊✨



