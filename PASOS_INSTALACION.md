# 📝 Guía de Instalación Paso a Paso

## ✅ CHECKLIST DE INSTALACIÓN

- [ ] **Paso 1:** Instalar Python 3.11
- [ ] **Paso 2:** Verificar Python 3.11
- [ ] **Paso 3:** Ejecutar script de instalación automática
- [ ] **Paso 4:** Descargar wheel de dlib
- [ ] **Paso 5:** Instalar dlib y face_recognition
- [ ] **Paso 6:** Verificar instalación
- [ ] **Paso 7:** Ejecutar script SQL en base de datos
- [ ] **Paso 8:** Probar el sistema

---

## 📥 PASO 1: Instalar Python 3.11

### Opción A: Descarga Directa (Recomendado)
1. **Copia y pega este link en tu navegador:**
   ```
   https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
   ```

2. **Ejecuta el instalador**

3. **⚠️ IMPORTANTE:** En la primera pantalla:
   ```
   ┌─────────────────────────────────────────────┐
   │  Install Python 3.11.9 (64-bit)             │
   │                                             │
   │  [Install Now]                              │
   │                                             │
   │  ☑ Install launcher for all users          │
   │  ☑ Add python.exe to PATH   ← ¡IMPORTANTE! │
   └─────────────────────────────────────────────┘
   ```
   **Marca la casilla "Add python.exe to PATH"**

4. **Click en "Install Now"**

5. **Espera** (2-3 minutos)

6. **Click en "Close"** cuando termine

### Opción B: Desde Python.org
1. Ve a: https://www.python.org/downloads/
2. Busca "Python 3.11.9"
3. Descarga "Windows installer (64-bit)"
4. Sigue los pasos de arriba

---

## ✔️ PASO 2: Verificar Python 3.11

1. **Cierra todas las terminales PowerShell abiertas**

2. **Abre una NUEVA terminal PowerShell**

3. **Ejecuta:**
   ```powershell
   py -3.11 --version
   ```

4. **Deberías ver:**
   ```
   Python 3.11.9
   ```

✅ Si ves esto, continúa al Paso 3
❌ Si ves error, reinicia tu PC y vuelve a intentar

---

## 🚀 PASO 3: Ejecutar Script de Instalación Automática

1. **Ve a tu carpeta del proyecto:**
   ```powershell
   cd "C:\Users\cance\OneDrive\Desktop\WILLIAMS GC\USAT\CICLO VIII\GOBIERNO\UNIDAD III\ENSA-CURSOR\pryGobierno"
   ```

2. **Ejecuta el script de instalación:**
   ```powershell
   .\instalar_biometria.ps1
   ```

   **Si sale error de permisos:**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   .\instalar_biometria.ps1
   ```

3. **El script hará automáticamente:**
   - ✓ Verificar Python 3.11
   - ✓ Respaldar tu entorno virtual anterior
   - ✓ Crear nuevo entorno con Python 3.11
   - ✓ Instalar dependencias básicas (Flask, numpy, opencv, etc.)

4. **Tiempo estimado:** 2-3 minutos

---

## 📦 PASO 4: Descargar Wheel de dlib

1. **Abre este link en tu navegador:**
   ```
   https://github.com/z-mahmud22/Dlib_Windows_Python3.x
   ```

2. **Busca en la página el archivo:**
   ```
   dlib-19.24.1-cp311-cp311-win_amd64.whl
   ```

3. **Haz click en el archivo para descargarlo**

4. **Se descargará a tu carpeta de Descargas:**
   ```
   C:\Users\cance\Downloads\dlib-19.24.1-cp311-cp311-win_amd64.whl
   ```

---

## 🔧 PASO 5: Instalar dlib y face_recognition

1. **Asegúrate de estar en la carpeta del proyecto:**
   ```powershell
   cd "C:\Users\cance\OneDrive\Desktop\WILLIAMS GC\USAT\CICLO VIII\GOBIERNO\UNIDAD III\ENSA-CURSOR\pryGobierno"
   ```

2. **Activa el entorno virtual:**
   ```powershell
   .\.venv\Scripts\activate
   ```

3. **Instala dlib desde el wheel descargado:**
   ```powershell
   pip install "C:\Users\cance\Downloads\dlib-19.24.1-cp311-cp311-win_amd64.whl"
   ```

4. **Instala face_recognition:**
   ```powershell
   pip install face_recognition
   ```

5. **Tiempo estimado:** 1-2 minutos

---

## ✅ PASO 6: Verificar Instalación

**Ejecuta este comando:**
```powershell
python -c "import dlib; import face_recognition; print('✅ Biometría instalada correctamente')"
```

**Si ves:**
```
✅ Biometría instalada correctamente
```

**¡Éxito! Continúa al Paso 7**

---

## 🗄️ PASO 7: Ejecutar Script SQL

1. **Abre pgAdmin o tu cliente de PostgreSQL**

2. **Conéctate a tu base de datos `Gobierno2`**

3. **Abre el archivo:**
   ```
   scripts_sql/agregar_biometria.sql
   ```

4. **Ejecuta el script completo**

5. **Deberías ver:**
   ```
   ALTER TABLE
   Query returned successfully
   ```

---

## 🧪 PASO 8: Probar el Sistema

1. **Ejecuta tu aplicación:**
   ```powershell
   cd app
   python run.py
   ```

2. **Abre tu navegador:**
   ```
   http://localhost:5000/login
   ```

3. **Deberías ver:**
   - ✓ Login con selector "🔐 Biométrico" / "🔑 Tradicional"
   - ✓ Sección de cámara web
   - ✓ Botón "Activar Cámara"

4. **Para registrar tu rostro:**
   ```
   http://localhost:5000/enrolamiento_facial
   ```

---

## 🎉 ¡Listo!

Tu sistema de biometría facial está completamente instalado y funcionando.

---

## 🆘 Solución de Problemas

### Error: "No module named 'dlib'"
```powershell
# Verifica que instalaste en el entorno correcto
.\.venv\Scripts\activate
pip list | findstr dlib
```

### Error: "is not a supported wheel"
- Verifica que descargaste el archivo correcto para Python 3.11
- El nombre debe ser: `dlib-19.24.1-cp311-cp311-win_amd64.whl`

### Error en el script PowerShell
```powershell
# Cambia la política de ejecución
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### La cámara no funciona
- Verifica permisos de cámara en Windows
- Cierra otras aplicaciones que usen la cámara (Zoom, Teams, etc.)

---

## 📞 Contacto

Si tienes problemas, revisa los archivos:
- `SOLUCION_DLIB_WINDOWS.md`
- `INSTRUCCIONES_PYTHON_311.md`
- `INSTALACION_BIOMETRIA.md`

