"""
Script de prueba para verificar credenciales en la base de datos
"""
import sys
sys.path.append('app')

from ConexionBD import get_connection

def verificar_usuario(correo, contrasena):
    """Verifica si existe un usuario con las credenciales dadas"""
    print("="*60)
    print("🔍 VERIFICANDO CREDENCIALES")
    print("="*60)
    print(f"Correo buscado: '{correo}'")
    print(f"Contraseña buscada: '{contrasena}'")
    print(f"Longitud contraseña: {len(contrasena)}")
    print()
    
    try:
        conexion = get_connection()
        if not conexion:
            print("❌ No se pudo conectar a la base de datos")
            return
        
        print("✅ Conexión a BD exitosa")
        print()
        
        # Primero, buscar todos los usuarios
        sql_todos = "SELECT id_usuario, correo, contrasena, nombre, estado FROM USUARIO"
        
        with conexion.cursor() as cursor:
            cursor.execute(sql_todos)
            usuarios = cursor.fetchall()
        
        print(f"📋 Total de usuarios en la BD: {len(usuarios)}")
        print()
        print("Usuarios encontrados:")
        print("-" * 100)
        print(f"{'ID':<5} {'Correo':<30} {'Contraseña':<20} {'Nombre':<20} {'Estado':<10}")
        print("-" * 100)
        
        for u in usuarios:
            print(f"{u[0]:<5} {u[1]:<30} {u[2]:<20} {u[3]:<20} {'Activo' if u[4] else 'Inactivo':<10}")
        
        print()
        print("="*60)
        print("🔎 BUSCANDO USUARIO ESPECÍFICO")
        print("="*60)
        
        # Ahora buscar el usuario específico
        sql_buscar = """
            SELECT id_usuario, nombre, ape_pat, ape_mat, correo, contrasena, id_rol, estado 
            FROM USUARIO 
            WHERE correo = %s AND contrasena = %s
        """
        
        with conexion.cursor() as cursor:
            cursor.execute(sql_buscar, (correo, contrasena))
            usuario = cursor.fetchone()
        
        if usuario:
            print("✅ USUARIO ENCONTRADO:")
            print(f"   ID: {usuario[0]}")
            print(f"   Nombre: {usuario[1]} {usuario[2]} {usuario[3]}")
            print(f"   Correo: {usuario[4]}")
            print(f"   Contraseña: {usuario[5]}")
            print(f"   Rol: {usuario[6]}")
            print(f"   Estado: {'Activo' if usuario[7] else 'Inactivo'}")
            
            # Verificar biometría
            sql_bio = """
                SELECT tiene_biometria, fecha_registro_facial 
                FROM USUARIO 
                WHERE id_usuario = %s
            """
            with conexion.cursor() as cursor:
                cursor.execute(sql_bio, (usuario[0],))
                bio = cursor.fetchone()
            
            if bio:
                print(f"   Tiene biometría: {bio[0]}")
                print(f"   Fecha registro: {bio[1] if bio[1] else 'N/A'}")
        else:
            print("❌ NO SE ENCONTRÓ USUARIO CON ESAS CREDENCIALES")
            print()
            print("💡 Posibles causas:")
            print("   1. El correo no coincide exactamente")
            print("   2. La contraseña no coincide exactamente")
            print("   3. Hay espacios extra en el correo o contraseña")
            print()
            
            # Buscar solo por correo
            sql_correo = "SELECT id_usuario, correo, contrasena, estado FROM USUARIO WHERE correo = %s"
            with conexion.cursor() as cursor:
                cursor.execute(sql_correo, (correo,))
                usuario_correo = cursor.fetchone()
            
            if usuario_correo:
                print(f"✓ Se encontró un usuario con el correo '{correo}'")
                print(f"  ID: {usuario_correo[0]}")
                print(f"  Contraseña en BD: '{usuario_correo[2]}'")
                print(f"  Contraseña ingresada: '{contrasena}'")
                print(f"  ¿Coinciden?: {usuario_correo[2] == contrasena}")
                print(f"  Estado: {'Activo' if usuario_correo[3] else 'Inactivo'}")
            else:
                print(f"✗ No existe ningún usuario con el correo '{correo}'")
        
        conexion.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print()
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  SCRIPT DE VERIFICACIÓN DE CREDENCIALES                   ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Pedir credenciales
    correo = input("Ingresa el correo: ").strip()
    contrasena = input("Ingresa la contraseña: ").strip()
    
    print()
    verificar_usuario(correo, contrasena)
    print()
    print("="*60)

