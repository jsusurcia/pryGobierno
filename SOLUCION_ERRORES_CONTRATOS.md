# 🔧 Solución de Errores - Sistema de Contratos

## 📋 Problemas Solucionados

### 1. **Error de Conexión con Catbox**
❌ **Problema:** `Connection aborted - Remote end closed connection`
✅ **Solución:**
- Aumentado timeout a 60 segundos
- Agregados 3 reintentos automáticos con backoff exponencial
- Agregados headers para evitar bloqueos
- Descarga en streaming por chunks

### 2. **Falta Campo para Sello en BD**
❌ **Problema:** No hay campo para guardar URL del sello institucional
✅ **Solución:**
- Creado script SQL para agregar campo `url_sello`
- Creado servicio completo para gestionar sellos
- Integración con Cloudinary (más estable que Catbox)

---

## 🚀 INSTRUCCIONES DE INSTALACIÓN

### **Paso 1: Ejecutar Script SQL**

Abre tu cliente PostgreSQL (pgAdmin, DBeaver, etc.) y ejecuta:

```sql
-- Agregar columna para URL del sello institucional
ALTER TABLE USUARIO 
ADD COLUMN url_sello TEXT;

-- Verificar que se agregó correctamente
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'usuario' AND column_name = 'url_sello';
```

O ejecuta el archivo completo:
```bash
psql -U tu_usuario -d tu_base_de_datos -f scripts_sql/AGREGAR_CAMPO_SELLO.sql
```

### **Paso 2: Reiniciar el Servidor**

```bash
# Detener el servidor (Ctrl+C)
# Reiniciar
python app/run.py
```

---

## 📝 CÓMO USAR EL SISTEMA

### **Para Jefe de TI (Crear Contrato):**

1. **Subir tu Sello (Solo primera vez):**
   - Ir a "Contratos" → "Nuevo Contrato"
   - Subir imagen de tu sello institucional (PNG/JPG)
   - Clic en "📤 Subir Sello"
   - El sello se guardará en Cloudinary

2. **Crear Contrato:**
   - El sello ya aparecerá automáticamente
   - Llenar título y descripción
   - **IMPORTANTE:** Subir el PDF del contrato
   - El PDF puede ser simple, las firmas se añadirán digitalmente después
   - Clic en "Crear Contrato"
   - Los firmantes se asignan automáticamente (roles 8, 10, 11, 9, 12)

3. **Resultado:**
   - El PDF se sube a Catbox (con reintentos automáticos)
   - Primer firmante recibe notificación

### **Para Firmantes (Roles 8, 10, 11, 9, 12):**

1. **Ver Contratos Pendientes:**
   - Ir a "Mis Contratos" en el menú lateral
   - Ver lista de contratos pendientes de firma

2. **Firmar Contrato:**
   - Esperar notificación: "Es tu turno para firmar"
   - Clic en "Firmar Ahora" 🟢
   - Ver el PDF actual
   - Dibujar firma en el canvas
   - Clic en "Firmar Contrato"

3. **Resultado:**
   - Tu firma se añade visualmente al PDF
   - PDF actualizado se sube nuevamente
   - Siguiente firmante recibe notificación

---

## 🔧 ARCHIVOS MODIFICADOS/CREADOS

### **Nuevos Archivos:**
```
✅ scripts_sql/AGREGAR_CAMPO_SELLO.sql
✅ app/services/sello_service.py
✅ SOLUCION_ERRORES_CONTRATOS.md
```

### **Archivos Actualizados:**
```
✅ app/services/catbox_service.py
   - Mejorado método descargar_pdf() con reintentos
   
✅ app/run.py
   - Import de SelloService
   - 2 rutas nuevas: /api/sello/subir, /api/sello/obtener
   
✅ app/templates/formCrearContrato.html
   - Sección para subir sello
   - JavaScript para gestionar sello
```

---

## 🧪 PROBAR EL SISTEMA

### **Test 1: Subir Sello**
```
1. Iniciar sesión como Jefe de TI
2. Ir a "Contratos" → "Nuevo Contrato"
3. Subir imagen de sello (PNG/JPG, máx 5MB)
4. Verificar que aparece: "✅ Ya tienes un sello registrado"
```

### **Test 2: Crear Contrato con Reintentos**
```
1. Crear un contrato nuevo
2. Observar consola del servidor
3. Debe mostrar:
   - "📤 Subiendo PDF con sello a Catbox..."
   - "📥 Descargando PDF desde..." (cuando alguien firme)
   - "✅ PDF descargado exitosamente"
```

### **Test 3: Firmar Contrato**
```
1. Iniciar sesión como usuario firmante (rol 8, 10, 11, 9, 12)
2. Ir a "Mis Contratos"
3. Ver contrato con estado "🟢 Es tu turno"
4. Firmar y verificar que funciona
```

---

## 🐛 TROUBLESHOOTING

### **Error: "No se pudo descargar el PDF"**
**Causa:** Catbox sigue fallando después de 3 reintentos
**Solución:** 
- Verificar conexión a internet
- Esperar unos minutos (Catbox puede estar temporalmente caído)
- Considerar usar Cloudinary para PDFs también (ver abajo)

### **Error: "column url_sello does not exist"**
**Causa:** No se ejecutó el script SQL
**Solución:**
```sql
ALTER TABLE USUARIO ADD COLUMN url_sello TEXT;
```

### **Sello no aparece después de subirlo**
**Causa:** Error en Cloudinary
**Solución:**
- Verificar credenciales de Cloudinary en `run.py`
- Ver logs del servidor para más detalles

---

## 💡 MEJORAS OPCIONALES

### **Usar Cloudinary en lugar de Catbox para PDFs**

Si Catbox sigue dando problemas, puedes cambiar a Cloudinary:

1. **Modificar `control_contratos.py`:**
```python
# En lugar de:
url_catbox = CatboxService.subir_pdf(pdf_temporal)

# Usar:
resultado = cloudinary.uploader.upload(
    pdf_temporal,
    resource_type="raw",  # Para archivos no-imagen
    folder="contratos_pdfs"
)
url_pdf = resultado.get('secure_url')
```

2. **Ventajas de Cloudinary:**
- Más estable
- Mejor velocidad
- Ya está configurado en tu proyecto
- Transformaciones automáticas

---

## 📊 ORDEN DE FIRMANTES

Los firmantes se asignan automáticamente en este orden:

```
1️⃣ Rol 8  → Primera firma electrónica
2️⃣ Rol 10 → Segunda firma electrónica
3️⃣ Rol 11 → Tercera firma electrónica
4️⃣ Rol 9  → Cuarta firma electrónica
5️⃣ Rol 12 → Quinta firma electrónica (final)
```

Solo usuarios **activos** (`estado = TRUE`) son incluidos.

---

## 📞 SOPORTE

Si continúan los problemas:

1. **Ver logs del servidor:** Los mensajes 📥 📤 ✅ ❌ ayudan a identificar dónde falla
2. **Verificar BD:** Confirmar que el campo `url_sello` existe
3. **Probar Cloudinary:** Como alternativa más estable que Catbox

---

**Última actualización:** Noviembre 2025  
**Estado:** Sistema funcionando con reintentos automáticos y gestión de sellos

