# 📐 Distribución de Firmas en el PDF

## 🎯 Problema Resuelto

**ANTES:**
- ❌ Todas las firmas aparecían MUY ABAJO en el PDF (y=50)
- ❌ Las firmas se SUPERPONÍAN entre sí
- ❌ Solo había 6 posiciones predefinidas

**AHORA:**
- ✅ Las firmas aparecen en posiciones VISIBLES y BIEN DISTRIBUIDAS
- ✅ Cada firma tiene su PROPIA POSICIÓN calculada dinámicamente
- ✅ Soporte para ILIMITADAS firmas sin superposición

---

## 📊 Nueva Distribución de Firmas

### **Vista del PDF (Última Página):**

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│          CONTRATO DE SERVICIOS 2025                 │
│                                                     │
│  [...contenido del contrato...]                    │
│                                                     │
│                                                     │
├─────────────────────────────────────────────────────┤
│  🖊️ FIRMAS ELECTRÓNICAS:                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  FILA 3 (Orden 6-8):                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ Orden 6 │  │ Orden 7 │  │ Orden 8 │   y=320    │
│  └─────────┘  └─────────┘  └─────────┘            │
│                                                     │
│  FILA 2 (Orden 3-5):                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ Orden 3 │  │ Orden 4 │  │ Orden 5 │   y=220    │
│  └─────────┘  └─────────┘  └─────────┘            │
│                                                     │
│  FILA 1 (Orden 0-2):                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ Orden 0 │  │ Orden 1 │  │ Orden 2 │   y=120    │
│  │ CREADOR │  │         │  │         │            │
│  └─────────┘  └─────────┘  └─────────┘            │
│     x=50       x=250       x=450                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📏 Parámetros de Configuración

```python
FIRMA_BASE_Y = 120        # Altura inicial desde abajo (más alto que antes)
FIRMA_ANCHO = 150         # Ancho de cada firma
FIRMA_ALTO = 60           # Alto de cada firma
FIRMA_MARGEN_X = 50       # Margen izquierdo
FIRMA_ESPACIADO_X = 200   # Espacio horizontal entre firmas
FIRMA_ESPACIADO_Y = 100   # Espacio vertical entre filas
FIRMAS_POR_FILA = 3       # Número de firmas por fila
```

---

## 🧮 Fórmula de Cálculo

### **Para cada firma con orden N:**

```python
fila = N ÷ 3          # División entera (0, 1, 2, ...)
columna = N mod 3     # Resto (0, 1, 2)

x = 50 + (columna × 200)
y = 120 + (fila × 100)
```

### **Ejemplos:**

| Orden | Nombre | Fila | Columna | X | Y | Posición |
|-------|--------|------|---------|---|---|----------|
| 0 | Creador | 0 | 0 | 50 | 120 | Abajo Izquierda |
| 1 | Firmante 1 | 0 | 1 | 250 | 120 | Abajo Centro |
| 2 | Firmante 2 | 0 | 2 | 450 | 120 | Abajo Derecha |
| 3 | Firmante 3 | 1 | 0 | 50 | 220 | Fila 2 Izquierda |
| 4 | Firmante 4 | 1 | 1 | 250 | 220 | Fila 2 Centro |
| 5 | Firmante 5 | 1 | 2 | 450 | 220 | Fila 2 Derecha |
| 6 | Firmante 6 | 2 | 0 | 50 | 320 | Fila 3 Izquierda |

---

## 🎨 Distribución Visual Detallada

### **3 Firmas (1 fila):**

```
┌─────────────────────────────────────────┐
│                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  │ 🔐 ✍️        │  │ ✍️           │  │ ✍️           │
│  │ Creador      │  │ Firmante 1   │  │ Firmante 2   │
│  │ 28/11/2025   │  │ 29/11/2025   │  │ 30/11/2025   │
│  └──────────────┘  └──────────────┘  └──────────────┘
│   50, 120          250, 120          450, 120
└─────────────────────────────────────────┘
```

---

### **6 Firmas (2 filas):**

```
┌─────────────────────────────────────────┐
│                                         │
│  FILA 2:                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  │ ✍️           │  │ ✍️           │  │ ✍️           │
│  │ Firmante 3   │  │ Firmante 4   │  │ Firmante 5   │
│  └──────────────┘  └──────────────┘  └──────────────┘
│   50, 220          250, 220          450, 220
│                                         │
│  FILA 1:                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  │ 🔐 ✍️        │  │ ✍️           │  │ ✍️           │
│  │ Creador      │  │ Firmante 1   │  │ Firmante 2   │
│  └──────────────┘  └──────────────┘  └──────────────┘
│   50, 120          250, 120          450, 120
└─────────────────────────────────────────┘
```

---

### **9 Firmas (3 filas):**

```
┌─────────────────────────────────────────┐
│  FILA 3: (y=320)                        │
│  [Orden 6]    [Orden 7]    [Orden 8]    │
│                                         │
│  FILA 2: (y=220)                        │
│  [Orden 3]    [Orden 4]    [Orden 5]    │
│                                         │
│  FILA 1: (y=120)                        │
│  [Orden 0]    [Orden 1]    [Orden 2]    │
│  (Creador)                              │
└─────────────────────────────────────────┘
```

---

## 📝 Contenido de Cada Firma

### **Con Sello (Solo Jefes):**

```
┌──────────────────────────┐
│ ┌────┐                   │
│ │🔐  │  ✍️ [Firma]       │  ← 150px ancho total
│ │    │                   │     55px sello + 95px firma
│ └────┘                   │
│                          │
│ Juan Pérez González      │  ← Nombre completo
│ Fecha: 28/11/2025 14:30  │  ← Fecha y hora
└──────────────────────────┘
   60px alto
```

### **Sin Sello (Técnicos y otros):**

```
┌──────────────────────────┐
│                          │
│  ✍️ [Firma completa]     │  ← 150px ancho completo
│                          │
│                          │
│ María López García       │  ← Nombre completo
│ Fecha: 29/11/2025 10:15  │  ← Fecha y hora
└──────────────────────────┘
   60px alto
```

---

## 🔧 Cambios en el Código

### **ANTES (Estático):**

```python
POSICIONES_FIRMA = {
    1: {'x': 50, 'y': 50, 'ancho': 150, 'alto': 60},    # ❌ Muy abajo
    2: {'x': 250, 'y': 50, 'ancho': 150, 'alto': 60},   # ❌ Superposición
    3: {'x': 450, 'y': 50, 'ancho': 150, 'alto': 60},   # ❌ Solo 6 posiciones
    # ...
}

posicion = POSICIONES_FIRMA.get(orden_firma)
if not posicion:  # ❌ Sin posición para orden > 6
    posicion = {'x': 50, 'y': 50, 'ancho': 150, 'alto': 60}
```

### **AHORA (Dinámico):**

```python
@staticmethod
def calcular_posicion_firma(orden_firma):
    """Calcula dinámicamente la posición sin superposiciones"""
    fila = orden_firma // 3     # División entera
    columna = orden_firma % 3    # Resto
    
    x = 50 + (columna * 200)    # Espaciado horizontal
    y = 120 + (fila * 100)      # Espaciado vertical
    
    return {'x': x, 'y': y, 'ancho': 150, 'alto': 60}

# ✅ Funciona para CUALQUIER cantidad de firmas
posicion = FirmaService.calcular_posicion_firma(orden_firma)
```

---

## 🎯 Ventajas del Nuevo Sistema

### **1. Sin Superposiciones:**
- Cada firma tiene su posición única
- Espaciado uniforme entre firmas
- Sistema de cuadrícula ordenado

### **2. Escalable:**
- Soporta ilimitadas firmas
- Se crean filas automáticamente
- No hay límite de posiciones

### **3. Visibilidad Mejorada:**
- Firmas más arriba en la página (y=120 en lugar de y=50)
- Mejor uso del espacio vertical
- Fácil de leer y verificar

### **4. Predecible:**
- Siempre 3 firmas por fila
- Espaciado consistente
- Fácil de localizar cada firma

---

## 📊 Comparación: ANTES vs AHORA

### **ANTES:**

```
┌─────────────────────────┐
│                         │
│  [Contenido del PDF]    │
│                         │
│                         │ ← Mucho espacio vacío
│                         │
│                         │
│ ┌────┐┌────┐┌────┐      │ ← Firmas MUY abajo
│ │ 1  ││ 2  ││ 3  │      │   (y=50)
│ └────┘└────┘└────┘      │   Se superponen si
│ ┌────┐                  │   hay más de 6
│ │ 4  │  ← Superpuesta   │
│ └────┘                  │
└─────────────────────────┘
```

### **AHORA:**

```
┌─────────────────────────┐
│                         │
│  [Contenido del PDF]    │
│                         │
│                         │
│ ┌────┐┌────┐┌────┐      │ ← Fila 2 (y=220)
│ │ 3  ││ 4  ││ 5  │      │   Espaciadas
│ └────┘└────┘└────┘      │
│                         │
│ ┌────┐┌────┐┌────┐      │ ← Fila 1 (y=120)
│ │ 0  ││ 1  ││ 2  │      │   Bien visible
│ └────┘└────┘└────┘      │
└─────────────────────────┘
```

---

## 🧪 Cómo Verificar

### **Test 1: Crear Contrato Con Firma**
```
1. Crear contrato (Orden 0 - Creador)
2. Descargar PDF
3. Verificar: Firma visible en posición (50, 120)
4. NO debe estar pegada al borde inferior
```

### **Test 2: Múltiples Firmantes**
```
1. Crear contrato con 5 firmantes
2. Firmar en orden: 1, 2, 3, 4, 5
3. Descargar PDF final
4. Verificar:
   - Fila 1: Orden 0, 1, 2 (y=120)
   - Fila 2: Orden 3, 4, 5 (y=220)
   - Sin superposiciones
```

### **Test 3: Muchos Firmantes (9+)**
```
1. Crear contrato con 9 firmantes
2. Firmar todos
3. Descargar PDF
4. Verificar 3 filas completas:
   - Fila 1: (y=120)
   - Fila 2: (y=220)
   - Fila 3: (y=320)
```

---

## 🎨 Ajustes Disponibles

Si necesitas modificar el espaciado:

```python
# En firma_service.py

# Para mover TODO más arriba:
FIRMA_BASE_Y = 150  # Aumentar este valor

# Para más espacio horizontal:
FIRMA_ESPACIADO_X = 220  # Aumentar separación

# Para más espacio vertical:
FIRMA_ESPACIADO_Y = 120  # Aumentar separación entre filas

# Para más firmas por fila:
FIRMAS_POR_FILA = 4  # Cambiar de 3 a 4 columnas
```

---

## 📐 Coordenadas del PDF

**Sistema de coordenadas de ReportLab:**
```
(0, 792) ← Esquina superior izquierda
    ↓
    │
    │  Altura de página Letter = 792 puntos
    │
    ↓
(0, 0) ← Esquina inferior izquierda
→ Ancho de página Letter = 612 puntos
```

**Nuestras firmas:**
- Empiezan en y=120 (desde abajo)
- Están a 120 puntos del borde inferior
- Cada fila adicional suma +100 puntos

---

## ✅ Resultado Final

Ahora cuando descargues un PDF firmado, verás:

1. ✅ Firmas **visibles** y **bien posicionadas**
2. ✅ **Sin superposiciones** entre firmas
3. ✅ **Espaciado uniforme** y profesional
4. ✅ **Escalable** a cualquier cantidad de firmantes
5. ✅ **Orden claro**: Fila 1 = primeras 3, Fila 2 = siguientes 3, etc.

---

**Última actualización:** 28 de Noviembre de 2025  
**Versión:** 2.2.0  
**Archivo:** `app/services/firma_service.py`

