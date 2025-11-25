# 🔧 Solución: Error de Instalación de dlib en Windows

## ❌ Error Recibido:
```
CMake is not installed on your system!
ERROR: Failed building wheel for dlib
```

---

## ✅ Solución Rápida (Recomendada)

### Paso 1: Verificar tu versión de Python

```powershell
python --version
```

Ejemplo de salida: `Python 3.11.X` o `Python 3.10.X`

---

### Paso 2: Descargar el Wheel Precompilado

Ve a uno de estos repositorios según tu versión de Python:

#### Opción A: Repository de z-mahmud22 (Actualizado)
🔗 https://github.com/z-mahmud22/Dlib_Windows_Python3.x

**Archivos disponibles:**
- Python 3.11 (64-bit): `dlib-19.24.1-cp311-cp311-win_amd64.whl`
- Python 3.10 (64-bit): `dlib-19.24.1-cp310-cp310-win_amd64.whl`
- Python 3.9 (64-bit): `dlib-19.24.1-cp39-cp39-win_amd64.whl`

#### Opción B: Christoph Gohlke's Unofficial Binaries
🔗 https://github.com/cgohlke/dlib-build/releases

---

### Paso 3: Instalar el Wheel Descargado

Después de descargar el archivo `.whl`, navega a la carpeta de descargas y ejecuta:

```powershell
# Ejemplo para Python 3.11
pip install dlib-19.24.1-cp311-cp311-win_amd64.whl

# O especifica la ruta completa
pip install "C:\Users\cance\Downloads\dlib-19.24.1-cp311-cp311-win_amd64.whl"
```

---

### Paso 4: Instalar face_recognition

Ahora sí, instala face_recognition:

```powershell
pip install face_recognition
```

---

### Paso 5: Verificar la instalación

```powershell
python -c "import dlib; import face_recognition; print('✅ Todo instalado correctamente')"
```

---

## 🔄 Alternativa: Instalar CMake (Método Largo)

Si prefieres compilar desde el código fuente:

### 1. Instalar CMake
- Descarga: https://cmake.org/download/
- Versión: **cmake-3.XX.X-windows-x86_64.msi** (Installer)
- Durante la instalación: ✅ **Marcar "Add CMake to system PATH"**

### 2. Instalar Visual Studio Build Tools
- Descarga: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Seleccionar: **"Desarrollo de escritorio con C++"**
- Tamaño de descarga: ~6-7 GB
- Tiempo de instalación: ~30-45 minutos

### 3. Reiniciar PowerShell

```powershell
# Verificar que CMake esté disponible
cmake --version
```

### 4. Instalar dlib

```powershell
pip install dlib
pip install face_recognition
```

---

## 📋 Resumen de Comandos Rápidos

```powershell
# 1. Verificar Python
python --version

# 2. Descargar wheel desde GitHub
# https://github.com/z-mahmud22/Dlib_Windows_Python3.x

# 3. Instalar dlib desde wheel
pip install dlib-19.24.1-cp311-cp311-win_amd64.whl

# 4. Instalar face_recognition
pip install face_recognition

# 5. Verificar
python -c "import dlib; import face_recognition; print('OK')"
```

---

## 🐛 Solución de Problemas

### Error: "dlib-19.24.1-cp311-cp311-win_amd64.whl is not a supported wheel"

**Causa:** Tu versión de Python no coincide con el wheel.

**Solución:** 
```powershell
# Ver tu versión exacta de Python
python --version

# Instalar la versión correcta de Python si es necesario
```

### Error: "No module named 'dlib'" después de instalar

**Solución:**
```powershell
# Asegúrate de estar en el entorno virtual correcto
.\.venv\Scripts\activate

# Reinstala en el entorno virtual
pip install ruta\al\archivo\dlib-19.24.1-cp311-cp311-win_amd64.whl
```

---

## 📚 Recursos Adicionales

- **face_recognition docs:** https://github.com/ageitgey/face_recognition
- **dlib docs:** http://dlib.net/
- **Tutorial instalación Windows:** https://medium.com/@ageitgey/build-a-face-recognition-system-on-windows-in-5-minutes-c1b42fc4c26d

---

**¿Listo?** Una vez instalado, continúa con el paso 1 del archivo `INSTALACION_BIOMETRIA.md` (ejecutar el script SQL).

