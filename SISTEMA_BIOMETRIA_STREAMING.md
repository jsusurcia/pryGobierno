# 🎥 Sistema de Biometría con Video Streaming

## 📋 Descripción

Sistema de reconocimiento facial en tiempo real usando **face_recognition** (dlib) con verificación por video streaming. El sistema requiere **múltiples frames coincidentes consecutivos** para autorizar el login, lo que lo hace más robusto y seguro.

---

## 🚀 Características Principales

### 1. **Enrolamiento Facial**
- Captura una foto del usuario
- Detecta el rostro usando `face_recognition.face_locations()`
- Codifica el rostro a un vector de 128 dimensiones con `face_recognition.face_encodings()`
- Almacena el encoding en la base de datos (columna `encoding_facial`)

### 2. **Login con Video Streaming**
- **Video en tiempo real** de la cámara del usuario
- Verificación **frame por frame** (procesa cada cuadro del video)
- Cuenta los **matches consecutivos** entre el rostro detectado y el registrado
- Requiere **50 frames coincidentes** para autorizar el login (configurable)
- Muestra progreso visual en tiempo real

### 3. **Seguridad Mejorada**
- **Umbral de distancia**: 0.5 (más estricto que el 0.6 recomendado por defecto)
- **Múltiples verificaciones**: No basta con una sola foto, requiere video continuo
- **Detección de rostro en vivo**: Más difícil de engañar con fotos estáticas
- **Reinicio de contador**: Si un frame no coincide, el contador se reinicia a cero

---

## 🔧 Configuración

### Parámetros Ajustables

En `app/controllers/control_biometria_face_recognition.py`:

```python
class ControlBiometriaFR:
    # Umbral de distancia (0.0 = idéntico, 1.0 = muy diferente)
    # Valores típicos: 0.5 (estricto), 0.6 (recomendado), 0.7 (permisivo)
    UMBRAL_DISTANCIA = 0.5
    
    # Número de frames consecutivos requeridos para login exitoso
    # Valores recomendados: 30-100 frames
    # A 30 FPS: 50 frames = ~1.7 segundos
    FRAMES_REQUERIDOS = 50
```

---

## 📝 Flujo de Uso

### **Registro de Rostro (Primera vez)**

1. Ir a `/enrolamiento_facial`
2. Ingresar correo y contraseña
3. Hacer clic en "Verificar Identidad"
4. Capturar foto con la cámara
5. El sistema detecta y codifica el rostro
6. Se guarda el encoding en la BD

### **Login con Reconocimiento Facial**

1. Ir a `/login_streaming`
2. Ingresar correo y contraseña
3. Hacer clic en "Iniciar Verificación Facial"
4. La cámara se activa automáticamente
5. Posicionar el rostro frente a la cámara
6. **El sistema verifica frame por frame:**
   - 🟢 **Verde**: Rostro coincide (+1 al contador)
   - 🔴 **Rojo**: Rostro no coincide (contador se reinicia a 0)
7. Cuando alcanza 50 matches → **¡Login exitoso!** ✅
8. Redirección automática al dashboard

---

## 🎨 Interfaz de Usuario

### Indicadores Visuales

#### **Barra de Progreso**
```
Progreso: [███████░░░░░░░] 50%
Matches: 25/50
```

#### **Estado del Rostro**
- 🟢 **"✓ Rostro Coincidente"** (verde): El rostro actual coincide
- 🔴 **"✗ No coincide"** (rojo): El rostro no coincide
- ⚪ **"Buscando rostro..."** (gris): No se detectó rostro en el frame

#### **Rectángulo de Detección**
- **Verde**: Rostro detectado y coincidente
- **Rojo**: Rostro detectado pero no coincide

#### **Estadísticas en Tiempo Real**
- Frames procesados: Contador total de frames analizados
- Distancia: Valor numérico de similitud (menor = más similar)

---

## 🔌 API Endpoints

### 1. `POST /api/biometria/iniciar-verificacion-streaming`

Inicia una sesión de verificación por video streaming.

**Request:**
```json
{
  "correo": "usuario@ejemplo.com",
  "contrasena": "mipassword"
}
```

**Response exitoso:**
```json
{
  "exito": true,
  "mensaje": "Verificación iniciada",
  "frames_requeridos": 50,
  "usuario": {
    "id_usuario": 1,
    "nombre": "Juan",
    "ape_pat": "Pérez",
    "ape_mat": "García",
    "correo": "usuario@ejemplo.com",
    "id_rol": 2
  }
}
```

### 2. `POST /api/biometria/verificar-frame`

Verifica un frame individual del video.

**Request:**
```json
{
  "imagen_facial": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response durante verificación:**
```json
{
  "exito": true,
  "login_exitoso": false,
  "coincide": true,
  "match_count": 25,
  "total_frames": 30,
  "frames_requeridos": 50,
  "progreso": 50,
  "mensaje": "Match",
  "distancia": 0.3542,
  "face_location": [100, 400, 300, 200]
}
```

**Response login exitoso:**
```json
{
  "exito": true,
  "login_exitoso": true,
  "coincide": true,
  "match_count": 50,
  "total_frames": 55,
  "frames_requeridos": 50,
  "progreso": 100,
  "mensaje": "¡Login exitoso! 50 frames coincidentes",
  "distancia": 0.3201,
  "face_location": [100, 400, 300, 200]
}
```

### 3. `POST /api/biometria/cancelar-verificacion`

Cancela la verificación en curso y limpia la sesión.

**Response:**
```json
{
  "exito": true,
  "mensaje": "Verificación cancelada"
}
```

### 4. `POST /api/biometria/registrar-rostro`

Registra el rostro de un usuario (enrolamiento).

**Request:**
```json
{
  "id_usuario": 1,
  "imagen_facial": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response:**
```json
{
  "exito": true,
  "mensaje": "Rostro registrado exitosamente",
  "face_location": [100, 400, 300, 200]
}
```

---

## 🗄️ Estructura de Base de Datos

El sistema usa las siguientes columnas en la tabla `USUARIO`:

```sql
ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS encoding_facial BYTEA;
ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS tiene_biometria BOOLEAN DEFAULT FALSE;
ALTER TABLE USUARIO ADD COLUMN IF NOT EXISTS fecha_registro_facial TIMESTAMP;
```

- **`encoding_facial`**: Vector de 128 dimensiones serializado (pickle) que representa el rostro
- **`tiene_biometria`**: Flag booleano indicando si el usuario tiene rostro registrado
- **`fecha_registro_facial`**: Timestamp del registro

---

## 🛠️ Archivos del Sistema

### Backend
| Archivo | Descripción |
|---------|-------------|
| `controllers/control_biometria_face_recognition.py` | Controlador principal con face_recognition |
| `controllers/control_biometria.py` | Controlador anterior (OpenCV/histogramas) - mantenido como backup |

### Frontend
| Archivo | Descripción |
|---------|-------------|
| `templates/login_streaming.html` | Login con video streaming en tiempo real |
| `templates/enrolamiento_facial.html` | Página de registro de rostro |
| `templates/login.html` | Login tradicional (sin streaming) |

### Rutas en `run.py`
```python
@app.route('/login_streaming')  # Login con video streaming
@app.route('/enrolamiento_facial')  # Registro de rostro
@app.route('/api/biometria/iniciar-verificacion-streaming', methods=['POST'])
@app.route('/api/biometria/verificar-frame', methods=['POST'])
@app.route('/api/biometria/cancelar-verificacion', methods=['POST'])
@app.route('/api/biometria/registrar-rostro', methods=['POST'])
```

---

## 🎯 Ventajas del Sistema

### Comparación: Sistema Anterior vs Actual

| Característica | Sistema Anterior (OpenCV) | Sistema Actual (face_recognition) |
|----------------|---------------------------|-----------------------------------|
| **Algoritmo** | Haar Cascade + Histogramas | HOG/CNN + Red Neuronal (dlib) |
| **Precisión** | ~70-80% | ~99.38% |
| **Encoding** | Histogramas 3D (HSV) | Vector 128-d (embeddings) |
| **Verificación** | Foto única | Video streaming (50+ frames) |
| **Umbral** | Similitud 65% | Distancia 0.5 |
| **Seguridad** | Media | Alta |
| **Velocidad** | Rápido | Moderado (pero más preciso) |

---

## 🐛 Solución de Problemas

### Error: "No se detectó ningún rostro"
**Causas:**
- Iluminación insuficiente
- Rostro muy pequeño en la imagen
- Ángulo extremo del rostro
- Gafas de sol o cubrebocas

**Solución:**
- Mejorar la iluminación
- Acercar el rostro a la cámara
- Mirar directamente a la cámara
- Remover gafas oscuras y cubrebocas

### Error: "El rostro no coincide"
**Causas:**
- Cambios significativos en apariencia (barba, gafas, etc.)
- Encoding desactualizado
- Umbral muy estricto

**Solución:**
- Re-enrolar el rostro si hubo cambios físicos
- Ajustar `UMBRAL_DISTANCIA` a 0.6 (menos estricto)
- Verificar que la iluminación sea similar al enrolamiento

### Error: "No se pudo acceder a la cámara"
**Causas:**
- Permisos de cámara denegados en el navegador
- Cámara en uso por otra aplicación
- Conexión HTTPS requerida (en producción)

**Solución:**
- Permitir acceso a la cámara en el navegador
- Cerrar otras aplicaciones que usen la cámara
- Usar HTTPS en producción (HTTP solo funciona en localhost)

### Contador se reinicia constantemente
**Causas:**
- Rostro no está centrado
- Movimiento excesivo
- Iluminación inconsistente

**Solución:**
- Mantener el rostro centrado y quieto
- Estabilizar la cámara
- Mantener iluminación constante

---

## ⚡ Optimización de Rendimiento

### Ajustes Recomendados

#### Para Mayor Velocidad (sacrificando un poco de precisión):
```python
# En el frontend (login_streaming.html)
const stream = await navigator.mediaDevices.getUserMedia({ 
    video: { 
        width: { ideal: 320 },  # Reducir resolución
        height: { ideal: 240 }
    } 
});

# En el backend
FRAMES_REQUERIDOS = 30  # Reducir frames requeridos
```

#### Para Mayor Precisión (sacrificando velocidad):
```python
UMBRAL_DISTANCIA = 0.4  # Más estricto
FRAMES_REQUERIDOS = 100  # Más frames requeridos
```

---

## 📚 Referencias

- **face_recognition**: https://github.com/ageitgey/face_recognition
- **dlib**: http://dlib.net/
- **Documentación del encoding facial**: https://github.com/ageitgey/face_recognition/wiki/Face-Recognition-Accuracy

---

## ✅ Checklist de Instalación

- [x] Python 3.11 instalado
- [x] Entorno virtual activado
- [x] dlib instalado (desde wheel precompilado)
- [x] face_recognition instalado
- [x] opencv-python instalado
- [x] Columnas de biometría agregadas a la BD
- [x] Controlador `control_biometria_face_recognition.py` creado
- [x] Rutas API agregadas en `run.py`
- [x] Template `login_streaming.html` creado

---

**¿Listo para probar?** 🚀

1. Activa el venv: `.\venv\Scripts\activate`
2. Ejecuta la app: `cd app && python run.py`
3. Visita: `http://localhost:5000/login_streaming`
4. ¡Disfruta del reconocimiento facial en tiempo real!

