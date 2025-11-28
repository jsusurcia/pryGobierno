from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from controllers.control_Usuarios import controlUsuarios
from controllers.control_incidentes import ControlIncidentes
from controllers.control_categorias import controlCategorias
from controllers.control_diagnostico import ControlDiagnosticos
from controllers.control_notificaciones import ControlNotificaciones
from controllers.control_evidencias import controlEvidencias
from controllers.control_biometria import ControlBiometria
from controllers.control_biometria_opencv import ControlBiometriaOpenCV
from controllers.control_predicciones import ControlPredicciones
from controllers.control_contratos import ControlContratos
from services.sello_service import SelloService
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__, template_folder="./templates")
app.secret_key = 'tu_clave_secreta_aqui'

# Configurar encoding UTF-8 para Flask
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuración de Cloudinary
cloudinary.config(
    cloud_name='dazo1emme',
    api_key='162899849954513',
    api_secret='SQM5RA1S0F1v7RDXLdbQhDIwfIw'
)

# Configuración para archivos (backup local si Cloudinary falla)
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'evidencias')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Crear carpeta de evidencias si no existe
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE * 10  # Máximo 10 archivos de 10MB cada uno

def allowed_file(filename):
    """Verifica si el archivo tiene una extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def subir_a_cloudinary(archivo, id_incidente):
    """Sube un archivo a Cloudinary y retorna la URL"""
    try:
        from io import BytesIO
        import uuid
        import hashlib
        
        # Obtener el nombre del archivo
        nombre_archivo = getattr(archivo, 'filename', None) or getattr(archivo, 'name', 'archivo')
        
        # Asegurarse de que el archivo esté al inicio
        archivo.seek(0)
        
        # Si ya es un BytesIO, usar directamente; si no, leer en memoria
        if isinstance(archivo, BytesIO):
            archivo_stream = archivo
            archivo_stream.seek(0)
            # Leer datos para generar hash único
            archivo_data = archivo_stream.read()
            archivo_stream.seek(0)
        else:
            # Leer el contenido del archivo en memoria para evitar problemas con el stream
            archivo_data = archivo.read()
            archivo.seek(0)  # Volver al inicio
            
            # Crear un nuevo stream desde los datos
            archivo_stream = BytesIO(archivo_data)
        
        # Generar nombre único con múltiples factores para evitar colisiones
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        # Generar hash del contenido para garantizar unicidad
        hash_contenido = hashlib.md5(archivo_data).hexdigest()[:8]
        # Generar UUID corto adicional
        uuid_corto = str(uuid.uuid4())[:8]
        nombre_seguro = secure_filename(nombre_archivo)
        nombre_base = nombre_seguro.rsplit('.', 1)[0] if '.' in nombre_seguro else nombre_seguro
        # Public ID único: incidente_id + timestamp + hash + uuid + nombre
        public_id = f"incidentes_{id_incidente}_{timestamp}_{hash_contenido}_{uuid_corto}_{nombre_base}"
        
        # Subir a Cloudinary (solo imágenes)
        resultado = cloudinary.uploader.upload(
            archivo_stream,
            public_id=public_id,
            resource_type="image",  # Solo imágenes
            folder="evidencias_incidentes",
            overwrite=False  # No sobrescribir si existe (aunque con este ID único nunca debería pasar)
        )
        
        url = resultado.get('secure_url')
        print(f"   ✅ Archivo '{nombre_archivo}' subido exitosamente a Cloudinary (ID: {public_id})")
        return url
    except Exception as e:
        nombre_archivo = getattr(archivo, 'filename', None) or getattr(archivo, 'name', 'archivo')
        print(f"❌ Error al subir '{nombre_archivo}' a Cloudinary: {e}")
        import traceback
        traceback.print_exc()
        return None  

@app.route('/')
def index():
    """Ruta principal que redirige al login"""
    if 'user_id' in session:
        print(session.get('user_role'))
        # Solo el jefe de TI (id_rol = 1) va a revisión de diagnósticos
        if controlUsuarios.es_jefe_ti_rol_1(int(session['user_id'])):
            return redirect(url_for('revision_diagnostico'))
        elif session.get('user_role'):
            return redirect(url_for('gestion_incidentes'))
    return redirect(url_for('login'))


@app.route('/login_streaming')
def login_streaming():
    """Login con video streaming y reconocimiento facial en tiempo real"""
    return render_template('login_streaming.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta para el login"""
    if request.method == 'POST':
        correo = request.form.get('email')
        contrasena = request.form.get('password')
        
        if not correo or not contrasena:
            flash('Por favor, complete todos los campos', 'error')
            return render_template('login.html')
        
        # Buscar usuario por correo
        usuario = controlUsuarios.buscar_por_correo(correo,contrasena)
        
        if usuario and controlUsuarios.verificar_contrasena(correo, contrasena):
            if usuario['estado']:  # Campo 'activo' en PostgreSQL
                session['user_id'] = str(usuario['id_usuario'])
                session['user_name'] = f"{usuario['nombre']} {usuario['ape_pat']} {usuario['ape_mat']}"
                session['user_role'] = usuario['id_rol']
                session['user_role_name'] = usuario.get('rol_nombre', 'Usuario')
                flash('Inicio de sesión exitoso', 'success')
                return redirect(url_for('index'))
            else:
                flash('Usuario inactivo. Contacte al administrador', 'error')
        else:
            flash('Correo o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Ruta para cerrar sesión"""
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('login'))

# ========== RUTAS DE BIOMETRÍA FACIAL ==========

@app.route('/login_biometrico', methods=['POST'])
def login_biometrico():
    """Login con verificación biométrica (correo + contraseña + rostro)"""
    correo = request.form.get('email')
    contrasena = request.form.get('password')
    imagen_facial = request.form.get('imagen_facial')
    
    if not correo or not contrasena:
        flash('Por favor, complete todos los campos', 'error')
        return render_template('login.html')
    
    if not imagen_facial:
        flash('Por favor, capture su rostro para la verificación biométrica', 'error')
        return render_template('login.html')
    
    # Verificar credenciales y rostro con OpenCV ORB
    resultado = ControlBiometriaOpenCV.verificar_rostro(correo, contrasena, imagen_facial)
    
    if resultado['exito']:
        usuario = resultado['usuario']
        session['user_id'] = str(usuario['id_usuario'])
        session['user_name'] = f"{usuario['nombre']} {usuario['ape_pat']} {usuario['ape_mat']}"
        session['user_role'] = usuario['id_rol']
        flash(f'Inicio de sesión biométrico exitoso (Distancia: {resultado.get("distancia", 0):.2f})', 'success')
        return redirect(url_for('index'))
    else:
        # Si requiere registro de rostro, redirigir a enrolamiento
        if resultado.get('requiere_registro'):
            flash('Necesita registrar su rostro primero. Use sus credenciales para registrarlo.', 'info')
            return redirect(url_for('enrolamiento_facial'))
        
        flash(resultado['mensaje'], 'error')
        return render_template('login.html')

@app.route('/enrolamiento_facial')
def enrolamiento_facial():
    """Página para registrar el rostro del usuario"""
    return render_template('enrolamiento_facial.html')

@app.route('/api/biometria/verificar-credenciales', methods=['POST'])
def api_verificar_credenciales():
    """API para verificar credenciales antes del registro facial"""
    try:
        data = request.get_json()
        correo = data.get('correo')
        contrasena = data.get('contrasena')
        
        if not correo or not contrasena:
            return jsonify({'exito': False, 'mensaje': 'Credenciales incompletas'})
        
        # Buscar usuario
        usuario = controlUsuarios.buscar_por_correo(correo, contrasena)
        
        if not usuario:
            return jsonify({'exito': False, 'mensaje': 'Correo o contraseña incorrectos'})
        
        if not usuario.get('estado'):
            return jsonify({'exito': False, 'mensaje': 'Usuario inactivo'})
        
        # Verificar si ya tiene biometría
        if ControlBiometriaOpenCV.tiene_biometria(usuario['id_usuario']):
            return jsonify({
                'exito': False, 
                'mensaje': 'Ya tiene un rostro registrado. Si desea actualizarlo, contacte al administrador.'
            })
        
        return jsonify({
            'exito': True,
            'id_usuario': usuario['id_usuario'],
            'nombre_completo': f"{usuario['nombre']} {usuario['ape_pat']} {usuario['ape_mat']}"
        })
        
    except Exception as e:
        print(f"Error en api_verificar_credenciales: {e}")
        return jsonify({'exito': False, 'mensaje': 'Error interno del servidor'}), 500

@app.route('/api/biometria/registrar-rostro', methods=['POST'])
def api_registrar_rostro():
    """API para registrar el rostro de un usuario usando face_recognition"""
    try:
        data = request.get_json()
        id_usuario = data.get('id_usuario')
        imagen_facial = data.get('imagen_facial')
        
        if not id_usuario or not imagen_facial:
            return jsonify({'exito': False, 'mensaje': 'Datos incompletos'})
        
        # Registrar rostro con OpenCV
        resultado = ControlBiometriaOpenCV.registrar_rostro(id_usuario, imagen_facial)
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Error en api_registrar_rostro: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'exito': False, 'mensaje': f'Error: {str(e)}'}), 500

@app.route('/api/biometria/verificar-rostro', methods=['POST'])
def api_verificar_rostro():
    """API para verificar solo el rostro de un usuario (re-autenticación)"""
    if 'user_id' not in session:
        return jsonify({'exito': False, 'mensaje': 'No autorizado'}), 401
    
    try:
        data = request.get_json()
        imagen_facial = data.get('imagen_facial')
        
        if not imagen_facial:
            return jsonify({'exito': False, 'mensaje': 'Imagen facial requerida'})
        
        resultado = ControlBiometria.verificar_solo_rostro(int(session['user_id']), imagen_facial)
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Error en api_verificar_rostro: {e}")
        return jsonify({'exito': False, 'mensaje': str(e)}), 500

@app.route('/api/biometria/estado/<int:id_usuario>')
def api_estado_biometria(id_usuario):
    """API para verificar si un usuario tiene biometría registrada"""
    tiene = ControlBiometria.tiene_biometria(id_usuario)
    return jsonify({'tiene_biometria': tiene})

# ============================================================================
# NUEVAS RUTAS - SISTEMA DE VIDEO STREAMING CON FACE_RECOGNITION
# ============================================================================

@app.route('/api/biometria/iniciar-verificacion-streaming', methods=['POST'])
def api_iniciar_verificacion_streaming():
    """
    Inicia la verificación por video streaming.
    Obtiene el encoding del usuario y lo guarda en la sesión.
    """
    try:
        data = request.get_json()
        correo = data.get('correo')
        contrasena = data.get('contrasena')
        
        if not correo or not contrasena:
            return jsonify({'exito': False, 'mensaje': 'Credenciales incompletas'})
        
        # Obtener rostro del usuario
        resultado = ControlBiometriaOpenCV.obtener_rostro_usuario(correo, contrasena)
        
        if resultado['exito']:
            # Guardar el rostro en la sesión temporalmente
            import pickle
            import base64
            
            rostro_serializado = base64.b64encode(pickle.dumps(resultado['rostro'])).decode('utf-8')
            
            session['temp_rostro'] = rostro_serializado
            session['temp_usuario'] = resultado['usuario']
            session['match_count'] = 0  # Contador de matches
            session['total_frames'] = 0  # Total de frames procesados
            
            return jsonify({
                'exito': True,
                'mensaje': 'Verificación iniciada',
                'frames_requeridos': ControlBiometriaOpenCV.FRAMES_REQUERIDOS,
                'usuario': resultado['usuario']
            })
        else:
            return jsonify(resultado)
        
    except Exception as e:
        print(f"❌ Error en api_iniciar_verificacion_streaming: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'exito': False, 'mensaje': f'Error: {str(e)}'}), 500

@app.route('/api/biometria/verificar-frame', methods=['POST'])
def api_verificar_frame():
    """
    Verifica un frame del video contra el encoding almacenado en la sesión.
    Cuenta los matches consecutivos.
    """
    try:
        # Verificar que hay una sesión activa
        if 'temp_rostro' not in session:
            return jsonify({
                'exito': False,
                'mensaje': 'No hay sesión de verificación activa',
                'reiniciar': True
            })
        
        data = request.get_json()
        imagen_base64 = data.get('imagen_facial')
        
        if not imagen_base64:
            return jsonify({'exito': False, 'mensaje': 'Imagen no proporcionada'})
        
        # Deserializar el rostro de la sesión
        import pickle
        import base64
        
        rostro_bytes = base64.b64decode(session['temp_rostro'])
        rostro_guardado = pickle.loads(rostro_bytes)
        
        # Verificar el frame
        resultado = ControlBiometriaOpenCV.verificar_frame(rostro_guardado, imagen_base64)
        
        # Actualizar contadores
        session['total_frames'] = session.get('total_frames', 0) + 1
        
        if resultado['coincide']:
            session['match_count'] = session.get('match_count', 0) + 1
        else:
            # Reiniciar contador si no coincide
            session['match_count'] = 0
        
        match_count = session['match_count']
        total_frames = session['total_frames']
        frames_requeridos = ControlBiometriaOpenCV.FRAMES_REQUERIDOS
        
        # Verificar si se alcanzó el umbral
        if match_count >= frames_requeridos:
            # Login exitoso
            usuario = session['temp_usuario']
            
            # Establecer sesión de usuario
            session['user_id'] = str(usuario['id_usuario'])
            session['user_name'] = f"{usuario['nombre']} {usuario['ape_pat']} {usuario['ape_mat']}"
            session['user_role'] = usuario['id_rol']
            
            # Limpiar datos temporales
            session.pop('temp_rostro', None)
            session.pop('temp_usuario', None)
            session.pop('match_count', None)
            session.pop('total_frames', None)
            
            return jsonify({
                'exito': True,
                'login_exitoso': True,
                'coincide': True,
                'match_count': match_count,
                'total_frames': total_frames,
                'frames_requeridos': frames_requeridos,
                'progreso': 100,
                'mensaje': f'¡Login exitoso! {match_count} frames coincidentes',
                'distancia': resultado.get('distancia', 0),
                'face_location': resultado.get('face_location')
            })
        
        # Calcular progreso
        progreso = int((match_count / frames_requeridos) * 100)
        
        return jsonify({
            'exito': True,
            'login_exitoso': False,
            'coincide': resultado['coincide'],
            'match_count': match_count,
            'total_frames': total_frames,
            'frames_requeridos': frames_requeridos,
            'progreso': progreso,
            'mensaje': resultado['mensaje'],
            'distancia': resultado.get('distancia', 0),
            'face_location': resultado.get('face_location')
        })
        
    except Exception as e:
        print(f"❌ Error en api_verificar_frame: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'exito': False, 'mensaje': f'Error: {str(e)}'}), 500

@app.route('/api/biometria/cancelar-verificacion', methods=['POST'])
def api_cancelar_verificacion():
    """Cancela la verificación en curso y limpia la sesión"""
    try:
        session.pop('temp_rostro', None)
        session.pop('temp_usuario', None)
        session.pop('match_count', None)
        session.pop('total_frames', None)
        
        return jsonify({'exito': True, 'mensaje': 'Verificación cancelada'})
        
    except Exception as e:
        return jsonify({'exito': False, 'mensaje': str(e)}), 500

# ============================================================================
# FIN NUEVAS RUTAS - VIDEO STREAMING
# ============================================================================

@app.route('/dashboard')
def dashboard():
    """Dashboard principal después del login"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener estadísticas para el dashboard
    try:
        incidentes = ControlIncidentes.listar_incidentes()
        total_incidentes = len(incidentes)
        incidentes_abiertos = len([i for i in incidentes if i['estado'] == 'Abierto'])
        incidentes_proceso = len([i for i in incidentes if i['estado'] == 'En Progreso'])
        incidentes_resueltos = len([i for i in incidentes if i['estado'] == 'Resuelto'])
        
        # Incidentes recientes (últimos 5)
        incidentes_recientes = incidentes[:5] if incidentes else []
        
        stats = {
            'total_incidentes': total_incidentes,
            'incidentes_abiertos': incidentes_abiertos,
            'incidentes_proceso': incidentes_proceso,
            'incidentes_resueltos': incidentes_resueltos,
            'incidentes_recientes': incidentes_recientes
        }
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        stats = {
            'total_incidentes': 0,
            'incidentes_abiertos': 0,
            'incidentes_proceso': 0,
            'incidentes_resueltos': 0,
            'incidentes_recientes': []
        }
    
    return render_template('gestionIncidente.html', 
                         user_name=session.get('user_name'),
                         user_role=session.get('user_role'),
                         stats=stats)

@app.route('/gestion_incidentes')
def gestion_incidentes():
    """Ruta para gestión de incidentes con filtros - Adaptado según rol"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    usuario_id = int(session['user_id'])
    usuario = controlUsuarios.buscar_por_ID(usuario_id)
    
    if not usuario:
        return redirect(url_for('login'))
    
    # Obtener rol
    from controllers.controlador_rol import ControlRol
    rol = ControlRol.buscar_por_IDRol(usuario['id_rol'])
    tipo_rol = rol.get('tipo') if rol else None
    
    # Obtener parámetros de filtro
    filtros = {
        'buscar': request.args.get('buscar', '').strip().lower(),
        'fecha_desde': request.args.get('fecha_desde', '').strip(),
        'fecha_hasta': request.args.get('fecha_hasta', '').strip(),
        'categoria': request.args.get('categoria', '').strip().lower(),
        'estado': request.args.get('estado', '').strip().lower()
    }

    try:
        # Obtener incidentes según el rol usando el método simplificado
        id_rol_usuario = usuario.get('id_rol')
        todos = ControlIncidentes.listar_incidentes(id_usuario=usuario_id, id_rol=id_rol_usuario)
        
        if not todos:
            todos = []

        incidentes = []
        for inc in todos:
            cumple = True

            # Normalizar campos
            titulo = str(inc.get('titulo', '')).lower()
            categoria = str(inc.get('categoria', '')).lower()
            estado = str(inc.get('estado', '')).lower()

            # Manejar fecha correctamente
            fecha = inc.get('fecha_reporte', '')
            if isinstance(fecha, datetime):
                fecha = fecha.strftime('%Y-%m-%d')
            else:
                fecha = str(fecha)

            # Buscar texto en ID o título
            if filtros['buscar']:
                id_str = str(inc.get('id_incidente', '')).lower()
                if filtros['buscar'] not in titulo and filtros['buscar'] not in id_str:
                    cumple = False

            # Filtrar por categoría
            if filtros['categoria'] and filtros['categoria'] != categoria:
                cumple = False

            # Filtrar por estado (normalizar para comparación)
            if filtros['estado']:
                estado_filtro = filtros['estado'].lower()
                estado_normalizado = estado.lower()
                # Mapear estados del filtro a estados de BD
                estado_map_filtro = {
                    'pendiente': 'pendiente',
                    'activo': 'activo',
                    'cancelado': 'cancelado',
                    'terminado': 'terminado'
                }
                estado_filtro_normalizado = estado_map_filtro.get(estado_filtro, estado_filtro)
                if estado_filtro_normalizado != estado_normalizado:
                    cumple = False

            # Filtrar por fechas
            if filtros['fecha_desde'] and fecha < filtros['fecha_desde']:
                cumple = False
            if filtros['fecha_hasta'] and fecha > filtros['fecha_hasta']:
                cumple = False

            if cumple:
                incidentes.append(inc)

        #  Si no hay incidentes, se envía una lista vacía (evita datos falsos)
        if not incidentes:
            incidentes_obj = []
        else:
            # Importar ControlDiagnosticos para verificar diagnósticos pendientes
            from controllers.control_diagnostico import ControlDiagnosticos
            
            class IncidenteObj:
                def __init__(self, data):
                    self.id_incidente = data.get('id_incidente') or data.get('id')
                    self.titulo = data.get('titulo', '')
                    self.descripcion = data.get('descripcion', '')
                    self.categoria = data.get('categoria', 'No asignada')
                    self.estado = data.get('estado', 'pendiente')
                    self.nivel = data.get('nivel', 'M')
                    
                    # Verificar si el usuario actual tiene diagnóstico pendiente para este incidente
                    if 'user_id' in session:
                        self.tiene_diagnostico_pendiente = ControlDiagnosticos.tiene_diagnostico_pendiente(
                            self.id_incidente, 
                            int(session['user_id'])
                        )
                    else:
                        self.tiene_diagnostico_pendiente = False

                    # Manejar fecha_creacion
                    fecha_reporte = data.get('fecha_reporte')
                    if isinstance(fecha_reporte, datetime):
                        self.fecha_creacion = fecha_reporte
                    elif fecha_reporte:
                        try:
                            self.fecha_creacion = datetime.strptime(str(fecha_reporte), '%Y-%m-%d')
                        except:
                            self.fecha_creacion = None
                    else:
                        self.fecha_creacion = None

            incidentes_obj = [IncidenteObj(inc) for inc in incidentes]

    except Exception as e:
        print(f"Error al obtener incidentes: {e}")
        import traceback
        traceback.print_exc()
        incidentes_obj = []
        flash('Error al cargar los incidentes', 'error')

    # Obtener categorías para el combo box
    categorias = controlCategorias.buscar_todos() or []
    
    return render_template('gestionIncidente.html',
                           incidentes=incidentes_obj,
                           categorias=categorias,
                           user_role=session.get('user_role'),
                           tipo_rol=tipo_rol,
                           es_jefe_ti=controlUsuarios.es_jefe_ti(usuario_id) if usuario else False)
    
@app.route('/registrar_incidente', methods=['GET'])
def mostrar_formulario_incidente():
    """Mostrar formulario de registro de incidente - Solo jefes"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Verificar que sea jefe
    if not controlUsuarios.es_jefe(int(session['user_id'])):
        flash('Solo los jefes pueden registrar incidentes', 'error')
        return redirect(url_for('gestion_incidentes'))
    
    # Obtener categorías
    categorias = controlCategorias.buscar_todos() or []
    
    return render_template('formRegistrarIncidente.html', categorias=categorias)

@app.route('/revision_diagnostico', methods=['GET'])
def revision_diagnostico():
    """Revisión de diagnósticos - Solo jefe de TI (id_rol = 1)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Verificar que sea jefe de TI con id_rol = 1
    if not controlUsuarios.es_jefe_ti_rol_1(int(session['user_id'])):
        flash('Solo el Jefe de Tecnología de la Información y Comunicaciones puede acceder a esta sección', 'error')
        return redirect(url_for('gestion_incidentes'))

    control_diag = ControlDiagnosticos()
    diagnosticos = control_diag.listado_diagnosticos_revision()

    # Agrupar por incidente
    incidentes = {}
    for d in diagnosticos:
        id_inc = d['id_incidente']
        if id_inc not in incidentes:
            incidentes[id_inc] = {
                'titulo': d['titulo_incidente'] or f'Incidente {id_inc}',
                'diagnosticos': []
            }
        incidentes[id_inc]['diagnosticos'].append(d)

    return render_template('revisionDiagnostico.html', incidentes=incidentes)

@app.route('/api/diagnostico/<int:id_diagnostico>/aceptar/<int:id_incidente>', methods=['POST'])
def api_aceptar_revision(id_diagnostico, id_incidente):
    """Aceptar revisión del diagnóstico - Solo jefe de TI"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti_rol_1(int(session['user_id'])):
        return jsonify({'success': False, 'message': 'No tiene permisos'}), 403

    exito = ControlDiagnosticos.aceptar_revision(id_diagnostico, id_incidente)
    if exito:
        return jsonify({'success': True, 'message': 'Diagnóstico aceptado correctamente. El incidente ha sido terminado y se notificó a todos los involucrados.'})
    else:
        return jsonify({'success': False, 'message': 'Error al aceptar diagnóstico'}), 500


@app.route('/api/diagnostico/<int:id_diagnostico>/actualizar', methods=['POST'])
def api_actualizar_diagnostico(id_diagnostico):
    """API para actualizar un diagnóstico"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    usuario_id = int(session['user_id'])
    
    try:
        data = request.get_json()
        descripcion = data.get('descripcion', '').strip()
        causa_raiz = data.get('causa_raiz', '').strip()
        solucion_propuesta = data.get('solucion_propuesta', '').strip()
        
        if not descripcion or not causa_raiz:
            return jsonify({'success': False, 'message': 'Descripción y Causa Raíz son obligatorios'}), 400
        
        # Si solucion_propuesta está vacío, establecer como None
        if not solucion_propuesta:
            solucion_propuesta = None
        
        resultado = ControlDiagnosticos.actualizar_diagnostico(
            id_diagnosticos=id_diagnostico,
            descripcion=descripcion,
            causa_raiz=causa_raiz,
            solucion_propuesta=solucion_propuesta,
            id_usuario=usuario_id
        )
        
        if resultado == 0:
            return jsonify({'success': True, 'message': 'Diagnóstico actualizado correctamente'})
        else:
            return jsonify({'success': False, 'message': 'Error al actualizar el diagnóstico'}), 500
            
    except Exception as e:
        print(f"Error en api_actualizar_diagnostico: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/diagnostico/<int:id_diagnostico>/cancelar/<int:id_incidente>', methods=['POST'])
def api_cancelar_revision(id_diagnostico, id_incidente):
    """Cancelar (rechazar) revisión del diagnóstico - Solo jefe de TI"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti_rol_1(int(session['user_id'])):
        return jsonify({'success': False, 'message': 'No tiene permisos'}), 403

    usuario_id = int(session['user_id'])
    exito = ControlDiagnosticos.cancelar_revision(id_diagnostico, id_incidente, usuario_id)
    if exito:
        return jsonify({'success': True, 'message': 'Diagnóstico rechazado correctamente. El técnico podrá actualizarlo y volverá a aparecer para revisión.'})
    else:
        return jsonify({'success': False, 'message': 'Error al rechazar diagnóstico'}), 500



@app.route('/registrar_incidente', methods=['POST'])
def registrar_incidente():
    """Registrar nuevo incidente - Solo jefes"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Verificar que sea jefe
    if not controlUsuarios.es_jefe(int(session['user_id'])):
        flash('Solo los jefes pueden registrar incidentes', 'error')
        return redirect(url_for('gestion_incidentes'))
    
    try:
        # Obtener datos del formulario
        titulo = request.form.get('titulo', '').strip()
        categoria = request.form.get('categoria')
        descripcion = request.form.get('descripcion', '').strip()
        
        # Validar campos
        if not titulo or not categoria or not descripcion:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('mostrar_formulario_incidente'))
        
        # Asegurar que los strings estén en UTF-8
        if isinstance(titulo, bytes):
            titulo = titulo.decode('utf-8', errors='replace')
        if isinstance(descripcion, bytes):
            descripcion = descripcion.decode('utf-8', errors='replace')
        
        id_categoria = int(categoria)
        id_usuario = int(session['user_id'])
        
        # Insertar incidente (estado P por defecto, nivel B por defecto)
        # El nivel de prioridad se asigna como 'B' (Bajo) por defecto
        # El jefe de TI puede cambiarlo después cuando acepte el incidente
        resultado = ControlIncidentes.insertar_incidentes(
            titulo, descripcion, id_categoria, id_usuario, None  # None = se usará 'B' por defecto
        )
        
        if resultado > 0:  # Retorna el ID del incidente
            id_incidente = resultado
            
            # Procesar archivos de evidencias si existen (máximo 5 imágenes)
            if 'evidencias' in request.files:
                archivos = request.files.getlist('evidencias')
                archivos_subidos = 0
                archivos_procesados = 0
                
                print(f"📁 Total de archivos recibidos: {len(archivos)}")
                
                # Filtrar archivos vacíos y limitar a máximo 5 archivos válidos
                archivos_validos = []
                for archivo in archivos:
                    if archivo and archivo.filename:
                        archivos_validos.append(archivo)
                        if len(archivos_validos) >= 5:
                            break
                
                print(f"📁 Archivos válidos a procesar: {len(archivos_validos)}")
                
                for idx, archivo in enumerate(archivos_validos):
                    nombre_archivo = archivo.filename
                    print(f"\n🔄 Procesando archivo {idx + 1}/{len(archivos_validos)}: {nombre_archivo}")
                    
                    # Leer el archivo completo en memoria primero
                    try:
                        from io import BytesIO
                        archivo.seek(0)
                        archivo_data = archivo.read()
                        tamaño = len(archivo_data)
                        print(f"   Tamaño: {tamaño / (1024*1024):.2f} MB")
                    except Exception as e:
                        print(f"❌ Error al leer archivo {nombre_archivo}: {e}")
                        continue
                    
                    # Validar que sea imagen
                    if not nombre_archivo.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                        print(f"❌ Archivo {nombre_archivo} no es una imagen válida")
                        continue
                    
                    # Validar tamaño (10MB)
                    if tamaño > MAX_FILE_SIZE:
                        print(f"❌ Archivo {nombre_archivo} excede 10MB ({tamaño / (1024*1024):.2f}MB)")
                        continue
                    
                    if tamaño == 0:
                        print(f"❌ Archivo {nombre_archivo} está vacío")
                        continue
                    
                    try:
                        # Crear un nuevo objeto file-like desde los datos en memoria
                        archivo_stream = BytesIO(archivo_data)
                        archivo_stream.name = nombre_archivo  # Asignar nombre para Cloudinary
                        
                        print(f"   ⬆️ Subiendo a Cloudinary...")
                        
                        # Subir a Cloudinary
                        url_archivo = subir_a_cloudinary(archivo_stream, id_incidente)
                        
                        if url_archivo:
                            # Guardar URL de Cloudinary en la base de datos
                            if controlEvidencias.insertar(id_incidente, url_archivo):
                                archivos_subidos += 1
                                print(f"   ✅ Evidencia {archivos_subidos} guardada exitosamente: {nombre_archivo}")
                            else:
                                print(f"   ❌ Error al guardar URL en BD: {nombre_archivo}")
                        else:
                            print(f"   ❌ Error: No se pudo subir {nombre_archivo} a Cloudinary")
                    except Exception as e:
                        print(f"   ❌ Error al procesar evidencia {nombre_archivo}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                    finally:
                        archivos_procesados += 1
                
                print(f"\n📊 Resumen: {archivos_subidos} de {len(archivos_validos)} archivos subidos exitosamente")
                
                if archivos_subidos > 0:
                    flash(f'¡Incidente registrado exitosamente con {archivos_subidos} evidencia(s)! Será revisado por el Jefe de TI.', 'success')
                else:
                    flash('¡Incidente registrado exitosamente! Será revisado por el Jefe de TI.', 'success')
            else:
                flash('¡Incidente registrado exitosamente! Será revisado por el Jefe de TI.', 'success')
            
            # Notificar al jefe de TI
            ControlNotificaciones.notificar_incidente_creado(id_incidente, id_usuario)
            return redirect(url_for('gestion_incidentes'))
        elif resultado == -2:
            flash('Error de conexión a la base de datos', 'error')
        else:
            flash('Error al registrar el incidente', 'error')

    except ValueError:
        flash('Error: La categoría seleccionada no es válida', 'error')
    except Exception as e:
        flash(f'Error inesperado: {str(e)}', 'error')
        print(f"Error en registrar_incidente: {e}")
    
    return redirect(url_for('mostrar_formulario_incidente'))


@app.route('/listar_incidentes')
def listar_incidentes():
    incidentes = ControlIncidentes.listar_incidentes()
    return render_template('lista_incidentes.html', incidentes=incidentes)

@app.route('/api/incidentes')
def api_incidentes():
    incidentes = ControlIncidentes.listar_incidentes()
    return jsonify(incidentes)

@app.route('/incidente/<int:id_incidente>')
def ver_incidente(id_incidente):
    incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
    if incidente:
        return render_template('detalle_incidente.html', incidente=incidente)
    else:
        flash('Incidente no encontrado', 'error')
        return redirect(url_for('listar_incidentes'))

@app.route('/incidentes/<incidente_id>/eliminar', methods=['POST'])
def eliminar_incidente(incidente_id):
    """Eliminar un incidente (solo administradores)"""
    if 'user_id' not in session or session.get('user_role') != 3:  # 3 = Administrador
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        resultado = ControlIncidentes.eliminar_incidente(incidente_id)
        if resultado:
            flash('Incidente eliminado correctamente', 'success')
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Error al eliminar incidente'}), 500
    except Exception as e:
        print(f"Error al eliminar incidente: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/incidentes/<incidente_id>/estado/<int:estado_id>')
def cambiar_estado_incidente(incidente_id, estado_id):
    """Cambiar el estado de un incidente"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Solo técnicos y administradores pueden cambiar estados
    if session.get('user_role') not in [2, 3]:  # 2 = Técnico, 3 = Administrador
        flash('No tiene permisos para cambiar el estado', 'error')
        return redirect(url_for('gestion_incidentes'))
    
    # Validar estados permitidos (1-4)
    if estado_id not in [1, 2, 3, 4]:
        flash('Estado no válido', 'error')
        return redirect(url_for('gestion_incidentes'))
    
    try:
        resultado = ControlIncidentes.actualizar_estado(incidente_id, estado_id, session['user_id'])
        if resultado:
            estados = {1: 'Abierto', 2: 'En Progreso', 3: 'Resuelto', 4: 'Cerrado'}
            flash(f'Estado del incidente actualizado a {estados[estado_id]}', 'success')
        else:
            flash('Error al actualizar el estado', 'error')
    except Exception as e:
        print(f"Error al cambiar estado: {e}")
        flash('Error interno del servidor', 'error')
    
    return redirect(url_for('gestion_incidentes'))

@app.route('/incidentes/<incidente_id>/detalle')
def detalle_incidente(incidente_id):
    """Obtener detalles de un incidente (API JSON)"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        incidente = ControlIncidentes.buscar_por_id(incidente_id)
        if incidente:
            # Convertir fechas para JSON
            if incidente.get('fecha_reporte'):
                incidente['fecha_reporte'] = incidente['fecha_reporte'].isoformat()
            if incidente.get('fecha_resolucion'):
                incidente['fecha_resolucion'] = incidente['fecha_resolucion'].isoformat()
            return jsonify(incidente)
        else:
            return jsonify({'error': 'Incidente no encontrado'}), 404
    except Exception as e:
        print(f"Error al obtener detalle: {e}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Ruta para registro de nuevos usuarios"""
    if request.method == 'POST':
        nombre_completo = request.form.get('nombre_completo')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        confirmar_contrasena = request.form.get('confirmar_contrasena')
        rol_id = int(request.form.get('rol_id', 1))  # Default: Usuario
        
        # Validaciones
        if not all([nombre_completo, correo, contrasena, confirmar_contrasena]):
            flash('Todos los campos son obligatorios', 'error')
            return render_template('registro.html')
        
        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('registro.html')
        
        if len(contrasena) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('registro.html')
        
        # Verificar si el correo ya existe
        try:
            usuario_existente = controlUsuarios.buscar_por_correo(correo)
            if usuario_existente:
                flash('El correo electrónico ya está registrado', 'error')
                return render_template('registro.html')
            
            # Insertar usuario con hash de contraseña
            if controlUsuarios.insertar(nombre_completo, correo, contrasena, rol_id):
                flash('Usuario registrado correctamente', 'success')
                return redirect(url_for('login'))
            else:
                flash('Error al registrar usuario', 'error')
                
        except Exception as e:
            print(f"Error en registro: {e}")
            flash('Error interno del servidor', 'error')
    
    return render_template('registro.html')

@app.route('/asignar_diagnostico', methods=['GET', 'POST'])
def asignar_diagnostico():
    # Verificación de sesión

    # Verificar que sea técnico
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    usuario_id = int(session['user_id'])
    
    # Mostrar formulario - solo incidentes en estado 'A' asignados al técnico
    control_incidentes = ControlIncidentes()
    incidentes = control_incidentes.obtener_incidentes_sin_diagnostico(id_usuario=usuario_id)

    # Procesar formulario
    if request.method == 'POST':
        id_incidente = request.form.get('id_incidente')
        descripcion = request.form.get('descripcion')
        causa_raiz = request.form.get('causa_raiz')
        solucion = request.form.get('solucion')
        comentario = request.form.get('comentario')

        if not (id_incidente and descripcion and causa_raiz):
            flash('Completa todos los campos obligatorios (Descripción y Causa Raíz).', 'error')
            return redirect(url_for('asignar_diagnostico'))
        
        # Solución propuesta es opcional, puede ser None o vacío
        if not solucion:
            solucion = None

        # Verificar primero si el usuario ya tiene un diagnóstico pendiente para este incidente
        control_diagnostico = ControlDiagnosticos()
        if control_diagnostico.tiene_diagnostico_pendiente(id_incidente, usuario_id):
            flash('Ya tienes un diagnóstico pendiente de revisión para este incidente. Espera a que sea aceptado o rechazado antes de agregar otro.', 'error')
            return redirect(url_for('asignar_diagnostico'))
        
        # Verificar que el técnico esté en el equipo técnico, si no, agregarlo
        usuario_id = int(session.get('user_id'))
        equipo = ControlIncidentes.obtener_equipo_tecnico(id_incidente)
        esta_en_equipo = any(m['id_usuario'] == usuario_id for m in equipo)
        
        if not esta_en_equipo:
            # Verificar si el incidente está asignado directamente al técnico
            incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
            if incidente and incidente.get('id_tecnico_asignado') == usuario_id:
                # Si está asignado directamente, agregarlo directamente a EQUIPO_TECNICO
                exito_equipo = ControlIncidentes.agregar_a_equipo_tecnico(id_incidente, usuario_id, es_responsable=False)
                if not exito_equipo:
                    flash('Error al agregar al equipo técnico', 'error')
                    return redirect(url_for('asignar_diagnostico'))
            else:
                # Si no está asignado directamente, usar tomar_incidente_disponible (solo para M y B)
                resultado_tomar = ControlIncidentes.tomar_incidente_disponible(id_incidente, usuario_id)
                if not resultado_tomar.get('exito'):
                    flash(f'Error: {resultado_tomar.get("mensaje", "No se pudo agregar al equipo técnico")}', 'error')
                    return redirect(url_for('asignar_diagnostico'))
        
        exito = control_diagnostico.insertar_diagnostico(
            id_incidente=id_incidente,
            descripcion=descripcion,
            causa_raiz=causa_raiz,
            solucion=solucion,
            comentario=comentario,
            usuario_id=usuario_id  # registra quién lo hizo
        )

        if exito:
            flash('Diagnóstico asignado correctamente.', 'success')
            return redirect(url_for('gestion_incidentes'))
        else:
            flash('Error al asignar el diagnóstico.', 'error')

    return render_template('agregarDiagnostico.html', incidentes=incidentes)

@app.route('/gestion_diagnostico', methods=['GET'])
def gestion_diagnostico():
    """Gestión de diagnósticos - Solo técnicos del área 1 pueden ver sus propios diagnósticos"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    id_usuario = int(session['user_id'])
    
    # Verificar que sea técnico del área 1
    if not controlUsuarios.es_tecnico_area_1(id_usuario):
        flash('Solo los técnicos del área de Desarrollo y Control de Gestión pueden acceder a esta sección', 'error')
        return redirect(url_for('gestion_incidentes'))
    
    titulo = request.args.get('titulo', '')
    causa = request.args.get('causa', '')

    control_diag = ControlDiagnosticos()
    diagnosticos = control_diag.obtener_diagnosticos_filtrados(id_usuario, titulo, causa)

    return render_template('gestionDiagnostico.html', diagnosticos=diagnosticos, titulo=titulo, causa=causa)




@app.route('/usuarios')
def listar_usuarios():
    """Ruta para listar usuarios (solo para administradores)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_role') != 3:  # 3 = Administrador
        flash('No tiene permisos para acceder a esta sección', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        usuarios = controlUsuarios.buscar_todos()
    except Exception as e:
        print(f"Error al obtener usuarios: {e}")
        usuarios = []
        flash('Error al cargar los usuarios', 'error')
    
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/<user_id>/estado/<int:nuevo_estado>')
def cambiar_estado_usuario(user_id, nuevo_estado):
    """Cambiar estado de un usuario"""
    if 'user_id' not in session or session.get('user_role') != 3:
        flash('No tiene permisos para realizar esta acción', 'error')
        return redirect(url_for('dashboard'))
    
    # Convertir nuevo_estado a boolean
    activo = nuevo_estado == 1
    
    try:
        if controlUsuarios.cambiar_estado_usuario(user_id, activo):
            estado_texto = "activado" if activo else "desactivado"
            flash(f'Usuario {estado_texto} correctamente', 'success')
        else:
            flash('Error al cambiar el estado del usuario', 'error')
    except Exception as e:
        print(f"Error al cambiar estado de usuario: {e}")
        flash('Error interno del servidor', 'error')
    
    return redirect(url_for('listar_usuarios'))

@app.route('/usuarios/<user_id>/eliminar')
def eliminar_usuario(user_id):
    """Eliminar un usuario"""
    if 'user_id' not in session or session.get('user_role') != 3:
        flash('No tiene permisos para realizar esta acción', 'error')
        return redirect(url_for('dashboard'))
    
    # No permitir que el admin se elimine a sí mismo
    if user_id == session.get('user_id'):
        flash('No puede eliminarse a sí mismo', 'error')
        return redirect(url_for('listar_usuarios'))
    
    try:
        if controlUsuarios.eliminar_usuario(user_id):
            flash('Usuario eliminado correctamente', 'success')
        else:
            flash('Error al eliminar el usuario', 'error')
    except Exception as e:
        print(f"Error al eliminar usuario: {e}")
        flash('Error interno del servidor', 'error')
    
    return redirect(url_for('listar_usuarios'))

@app.route('/crear_admin')
def crear_admin():
    """Ruta para crear usuario administrador inicial (solo usar una vez)"""
    try:
        # Verificar si ya existe un administrador
        usuarios = controlUsuarios.buscar_todos()
        admin_existe = any(usuario.get('rol_id') == 3 for usuario in usuarios or [])
        
        if admin_existe:
            flash('Ya existe un usuario administrador', 'info')
            return redirect(url_for('login'))
        
        # Crear usuario administrador
        if controlUsuarios.insertar("Administrador del Sistema", "admin@sistema.com", "admin123", 3):
            flash('Usuario administrador creado: admin@sistema.com / admin123', 'success')
        else:
            flash('Error al crear usuario administrador', 'error')
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('login'))

# Context processor para hacer variables disponibles en todos los templates
@app.context_processor
def inject_user():
    user_id = session.get('user_id')
    user_role = session.get('user_role')
    
    # Obtener información del rol si hay usuario logueado
    es_jefe = False
    es_jefe_ti = False
    es_jefe_ti_rol_1 = False
    es_tecnico = False
    es_tecnico_area_1 = False
    es_rol_firmante = False
    puede_crear_contratos = False
    tipo_rol = None
    notificaciones_no_leidas = 0
    
    if user_id and user_role:
        try:
            usuario = controlUsuarios.buscar_por_ID(int(user_id))
            if usuario:
                from controllers.controlador_rol import ControlRol
                rol = ControlRol.buscar_por_IDRol(usuario['id_rol'])
                if rol:
                    tipo_rol = rol.get('tipo')
                    es_jefe = tipo_rol == 'J'
                    es_jefe_ti = controlUsuarios.es_jefe_ti(int(user_id))
                    es_jefe_ti_rol_1 = controlUsuarios.es_jefe_ti_rol_1(int(user_id))
                    es_tecnico = tipo_rol == 'T'
                    es_tecnico_area_1 = controlUsuarios.es_tecnico_area_1(int(user_id))
                    es_rol_firmante = controlUsuarios.es_rol_firmante(int(user_id))
                    puede_crear_contratos = controlUsuarios.puede_crear_contratos(int(user_id))
                
                # Contar notificaciones no leídas
                notificaciones_no_leidas = ControlNotificaciones.contar_no_leidas(int(user_id))
                
                # Obtener id_rol para el sidebar
                current_user_role = usuario.get('id_rol')
        except Exception as e:
            print(f"Error en context processor: {e}")
    
    # Obtener id_rol para el sidebar
    id_rol_usuario = None
    if user_id and user_role:
        try:
            usuario = controlUsuarios.buscar_por_ID(int(user_id))
            if usuario:
                id_rol_usuario = usuario.get('id_rol')
        except:
            pass
    
    return dict(
        current_user_id=user_id,
        current_user_name=session.get('user_name'),
        current_user_role=user_role,
        current_user_role_id=id_rol_usuario,
        current_user_role_name=session.get('user_role_name'),
        es_jefe=es_jefe,
        es_jefe_ti=es_jefe_ti,
        es_jefe_ti_rol_1=es_jefe_ti_rol_1,
        es_tecnico=es_tecnico,
        es_tecnico_area_1=es_tecnico_area_1,
        es_rol_firmante=es_rol_firmante,
        puede_crear_contratos=puede_crear_contratos,
        tipo_rol=tipo_rol,
        notificaciones_no_leidas=notificaciones_no_leidas
    )
@app.route('/gestion_mttr')
def gestion_mttr():
    """Ruta principal para mostrar métricas MTTR - SOLO DATOS REALES"""
    try:
        print("🔍 Cargando métricas MTTR desde base de datos...")
        
        control_incidentes = ControlIncidentes()
        
        # Obtener datos reales de MTTR
        mttr_data = control_incidentes.obtener_mttr_completo_por_categoria()
        print(f"✅ Datos MTTR obtenidos: {len(mttr_data)} categorías")
        
        # Obtener estadísticas reales
        estadisticas = control_incidentes.obtener_estadisticas_mttr()
        print(f"✅ Estadísticas calculadas: MTTR global = {estadisticas.get('mttr_global', 0)}")
        
        # Obtener categorías disponibles directamente de la BD
        categorias_disponibles = control_incidentes.obtener_categorias_disponibles()
        print(f"📋 Categorías en BD: {categorias_disponibles}")
        
        # Obtener datos adicionales para gráficos
        tendencia_data = control_incidentes.obtener_tendencia_mttr()
        distribucion_data = control_incidentes.obtener_distribucion_incidentes()
        
        return render_template(
            'reportesMTTR.html', 
            mttr_data=mttr_data,
            estadisticas=estadisticas,
            categorias_disponibles=categorias_disponibles,
            tendencia_data=tendencia_data,
            distribucion_data=distribucion_data
        )
        
    except Exception as e:
        print(f"❌ Error al cargar métricas MTTR => {e}")
        import traceback
        traceback.print_exc()
        
        # En caso de error, mostrar datos vacíos en lugar de datos de ejemplo
        flash('Error al cargar datos. Verifica la conexión a la base de datos.', 'error')
        
        return render_template(
            'reportesMTTR.html', 
            mttr_data=[],
            estadisticas={
                'mttr_global': 0,
                'total_incidentes': 0,
                'mejor_categoria': 'N/A',
                'mejor_mttr': 0,
                'categoria_critica': 'N/A',
                'crit_mttr': 0
            },
            categorias_disponibles=[],
            tendencia_data=[],
            distribucion_data=[]
        )

# Tu ruta API también se mantiene igual, ya funciona correctamente
@app.route('/api/mttr/filtrar')
def api_filtrar_mttr():
    """API para filtrar datos de MTTR dinámicamente - SOLO DATOS REALES"""
    try:
        # Obtener parámetros de filtro
        categoria = request.args.get('categoria', '').strip()
        periodo = int(request.args.get('periodo', 6))
        
        control_incidentes = ControlIncidentes()
        
        # Obtener datos filtrados de la BD
        if categoria and categoria != 'Todas':
            mttr_data = control_incidentes.obtener_mttr_filtrado(
                categoria=categoria, 
                periodo_meses=periodo
            )
        else:
            mttr_data = control_incidentes.obtener_mttr_filtrado(
                periodo_meses=periodo
            )
        
        # Calcular estadísticas de los datos filtrados
        if mttr_data:
            mttr_global = sum(float(item['mttr_horas']) for item in mttr_data) / len(mttr_data)
            total_incidentes = sum(item['total_incidentes'] for item in mttr_data)
            
            mejor = min(mttr_data, key=lambda x: float(x['mttr_horas']))
            critica = max(mttr_data, key=lambda x: float(x['mttr_horas']))
            
            estadisticas = {
                'mttr_global': round(mttr_global, 2),
                'total_incidentes': total_incidentes,
                'mejor_categoria': mejor['categoria'],
                'mejor_mttr': mejor['mttr_horas'],
                'categoria_critica': critica['categoria'],
                'crit_mttr': critica['mttr_horas']
            }
        else:
            estadisticas = {
                'mttr_global': 0,
                'total_incidentes': 0,
                'mejor_categoria': 'N/A',
                'mejor_mttr': 0,
                'categoria_critica': 'N/A',
                'crit_mttr': 0
            }
        
        return jsonify({
            'success': True,
            'mttr_data': mttr_data,
            'estadisticas': estadisticas
        })
   
    except Exception as e:
        print(f"Error en API filtrar MTTR => {e}")
        return jsonify({
            'success': False, 
            'error': 'Error al filtrar los datos'
        }), 500

# ========== RUTAS PARA JEFE DE TI ==========

@app.route('/gestion_pendientes')
def gestion_pendientes():
    """Vista para que el jefe de TI gestione incidentes pendientes"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Verificar que sea jefe de TI
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        flash('No tiene permisos para acceder a esta sección', 'error')
        return redirect(url_for('gestion_incidentes'))
    
    incidentes_pendientes = ControlIncidentes.obtener_incidentes_pendientes_jefe_ti()
    
    return render_template('gestionPendientes.html', 
                         incidentes=incidentes_pendientes,
                         user_name=session.get('user_name'))

@app.route('/api/incidente/<int:id_incidente>/detalles', methods=['GET'])
def api_detalles_incidente(id_incidente):
    """Obtener detalles completos de un incidente incluyendo evidencias e historial"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    # Permitir acceso a cualquier usuario autenticado que pueda ver incidentes
    
    try:
        # Obtener incidente con área directamente de la consulta
        from ConexionBD import get_connection
        conexion = get_connection()
        if not conexion:
            return jsonify({'error': 'Error de conexión'}), 500
        
        sql = """
            SELECT 
                i.id_incidente,
                i.titulo,
                i.descripcion,
                i.fecha_reporte,
                i.nivel,
                a.nombre as area,
                u.nombre || ' ' || u.ape_pat || ' ' || u.ape_mat as reportado_por,
                c.nombre as categoria
            FROM INCIDENTE i
            LEFT JOIN USUARIO u ON i.id_usuario = u.id_usuario
            LEFT JOIN ROL r ON u.id_rol = r.id_rol
            LEFT JOIN AREA a ON r.id_area = a.id_area
            LEFT JOIN CATEGORIA c ON i.id_categoria = c.id_categoria
            WHERE i.id_incidente = %s
        """
        
        with conexion.cursor() as cursor:
            cursor.execute(sql, (id_incidente,))
            resultado = cursor.fetchone()
        
        conexion.close()
        
        if not resultado:
            return jsonify({'error': 'Incidente no encontrado'}), 404
        
        evidencias = ControlIncidentes.obtener_evidencias_incidente(id_incidente)
        historial = ControlIncidentes.obtener_historial_incidente(id_incidente)
        
        # Obtener estado actual del incidente
        estado_actual = resultado[4] if len(resultado) > 4 else None
        estado_map = {
            'P': 'Pendiente',
            'A': 'Activo',
            'T': 'Terminado',
            'C': 'Cancelado'
        }
        estado_actual_texto = estado_map.get(estado_actual, estado_actual) if estado_actual else 'Desconocido'
        
        # Verificar si el usuario actual tiene diagnóstico pendiente
        from controllers.control_diagnostico import ControlDiagnosticos
        usuario_id = int(session['user_id'])
        tiene_diagnostico_pendiente = ControlDiagnosticos.tiene_diagnostico_pendiente(
            id_incidente, 
            usuario_id
        )
        
        return jsonify({
            'success': True,
            'incidente': {
                'id_incidente': resultado[0],
                'titulo': resultado[1],
                'descripcion': resultado[2],
                'fecha_reporte': resultado[3].isoformat() if resultado[3] else None,
                'nivel': resultado[4] if len(resultado) > 4 else None,
                'estado': estado_actual_texto,
                'estado_corto': estado_actual,
                'area': resultado[5],
                'reportado_por': resultado[6],
                'categoria': resultado[7]
            },
            'evidencias': evidencias,
            'historial': historial,
            'tiene_diagnostico_pendiente': tiene_diagnostico_pendiente
        })
    except Exception as e:
        print(f"Error en api_detalles_incidente: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Error al obtener detalles'}), 500

@app.route('/api/incidente/<int:id_incidente>/aceptar', methods=['POST'])
def api_aceptar_incidente(id_incidente):
    """Aceptar incidente (cambiar a estado A)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        return jsonify({'success': False, 'message': 'No tiene permisos'}), 403
    
    exito = ControlIncidentes.cambiar_estado_jefe_ti(id_incidente, 'A')
    if exito:
        # Notificar al jefe que reportó
        incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
        if incidente:
            ControlNotificaciones.notificar_estado_incidente(id_incidente, 'A', incidente['id_usuario'])
        return jsonify({'success': True, 'message': 'Incidente aceptado correctamente'})
    else:
        return jsonify({'success': False, 'message': 'Error al aceptar incidente'}), 500

@app.route('/api/incidente/<int:id_incidente>/cancelar', methods=['POST'])
def api_cancelar_incidente(id_incidente):
    """Cancelar incidente (cambiar a estado C)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        return jsonify({'success': False, 'message': 'No tiene permisos'}), 403
    
    exito = ControlIncidentes.cambiar_estado_jefe_ti(id_incidente, 'C')
    if exito:
        # Notificar al jefe que reportó
        incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
        if incidente:
            ControlNotificaciones.notificar_estado_incidente(id_incidente, 'C', incidente['id_usuario'])
        return jsonify({'success': True, 'message': 'Incidente cancelado correctamente'})
    else:
        return jsonify({'success': False, 'message': 'Error al cancelar incidente'}), 500

@app.route('/api/incidente/<int:id_incidente>/evidencias', methods=['POST'])
def api_agregar_evidencias(id_incidente):
    """Agregar evidencias (imágenes) a un incidente existente"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    # Verificar que el incidente existe
    incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
    if not incidente:
        return jsonify({'success': False, 'message': 'Incidente no encontrado'}), 404
    
    # Verificar permisos: el usuario que reportó el incidente o técnicos asignados pueden agregar evidencias
    id_usuario = int(session['user_id'])
    puede_agregar = False
    
    # El usuario que reportó puede agregar evidencias
    if incidente.get('id_usuario') == id_usuario:
        puede_agregar = True
    # Los técnicos asignados también pueden agregar evidencias
    elif controlUsuarios.es_tecnico_area_1(id_usuario):
        puede_agregar = True
    # El jefe de TI también puede
    elif controlUsuarios.es_jefe_ti(id_usuario):
        puede_agregar = True
    
    if not puede_agregar:
        return jsonify({'success': False, 'message': 'No tiene permisos para agregar evidencias a este incidente'}), 403
    
    try:
        # Obtener evidencias existentes para verificar límite
        evidencias_existentes = ControlIncidentes.obtener_evidencias_incidente(id_incidente)
        cantidad_existente = len(evidencias_existentes)
        max_evidencias = 5
        
        if cantidad_existente >= max_evidencias:
            return jsonify({
                'success': False, 
                'message': f'Ya se alcanzó el límite de {max_evidencias} evidencias por incidente'
            }), 400
        
        # Procesar archivos de evidencias
        if 'evidencias' not in request.files:
            return jsonify({'success': False, 'message': 'No se recibieron archivos'}), 400
        
        archivos = request.files.getlist('evidencias')
        archivos_subidos = 0
        errores = []
        
        print(f"📁 Agregando evidencias al incidente {id_incidente}. Total de archivos recibidos: {len(archivos)}")
        
        # Filtrar archivos válidos y calcular cuántos se pueden agregar
        archivos_validos = []
        espacios_disponibles = max_evidencias - cantidad_existente
        
        for archivo in archivos:
            if archivo and archivo.filename:
                archivos_validos.append(archivo)
                if len(archivos_validos) >= espacios_disponibles:
                    break
        
        print(f"📁 Archivos válidos a procesar: {len(archivos_validos)} (espacios disponibles: {espacios_disponibles})")
        
        for idx, archivo in enumerate(archivos_validos):
            nombre_archivo = archivo.filename
            print(f"\n🔄 Procesando archivo {idx + 1}/{len(archivos_validos)}: {nombre_archivo}")
            
            # Leer el archivo completo en memoria primero
            try:
                from io import BytesIO
                archivo.seek(0)
                archivo_data = archivo.read()
                tamaño = len(archivo_data)
                print(f"   Tamaño: {tamaño / (1024*1024):.2f} MB")
            except Exception as e:
                print(f"❌ Error al leer archivo {nombre_archivo}: {e}")
                errores.append(f"Error al leer {nombre_archivo}")
                continue
            
            # Validar que sea imagen
            if not nombre_archivo.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                print(f"❌ Archivo {nombre_archivo} no es una imagen válida")
                errores.append(f"{nombre_archivo} no es una imagen válida")
                continue
            
            # Validar tamaño (10MB)
            if tamaño > MAX_FILE_SIZE:
                print(f"❌ Archivo {nombre_archivo} excede 10MB ({tamaño / (1024*1024):.2f}MB)")
                errores.append(f"{nombre_archivo} excede 10MB")
                continue
            
            if tamaño == 0:
                print(f"❌ Archivo {nombre_archivo} está vacío")
                errores.append(f"{nombre_archivo} está vacío")
                continue
            
            try:
                # Crear un nuevo objeto file-like desde los datos en memoria
                archivo_stream = BytesIO(archivo_data)
                archivo_stream.name = nombre_archivo
                
                print(f"   ⬆️ Subiendo a Cloudinary...")
                
                # Subir a Cloudinary
                url_archivo = subir_a_cloudinary(archivo_stream, id_incidente)
                
                if url_archivo:
                    # Guardar URL de Cloudinary en la base de datos
                    if controlEvidencias.insertar(id_incidente, url_archivo):
                        archivos_subidos += 1
                        print(f"   ✅ Evidencia {archivos_subidos} agregada exitosamente: {nombre_archivo}")
                    else:
                        print(f"   ❌ Error al guardar URL en BD: {nombre_archivo}")
                        errores.append(f"Error al guardar {nombre_archivo} en la base de datos")
                else:
                    print(f"   ❌ Error: No se pudo subir {nombre_archivo} a Cloudinary")
                    errores.append(f"Error al subir {nombre_archivo} a Cloudinary")
            except Exception as e:
                print(f"   ❌ Error al procesar evidencia {nombre_archivo}: {e}")
                import traceback
                traceback.print_exc()
                errores.append(f"Error al procesar {nombre_archivo}: {str(e)}")
                continue
        
        print(f"\n📊 Resumen: {archivos_subidos} de {len(archivos_validos)} archivos agregados exitosamente")
        
        if archivos_subidos > 0:
            mensaje = f'Se agregaron {archivos_subidos} evidencia(s) exitosamente'
            if errores:
                mensaje += f'. Errores: {len(errores)} archivo(s) no se pudieron agregar'
            return jsonify({
                'success': True, 
                'message': mensaje,
                'archivos_subidos': archivos_subidos,
                'errores': errores if errores else None
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'No se pudo agregar ninguna evidencia',
                'errores': errores
            }), 400
            
    except Exception as e:
        print(f"Error en api_agregar_evidencias: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error inesperado: {str(e)}'}), 500

@app.route('/asignar_prioridad/<int:id_incidente>', methods=['GET', 'POST'])
def asignar_prioridad(id_incidente):
    """Asignar nivel de prioridad a un incidente aceptado"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        flash('No tiene permisos', 'error')
        return redirect(url_for('gestion_incidentes'))
    
    if request.method == 'POST':
        nivel = request.form.get('nivel')
        if nivel not in ['B', 'M', 'A', 'C']:
            flash('Nivel de prioridad inválido', 'error')
            return redirect(url_for('asignar_prioridad', id_incidente=id_incidente))
        
        exito = ControlIncidentes.asignar_nivel_prioridad(id_incidente, nivel)
        if exito:
            flash('Prioridad asignada correctamente', 'success')
            # Si es Alto o Crítico, redirigir a asignación de técnicos
            if nivel in ['A', 'C']:
                return redirect(url_for('asignar_tecnicos', id_incidente=id_incidente))
            else:
                return redirect(url_for('gestion_pendientes'))
        else:
            flash('Error al asignar prioridad', 'error')
    
    incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
    if not incidente or incidente.get('estado') != 'A':
        flash('Incidente no encontrado o no está aceptado', 'error')
        return redirect(url_for('gestion_pendientes'))
    
    return render_template('asignarPrioridad.html', incidente=incidente)

@app.route('/asignar_tecnicos/<int:id_incidente>', methods=['GET', 'POST'])
def asignar_tecnicos(id_incidente):
    """Asignar técnicos a un incidente Alto o Crítico"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        flash('No tiene permisos', 'error')
        return redirect(url_for('gestion_incidentes'))
    
    incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
    if not incidente or incidente.get('estado') != 'A' or incidente.get('nivel') not in ['A', 'C']:
        flash('Este incidente no requiere asignación de técnicos', 'error')
        return redirect(url_for('gestion_pendientes'))
    
    if request.method == 'POST':
        tipo_asignacion = request.form.get('tipo_asignacion')  # 'individual' o 'grupo'
        
        if tipo_asignacion == 'individual':
            id_tecnico = request.form.get('id_tecnico')
            if id_tecnico:
                exito = ControlIncidentes.asignar_tecnico_individual(id_incidente, int(id_tecnico))
                if exito:
                    # Obtener nombre del técnico
                    tecnico = controlUsuarios.buscar_por_ID(int(id_tecnico))
                    nombre_tecnico = f"{tecnico['nombre']} {tecnico['ape_pat']}" if tecnico else "un técnico"
                    
                    # Notificar al técnico
                    ControlNotificaciones.notificar_asignacion_tecnico(id_incidente, int(id_tecnico), False)
                    # Notificar al usuario que reportó el incidente
                    ControlNotificaciones.notificar_asignacion_a_reportante(id_incidente, int(id_tecnico), nombre_tecnico, False)
                    flash('Técnico asignado correctamente', 'success')
                else:
                    flash('Error al asignar técnico', 'error')
        elif tipo_asignacion == 'grupo':
            tecnicos = request.form.getlist('tecnicos[]')
            responsable = request.form.get('responsable')
            
            if not tecnicos or not responsable:
                flash('Debe seleccionar al menos un técnico y un responsable', 'error')
            else:
                exito = True
                primer_tecnico = tecnicos[0] if tecnicos else None
                for id_tecnico in tecnicos:
                    es_responsable = (id_tecnico == responsable)
                    if ControlIncidentes.agregar_a_equipo_tecnico(id_incidente, int(id_tecnico), es_responsable):
                        # Notificar a cada técnico
                        ControlNotificaciones.notificar_asignacion_tecnico(id_incidente, int(id_tecnico), True)
                    else:
                        exito = False
                
                if exito:
                    # Notificar al usuario que reportó sobre la asignación del equipo (una sola vez)
                    if primer_tecnico:
                        ControlNotificaciones.notificar_asignacion_a_reportante(id_incidente, int(primer_tecnico), "", True)
                    flash('Equipo técnico asignado correctamente', 'success')
                else:
                    flash('Error al asignar algunos técnicos', 'error')
        
        return redirect(url_for('gestion_pendientes'))
    
    tecnicos = controlUsuarios.obtener_tecnicos()
    equipo_actual = ControlIncidentes.obtener_equipo_tecnico(id_incidente)
    
    return render_template('asignarTecnicos.html', 
                         incidente=incidente,
                         tecnicos=tecnicos,
                         equipo_actual=equipo_actual)

# ========== RUTAS PARA TÉCNICOS ==========

@app.route('/incidentes_disponibles')
def incidentes_disponibles():
    """Vista para que técnicos vean y tomen incidentes disponibles"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Verificar que sea técnico (tipo 'T')
    usuario = controlUsuarios.buscar_por_ID(int(session['user_id']))
    if not usuario:
        return redirect(url_for('login'))
    
    # Obtener rol del usuario
    from controllers.controlador_rol import ControlRol
    rol = ControlRol.buscar_por_IDRol(usuario['id_rol'])
    if not rol or rol.get('tipo') != 'T':
        flash('Solo los técnicos pueden acceder a esta sección', 'error')
        return redirect(url_for('gestion_incidentes'))
    
    id_usuario = int(session['user_id'])
    incidentes = ControlIncidentes.obtener_incidentes_disponibles_tecnicos(id_usuario)
    tickets_activos = controlUsuarios.contar_tickets_activos(id_usuario)
    tickets_equipo = controlUsuarios.contar_tickets_en_equipo(id_usuario)
    
    return render_template('incidentesDisponibles.html',
                         incidentes=incidentes,
                         tickets_activos=tickets_activos + tickets_equipo,
                         max_tickets=3)

@app.route('/api/incidente/<int:id_incidente>/tomar', methods=['POST'])
def api_tomar_incidente(id_incidente):
    """Tomar un incidente disponible"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    resultado = ControlIncidentes.tomar_incidente_disponible(id_incidente, int(session['user_id']))
    
    if resultado.get('exito'):
        return jsonify({'success': True, 'message': resultado['mensaje']})
    else:
        return jsonify({'success': False, 'message': resultado['mensaje']}), 400

@app.route('/api/incidente/<int:id_incidente>/terminar', methods=['POST'])
def api_terminar_incidente(id_incidente):
    """Terminar incidente (cambiar a estado T) - Solo jefe de TI"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        return jsonify({'success': False, 'message': 'No tiene permisos'}), 403
    
    exito = ControlIncidentes.actualizar_estado(id_incidente, 'T')
    if exito == 0:
        # Notificar al jefe que reportó y a los técnicos asignados
        incidente = ControlIncidentes.buscar_por_IDIncidente(id_incidente)
        if incidente:
            # Notificar al jefe que reportó
            ControlNotificaciones.notificar_estado_incidente(id_incidente, 'T', incidente['id_usuario'])
            
            # Notificar a técnicos asignados
            equipo = ControlIncidentes.obtener_equipo_tecnico(id_incidente)
            for miembro in equipo:
                ControlNotificaciones.crear_notificacion(
                    id_usuario=miembro['id_usuario'],
                    titulo=f"Incidente #{id_incidente} Terminado",
                    mensaje=f"El incidente '{incidente['titulo']}' ha sido terminado",
                    tipo="incidente",
                    id_referencia=id_incidente
                )
            
            # Si hay técnico asignado directamente
            if incidente.get('id_tecnico_asignado'):
                ControlNotificaciones.crear_notificacion(
                    id_usuario=incidente['id_tecnico_asignado'],
                    titulo=f"Incidente #{id_incidente} Terminado",
                    mensaje=f"El incidente '{incidente['titulo']}' ha sido terminado",
                    tipo="incidente",
                    id_referencia=id_incidente
                )
        
        return jsonify({'success': True, 'message': 'Incidente terminado correctamente'})
    else:
        return jsonify({'success': False, 'message': 'Error al terminar incidente'}), 500

# ========== RUTAS PARA NOTIFICACIONES ==========

@app.route('/notificaciones')
def ver_notificaciones():
    """Vista para ver todas las notificaciones del usuario"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = int(session['user_id'])
    notificaciones = ControlNotificaciones.obtener_notificaciones_usuario(user_id)
    
    return render_template('notificaciones.html', 
                         notificaciones=notificaciones,
                         user_name=session.get('user_name'))

@app.route('/api/notificaciones')
def api_notificaciones():
    """API para obtener notificaciones no leídas (para AJAX)"""
    if 'user_id' not in session:
        return jsonify({'notificaciones': [], 'count': 0})
    
    user_id = int(session['user_id'])
    notificaciones = ControlNotificaciones.obtener_notificaciones_usuario(user_id, no_leidas=True)
    
    # Formatear fechas para JSON
    for notif in notificaciones:
        if notif.get('fecha'):
            notif['fecha'] = notif['fecha'].isoformat() if hasattr(notif['fecha'], 'isoformat') else str(notif['fecha'])
    
    return jsonify({
        'notificaciones': notificaciones,
        'count': len(notificaciones)
    })

@app.route('/api/notificacion/<int:id_notificacion>/leer', methods=['POST'])
def api_marcar_leida(id_notificacion):
    """Marca una notificación como leída"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    exito = ControlNotificaciones.marcar_como_leida(id_notificacion, int(session['user_id']))
    if exito:
        return jsonify({'success': True, 'message': 'Notificación marcada como leída'})
    else:
        return jsonify({'success': False, 'message': 'Error al marcar notificación'}), 500

@app.route('/api/notificaciones/leer-todas', methods=['POST'])
def api_marcar_todas_leidas():
    """Marca todas las notificaciones como leídas"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    exito = ControlNotificaciones.marcar_todas_como_leidas(int(session['user_id']))
    if exito:
        return jsonify({'success': True, 'message': 'Todas las notificaciones marcadas como leídas'})
    else:
        return jsonify({'success': False, 'message': 'Error al marcar notificaciones'}), 500

# ========== MÓDULO DE PREDICCIONES CON IA ==========

@app.route('/predicciones_ia')
def predicciones_ia():
    """Vista principal del módulo de predicciones con IA"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Solo jefes de TI pueden ver predicciones
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        flash('No tiene permisos para acceder a esta sección', 'error')
        return redirect(url_for('gestion_incidentes'))
    
    return render_template('predicciones_ia.html', 
                         user_name=session.get('user_name'))

@app.route('/api/predicciones/categorias', methods=['GET'])
def api_predicciones_categorias():
    """API para obtener predicciones de incidentes por categoría"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        return jsonify({'error': 'No tiene permisos'}), 403
    
    try:
        meses_historico = int(request.args.get('meses', 3))
        predicciones = ControlPredicciones.predecir_incidentes_por_categoria(meses_historico)
        
        return jsonify({
            'success': True,
            'predicciones': predicciones
        })
    except Exception as e:
        print(f"Error en API predicciones categorías => {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predicciones/tiempo-resolucion', methods=['GET'])
def api_predicciones_tiempo():
    """API para predecir tiempo de resolución"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        return jsonify({'error': 'No tiene permisos'}), 403
    
    try:
        id_categoria = request.args.get('categoria', None)
        nivel = request.args.get('nivel', 'M')
        
        prediccion = ControlPredicciones.predecir_tiempo_resolucion(id_categoria, nivel)
        
        return jsonify({
            'success': True,
            'prediccion': prediccion
        })
    except Exception as e:
        print(f"Error en API predicción tiempo => {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predicciones/patrones-temporales', methods=['GET'])
def api_patrones_temporales():
    """API para analizar patrones temporales"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        return jsonify({'error': 'No tiene permisos'}), 403
    
    try:
        meses = int(request.args.get('meses', 3))
        patrones = ControlPredicciones.analizar_patrones_temporales(meses)
        
        return jsonify({
            'success': True,
            'patrones': patrones
        })
    except Exception as e:
        print(f"Error en API patrones temporales => {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predicciones/anomalias', methods=['GET'])
def api_detectar_anomalias():
    """API para detectar anomalías en incidentes"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        return jsonify({'error': 'No tiene permisos'}), 403
    
    try:
        threshold = float(request.args.get('threshold', 2.0))
        anomalias = ControlPredicciones.detectar_anomalias(threshold)
        
        return jsonify({
            'success': True,
            'anomalias': anomalias
        })
    except Exception as e:
        print(f"Error en API detección anomalías => {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predicciones/carga-tecnicos', methods=['GET'])
def api_carga_tecnicos():
    """API para predecir carga de trabajo de técnicos"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        return jsonify({'error': 'No tiene permisos'}), 403
    
    try:
        dias = int(request.args.get('dias', 7))
        predicciones = ControlPredicciones.predecir_carga_tecnicos(dias)
        
        return jsonify({
            'success': True,
            'predicciones': predicciones
        })
    except Exception as e:
        print(f"Error en API carga técnicos => {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/predicciones/recomendaciones', methods=['GET'])
def api_recomendaciones():
    """API para obtener recomendaciones basadas en predicciones"""
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    if not controlUsuarios.es_jefe_ti(int(session['user_id'])):
        return jsonify({'error': 'No tiene permisos'}), 403
    
    try:
        recomendaciones = ControlPredicciones.obtener_recomendaciones()
        
        return jsonify({
            'success': True,
            'recomendaciones': recomendaciones
        })
    except Exception as e:
        print(f"Error en API recomendaciones => {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# RUTAS PARA GESTIÓN DE CONTRATOS Y FIRMAS
# ============================================

@app.route('/contratos')
def contratos():
    """Vista principal de contratos - Accesible para todos (cada uno verá lo que le corresponde)"""
    if 'user_id' not in session:
        flash('Por favor inicia sesión', 'error')
        return redirect(url_for('login'))
    
    id_usuario = int(session['user_id'])
    
    # Verificar roles y permisos
    es_jefe_ti = controlUsuarios.es_jefe_ti_rol_1(id_usuario)
    puede_crear = controlUsuarios.puede_crear_contratos(id_usuario)
    
    # Todos los usuarios tienen acceso (verán sus contratos pendientes)
    # La lógica de qué pueden ver se maneja en el template y en las APIs
    
    return render_template(
        'gestionContratos.html',
        es_jefe_ti=es_jefe_ti,
        puede_crear_contratos=puede_crear
    )

@app.route('/crear_contrato', methods=['GET', 'POST'])
def crear_contrato():
    """Crear un nuevo contrato - Accesible para TODOS los jefes de CUALQUIER área"""
    if 'user_id' not in session:
        flash('Por favor inicia sesión', 'error')
        return redirect(url_for('login'))
    
    # Todos los jefes (tipo 'J') de cualquier área pueden crear contratos
    if not controlUsuarios.puede_crear_contratos(int(session['user_id'])):
        flash('No tienes permisos para crear contratos', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            titulo = request.form.get('titulo')
            descripcion = request.form.get('descripcion')
            pdf_file = request.files.get('pdf_file')
            firmantes_json = request.form.get('firmantes')  # Lista de firmantes en JSON
            firma_creador_base64 = request.form.get('firma_creador')  # Firma del creador (obligatorio)
            sello_creador_base64 = request.form.get('sello_creador')  # Sello del creador (opcional, solo jefes)
            
            # Validar campos obligatorios
            if not titulo or not descripcion or not pdf_file or not firmantes_json or not firma_creador_base64:
                return jsonify({'success': False, 'message': 'Todos los campos son obligatorios, incluyendo tu firma'}), 400
            
            # Parsear firmantes
            import json
            firmantes_lista = json.loads(firmantes_json)
            
            if not firmantes_lista or len(firmantes_lista) == 0:
                return jsonify({'success': False, 'message': 'Debes seleccionar al menos un firmante'}), 400
            
            # Validar que sea PDF
            if not pdf_file.filename.lower().endswith('.pdf'):
                return jsonify({'success': False, 'message': 'El archivo debe ser un PDF'}), 400
            
            # Leer el PDF original
            pdf_bytes = pdf_file.read()
            
            print(f"✍️ Creando contrato con firma del creador...")
            if sello_creador_base64:
                print(f"🔐 El creador también subió su sello institucional")
            
            # Crear contrato (el controlador agregará la firma y sello del creador al PDF)
            resultado = ControlContratos.crear_contrato(
                titulo=titulo,
                descripcion=descripcion,
                pdf_bytes=pdf_bytes,
                id_usuario_creador=int(session['user_id']),
                firmantes_lista=firmantes_lista,
                firma_creador_base64=firma_creador_base64,
                sello_creador_base64=sello_creador_base64
            )
            
            if resultado['success']:
                return jsonify({'success': True, 'message': resultado['message']}), 200
            else:
                return jsonify({'success': False, 'message': resultado['message']}), 400
                
        except Exception as e:
            print(f"❌ Error al crear contrato: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': f'Error al crear contrato: {str(e)}'}), 500
    
    # GET: Mostrar formulario
    return render_template('formCrearContrato.html')

@app.route('/ver_contrato/<int:id_contrato>')
def ver_contrato(id_contrato):
    """Vista para ver un contrato (para firmantes que ya firmaron o contratos completados)"""
    if 'user_id' not in session:
        flash('Por favor inicia sesión', 'error')
        return redirect(url_for('login'))
    
    id_usuario = int(session['user_id'])
    
    # Obtener datos del contrato
    contrato = ControlContratos.obtener_contrato_por_id(id_contrato)
    if not contrato:
        flash('Contrato no encontrado', 'error')
        return redirect(url_for('contratos'))
    
    # Verificar permisos (creador, jefe TI, o alguien que firmó)
    es_creador = contrato.get('id_usuario_creador') == id_usuario
    es_jefe_ti = controlUsuarios.es_jefe_ti_rol_1(id_usuario)
    contratos_firmados = ControlContratos.obtener_contratos_firmados_por_usuario(id_usuario)
    ya_firmo = any(c['id_contrato'] == id_contrato for c in contratos_firmados)
    
    if not (es_creador or es_jefe_ti or ya_firmo):
        flash('No tienes permisos para ver este contrato', 'error')
        return redirect(url_for('contratos'))
    
    # Obtener historial
    historial = ControlContratos.obtener_historial_contrato(id_contrato)
    
    return render_template(
        'verContrato.html',
        contrato=contrato,
        historial=historial
    )

@app.route('/firmar_contrato/<int:id_contrato>')
def firmar_contrato(id_contrato):
    """Vista para firmar un contrato"""
    if 'user_id' not in session:
        flash('Por favor inicia sesión', 'error')
        return redirect(url_for('login'))
    
    id_usuario = int(session['user_id'])
    
    # Verificar que es el turno del usuario
    if not ControlContratos.es_turno_de_firmar(id_contrato, id_usuario):
        flash('Aún no es tu turno para firmar este contrato', 'warning')
        return redirect(url_for('contratos'))
    
    # Obtener datos del contrato
    contrato = ControlContratos.obtener_contrato_por_id(id_contrato)
    if not contrato:
        flash('Contrato no encontrado', 'error')
        return redirect(url_for('contratos'))
    
    # Obtener historial
    historial = ControlContratos.obtener_historial_contrato(id_contrato)
    
    # Verificar si es jefe (necesita sello)
    es_jefe = controlUsuarios.es_jefe(id_usuario)
    
    return render_template(
        'firmarContrato.html',
        contrato=contrato,
        historial=historial,
        es_jefe=es_jefe
    )

@app.route('/api/contrato/<int:id_contrato>/firmar', methods=['POST'])
def api_firmar_contrato(id_contrato):
    """API para firmar un contrato"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        id_usuario = int(session['user_id'])
        data = request.get_json()
        firma_base64 = data.get('firma')
        sello_base64 = data.get('sello')  # Opcional, solo para jefes
        
        if not firma_base64:
            return jsonify({'success': False, 'message': 'Firma no proporcionada'}), 400
        
        # Firmar contrato (con sello opcional)
        resultado = ControlContratos.firmar_contrato(
            id_contrato=id_contrato,
            id_usuario=id_usuario,
            firma_base64=firma_base64,
            sello_base64=sello_base64
        )
        
        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        print(f"Error al firmar contrato: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/contrato/<int:id_contrato>/rechazar', methods=['POST'])
def api_rechazar_contrato(id_contrato):
    """API para rechazar un contrato"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        id_usuario = int(session['user_id'])
        data = request.get_json()
        motivo = data.get('motivo', 'Sin motivo especificado')
        
        # Rechazar contrato
        resultado = ControlContratos.rechazar_contrato(
            id_contrato=id_contrato,
            id_usuario=id_usuario,
            motivo=motivo
        )
        
        if resultado['success']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        print(f"Error al rechazar contrato: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/contratos/pendientes')
def api_contratos_pendientes():
    """API para obtener contratos pendientes del usuario"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        id_usuario = int(session['user_id'])
        contratos = ControlContratos.obtener_contratos_pendientes_usuario(id_usuario)
        
        return jsonify({
            'success': True,
            'contratos': contratos
        })
    except Exception as e:
        print(f"Error al obtener contratos pendientes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contratos/todos')
def api_todos_contratos():
    """API para obtener todos los contratos (solo Jefe de TI)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    # Verificar que sea Jefe de TI
    if not controlUsuarios.es_jefe_ti_rol_1(int(session['user_id'])):
        return jsonify({'success': False, 'message': 'No tiene permisos'}), 403
    
    try:
        contratos = ControlContratos.obtener_todos_contratos()
        
        return jsonify({
            'success': True,
            'contratos': contratos
        })
    except Exception as e:
        print(f"Error al obtener todos los contratos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contratos/mis-creados')
def api_contratos_creados():
    """API para obtener contratos creados por el usuario actual"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        id_usuario = int(session['user_id'])
        contratos = ControlContratos.obtener_contratos_creados_por_usuario(id_usuario)
        
        return jsonify({
            'success': True,
            'contratos': contratos
        })
    except Exception as e:
        print(f"Error al obtener contratos creados: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contratos/firmados')
def api_contratos_firmados():
    """API para obtener contratos firmados por el usuario actual"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        id_usuario = int(session['user_id'])
        contratos = ControlContratos.obtener_contratos_firmados_por_usuario(id_usuario)
        
        return jsonify({
            'success': True,
            'contratos': contratos
        })
    except Exception as e:
        print(f"Error al obtener contratos firmados: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/areas')
def api_obtener_areas():
    """API para obtener todas las áreas"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        areas = controlUsuarios.obtener_todas_areas()
        
        return jsonify({
            'success': True,
            'areas': areas
        })
    except Exception as e:
        print(f"Error al obtener áreas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/usuarios/por-area/<int:id_area>')
def api_obtener_usuarios_por_area(id_area):
    """API para obtener usuarios de un área específica (excluyendo al usuario actual)"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        id_usuario_actual = int(session['user_id'])
        usuarios = controlUsuarios.obtener_usuarios_por_area(id_area)
        
        # Filtrar al usuario actual de la lista
        usuarios_filtrados = [u for u in usuarios if u['id_usuario'] != id_usuario_actual]
        
        return jsonify({
            'success': True,
            'usuarios': usuarios_filtrados
        })
    except Exception as e:
        print(f"Error al obtener usuarios por área: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contrato/<int:id_contrato>/historial')
def api_historial_contrato(id_contrato):
    """API para obtener el historial de un contrato - Accesible para creador y firmantes"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        id_usuario = int(session['user_id'])
        
        # Verificar que el usuario tenga permiso para ver este contrato
        # (es el creador, es firmante actual, ya firmó, o es Jefe de TI)
        contrato = ControlContratos.obtener_contrato_por_id(id_contrato)
        if not contrato:
            return jsonify({'success': False, 'message': 'Contrato no encontrado'}), 404
        
        es_creador = contrato.get('id_usuario_creador') == id_usuario
        es_jefe_ti = controlUsuarios.es_jefe_ti_rol_1(id_usuario)
        
        # Verificar si es firmante pendiente
        contratos_pendientes = ControlContratos.obtener_contratos_pendientes_usuario(id_usuario)
        es_firmante_pendiente = any(c['id_contrato'] == id_contrato for c in contratos_pendientes)
        
        # Verificar si ya firmó este contrato
        contratos_firmados = ControlContratos.obtener_contratos_firmados_por_usuario(id_usuario)
        ya_firmo = any(c['id_contrato'] == id_contrato for c in contratos_firmados)
        
        if not (es_creador or es_firmante_pendiente or ya_firmo or es_jefe_ti):
            return jsonify({'success': False, 'message': 'No tienes permisos para ver este contrato'}), 403
        
        historial = ControlContratos.obtener_historial_contrato(id_contrato)
        
        if historial is not None:
            return jsonify({
                'success': True,
                'historial': historial,
                'es_creador': es_creador
            })
        else:
            return jsonify({'success': False, 'message': 'Contrato no encontrado'}), 404
    except Exception as e:
        print(f"Error al obtener historial: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# RUTAS PARA GESTIÓN DE SELLOS
# ============================================

@app.route('/api/sello/subir', methods=['POST'])
def api_subir_sello():
    """API para subir el sello institucional del usuario"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        if 'sello' not in request.files:
            return jsonify({'success': False, 'message': 'No se proporcionó archivo'}), 400
        
        archivo_sello = request.files['sello']
        
        if archivo_sello.filename == '':
            return jsonify({'success': False, 'message': 'No se seleccionó archivo'}), 400
        
        id_usuario = int(session['user_id'])
        
        # Subir a Cloudinary
        url_sello = SelloService.subir_sello(archivo_sello, id_usuario)
        
        if not url_sello:
            return jsonify({'success': False, 'message': 'Error al subir el sello'}), 500
        
        # Actualizar en BD
        if SelloService.actualizar_sello_usuario(id_usuario, url_sello):
            return jsonify({
                'success': True,
                'message': 'Sello subido exitosamente',
                'url_sello': url_sello
            })
        else:
            return jsonify({'success': False, 'message': 'Error al guardar en BD'}), 500
            
    except Exception as e:
        print(f"Error al subir sello: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/api/sello/obtener')
def api_obtener_sello():
    """API para obtener el sello del usuario actual"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'No autorizado'}), 401
    
    try:
        id_usuario = int(session['user_id'])
        url_sello = SelloService.obtener_sello_usuario(id_usuario)
        
        return jsonify({
            'success': True,
            'url_sello': url_sello,
            'tiene_sello': url_sello is not None
        })
    except Exception as e:
        print(f"Error al obtener sello: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # host='0.0.0.0' permite acceso desde otros dispositivos en la red
    app.run(debug=True, host='0.0.0.0', port=5000)