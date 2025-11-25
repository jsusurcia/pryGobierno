import psycopg2

# Credenciales
CORREO = "6@6"
CONTRASENA = "6"  # Cambiar si es diferente

print("="*60)
print("Probando conexión y credenciales...")
print(f"Correo: {CORREO}")
print(f"Contraseña: {CONTRASENA}")
print("="*60)

try:
    # Conectar con encoding específico
    conn = psycopg2.connect(
        host="localhost",
        database="Gobierno2",
        user="postgres",
        password="070905",
        options="-c client_encoding=UTF8"
    )
    
    print("✅ Conexión exitosa")
    
    cursor = conn.cursor()
    
    # Ver todos los usuarios
    cursor.execute("SELECT id_usuario, correo, contrasena, nombre, estado FROM USUARIO")
    usuarios = cursor.fetchall()
    
    print(f"\n📋 Usuarios en la BD ({len(usuarios)} total):")
    print("-"*80)
    for u in usuarios:
        print(f"ID: {u[0]} | Correo: '{u[1]}' | Pass: '{u[2]}' | Nombre: {u[3]} | Estado: {u[4]}")
    
    # Buscar el usuario específico
    print("\n" + "="*60)
    print("Buscando usuario específico...")
    cursor.execute(
        "SELECT * FROM USUARIO WHERE correo = %s AND contrasena = %s",
        (CORREO, CONTRASENA)
    )
    usuario = cursor.fetchone()
    
    if usuario:
        print("✅ USUARIO ENCONTRADO")
        print(f"ID: {usuario[0]}")
        print(f"Nombre: {usuario[1]} {usuario[2]} {usuario[3]}")
    else:
        print("❌ NO ENCONTRADO con esas credenciales exactas")
        
        # Buscar solo por correo
        cursor.execute("SELECT id_usuario, correo, contrasena FROM USUARIO WHERE correo = %s", (CORREO,))
        por_correo = cursor.fetchone()
        
        if por_correo:
            print(f"\n✓ Existe usuario con correo '{CORREO}':")
            print(f"  Contraseña en BD: '{por_correo[2]}'")
            print(f"  Contraseña buscada: '{CONTRASENA}'")
            print(f"  ¿Coinciden? {por_correo[2] == CONTRASENA}")
        else:
            print(f"\n✗ No existe usuario con correo '{CORREO}'")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("="*60)

