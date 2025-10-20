from flask import Flask, render_template, request, redirect, url_for, flash, session
from controlUsuarios import controlUsuarios

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Cambia esto por una clave más segura

@app.route('/')
def index():
    """Ruta principal que redirige al login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
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
        usuario = controlUsuarios.buscar_por_correo(correo)
        
        if usuario and usuario['contrasena'] == contrasena:  # Comparación directa sin hash
            if usuario['estado'] == 1:  # Usuario activo
                session['user_id'] = usuario['id_usuario']
                session['user_name'] = f"{usuario['nombre']} {usuario['ape_pat']}"
                session['user_role'] = usuario['id_rol']
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
    
    return render_template('dashboard.html', 
                         user_name=session.get('user_name'),
                         user_role=session.get('user_role'))

@app.route('/usuarios')
def listar_usuarios():
    """Ruta para listar usuarios (solo para administradores)"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('user_role') != 1:  # Asumiendo que 1 = admin
        flash('No tiene permisos para acceder a esta sección', 'error')
        return redirect(url_for('dashboard'))
    
    usuarios = controlUsuarios.buscar_todos()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/usuarios/<int:id_usuario>/estado/<int:nuevo_estado>')
def cambiar_estado_usuario(id_usuario, nuevo_estado):
    """Cambiar estado de un usuario"""
    if 'user_id' not in session or session.get('user_role') != 1:
        flash('No tiene permisos para realizar esta acción', 'error')
        return redirect(url_for('dashboard'))
    
    if controlUsuarios.cambiar_estado_usuario(id_usuario, nuevo_estado):
        estado_texto = "activado" if nuevo_estado == 1 else "desactivado"
        flash(f'Usuario {estado_texto} correctamente', 'success')
    else:
        flash('Error al cambiar el estado del usuario', 'error')
    
    return redirect(url_for('listar_usuarios'))

@app.route('/usuarios/<int:id_usuario>/eliminar')
def eliminar_usuario(id_usuario):
    """Eliminar un usuario"""
    if 'user_id' not in session or session.get('user_role') != 1:
        flash('No tiene permisos para realizar esta acción', 'error')
        return redirect(url_for('dashboard'))
    
    # No permitir que el admin se elimine a sí mismo
    if id_usuario == session.get('user_id'):
        flash('No puede eliminarse a sí mismo', 'error')
        return redirect(url_for('listar_usuarios'))
    
    if controlUsuarios.eliminar_usuario(id_usuario):
        flash('Usuario eliminado correctamente', 'success')
    else:
        flash('Error al eliminar el usuario', 'error')
    
    return redirect(url_for('listar_usuarios'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Ruta para registro de nuevos usuarios"""
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        ape_pat = request.form.get('ape_pat')
        ape_mat = request.form.get('ape_mat')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        confirmar_contrasena = request.form.get('confirmar_contrasena')
        
        # Validaciones
        if not all([nombre, ape_pat, ape_mat, correo, contrasena, confirmar_contrasena]):
            flash('Todos los campos son obligatorios', 'error')
            return render_template('registro.html')
        
        if contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('registro.html')
        
        if len(contrasena) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('registro.html')
        
        # Verificar si el correo ya existe
        usuario_existente = controlUsuarios.buscar_por_correo(correo)
        if usuario_existente:
            flash('El correo electrónico ya está registrado', 'error')
            return render_template('registro.html')
        
        # Insertar usuario con contraseña en texto plano (rol 2 = usuario normal, estado 1 = activo)
        if controlUsuarios.insertar(nombre, ape_pat, ape_mat, correo, contrasena, 2, 1):
            flash('Usuario registrado correctamente', 'success')
            return redirect(url_for('login'))
        else:
            flash('Error al registrar usuario', 'error')
    
    return render_template('registro.html')

@app.route('/asignar_diagnostico', methods=['GET', 'POST'])
def asignar_diagnostico():
    """Ruta para asignar diagnóstico a incidentes"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Solo técnicos y administradores pueden asignar diagnósticos
    if session.get('user_role') not in [1, 3]:  # 1 = admin, 3 = técnico
        flash('No tiene permisos para asignar diagnósticos', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        id_incidente = request.form.get('id_incidente')
        descripcion = request.form.get('descripcion')
        causa_raiz = request.form.get('causa_raiz')
        solucion = request.form.get('solucion')
        comentario = request.form.get('comentario', '')
        
        # Validaciones
        if not all([id_incidente, descripcion, causa_raiz, solucion]):
            flash('Todos los campos requeridos deben ser completados', 'error')
            return render_template('asignar_diagnostico.html')
        
        try:
            # Aquí iría la lógica para guardar el diagnóstico en la base de datos
            # Por ahora simulamos que se guarda correctamente
            
            # Ejemplo de lo que haría el controlador de diagnósticos:
            # diagnostico_data = {
            #     'id_incidente': id_incidente,
            #     'descripcion': descripcion,
            #     'causa_raiz': causa_raiz,
            #     'solucion': solucion,
            #     'comentario': comentario,
            #     'id_usuario_asigna': session['user_id']
            # }
            # 
            # if controlDiagnosticos.insertar(diagnostico_data):
            #     flash('Diagnóstico asignado correctamente', 'success')
            #     return redirect(url_for('dashboard'))
            # else:
            #     flash('Error al asignar diagnóstico', 'error')
            
            # Simulación de éxito
            flash(f'Diagnóstico asignado correctamente al incidente INC-{id_incidente.zfill(3)}', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error al procesar el diagnóstico: {str(e)}', 'error')
    
    # Obtener lista de incidentes (por ahora datos estáticos)
    # En una implementación real, esto vendría de la base de datos
    incidentes = [
        {'id_incidente': 1, 'titulo': 'Fallo en servidor principal'},
        {'id_incidente': 2, 'titulo': 'Software de contabilidad no inicia'},
        {'id_incidente': 3, 'titulo': 'Monitor defectuoso'},
        {'id_incidente': 4, 'titulo': 'Acceso no autorizado detectado'},
        {'id_incidente': 5, 'titulo': 'Impresora no responde'},
        {'id_incidente': 6, 'titulo': 'Conexión VPN intermitente'}
    ]
    
    return render_template('asignar_diagnostico.html', incidentes=incidentes)

@app.route('/crear_admin')
def crear_admin():
    """Ruta para crear usuario administrador inicial (solo usar una vez)"""
    try:
        # Verificar si ya existe un administrador
        usuarios = controlUsuarios.buscar_todos()
        admin_existe = any(usuario.get('id_rol') == 1 for usuario in usuarios or [])
        
        if admin_existe:
            flash('Ya existe un usuario administrador', 'info')
            return redirect(url_for('login'))
        
        # Crear usuario administrador
        if controlUsuarios.insertar("Admin", "Sistema", "Principal", "admin@sistema.com", "admin123", 1, 1):
            flash('Usuario administrador creado: admin@sistema.com / admin123', 'success')
        else:
            flash('Error al crear usuario administrador', 'error')
            
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('login'))

@app.route('/gestion_incidentes')
def gestion_incidentes():
    """Ruta para gestión de incidentes"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener parámetros de filtro
    buscar = request.args.get('buscar', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    categoria = request.args.get('categoria', '')
    estado = request.args.get('estado', '')
    
    # Aquí iría la lógica para obtener incidentes de la base de datos
    # Por ahora usamos datos estáticos
    incidentes = []
    
    # Si no hay incidentes en BD, mostrar datos de ejemplo
    if not incidentes:
        incidentes = [
            {
                'id_incidente': 1,
                'titulo': 'Fallo en servidor principal',
                'descripcion': 'El servidor principal no responde desde las 10:30 AM',
                'categoria': 'Red',
                'estado': 'en_proceso',
                'fecha_creacion': '2025-10-19'
            },
            {
                'id_incidente': 2,
                'titulo': 'Software de contabilidad no inicia',
                'descripcion': 'Error al abrir la aplicación de contabilidad',
                'categoria': 'Software',
                'estado': 'abierto',
                'fecha_creacion': '2025-10-18'
            },
            {
                'id_incidente': 3,
                'titulo': 'Monitor defectuoso',
                'descripcion': 'Monitor de la estación 5 presenta líneas verticales',
                'categoria': 'Hardware',
                'estado': 'resuelto',
                'fecha_creacion': '2025-10-17'
            },
            {
                'id_incidente': 4,
                'titulo': 'Acceso no autorizado detectado',
                'descripcion': 'Se detectó un intento de acceso no autorizado al sistema',
                'categoria': 'Seguridad',
                'estado': 'abierto',
                'fecha_creacion': '2025-10-16'
            }
        ]
        
        # Simular objetos con atributos para el template
        class IncidenteObj:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
                # Simular fecha como objeto datetime para el template
                from datetime import datetime
                if isinstance(self.fecha_creacion, str):
                    try:
                        self.fecha_creacion = datetime.strptime(value, '%Y-%m-%d')
                    except:
                        self.fecha_creacion = datetime.now()
        
        incidentes = [IncidenteObj(inc) for inc in incidentes]
    
    # Aplicar filtros (simulación)
    if buscar:
        incidentes = [inc for inc in incidentes if buscar.lower() in inc.titulo.lower()]
    if categoria:
        incidentes = [inc for inc in incidentes if inc.categoria == categoria]
    if estado:
        incidentes = [inc for inc in incidentes if inc.estado == estado]
    
    return render_template('gestion_incidentes.html', incidentes=incidentes)

@app.route('/incidentes/<int:id_incidente>/eliminar', methods=['POST'])
def eliminar_incidente(id_incidente):
    """Eliminar un incidente (solo administradores)"""
    if 'user_id' not in session or session.get('user_role') != 1:
        return {'error': 'No autorizado'}, 403
    
    try:
        # Aquí iría la lógica para eliminar de la base de datos
        # Por ahora simulamos que se elimina correctamente
        flash(f'Incidente INC-{id_incidente:03d} eliminado correctamente', 'success')
        return {'success': True}, 200
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)