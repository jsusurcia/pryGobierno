# 🐍 Solución: Usar Python 3.11 para Biometría

## Problema
Python 3.13 es muy nuevo y `dlib` no tiene wheels precompilados disponibles.

---

## ✅ Solución: Instalar Python 3.11 y crear nuevo entorno virtual

### Paso 1: Descargar Python 3.11

1. Ve a: https://www.python.org/downloads/
2. Busca **Python 3.11.X** (última versión de la serie 3.11)
3. Descarga el instalador: **Windows installer (64-bit)**

### Paso 2: Instalar Python 3.11

Durante la instalación:
- ✅ **Marcar "Add Python 3.11 to PATH"**
- ✅ Marcar "Install for all users" (opcional)
- Click "Install Now"

### Paso 3: Verificar instalación

Abre una **nueva terminal PowerShell** y ejecuta:

```powershell
py -3.11 --version
```

Deberías ver: `Python 3.11.X`

---

## 📦 Crear Nuevo Entorno Virtual con Python 3.11

### En tu carpeta del proyecto:

```powershell
# Ir a la carpeta del proyecto
cd "C:\Users\cance\OneDrive\Desktop\WILLIAMS GC\USAT\CICLO VIII\GOBIERNO\UNIDAD III\ENSA-CURSOR\pryGobierno"

# Renombrar el entorno virtual anterior (backup)
Rename-Item .venv .venv_old

# Crear nuevo entorno con Python 3.11
py -3.11 -m venv .venv

# Activar el nuevo entorno
.\.venv\Scripts\activate

# Verificar que estés usando Python 3.11
python --version
```

---

## 🔧 Instalar Dependencias

### 1. Instalar dependencias básicas

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

**Nota:** Esto instalará todo excepto `dlib` y `face_recognition` (que fallarán).

### 2. Descargar wheel de dlib para Python 3.11

Ve a: https://github.com/z-mahmud22/Dlib_Windows_Python3.x

Descarga: **`dlib-19.24.1-cp311-cp311-win_amd64.whl`**

### 3. Instalar dlib desde el wheel

```powershell
# Asegúrate de estar en el entorno virtual activado
pip install "C:\Users\cance\Downloads\dlib-19.24.1-cp311-cp311-win_amd64.whl"
```

### 4. Instalar face_recognition

```powershell
pip install face_recognition
```

---

## ✔️ Verificar Instalación

```powershell
python -c "import dlib; import face_recognition; print('✅ Biometría lista')"
```

Si ves `✅ Biometría lista`, ¡todo funcionó!

---

## 🗑️ Limpiar (Opcional)

Una vez que todo funcione, puedes eliminar el entorno anterior:

```powershell
Remove-Item -Recurse -Force .venv_old
```

---

## 📋 Comandos Rápidos (Resumen)

```powershell
# 1. Verificar Python 3.11 instalado
py -3.11 --version

# 2. Crear entorno virtual con Python 3.11
py -3.11 -m venv .venv

# 3. Activar entorno
.\.venv\Scripts\activate

# 4. Instalar dependencias básicas
pip install Flask psycopg2 numpy opencv-python Pillow cloudinary

# 5. Instalar dlib desde wheel (descargado previamente)
pip install dlib-19.24.1-cp311-cp311-win_amd64.whl

# 6. Instalar face_recognition
pip install face_recognition

# 7. Verificar
python -c "import face_recognition; print('OK')"
```

---

## 🔄 Alternativa: Mantener Python 3.13 e instalar CMake

Si prefieres mantener Python 3.13, necesitarás:

1. **Instalar CMake**: https://cmake.org/download/
   - Marcar "Add CMake to PATH"
   
2. **Instalar Visual Studio Build Tools**: 
   - https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Seleccionar "Desarrollo de escritorio con C++"
   - Tamaño: ~6 GB
   - Tiempo: ~30-45 minutos

3. **Compilar dlib**:
   ```powershell
   pip install dlib
   pip install face_recognition
   ```

**Esta opción es más lenta y puede tener otros problemas de compatibilidad.**

---

**Recomendación:** Usa Python 3.11 para este proyecto. Es estable y tiene todos los wheels disponibles. ✅

