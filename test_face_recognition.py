"""
Test simple de face_recognition para verificar que dlib funciona
"""
import cv2
import face_recognition
import numpy as np

print("=" * 60)
print("TEST DE FACE_RECOGNITION")
print("=" * 60)

# Crear una imagen de prueba simple (un cuadrado rojo)
print("\n1. Creando imagen de prueba...")
imagen_test = np.zeros((480, 640, 3), dtype=np.uint8)
imagen_test[:, :] = [0, 0, 255]  # Rojo en RGB

print(f"   Shape: {imagen_test.shape}")
print(f"   Dtype: {imagen_test.dtype}")
print(f"   Min/Max: {imagen_test.min()}/{imagen_test.max()}")
print(f"   Flags C_CONTIGUOUS: {imagen_test.flags['C_CONTIGUOUS']}")

# Intentar detectar rostros en la imagen de prueba
print("\n2. Intentando detectar rostros en imagen de prueba...")
try:
    face_locations = face_recognition.face_locations(imagen_test)
    print(f"   ✓ face_recognition funciona! Rostros detectados: {len(face_locations)}")
except Exception as e:
    print(f"   ✗ ERROR: {e}")
    print("\n   Esto indica un problema con la instalación de dlib")

# Test con cv2
print("\n3. Test con cv2.VideoCapture...")
print("   Intentando abrir la cámara...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("   ✗ No se pudo abrir la cámara")
else:
    print("   ✓ Cámara abierta correctamente")
    
    # Capturar un frame
    ret, frame = cap.read()
    
    if ret:
        print(f"   ✓ Frame capturado - Shape: {frame.shape}, Dtype: {frame.dtype}")
        
        # Convertir a RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        print(f"   ✓ Convertido a RGB - Shape: {frame_rgb.shape}, Dtype: {frame_rgb.dtype}")
        
        # Intentar detectar rostros
        print("\n4. Intentando detectar rostros en frame de cámara...")
        try:
            face_locations = face_recognition.face_locations(frame_rgb)
            print(f"   ✓ face_recognition funciona! Rostros detectados: {len(face_locations)}")
            
            if len(face_locations) > 0:
                print(f"   Ubicaciones: {face_locations[0]}")
        except Exception as e:
            print(f"   ✗ ERROR: {e}")
    else:
        print("   ✗ No se pudo capturar frame")
    
    cap.release()

print("\n" + "=" * 60)
print("FIN DEL TEST")
print("=" * 60)

