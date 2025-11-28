# 📝 Firma del Creador en Contratos

## 🎯 Problema Resuelto

**ANTES:** Cuando un jefe creaba un contrato, su firma NO se agregaba al PDF inicial. Solo cuando alguien entraba a `firmar_contrato` se agregaba la firma.

**AHORA:** La firma (y sello si es jefe) del creador se agrega automáticamente al PDF inicial antes de enviarlo al primer firmante.

---

## 🔄 Flujo Actualizado

### **1️⃣ Crear Contrato (formCrearContrato.html)**

```
Usuario Creador:
├─ Sube PDF original ✅
├─ Ingresa título y descripción ✅
├─ Dibuja su firma en canvas ✅ NUEVO
├─ Sube su sello (opcional, si es jefe) ✅ NUEVO
├─ Selecciona firmantes ✅
└─ Hace clic en "Crear Contrato"
```

**JavaScript captura:**
```javascript
// Firma del canvas
const firmaBase64 = obtenerFirmaBase64();

// Sello del input file
const selloFile = document.getElementById('archivo_sello').files[0];
const selloBase64 = await convertirArchivoABase64(selloFile);

// Envía al backend
formData.set('firma_creador', firmaBase64);
formData.set('sello_creador', selloBase64);
```

---

### **2️⃣ Backend Procesa (run.py)**

```python
@app.route('/crear_contrato', methods=['POST'])
def crear_contrato():
    # Recibe datos del formulario
    pdf_file = request.files.get('pdf_file')
    firma_creador_base64 = request.form.get('firma_creador')  # ✅ NUEVO
    sello_creador_base64 = request.form.get('sello_creador')  # ✅ NUEVO
    
    # Valida que la firma esté presente
    if not firma_creador_base64:
        return jsonify({'success': False, 'message': 'La firma es obligatoria'}), 400
    
    # Llama al controlador con firma y sello
    resultado = ControlContratos.crear_contrato(
        pdf_bytes=pdf_bytes,
        firma_creador_base64=firma_creador_base64,
        sello_creador_base64=sello_creador_base64,
        ...
    )
```

---

### **3️⃣ Controlador Agrega Firma (control_contratos.py)**

```python
def crear_contrato(..., firma_creador_base64, sello_creador_base64):
    # 1. Obtiene nombre del creador
    usuario_creador = controlUsuarios.buscar_por_ID(id_usuario_creador)
    nombre_creador = f"{usuario_creador['nombre']} {usuario_creador['ape_pat']}"
    
    # 2. Agrega firma (y sello) al PDF inicial
    pdf_con_firma = FirmaService.agregar_firma_a_pdf(
        pdf_bytes=pdf_bytes,
        firma_base64=firma_creador_base64,
        nombre_firmante=nombre_creador,
        orden_firma=0,  # ✅ Creador es orden 0
        sello_base64=sello_creador_base64
    )
    
    # 3. Sube PDF con firma inicial a Catbox
    url_catbox = CatboxService.subir_pdf(pdf_con_firma)
    
    # 4. Crea registro en BD y notifica primer firmante
    ...
```

---

## 📊 Estructura de Firmas

### **Orden de Firmas en el PDF:**

```
┌─────────────────────────────────┐
│     CONTRATO DE SERVICIOS       │
│                                 │
│  [Contenido del contrato...]    │
│                                 │
├─────────────────────────────────┤
│  📝 FIRMAS:                     │
├─────────────────────────────────┤
│  Orden 0 (CREADOR):             │
│  ┌─────────────────────────────┐│
│  │ 🔐 [Sello] ✍️ [Firma]       ││  ← Al crear
│  │ Juan Pérez (Jefe de TI)     ││
│  │ Fecha: 28/11/2025 10:30     ││
│  └─────────────────────────────┘│
├─────────────────────────────────┤
│  Orden 1 (PRIMER FIRMANTE):     │
│  ┌─────────────────────────────┐│
│  │ ✍️ [Firma]                  ││  ← Al firmar
│  │ María López (Jefe RRHH)     ││
│  │ Fecha: 29/11/2025 14:20     ││
│  └─────────────────────────────┘│
├─────────────────────────────────┤
│  Orden 2 (SEGUNDO FIRMANTE):    │
│  ┌─────────────────────────────┐│
│  │ ✍️ [Firma]                  ││  ← Al firmar
│  │ Carlos Ruiz (Técnico)       ││
│  │ Fecha: 30/11/2025 09:15     ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
```

---

## ✅ Validaciones Implementadas

### **Frontend (formCrearContrato.html):**

```javascript
// Validación antes de enviar
if (firmaVacia) {
    Swal.fire({
        icon: 'error',
        title: 'Falta tu firma',
        text: 'Dibuja tu firma electrónica en el recuadro morado'
    });
    return;
}
```

### **Backend (run.py):**

```python
if not firma_creador_base64:
    return jsonify({
        'success': False, 
        'message': 'Todos los campos son obligatorios, incluyendo tu firma'
    }), 400
```

### **Controlador (control_contratos.py):**

```python
if not firma_creador_base64:
    return {
        'success': False, 
        'message': 'La firma del creador es obligatoria'
    }
```

---

## 🎨 Vista del Usuario

### **Al Crear el Contrato:**

```
┌────────────────────────────────────┐
│  📄 Crear Nuevo Contrato           │
├────────────────────────────────────┤
│                                    │
│  📌 Título: [_______________]      │
│  📝 Descripción: [___________]     │
│  📎 Archivo PDF: [Seleccionar]     │
│                                    │
│  🔐 Tu Sello Institucional         │
│  [Subir archivo PNG/JPG]           │
│                                    │
│  ✍️ Tu Firma Electrónica *         │
│  ┌──────────────────────────────┐  │
│  │  [Canvas para dibujar]       │  │
│  │                              │  │
│  └──────────────────────────────┘  │
│  [🗑️ Limpiar Firma]               │
│                                    │
│  👥 Firmantes:                     │
│  [Seleccionar usuarios...]         │
│                                    │
│  [✅ Crear Contrato]               │
└────────────────────────────────────┘
```

### **Mensaje de Éxito:**

```
┌────────────────────────────────────┐
│            ✅ ¡Éxito!              │
│                                    │
│      ¡Contrato Creado!             │
│                                    │
│  El contrato se creó con tu        │
│  firma inicial                     │
│                                    │
│  Asignado a 3 firmante(s)          │
│                                    │
│          [Continuar]               │
└────────────────────────────────────┘
```

---

## 🔍 Logs del Sistema

### **Al Crear Contrato:**

```
✍️ Creando contrato con firma del creador...
🔐 El creador también subió su sello institucional
📋 Creando contrato con 3 firmantes seleccionados...
✍️ Agregando firma del creador (Juan Pérez) al PDF inicial...
🔐 También agregando sello institucional del creador...
📤 Subiendo PDF con firma inicial a Catbox...
✅ Contrato creado exitosamente (ID: 15)
   ✍️ Incluye firma del creador: Juan Pérez
   🔐 Incluye sello institucional del creador
   👥 Firmantes asignados: 3
```

---

## 🆚 Comparación: ANTES vs AHORA

### **ANTES:**

| Paso | Acción | Estado PDF |
|------|--------|-----------|
| 1 | Creador sube PDF | PDF original sin firmas ❌ |
| 2 | Primer firmante firma | PDF con 1 firma ✅ |
| 3 | Segundo firmante firma | PDF con 2 firmas ✅ |

**Problema:** El creador no figuraba en el documento.

---

### **AHORA:**

| Paso | Acción | Estado PDF |
|------|--------|-----------|
| 0 | Creador crea contrato | PDF con firma del creador ✅ |
| 1 | Primer firmante firma | PDF con 2 firmas ✅ |
| 2 | Segundo firmante firma | PDF con 3 firmas ✅ |

**Solución:** El creador siempre figura como "Orden 0".

---

## 🧪 Cómo Probar

### **Test 1: Crear Contrato Sin Firma**

1. Ir a `/crear_contrato`
2. Llenar título y PDF
3. **NO** dibujar firma
4. Hacer clic en "Crear Contrato"

**Resultado esperado:**
```
⚠️ Falta tu firma
Dibuja tu firma electrónica en el recuadro morado
```

---

### **Test 2: Crear Contrato Con Firma (Sin Sello)**

1. Ir a `/crear_contrato`
2. Llenar título y PDF
3. ✅ Dibujar firma en el canvas
4. Seleccionar firmantes
5. Hacer clic en "Crear Contrato"

**Resultado esperado:**
- PDF se crea con firma del creador (sin sello)
- Orden 0 muestra solo la firma (más grande)
- Mensaje: "Contrato creado con tu firma inicial"

---

### **Test 3: Crear Contrato Con Firma Y Sello**

1. Ir a `/crear_contrato` (como Jefe)
2. Llenar título y PDF
3. ✅ Subir sello institucional
4. ✅ Dibujar firma en el canvas
5. Seleccionar firmantes
6. Hacer clic en "Crear Contrato"

**Resultado esperado:**
- PDF se crea con sello Y firma del creador
- Orden 0 muestra: `[Sello 55x55] [Firma 90x60]`
- Logs: "🔐 Incluye sello institucional del creador"

---

### **Test 4: Verificar PDF Descargado**

1. Crear contrato con firma y sello
2. Ir a `/ver_contrato/[id]`
3. Descargar PDF

**Resultado esperado:**
- Al abrir el PDF, la primera firma (Orden 0) debe mostrar:
  - Sello del creador a la izquierda (si subió)
  - Firma del creador al lado
  - Nombre completo del creador
  - Fecha y hora de creación

---

## 🚨 Errores Comunes y Soluciones

### **Error: "firmaVacia is not defined"**

**Causa:** Variable `firmaVacia` no está inicializada.

**Solución:** Verificar que el JS tenga:
```javascript
let firmaVacia = true;
```

---

### **Error: "Cannot read property 'toDataURL' of null"**

**Causa:** Canvas no está cargado correctamente.

**Solución:** Verificar que el `canvas` se inicialice en `DOMContentLoaded`:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    canvas = document.getElementById('canvasFirma');
    ctx = canvas.getContext('2d');
});
```

---

### **Error: "Error al agregar firma del creador al PDF"**

**Causa:** La firma en base64 está mal formateada o es inválida.

**Solución:** Verificar que se envíe correctamente:
```javascript
const firmaBase64 = canvas.toDataURL('image/png');
// Debe empezar con: "data:image/png;base64,..."
```

---

## 📚 Archivos Modificados

1. ✅ **app/templates/formCrearContrato.html**
   - Captura firma del canvas
   - Convierte sello a base64
   - Envía ambos al backend

2. ✅ **app/run.py**
   - Recibe `firma_creador` y `sello_creador`
   - Valida presencia de firma
   - Pasa parámetros al controlador

3. ✅ **app/controllers/control_contratos.py**
   - Agrega firma y sello al PDF inicial
   - Usa orden 0 para el creador
   - Actualiza mensajes de log

4. ✅ **FIRMA_CREADOR_CONTRATO.md** (NUEVO)
   - Documentación completa del cambio

---

## 🎉 Beneficios

1. ✅ **Trazabilidad:** El creador siempre figura en el documento
2. ✅ **Legalidad:** Mayor validez legal al incluir firma del creador
3. ✅ **Claridad:** Se distingue quién creó vs quién firmó
4. ✅ **Orden:** Sistema de orden jerárquico (0 = creador, 1+ = firmantes)
5. ✅ **Flexibilidad:** Sello opcional para no-jefes

---

## 🔮 Próximas Mejoras

- [ ] Permitir que el creador edite el contrato antes de enviarlo
- [ ] Agregar vista previa del PDF con la firma antes de crear
- [ ] Permitir múltiples sellos institucionales por usuario
- [ ] Historial de modificaciones del PDF

---

**Última actualización:** 28 de Noviembre de 2025  
**Autor:** Sistema de Gestión de Contratos  
**Versión:** 2.1.0

