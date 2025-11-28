# 📄 Visualización del Sello y Firma en el PDF

## ✅ Cómo se ve en el PDF Final

### **Cuando un JEFE firma:**

```
┌────────────────────────────────────────────────┐
│                                                │
│  ┌──────┐  ┌─────────────────────────────┐   │
│  │      │  │                             │   │
│  │  🔐  │  │  ✍️ María López             │   │
│  │      │  │  ~~~~~~~~~~~~~~~~~~~        │   │
│  │SELLO │  │      [Firma dibujada]       │   │
│  │55x55 │  │                             │   │
│  │ px   │  │                             │   │
│  └──────┘  └─────────────────────────────┘   │
│  ↑           ↑                                │
│  Borde gris  Firma más pequeña (90x60)       │
│                                                │
│  Jefe Finanzas - María López                  │
│  Fecha: 15/11/2025 14:30                     │
│                                                │
└────────────────────────────────────────────────┘
```

**Características:**
- ✅ Sello a la **izquierda** (55x55 puntos)
- ✅ Borde gris alrededor del sello
- ✅ Firma a la **derecha** (90x60 puntos)
- ✅ Espacio de 10px entre sello y firma
- ✅ Nombre y fecha debajo

---

### **Cuando un TÉCNICO firma:**

```
┌────────────────────────────────────────────────┐
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │                                          │ │
│  │  ✍️ Carlos Ruiz                          │ │
│  │  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~     │ │
│  │          [Firma dibujada]                │ │
│  │                                          │ │
│  │      Firma completa (150x60 puntos)      │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Técnico TI - Carlos Ruiz                     │
│  Fecha: 17/11/2025 11:45                     │
│                                                │
└────────────────────────────────────────────────┘
```

**Características:**
- ❌ **Sin sello** (no es jefe)
- ✅ Firma ocupa **todo el espacio** (150x60 puntos)
- ✅ Nombre y fecha debajo

---

## 🎨 Comparación Visual

### **JEFE:**
```
[🔐 Sello 55x55] → [✍️ Firma 90x60]
     ↓                    ↓
  Con borde          Más pequeña
```

### **TÉCNICO:**
```
[✍️ Firma 150x60 - Espacio completo]
          ↓
     Más grande
```

---

## 📊 Tabla de Tamaños

| Elemento | Jefe (con sello) | Técnico (sin sello) |
|----------|------------------|---------------------|
| **Sello** | 55x55 px ✅ | No aplica ❌ |
| **Firma** | 90x60 px | 150x60 px |
| **Espacio total** | 150x60 px | 150x60 px |
| **Separación** | 10 px entre sello y firma | N/A |

---

## 🔍 Ejemplo Completo en el PDF

```
ÚLTIMA PÁGINA DEL CONTRATO
───────────────────────────────────────────

FIRMAS AUTORIZADAS:

1️⃣ [🔐] → [✍️~~~~~~]  Jefe Finanzas - María López
   Fecha: 15/11/2025 14:30

2️⃣ [🔐] → [✍️~~~~~~]  Jefe Logística - Juan García
   Fecha: 16/11/2025 09:15

3️⃣        [✍️~~~~~~~~~~~~~~~~]  Técnico TI - Carlos Ruiz
   Fecha: 17/11/2025 11:45

4️⃣ [🔐] → [✍️~~~~~~]  Gerente General - Ana Martínez
   Fecha: 18/11/2025 10:20
```

---

## 💡 Notas Importantes

### **El sello se dibuja AUTOMÁTICAMENTE:**
1. ✅ Cuando un **jefe** sube su sello en la interfaz
2. ✅ El backend (`firma_service.py`) lo procesa
3. ✅ Se dibuja en el PDF junto con la firma
4. ✅ Se añade un borde gris para destacarlo

### **Sin intervención manual:**
- ❌ NO necesitas agregar el sello manualmente al PDF
- ✅ El sistema lo hace automáticamente
- ✅ Solo sube la imagen del sello en la interfaz

### **Validaciones:**
- ✅ El sello debe ser una imagen (PNG, JPG)
- ✅ Máximo 5MB
- ✅ Se redimensiona automáticamente a 55x55 puntos
- ✅ Se mantiene la proporción (aspect ratio)

---

## 🧪 Para Verificar

### **En la consola del servidor (terminal):**

Cuando un jefe firma, verás:

```bash
🔐 Añadiendo sello institucional al PDF para María López
✍️ Añadiendo firma al PDF para María López
✅ FIRMA + SELLO de 'María López' añadidos al PDF (orden #1)
   📐 Layout: [🔐 Sello 55x55] → [✍️ Firma 90x60]
```

Cuando un técnico firma:

```bash
✍️ Añadiendo firma al PDF para Carlos Ruiz
✅ FIRMA de 'Carlos Ruiz' añadida al PDF (orden #3)
   📐 Layout: [✍️ Firma 150x60]
```

---

## 📥 Resultado Final

El PDF descargable incluirá:
- ✅ Todas las firmas en la última página
- ✅ Sellos visibles (con borde gris) para jefes
- ✅ Firmas más grandes para no-jefes
- ✅ Nombres y fechas debajo de cada firma
- ✅ Orden numérico claro (1, 2, 3...)

---

**Fecha:** 28/11/2025  
**Versión:** 2.1

