"""Probar conexión y credenciales usando el módulo de conexión del proyecto"""
import sys
sys.path.append('app')

from ConexionBD import get_connection

CORREO = "6@6"
CONTRASENA = "6"  # Cambia esto por tu contraseña real del usuario

print("="*60)
print("Probando conexión a la base de datos...")
print("="*60)

try:
    conn = get_connection()
    
    if not conn:
        print("❌ No se pudo conectar")
        exit(1)
    
    print("✅ Conexión exitosa")
    
    cursor = conn.cursor()
    
    # Ver todos los usuarios
    print("\n📋 Usuarios en la BD:")
    print("-"*80)
    cursor.execute("SELECT id_usuario, correo, contrasena, nombre, estado FROM USUARIO")
    usuarios = cursor.fetchall()
    
    for u in usuarios:
        print(f"ID: {u[0]:>3} | Correo: {u[1]:<25} | Pass: {u[2]:<15} | Nombre: {u[3]:<20} | Estado: {u[4]}")
    
    # Buscar el usuario específico
    print("\n" + "="*60)
    print(f"Buscando usuario con correo '{CORREO}' y contraseña '{CONTRASENA}'...")
    print("="*60)
    
    cursor.execute(
        "SELECT id_usuario, nombre, ape_pat, ape_mat, correo, contrasena, id_rol, estado FROM USUARIO WHERE correo = %s AND contrasena = %s",
        (CORREO, CONTRASENA)
    )
    usuario = cursor.fetchone()
    
    if usuario:
        print("\n✅ USUARIO ENCONTRADO - Las credenciales son correctas!")
        print(f"  ID: {usuario[0]}")
        print(f"  Nombre: {usuario[1]} {usuario[2]} {usuario[3]}")
        print(f"  Correo: {usuario[4]}")
        print(f"  Rol: {usuario[6]}")
        print(f"  Estado: {'Activo' if usuario[7] else 'Inactivo'}")
        print("\n✓ Puedes usar estas credenciales para el enrolamiento facial")
    else:
        print("\n❌ NO ENCONTRADO con esas credenciales")
        
        # Buscar solo por correo
        cursor.execute("SELECT id_usuario, correo, contrasena FROM USUARIO WHERE correo = %s", (CORREO,))
        por_correo = cursor.fetchone()
        
        if por_correo:
            print(f"\n⚠️  Existe usuario con correo '{CORREO}':")
            print(f"  ID: {por_correo[0]}")
            print(f"  Contraseña correcta en BD: '{por_correo[2]}'")
            print(f"  Contraseña que estás probando: '{CONTRASENA}'")
            print(f"\n  💡 Cambia CONTRASENA en la línea 7 de este archivo")
        else:
            print(f"\n✗ No existe ningún usuario con correo '{CORREO}'")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)

