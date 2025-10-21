from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from controllers.control_Usuarios import controlUsuarios
from controllers.control_incidentes import ControlIncidentes
from controllers.control_categorias import controlCategorias
from controllers.control_diagnostico import ControlDiagnosticos
from datetime import datetime

app = Flask(__name__, template_folder="./templates")
app.secret_key = 'tu_clave_secreta_aqui'  

@app.route('/')
def index():
    """Ruta principal que redirige al login"""
    if 'user_id' in session:
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
                return redirect(url_for('gestion_incidentes'))
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
    """Ruta para gestión de incidentes con filtros"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener parámetros de filtro
    filtros = {
        'buscar': request.args.get('buscar', '').strip().lower(),
        'fecha_desde': request.args.get('fecha_desde', '').strip(),
        'fecha_hasta': request.args.get('fecha_hasta', '').strip(),
        'categoria': request.args.get('categoria', '').strip().lower(),
        'estado': request.args.get('estado', '').strip().lower()
    }

    try:
        # Obtener todos los incidentes
        todos = ControlIncidentes.listar_incidentes()

        # 🧹 Si la función devuelve None o vacío, lo forzamos a lista vacía
        if not todos:
            todos = []

        print(f"Total de incidentes obtenidos: {len(todos)}")

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

            # Filtrar por estado
            if filtros['estado'] and filtros['estado'] != estado:
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
                    self.estado = data.get('estado', 'abierto')

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

        print(f"Filtrados: {len(incidentes_obj)} incidentes válidos")

    except Exception as e:
        print(f"Error al obtener incidentes: {e}")
        import traceback
        traceback.print_exc()
        incidentes_obj = []
        flash('Error al cargar los incidentes', 'error')

    return render_template('gestionIncidente.html',
                           incidentes=incidentes_obj,
                           user_role=session.get('user_role'))
    
@app.route('/registrar_incidente', methods=['GET'])
def mostrar_formulario_incidente():
    return render_template('formRegistrarIncidente.html')

@app.route('/revision_diagnostico', methods=['GET'])
def revision_diagnostico():
    if 'user_id' not in session:
        return redirect(url_for('login'))

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






@app.route('/registrar_incidente', methods=['POST'])
def registrar_incidente():
    try:
        # Obtener datos del formulario
        titulo = request.form.get('titulo')
        id_categoria = int(request.form.get('categoria'))
        descripcion = request.form.get('descripcion')
        
        # Validar campos
        if not titulo or not id_categoria or not descripcion:
            flash('Todos los campos son obligatorios', 'error')
            return redirect(url_for('mostrar_formulario_incidente'))
        
        # Usuario temporal hasta que integres login
        id_usuario = 1
        
        # Insertar incidente
        resultado = ControlIncidentes.insertar_incidentes(
            titulo, descripcion, id_categoria, id_usuario
        )
        
        if resultado == 0:
            flash('¡Incidente registrado exitosamente!', 'success')
        elif resultado == -2:
            flash('Error de conexión a la base de datos', 'error')
        else:
            flash('Error al registrar el incidente', 'error')

    except Exception as e:
        flash(f'Error inesperado: {str(e)}', 'error')
    
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

    # Mostrar formulario
    control_incidentes = ControlIncidentes()
    incidentes = control_incidentes.obtener_incidentes_sin_diagnostico()

    # Procesar formulario
    if request.method == 'POST':
        id_incidente = request.form.get('id_incidente')
        descripcion = request.form.get('descripcion')
        causa_raiz = request.form.get('causa_raiz')
        solucion = request.form.get('solucion')
        comentario = request.form.get('comentario')

        if not (id_incidente and descripcion and causa_raiz and solucion):
            flash('Completa todos los campos obligatorios.', 'error')
            return redirect(url_for('asignar_diagnostico'))

        control_diagnostico = ControlDiagnosticos()
        exito = control_diagnostico.insertar_diagnostico(
            id_incidente=id_incidente,
            descripcion=descripcion,
            causa_raiz=causa_raiz,
            solucion=solucion,
            comentario=comentario,
            usuario_id=session.get('user_id')  # registra quién lo hizo
        )

        if exito:
            flash('Diagnóstico asignado correctamente.', 'success')
            return redirect(url_for('gestion_incidentes'))
        else:
            flash('Error al asignar el diagnóstico.', 'error')

    return render_template('agregarDiagnostico.html', incidentes=incidentes)

@app.route('/gestion_diagnostico', methods=['GET'])
def gestion_diagnostico():
    titulo = request.args.get('titulo', '')
    causa = request.args.get('causa', '')

    control_diag = ControlDiagnosticos()
    diagnosticos = control_diag.obtener_diagnosticos_filtrados(titulo, causa)

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
    return dict(
        current_user_id=session.get('user_id'),
        current_user_name=session.get('user_name'),
        current_user_role=session.get('user_role'),
        current_user_role_name=session.get('user_role_name')
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

if __name__ == '__main__':
    app.run(debug=True)