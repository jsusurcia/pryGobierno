# 🔐 Guía de Instalación - Sistema de Biometría Facial

## Requisitos Previos

### 1. Python 3.9 - 3.11 (Recomendado: 3.11)
La librería `dlib` funciona mejor con estas versiones.

### 2. Visual Studio Build Tools (Windows)
Es necesario para compilar `dlib`.

1. Descarga: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Ejecuta el instalador
3. Selecciona **"Desarrollo de escritorio con C++"**
4. Instala y reinicia tu PC

### 3. CMake
1. Descarga: https://cmake.org/download/
2. Durante la instalación, **marca "Add CMake to PATH"**

---

## Instalación de Dependencias

### Opción A: Instalación Normal (puede tardar ~10-15 min)

```bash
# Activar entorno virtual (si tienes uno)
# .\venv\Scripts\activate

# Instalar dependencias básicas
pip install numpy opencv-python Pillow

# Instalar dlib (puede tardar varios minutos)
pip install dlib

# Instalar face_recognition
pip install face_recognition
```

### Opción B: Usar Wheel Precompilado (Más Rápido) ⭐ RECOMENDADO

Si tienes problemas compilando dlib:

1. Ve a: https://github.com/z-mahmud22/Dlib_Windows_Python3.x
2. Descarga el archivo `.whl` correspondiente a tu versión de Python:
   - Python 3.11: `dlib-19.24.1-cp311-cp311-win_amd64.whl`
   - Python 3.10: `dlib-19.24.1-cp310-cp310-win_amd64.whl`

3. Instala:
```bash
pip install ruta/al/archivo/dlib-19.24.1-cp311-cp311-win_amd64.whl
pip install face_recognition
```

---

## Configuración de Base de Datos

Ejecuta el script SQL en tu base de datos PostgreSQL:

```sql
-- Conectar a tu base de datos Gobierno2
-- Ejecutar el contenido de: scripts_sql/agregar_biometria.sql

ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS encoding_facial BYTEA;
ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS tiene_biometria BOOLEAN DEFAULT FALSE;
ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS fecha_registro_facial TIMESTAMP;
```

---

## Uso del Sistema

### 1. Registrar Rostro (Primera vez)

1. Accede a: `http://localhost:5000/enrolamiento_facial`
2. Ingresa tu correo y contraseña
3. Activa la cámara
4. Posiciona tu rostro en el óvalo
5. Haz clic en "Capturar y Registrar"

### 2. Iniciar Sesión con Biometría

1. Accede a: `http://localhost:5000/login`
2. Ingresa tu correo y contraseña
3. Activa la cámara
4. Captura tu rostro
5. Haz clic en "Iniciar Sesión con Biometría"

### 3. Login Tradicional (Sin Biometría)

Si prefieres no usar biometría:
1. En el login, haz clic en **"🔑 Tradicional"**
2. Ingresa solo correo y contraseña

---

## Solución de Problemas

### Error: "No module named 'dlib'"
- Asegúrate de tener Visual Studio Build Tools instalado
- Intenta con la Opción B (wheel precompilado)

### Error: "No se pudo acceder a la cámara"
- Verifica que la cámara no esté siendo usada por otra aplicación
- Asegúrate de dar permisos de cámara al navegador

### Error: "No se detectó ningún rostro"
- Mejora la iluminación
- Asegúrate de que tu rostro esté dentro del óvalo
- Evita usar gafas de sol o cubrebocas

### La verificación facial falla
- El umbral de tolerancia está en 0.5 (50%)
- Si hay muchos falsos rechazos, puedes aumentarlo a 0.6 en `control_biometria.py`

---

## Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                        FLUJO DE LOGIN                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Usuario                                                        │
│      │                                                           │
│      ▼                                                           │
│   ┌──────────────────┐                                           │
│   │ Ingresa correo   │                                           │
│   │ y contraseña     │                                           │
│   └────────┬─────────┘                                           │
│            │                                                     │
│            ▼                                                     │
│   ┌──────────────────┐     ┌──────────────────┐                  │
│   │ Captura rostro   │────▶│ Envía imagen     │                  │
│   │ con cámara web   │     │ base64 al server │                  │
│   └──────────────────┘     └────────┬─────────┘                  │
│                                     │                            │
│                                     ▼                            │
│                           ┌──────────────────┐                   │
│                           │ face_recognition │                   │
│                           │ genera encoding  │                   │
│                           │ (128 dimensiones)│                   │
│                           └────────┬─────────┘                   │
│                                    │                             │
│                                    ▼                             │
│                           ┌──────────────────┐                   │
│                           │ Compara con      │                   │
│                           │ encoding en BD   │                   │
│                           └────────┬─────────┘                   │
│                                    │                             │
│                    ┌───────────────┴───────────────┐             │
│                    │                               │             │
│                    ▼                               ▼             │
│           ┌──────────────┐               ┌──────────────┐        │
│           │ Coincide ✓   │               │ No coincide ✗│        │
│           │ (≤ 0.5 dist) │               │ (> 0.5 dist) │        │
│           └──────┬───────┘               └──────┬───────┘        │
│                  │                              │                │
│                  ▼                              ▼                │
│           ┌──────────────┐               ┌──────────────┐        │
│           │ Login exitoso│               │ Acceso       │        │
│           │              │               │ denegado     │        │
│           └──────────────┘               └──────────────┘        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Archivos Creados/Modificados

| Archivo | Descripción |
|---------|-------------|
| `scripts_sql/agregar_biometria.sql` | Script SQL para agregar columnas |
| `app/controllers/control_biometria.py` | Controlador de biometría facial |
| `app/templates/login.html` | Login con opción biométrica |
| `app/templates/enrolamiento_facial.html` | Página de registro de rostro |
| `app/run.py` | Rutas de biometría agregadas |
| `requirements.txt` | Dependencias actualizadas |

---

## Seguridad

- Los encodings faciales se almacenan como datos binarios (BYTEA)
- Las imágenes capturadas **NO** se guardan, solo se procesan
- El encoding es un vector matemático, no es reversible a imagen
- Se usa tolerancia de 0.5 (recomendado por face_recognition)

---

¿Preguntas? Revisa la documentación de:
- face_recognition: https://github.com/ageitgey/face_recognition
- dlib: http://dlib.net/

