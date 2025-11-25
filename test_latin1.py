import psycopg2
import os

# Forzar encoding Latin-1 para evitar problemas con tildes
os.environ['PGCLIENTENCODING'] = 'LATIN1'

# Credenciales
CORREO = "6@6"
CONTRASENA = "6"

print("="*60)
print("Probando con encoding LATIN1...")
print(f"Correo: {CORREO}")
print(f"Contraseña: {CONTRASENA}")
print("="*60)

try:
    conn = psycopg2.connect(
        host="localhost",
        database="Gobierno2",
        user="postgres",
        password="070905"
    )
    
    print("✅ Conexión exitosa")
    
    cursor = conn.cursor()
    
    # Ver todos los usuarios
    cursor.execute("SELECT id_usuario, correo, contrasena, nombre, estado FROM USUARIO")
    usuarios = cursor.fetchall()
    
    print(f"\n📋 Usuarios en la BD ({len(usuarios)} total):")
    print("-"*80)
    for u in usuarios:
        print(f"ID: {u[0]:>3} | Correo: {u[1]:<25} | Pass: {u[2]:<15} | Nombre: {u[3]:<20} | Estado: {u[4]}")
    
    # Buscar el usuario específico
    print("\n" + "="*60)
    print("Buscando usuario específico...")
    cursor.execute(
        "SELECT id_usuario, nombre, ape_pat, ape_mat, correo, contrasena, id_rol, estado FROM USUARIO WHERE correo = %s AND contrasena = %s",
        (CORREO, CONTRASENA)
    )
    usuario = cursor.fetchone()
    
    if usuario:
        print("✅ USUARIO ENCONTRADO")
        print(f"  ID: {usuario[0]}")
        print(f"  Nombre: {usuario[1]} {usuario[2]} {usuario[3]}")
        print(f"  Correo: {usuario[4]}")
        print(f"  Rol: {usuario[6]}")
        print(f"  Estado: {'Activo' if usuario[7] else 'Inactivo'}")
    else:
        print("❌ NO ENCONTRADO con esas credenciales exactas")
        
        # Buscar solo por correo
        cursor.execute("SELECT id_usuario, correo, contrasena FROM USUARIO WHERE correo = %s", (CORREO,))
        por_correo = cursor.fetchone()
        
        if por_correo:
            print(f"\n✓ Existe usuario con correo '{CORREO}':")
            print(f"  ID: {por_correo[0]}")
            print(f"  Contraseña en BD: '{por_correo[2]}'")
            print(f"  Contraseña buscada: '{CONTRASENA}'")
            print(f"  Longitud BD: {len(por_correo[2])}, Longitud buscada: {len(CONTRASENA)}")
            print(f"  ¿Coinciden? {por_correo[2] == CONTRASENA}")
            
            # Comparar byte a byte
            if por_correo[2] != CONTRASENA:
                print("\n  Comparación carácter por carácter:")
                max_len = max(len(por_correo[2]), len(CONTRASENA))
                for i in range(max_len):
                    c_bd = por_correo[2][i] if i < len(por_correo[2]) else '(vacío)'
                    c_bus = CONTRASENA[i] if i < len(CONTRASENA) else '(vacío)'
                    print(f"    Pos {i}: BD='{c_bd}' | Buscada='{c_bus}' | {'✓' if c_bd == c_bus else '✗'}")
        else:
            print(f"\n✗ No existe usuario con correo '{CORREO}'")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("="*60)

