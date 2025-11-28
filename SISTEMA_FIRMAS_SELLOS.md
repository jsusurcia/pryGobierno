# 🔐 Sistema de Firmas y Sellos - Documentación

## 📋 Resumen

Este documento explica cómo funciona el sistema de firmas electrónicas y sellos institucionales en el módulo de contratos.

---

## 👥 Roles y Requisitos

### **JEFES (Tipo 'J')**
```
Al CREAR un contrato:
✅ Sello institucional (imagen) *
✅ Firma electrónica (canvas) *

Al FIRMAR un contrato:
✅ Sello institucional (imagen) *
✅ Firma electrónica (canvas) *
```

### **OTROS ROLES (Técnicos, Administrativos, etc.)**
```
Al FIRMAR un contrato:
❌ Sello institucional (NO)
✅ Firma electrónica (canvas) *
```

---

## 🔄 Flujos de Trabajo

### **Escenario 1: Jefe crea contrato**

```
1. Jefe de Finanzas crea contrato
   ├─> Sube PDF
   ├─> Sube su SELLO 🔐
   ├─> Dibuja su FIRMA ✍️
   └─> Selecciona firmantes

2. PDF generado incluye:
   ├─> SELLO del creador
   └─> FIRMA del creador

3. Se envía al primer firmante
```

### **Escenario 2: Jefe firma contrato**

```
1. Jefe de Logística recibe notificación
   └─> Le toca firmar (orden #2)

2. Abre el contrato y ve:
   ├─> Sección SELLO INSTITUCIONAL 🔐
   │   └─> Campo para subir imagen
   └─> Canvas para FIRMA ✍️

3. Debe completar AMBOS campos

4. Al firmar:
   ├─> PDF se actualiza con SELLO + FIRMA
   └─> Se envía al siguiente firmante
```

### **Escenario 3: Técnico firma contrato**

```
1. Técnico recibe notificación
   └─> Le toca firmar (orden #3)

2. Abre el contrato y ve:
   ├─> ❌ NO hay sección de sello
   └─> ✅ Solo canvas para FIRMA ✍️

3. Dibuja su firma

4. Al firmar:
   ├─> PDF se actualiza solo con FIRMA
   └─> Se envía al siguiente firmante
```

---

## 🎨 Interfaz Visual

### **Vista para JEFES al firmar:**

```
┌──────────────────────────────────────┐
│  ✍️ Tu Firma                         │
├──────────────────────────────────────┤
│  ┌────────────────────────────────┐  │
│  │ 🔐 Tu Sello Institucional *    │  │
│  │                                │  │
│  │ [Subir archivo]                │  │
│  │                                │  │
│  │ ⚠️ Como jefe, debes subir      │  │
│  │    tu sello junto con tu firma │  │
│  └────────────────────────────────┘  │
│                                      │
│  ┌────────────────────────────────┐  │
│  │ ✍️ Tu Firma Electrónica *      │  │
│  │                                │  │
│  │  [Canvas para dibujar]         │  │
│  │                                │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

### **Vista para TÉCNICOS al firmar:**

```
┌──────────────────────────────────────┐
│  ✍️ Tu Firma                         │
├──────────────────────────────────────┤
│  ┌────────────────────────────────┐  │
│  │ ✍️ Tu Firma Electrónica *      │  │
│  │                                │  │
│  │  [Canvas para dibujar]         │  │
│  │                                │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
```

---

## 🔍 Validaciones Implementadas

### **Backend (`control_contratos.py`)**

```python
def firmar_contrato(id_contrato, id_usuario, firma_base64, sello_base64=None):
    # 1. Verificar si es jefe
    es_jefe = controlUsuarios.es_jefe(id_usuario)
    
    # 2. Validar que los jefes suban sello
    if es_jefe and not sello_base64:
        return {'success': False, 'message': 'Los jefes deben subir su sello institucional'}
    
    # 3. Añadir firma (y sello si aplica) al PDF
    pdf_firmado = FirmaService.agregar_firma_a_pdf(
        pdf_bytes,
        firma_base64,
        nombre_completo,
        orden_firma,
        sello_base64  # ← Opcional
    )
```

### **Frontend (`firmarContrato.html`)**

```javascript
// 1. Mostrar sección de sello solo para jefes
const esJefe = {{ 'true' if es_jefe else 'false' }};
if (esJefe) {
    document.getElementById('seccionSello').classList.remove('hidden');
}

// 2. Validar antes de enviar
if (esJefe && (!archivoSello.files || !archivoSello.files[0])) {
    alert('Como JEFE, debes subir tu sello institucional');
    return;
}

// 3. Enviar datos
const datos = {
    firma: firmaBase64
};

if (selloBase64) {
    datos.sello = selloBase64;  // ← Solo si es jefe
}
```

---

## 📄 Estructura del PDF Final

### **Contrato con 3 firmantes (Jefe, Jefe, Técnico):**

```
┌─────────────────────────────────────────────────┐
│  CONTRATO DE SERVICIOS                          │
│                                                 │
│  [... contenido del contrato ...]              │
│                                                 │
│  FIRMAS:                                        │
│  ┌─────────────────────────────────────────┐   │
│  │ ┌────┐                                  │   │
│  │ │🔐  │  ✍️ María López                 │   │
│  │ │    │  ~~~~~~~~~~~~~~~~~~             │   │
│  │ │55x │                                  │   │
│  │ │55px│                                  │   │
│  │ └────┘                                  │   │
│  │ Jefe Finanzas - María López             │   │
│  │ Fecha: 15/11/2025 14:30                │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │ ┌────┐                                  │   │
│  │ │🔐  │  ✍️ Juan García                 │   │
│  │ │    │  ~~~~~~~~~~~~~~~~~~             │   │
│  │ │55x │                                  │   │
│  │ │55px│                                  │   │
│  │ └────┘                                  │   │
│  │ Jefe Logística - Juan García            │   │
│  │ Fecha: 16/11/2025 09:15                │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │                                          │   │
│  │  ✍️ Carlos Ruiz                         │   │
│  │  ~~~~~~~~~~~~~~~~~~                     │   │
│  │  (Sin sello - no es jefe)              │   │
│  │                                          │   │
│  │ Técnico TI - Carlos Ruiz                │   │
│  │ Fecha: 17/11/2025 11:45                │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### **Detalles de Renderizado:**

#### **JEFE (con sello):**
```
┌──────────────────────────────────────┐
│  ┌─────┐  ┌──────────────────────┐  │
│  │     │  │                      │  │
│  │ 🔐  │  │  ✍️ [Firma dibujada] │  │
│  │     │  │                      │  │
│  │55x55│  │    90 x 60 puntos    │  │
│  └─────┘  └──────────────────────┘  │
│                                      │
│  Nombre del firmante                │
│  Fecha: DD/MM/YYYY HH:MM            │
└──────────────────────────────────────┘
```

#### **TÉCNICO (sin sello):**
```
┌──────────────────────────────────────┐
│  ┌────────────────────────────────┐  │
│  │                                │  │
│  │    ✍️ [Firma dibujada]         │  │
│  │                                │  │
│  │      150 x 60 puntos           │  │
│  └────────────────────────────────┘  │
│                                      │
│  Nombre del firmante                │
│  Fecha: DD/MM/YYYY HH:MM            │
└──────────────────────────────────────┘
```

---

## 🔧 Archivos Modificados

### **Backend:**
1. `app/controllers/control_contratos.py`
   - Método `firmar_contrato()` acepta `sello_base64` opcional
   
2. `app/services/firma_service.py`
   - Método `agregar_firma_a_pdf()` acepta `sello_base64` opcional
   - Dibuja sello (50x50px) a la izquierda de la firma

3. `app/run.py`
   - Ruta `firmar_contrato()` pasa variable `es_jefe` al template
   - API `/api/contrato/<id>/firmar` acepta campo `sello` opcional

### **Frontend:**
4. `app/templates/firmarContrato.html`
   - Sección de sello oculta por defecto
   - JavaScript muestra sección solo si `es_jefe == true`
   - Validación: jefes DEBEN subir sello
   - Vista previa del sello al cargarlo
   - Logs en consola para debugging

---

## 🧪 Pruebas

### **Test 1: Jefe firma sin sello**
```
❌ Resultado esperado: Error
   "Como JEFE, debes subir tu sello institucional..."
```

### **Test 2: Jefe firma con sello**
```
✅ Resultado esperado: Éxito
   PDF actualizado con SELLO + FIRMA
```

### **Test 3: Técnico firma**
```
✅ Resultado esperado: Éxito
   PDF actualizado solo con FIRMA
   No se muestra campo de sello
```

### **Test 4: Jefe firma con sello > 5MB**
```
❌ Resultado esperado: Error
   "El sello es muy grande. Máximo 5MB."
```

---

## 🎯 Resumen Visual

```
┌─────────────────────────────────────┐
│           CREAR CONTRATO            │
├─────────────────────────────────────┤
│  JEFES:                             │
│  • Sello ✅                         │
│  • Firma ✅                         │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│           FIRMAR CONTRATO           │
├─────────────────────────────────────┤
│  JEFES:                             │
│  • Sello ✅                         │
│  • Firma ✅                         │
│                                     │
│  OTROS ROLES:                       │
│  • Sello ❌                         │
│  • Firma ✅                         │
└─────────────────────────────────────┘
```

---

## 📞 Contacto

Para dudas o problemas con el sistema de firmas, consultar el log de la consola del navegador (F12) donde se muestran los pasos del proceso de firma.

---

**Fecha de actualización:** 28/11/2025  
**Versión:** 2.0

