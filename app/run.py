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
    return render_template('gestionDiagnostico.html')
    # if 'user_id' in session:
    #     return redirect(url_for('dashboard'))
    # return redirect(url_for('login'))


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
                return redirect(url_for('dashboard'))
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
    
    # Obtener parámetros de filtro
    filtros = {
        'buscar': request.args.get('buscar', ''),
        'fecha_desde': request.args.get('fecha_desde', ''),
        'fecha_hasta': request.args.get('fecha_hasta', ''),
        'categoria': request.args.get('categoria', ''),
        'estado': request.args.get('estado', '')
    }
    
    # Limpiar filtros vacíos
    filtros = {k: v for k, v in filtros.items() if v}
    
    try:
        # Obtener incidentes con filtros
        incidentes = ControlIncidentes.listar_incidentes(filtros if filtros else None)
        
        # Convertir incidentes a objetos para el template
        class IncidenteObj:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
                # Compatibilidad con el template
                if hasattr(self, 'fecha_reporte'):
                    self.fecha_creacion = self.fecha_reporte
                    self.id_incidente = str(self.id)[:8]  # Primeros 8 caracteres del UUID
        
        incidentes_obj = [IncidenteObj(inc) for inc in incidentes]
        
    except Exception as e:
        print(f"Error al obtener incidentes: {e}")
        incidentes_obj = []
        flash('Error al cargar los incidentes', 'error')
    
    return render_template('gestionIncidente.html', 
                         incidentes=incidentes_obj,
                         user_role=session.get('user_role'))

@app.route('/registrar_incidente', methods=['GET'])
def mostrar_formulario_incidente():
    return render_template('formRegistrarIncidente.html')

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
    """Ruta para asignar diagnóstico a incidentes"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Solo técnicos y administradores pueden asignar diagnósticos
    if session.get('user_role') not in [2, 3]:  # 2 = Técnico, 3 = Administrador
        flash('No tiene permisos para asignar diagnósticos', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        incidente_id = request.form.get('id_incidente')
        descripcion = request.form.get('descripcion')
        causa_raiz = request.form.get('causa_raiz')
        solucion = request.form.get('solucion')
        observaciones = request.form.get('comentario', '')
        
        # Validaciones
        if not all([incidente_id, descripcion, causa_raiz, solucion]):
            flash('Todos los campos requeridos deben ser completados', 'error')
            return render_template('asignar_diagnostico.html')
        
        try:
            resultado = ControlDiagnosticos.insertar_diagnostico(
                incidente_id, session['user_id'], descripcion, 
                causa_raiz, solucion, observaciones
            )
            
            if resultado:
                # Cambiar estado del incidente a "En Progreso" si está abierto
                incidente = ControlIncidentes.buscar_por_id(incidente_id)
                if incidente and incidente['estado_nombre'] == 'Abierto':
                    ControlIncidentes.actualizar_estado(incidente_id, 2, session['user_id'])
                
                flash('Diagnóstico asignado correctamente', 'success')
                return redirect(url_for('gestion_incidentes'))
            else:
                flash('Error al asignar diagnóstico', 'error')
            
        except Exception as e:
            print(f"Error al procesar el diagnóstico: {e}")
            flash(f'Error al procesar el diagnóstico: {str(e)}', 'error')
    
    # Obtener incidente específico si se pasa como parámetro
    incidente_seleccionado = request.args.get('incidente')
    
    # Obtener lista de incidentes abiertos y en progreso
    try:
        todos_incidentes = ControlIncidentes.listar_incidentes()
        incidentes_disponibles = [
            inc for inc in todos_incidentes 
            if inc['estado'] in ['Abierto', 'En Progreso']
        ]
        
        # Convertir a formato esperado por el template
        incidentes_para_template = []
        for inc in incidentes_disponibles:
            incidentes_para_template.append({
                'id_incidente': str(inc['id']),
                'titulo': inc['titulo']
            })
            
    except Exception as e:
        print(f"Error al obtener incidentes: {e}")
        incidentes_para_template = []
    
    return render_template('asignar_diagnostico.html', 
                         incidentes=incidentes_para_template,
                         incidente_seleccionado=incidente_seleccionado)

@app.route('/gestion_diagnosticos')
def gestion_diagnosticos():
    """Ruta para gestión de diagnósticos"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Solo técnicos y administradores pueden ver diagnósticos
    if session.get('user_role') not in [2, 3]:
        flash('No tiene permisos para ver diagnósticos', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Obtener todos los incidentes con sus diagnósticos
        incidentes = ControlIncidentes.listar_incidentes()
        
        # Agregar diagnósticos a cada incidente
        for incidente in incidentes:
            incidente['diagnosticos'] = ControlDiagnosticos.listar_por_incidente(incidente['id'])
        
        # Filtrar solo incidentes que tienen diagnósticos
        incidentes_con_diagnosticos = [inc for inc in incidentes if inc['diagnosticos']]
        
    except Exception as e:
        print(f"Error al obtener diagnósticos: {e}")
        incidentes_con_diagnosticos = []
        flash('Error al cargar los diagnósticos', 'error')
    
    return render_template('gestion_diagnosticos.html', 
                         incidentes=incidentes_con_diagnosticos,
                         user_role=session.get('user_role'))

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



if __name__ == '__main__':
    app.run(debug=True)