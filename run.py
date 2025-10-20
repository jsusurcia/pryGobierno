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

if __name__ == '__main__':
    app.run(debug=True)