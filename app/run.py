from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from controllers.control_Usuarios import controlUsuarios
from controllers.control_incidentes import ControlIncidentes
from controllers.control_categorias import controlCategorias
from controllers.control_diagnostico import ControlDiagnosticos
from controllers.control_notificaciones import ControlNotificaciones
from controllers.control_evidencias import controlEvidencias
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
import cloudinary.api

app = Flask(__name__, template_folder="./templates")
app.secret_key = 'tu_clave_secreta_aqui'

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
        # Asegurarse de que el archivo esté al inicio
        archivo.seek(0)
        
        # Leer el contenido del archivo en memoria para evitar problemas con el stream
        from io import BytesIO
        archivo_data = archivo.read()
        archivo.seek(0)  # Volver al inicio
        
        # Crear un nuevo stream desde los datos
        archivo_stream = BytesIO(archivo_data)
        
        # Generar nombre único
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        nombre_seguro = secure_filename(archivo.filename)
        nombre_base = nombre_seguro.rsplit('.', 1)[0] if '.' in nombre_seguro else nombre_seguro
        public_id = f"incidentes_{id_incidente}_{timestamp}_{nombre_base}"
        
        # Subir a Cloudinary (solo imágenes)
        resultado = cloudinary.uploader.upload(
            archivo_stream,
            public_id=public_id,
            resource_type="image",  # Solo imágenes
            folder="evidencias_incidentes",
            overwrite=False
        )
        
        url = resultado.get('secure_url')
        print(f"✅ Archivo '{archivo.filename}' subido exitosamente a Cloudinary")
        return url
    except Exception as e:
        print(f"❌ Error al subir '{archivo.filename}' a Cloudinary: {e}")
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
            class IncidenteObj:
                def __init__(self, data):
                    self.id_incidente = data.get('id_incidente') or data.get('id')
                    self.titulo = data.get('titulo', '')
                    self.descripcion = data.get('descripcion', '')
                    self.categoria = data.get('categoria', 'No asignada')
                    self.estado = data.get('estado', 'pendiente')
                    self.nivel = data.get('nivel', 'M')

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
        titulo = request.form.get('titulo')
        categoria = request.form.get('categoria')
        descripcion = request.form.get('descripcion')
        
        # Validar campos
        if not titulo or not categoria or not descripcion:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('mostrar_formulario_incidente'))
        
        id_categoria = int(categoria)
        id_usuario = int(session['user_id'])
        
        # Insertar incidente (estado P por defecto)
        # El nivel de prioridad será asignado por el jefe de TI (id_rol=1) cuando acepte el incidente
        resultado = ControlIncidentes.insertar_incidentes(
            titulo, descripcion, id_categoria, id_usuario, None  # Sin nivel, será asignado por el jefe de TI
        )
        
        if resultado > 0:  # Retorna el ID del incidente
            id_incidente = resultado
            
            # Procesar archivos de evidencias si existen (máximo 5 imágenes)
            if 'evidencias' in request.files:
                archivos = request.files.getlist('evidencias')
                archivos_subidos = 0
                archivos_procesados = 0
                
                # Limitar a máximo 5 archivos
                archivos_limite = archivos[:5]
                
                for idx, archivo in enumerate(archivos_limite):
                    if not archivo or not archivo.filename:
                        print(f"Archivo {idx + 1} vacío o sin nombre, saltando...")
                        continue
                    
                    # Validar que sea imagen
                    if not archivo.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                        print(f"Archivo {archivo.filename} no es una imagen válida")
                        continue
                    
                    # Validar tamaño (10MB)
                    try:
                        archivo.seek(0, os.SEEK_END)
                        tamaño = archivo.tell()
                        archivo.seek(0)  # Volver al inicio
                        
                        if tamaño > MAX_FILE_SIZE:
                            print(f"Archivo {archivo.filename} excede 10MB ({tamaño / (1024*1024):.2f}MB)")
                            continue
                    except Exception as e:
                        print(f"Error al validar tamaño de {archivo.filename}: {e}")
                        continue
                    
                    try:
                        # Asegurarse de que el archivo esté al inicio antes de subir
                        archivo.seek(0)
                        
                        print(f"Subiendo archivo {idx + 1}/{len(archivos_limite)}: {archivo.filename}")
                        
                        # Subir a Cloudinary
                        url_archivo = subir_a_cloudinary(archivo, id_incidente)
                        
                        if url_archivo:
                            # Guardar URL de Cloudinary en la base de datos
                            if controlEvidencias.insertar(id_incidente, url_archivo):
                                archivos_subidos += 1
                                print(f"✅ Evidencia {archivos_subidos} guardada: {archivo.filename}")
                            else:
                                print(f"❌ Error al guardar URL en BD: {archivo.filename}")
                        else:
                            print(f"❌ Error: No se pudo subir {archivo.filename} a Cloudinary")
                    except Exception as e:
                        print(f"❌ Error al procesar evidencia {archivo.filename}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                    finally:
                        archivos_procesados += 1
                        # Asegurarse de cerrar el archivo
                        try:
                            archivo.close()
                        except:
                            pass
                
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
        
        control_diagnostico = ControlDiagnosticos()
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
            'historial': historial
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
                    # Notificar al técnico
                    ControlNotificaciones.notificar_asignacion_tecnico(id_incidente, int(id_tecnico), False)
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
                for id_tecnico in tecnicos:
                    es_responsable = (id_tecnico == responsable)
                    if ControlIncidentes.agregar_a_equipo_tecnico(id_incidente, int(id_tecnico), es_responsable):
                        # Notificar a cada técnico
                        ControlNotificaciones.notificar_asignacion_tecnico(id_incidente, int(id_tecnico), True)
                    else:
                        exito = False
                
                if exito:
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
    
    incidentes = ControlIncidentes.obtener_incidentes_disponibles_tecnicos()
    tickets_activos = controlUsuarios.contar_tickets_activos(int(session['user_id']))
    tickets_equipo = controlUsuarios.contar_tickets_en_equipo(int(session['user_id']))
    
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

if __name__ == '__main__':
    app.run(debug=True)