# 📝 Sistema de Firmas Electrónicas

## 🎯 Descripción General

Sistema completo de gestión de contratos con firmas electrónicas digitales. Permite que múltiples usuarios firmen documentos PDF en un orden específico, con cada firma siendo integrada visualmente en el documento.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                   FLUJO DE FIRMAS                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Jefe TI Sube PDF Original                              │
│     └─> Define firmantes y orden (1, 2, 3...)             │
│                                                             │
│  2. PDF se sube a Catbox                                   │
│     └─> Se obtiene URL pública                             │
│                                                             │
│  3. Se notifica al Firmante #1                             │
│     └─> Solo puede firmar cuando es su turno               │
│                                                             │
│  4. Firmante #1 firma                                      │
│     ├─> Descarga PDF actual desde Catbox                   │
│     ├─> Añade su firma visual con ReportLab/PyPDF2        │
│     ├─> PDF firmado se sube nuevamente a Catbox           │
│     └─> Se notifica al Firmante #2                         │
│                                                             │
│  5. Proceso se repite para cada firmante                   │
│                                                             │
│  6. Último firmante firma                                  │
│     └─> Estado del contrato cambia a "Firmado" (F)        │
│     └─> Se notifica a TODOS los firmantes                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Estructura de Archivos

```
pryGobierno/
│
├── app/
│   ├── controllers/
│   │   ├── control_contratos.py        # Lógica de negocio de contratos
│   │   └── control_Usuarios.py         # (Actualizado con obtener_jefes_por_area)
│   │
│   ├── services/
│   │   ├── catbox_service.py           # Interacción con Catbox API
│   │   └── firma_service.py            # Añadir firmas visuales a PDFs
│   │
│   ├── templates/
│   │   ├── gestionContratos.html       # Lista de contratos
│   │   ├── formCrearContrato.html      # Crear nuevo contrato
│   │   ├── firmarContrato.html         # Interfaz de firma con canvas
│   │   └── sidebar.html                # (Actualizado con menú Contratos)
│   │
│   ├── temp/                            # PDFs temporales (auto-limpieza)
│   │
│   └── run.py                           # (Actualizado con rutas de contratos)
│
├── requirements.txt                     # (Actualizado con PyPDF2, reportlab)
└── SISTEMA_FIRMAS_ELECTRONICAS.md      # Esta documentación
```

## 🗄️ Estructura de Base de Datos

### Tablas Utilizadas

#### CONTRATO
```sql
CREATE TABLE CONTRATO (
    id_contrato SERIAL PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    url_archivo TEXT NOT NULL,      -- URL de Catbox con el PDF
    estado CHAR(1) NOT NULL         -- P=Pendiente, F=Firmado, R=Rechazado
        CHECK (estado IN ('P','F','R')) DEFAULT 'P',
    fecha_creacion TIMESTAMP DEFAULT NOW()
);
```

#### CONTRATO_FIRMA_PENDIENTE
```sql
CREATE TABLE CONTRATO_FIRMA_PENDIENTE (
    id_firma SERIAL PRIMARY KEY,
    id_contrato INTEGER NOT NULL,
    id_usuario INTEGER NOT NULL,
    orden INTEGER NOT NULL,              -- 1, 2, 3... (orden de firma)
    firmado BOOLEAN DEFAULT FALSE,
    fecha_firma TIMESTAMP,
    rechazo BOOLEAN DEFAULT FALSE,
    comentario_rechazo TEXT,
    FOREIGN KEY (id_contrato) REFERENCES CONTRATO(id_contrato),
    FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
);
```

#### CONTRATO_RECHAZO
```sql
CREATE TABLE CONTRATO_RECHAZO (
    id_rechazo SERIAL PRIMARY KEY,
    id_contrato INTEGER NOT NULL,
    id_usuario INTEGER NOT NULL,
    motivo TEXT NOT NULL,
    fecha_rechazo TIMESTAMP DEFAULT NOW(),
    id_firma_pendiente INTEGER,
    FOREIGN KEY (id_firma_pendiente) REFERENCES CONTRATO_FIRMA_PENDIENTE(id_firma),
    FOREIGN KEY (id_contrato) REFERENCES CONTRATO(id_contrato),
    FOREIGN KEY (id_usuario) REFERENCES USUARIO(id_usuario)
);
```

## 🔧 Tecnologías Utilizadas

### Backend
- **Flask**: Framework web
- **PyPDF2**: Lectura y manipulación de PDFs
- **ReportLab**: Generación de contenido PDF (firmas visuales)
- **Requests**: Conexión con Catbox API
- **PostgreSQL**: Base de datos

### Frontend
- **Tailwind CSS**: Estilos
- **Signature Pad JS**: Canvas para captura de firmas
- **Vanilla JavaScript**: Interacciones dinámicas

### Servicios Externos
- **Catbox (catbox.moe)**: Almacenamiento de PDFs
  - API pública sin autenticación
  - Endpoint: `https://catbox.moe/user/api.php`

## 🎨 Interfaz de Usuario

### 1. Gestión de Contratos (`/contratos`)
- **Tabs:**
  - "Mis Pendientes": Contratos que el usuario debe firmar
  - "Todos los Contratos" (Solo Jefe de TI): Vista completa

- **Indicadores visuales:**
  - 🟢 "Es tu turno": Puede firmar ahora
  - ⏳ "Esperando": Debe esperar firmas anteriores
  - ✅ "Firmado": Contrato completado
  - ❌ "Rechazado": Contrato rechazado

### 2. Crear Contrato (`/crear_contrato`)
- **Solo accesible para Jefe de TI**
- **Campos:**
  - Título del contrato
  - Descripción
  - Archivo PDF (máximo 10MB)
  - Lista de firmantes con orden

- **Funciones:**
  - Agregar firmantes por ID de usuario
  - Reordenar firmantes (flechas arriba/abajo)
  - Eliminar firmantes

### 3. Firmar Contrato (`/firmar_contrato/<id>`)
- **Columna Izquierda:**
  - Vista previa del PDF
  - Historial de firmas (quién firmó, quién falta)

- **Columna Derecha:**
  - Canvas de firma (Signature Pad)
  - Botón "Firmar Contrato"
  - Botón "Rechazar Contrato"

## 🔐 Seguridad y Permisos

### Control de Acceso
- **Crear Contratos**: Solo Jefe de TI
- **Ver Todos los Contratos**: Solo Jefe de TI
- **Firmar**: Solo cuando es el turno del usuario

### Validaciones
```python
# Verificar turno de firma
if not ControlContratos.es_turno_de_firmar(id_contrato, id_usuario):
    return {'success': False, 'message': 'Aún no es tu turno'}
```

### Auditoría
- Fecha y hora de cada firma
- Historial completo en `CONTRATO_FIRMA_PENDIENTE`
- Registro de rechazos en `CONTRATO_RECHAZO`
- Notificaciones a todos los involucrados

## 📡 API Endpoints

### Contratos
```python
GET  /contratos                           # Vista principal
GET  /crear_contrato                      # Formulario crear
POST /crear_contrato                      # Procesar creación
GET  /firmar_contrato/<id>                # Vista de firma
```

### API REST
```python
POST /api/contrato/<id>/firmar            # Firmar contrato
POST /api/contrato/<id>/rechazar          # Rechazar contrato
GET  /api/contratos/pendientes            # Contratos pendientes usuario
GET  /api/contratos/todos                 # Todos (solo Jefe TI)
GET  /api/contrato/<id>/historial         # Historial de firmas
```

## 🚀 Instalación

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

Nuevas librerías agregadas:
- `PyPDF2>=3.0.0`
- `reportlab>=4.0.0`
- `requests>=2.31.0`

### 2. Verificar Base de Datos
Las tablas ya están creadas según el script `SCRIPT DE BD_ELECTRO_VELVA.txt`

### 3. Crear Carpeta Temporal
La carpeta `app/temp/` se crea automáticamente al iniciar.

### 4. Iniciar Aplicación
```bash
python app/run.py
```

## 📝 Uso del Sistema

### Crear un Contrato (Jefe de TI)

1. **Acceder a Contratos**
   - Clic en "Contratos" en el menú lateral

2. **Crear Nuevo Contrato**
   - Clic en "Nuevo Contrato"
   - Llenar título y descripción
   - Subir archivo PDF

3. **Definir Firmantes**
   - Clic en "Agregar Firmante"
   - Ingresar ID del usuario
   - Repetir para cada firmante
   - Reordenar si es necesario

4. **Guardar**
   - Clic en "Crear Contrato"
   - El primer firmante recibe notificación automáticamente

### Firmar un Contrato (Usuario)

1. **Recibir Notificación**
   - Notificación indica: "Tu turno para firmar"

2. **Acceder al Contrato**
   - Ir a "Contratos" > "Mis Pendientes"
   - Clic en "Firmar Ahora" (solo si es tu turno)

3. **Revisar Documento**
   - Clic en "Ver PDF Completo" para leer

4. **Firmar**
   - Dibujar firma en el canvas
   - Clic en "Firmar Contrato"
   - Confirmar acción

5. **Resultado**
   - PDF se actualiza con tu firma
   - Siguiente firmante recibe notificación
   - Si eres el último, se notifica a todos

### Rechazar un Contrato

1. **Clic en "Rechazar Contrato"**
2. **Ingresar Motivo** (obligatorio)
3. **Confirmar Rechazo**
4. **Todos los firmantes son notificados**
5. **Contrato queda en estado "Rechazado"**

## 🎯 Características Avanzadas

### Posicionamiento de Firmas
Las firmas se posicionan automáticamente en la última página del PDF:

```python
POSICIONES_FIRMA = {
    1: {'x': 50, 'y': 50, 'ancho': 150, 'alto': 60},    # Abajo izquierda
    2: {'x': 250, 'y': 50, 'ancho': 150, 'alto': 60},   # Abajo centro
    3: {'x': 450, 'y': 50, 'ancho': 150, 'alto': 60},   # Abajo derecha
    # ... hasta 6 firmantes
}
```

### Información de cada Firma
Cada firma incluye:
- Imagen de la firma digital
- Nombre completo del firmante
- Fecha y hora de la firma

### Auto-limpieza de Archivos Temporales
```python
# Archivos mayores a 24 horas se eliminan automáticamente
FirmaService.limpiar_archivos_temporales(max_edad_horas=24)
```

## ⚠️ Consideraciones

### Limitaciones de Catbox
- Tamaño máximo de archivo: depende del servicio (generalmente 200MB)
- Sin autenticación requerida
- URLs públicas (cualquiera con el link puede ver)

### Alternativa: Cloudinary
Si Catbox falla, puedes modificar para usar Cloudinary (ya configurado en el proyecto):
```python
# En catbox_service.py, reemplazar upload con:
cloudinary.uploader.upload(pdf_bytes, resource_type="raw")
```

### Rendimiento
- La descarga y subida de PDFs puede tardar según el tamaño
- Se muestran indicadores de "Procesando..." durante la firma

## 🐛 Troubleshooting

### Error: "No se pudo subir a Catbox"
- **Causa**: Conexión a internet o servicio Catbox caído
- **Solución**: Verificar conexión, reintentar más tarde, o usar Cloudinary

### Error: "El archivo no es un PDF válido"
- **Causa**: Archivo corrupto o formato incorrecto
- **Solución**: Verificar que el archivo sea PDF válido

### Error: "Aún no es tu turno para firmar"
- **Causa**: Firmantes anteriores no han firmado
- **Solución**: Esperar a que los anteriores firmen

### La firma no aparece en el PDF
- **Causa**: Error en la generación de firma con ReportLab
- **Solución**: Verificar instalación de `reportlab` y `Pillow`

## 📊 Métricas y Reportes

El sistema registra:
- ✅ Cantidad de contratos creados
- ✅ Contratos firmados vs rechazados
- ✅ Tiempo promedio de firma
- ✅ Usuarios más activos

Estos datos pueden consultarse en:
- Historial de cada contrato
- Vista "Todos los Contratos" (Jefe de TI)

## 🔄 Flujo de Notificaciones

```
Contrato Creado
    └─> Notificación a Firmante #1

Firmante #1 Firma
    └─> Notificación a Firmante #2

Firmante #2 Firma
    └─> Notificación a Firmante #3

Último Firmante Firma
    └─> Notificación a TODOS
    └─> Estado: Firmado (F)

Cualquier Rechazo
    └─> Notificación a TODOS
    └─> Estado: Rechazado (R)
```

## 📞 Soporte

Para dudas o problemas con el sistema de firmas:
1. Revisar este documento
2. Verificar logs en consola del servidor
3. Contactar al administrador del sistema

---

**Última actualización**: Noviembre 2025  
**Versión del Sistema**: 1.0  
**Desarrollado para**: Sistema de Gobierno - Electro Oriente S.A.

