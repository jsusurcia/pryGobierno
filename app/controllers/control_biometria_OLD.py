"""
Controlador de Biometría Facial
===============================
Sistema de reconocimiento facial usando face_recognition y OpenCV.
Permite registrar y verificar rostros de usuarios.
"""

import face_recognition
import numpy as np
import cv2
import base64
import pickle
from io import BytesIO
from PIL import Image
from ConexionBD import get_connection


class ControlBiometria:
    """Controlador para gestión de biometría facial"""
    
    # Umbral de tolerancia para comparación de rostros
    # Menor valor = más estricto (0.4-0.6 es recomendado)
    # Aumentado a 0.6 para ser más permisivo
    TOLERANCIA = 0.6
    
    @staticmethod
    def base64_a_imagen(base64_string):
        """
        Convierte una imagen en base64 a un array numpy (BGR para OpenCV)
        
        Args:
            base64_string: String en formato base64 (puede incluir prefijo data:image)
            
        Returns:
            numpy.ndarray: Imagen en formato BGR, o None si hay error
        """
        try:
            # Remover el prefijo data:image si existe
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decodificar base64
            imagen_bytes = base64.b64decode(base64_string)
            
            # Convertir a imagen PIL
            imagen_pil = Image.open(BytesIO(imagen_bytes))
            
            # Convertir a RGB si es necesario
            if imagen_pil.mode != 'RGB':
                imagen_pil = imagen_pil.convert('RGB')
            
            # Convertir a numpy array
            imagen_np = np.array(imagen_pil)
            
            # Asegurarse de que sea uint8 y RGB
            if imagen_np.dtype != np.uint8:
                imagen_np = imagen_np.astype(np.uint8)
            
            # Verificar que tenga 3 canales (RGB)
            if len(imagen_np.shape) == 2:
                import cv2
                imagen_np = cv2.cvtColor(imagen_np, cv2.COLOR_GRAY2RGB)
            
            # CRÍTICO: Asegurar que sea C-contiguous (requerido por face_recognition)
            if not imagen_np.flags['C_CONTIGUOUS']:
                imagen_np = np.ascontiguousarray(imagen_np)
            
            return imagen_np
            
        except Exception as e:
            print(f"❌ Error al convertir base64 a imagen: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def detectar_rostro(imagen_np):
        """
        Detecta si hay un rostro en la imagen usando OpenCV Haar Cascade (MÁS PERMISIVO)
        
        Args:
            imagen_np: Imagen como numpy array (RGB)
            
        Returns:
            tuple: (hay_rostro: bool, cantidad_rostros: int, ubicaciones: list)
        """
        try:
            import cv2
            
            print("🔍 Usando detector Haar Cascade de OpenCV (mucho más permisivo)...")
            
            # Asegurar que sea uint8
            if imagen_np.dtype != np.uint8:
                imagen_np = imagen_np.astype(np.uint8)
            
            # Convertir RGB a BGR para OpenCV
            imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_RGB2BGR)
            # Convertir a escala de grises
            gray = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2GRAY)
            
            # Cargar el clasificador Haar Cascade para detección facial
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Detectar rostros (configuración MUY permisiva)
            rostros = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,      # Factor de escala (1.1 es más permisivo que 1.3)
                minNeighbors=3,       # Mínimo 3 vecinos (menos estricto que 5)
                minSize=(30, 30),     # Tamaño mínimo del rostro
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            cantidad = len(rostros)
            hay_rostro = cantidad > 0
            
            if hay_rostro:
                print(f"✅ Haar Cascade detectó {cantidad} rostro(s)")
            else:
                print("⚠️ Haar Cascade no detectó rostros")
            
            # Convertir formato de OpenCV (x, y, w, h) a formato face_recognition (top, right, bottom, left)
            ubicaciones = []
            for (x, y, w, h) in rostros:
                # face_recognition usa: (top, right, bottom, left)
                top = y
                right = x + w
                bottom = y + h
                left = x
                ubicaciones.append((top, right, bottom, left))
            
            return hay_rostro, cantidad, ubicaciones
            
        except Exception as e:
            print(f"❌ Error al detectar rostro: {e}")
            import traceback
            traceback.print_exc()
            return False, 0, []
    
    @staticmethod
    def generar_encoding(imagen_np):
        """
        Genera el encoding facial (vector de 128 dimensiones) de una imagen
        USA OPENCV HAAR CASCADE para detección (MUY PERMISIVO) + face_recognition para encoding
        
        Args:
            imagen_np: Imagen como numpy array (RGB)
            
        Returns:
            numpy.ndarray: Encoding facial de 128 dimensiones, o None si no hay rostro
        """
        try:
            import cv2
            
            print("🔍 Iniciando detección con OpenCV Haar Cascade...")
            
            # PASO 0: Preparar imagen original para face_recognition (RGB)
            # Asegurar que sea una copia limpia
            imagen_original = imagen_np.copy()
            
            # Asegurar uint8
            if imagen_original.dtype != np.uint8:
                imagen_original = imagen_original.astype(np.uint8)
            
            # Asegurar RGB
            if len(imagen_original.shape) == 2:  # Grayscale
                imagen_original = cv2.cvtColor(imagen_original, cv2.COLOR_GRAY2RGB)
            elif imagen_original.shape[2] == 4:  # RGBA
                imagen_original = cv2.cvtColor(imagen_original, cv2.COLOR_RGBA2RGB)
            
            # Asegurar C-contiguous (CRÍTICO para dlib)
            imagen_original = np.ascontiguousarray(imagen_original, dtype=np.uint8)
            
            # PASO 1: Detectar rostro con OpenCV Haar Cascade (MUY PERMISIVO)
            # Convertir a escala de grises DIRECTAMENTE desde la imagen original
            gray = cv2.cvtColor(imagen_original, cv2.COLOR_RGB2GRAY)
            
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Detección permisiva
            rostros = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            if len(rostros) == 0:
                print("❌ OpenCV Haar Cascade no detectó ningún rostro")
                return None
            
            print(f"✅ OpenCV detectó {len(rostros)} rostro(s)")
            
            # Si hay múltiples rostros, usar el más grande
            if len(rostros) > 1:
                rostros = [max(rostros, key=lambda r: r[2] * r[3])]  # El más grande por área
                print(f"⚠️ Usando el rostro más grande")
            
            # PASO 2: Recortar la región del rostro (más confiable)
            x, y, w, h = rostros[0]
            
            # Agregar margen del 20% para capturar todo el rostro
            margen_x = int(w * 0.2)
            margen_y = int(h * 0.2)
            
            x1 = max(0, x - margen_x)
            y1 = max(0, y - margen_y)
            x2 = min(imagen_original.shape[1], x + w + margen_x)
            y2 = min(imagen_original.shape[0], y + h + margen_y)
            
            # Recortar rostro
            rostro_recortado = imagen_original[y1:y2, x1:x2].copy()
            
            # SOLUCIÓN EXTREMA: Guardar como archivo temporal y cargar con face_recognition
            print("💾 Guardando imagen temporal para cargar con método oficial...")
            import tempfile
            import os
            from PIL import Image as PILImage
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_path = tmp_file.name
                
            try:
                # Guardar como JPG usando PIL
                pil_image = PILImage.fromarray(rostro_recortado, mode='RGB')
                pil_image.save(tmp_path, 'JPEG', quality=95)
                print(f"✓ Imagen guardada en: {tmp_path}")
                
                # Cargar con el método oficial de face_recognition
                print("📂 Cargando imagen con face_recognition.load_image_file()...")
                imagen_cargada = face_recognition.load_image_file(tmp_path)
                
                print(f"📊 Imagen cargada: dtype={imagen_cargada.dtype}, shape={imagen_cargada.shape}")
                
                # PASO 3: Generar encoding
                print("🧬 Generando encoding con face_recognition...")
                encodings = face_recognition.face_encodings(
                    imagen_cargada,
                    num_jitters=1
                )
                
            finally:
                # Eliminar archivo temporal
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    print("🗑️ Archivo temporal eliminado")
            
            if encodings:
                print("✅ Encoding generado exitosamente!")
                return encodings[0]
            else:
                print("⚠️ No se pudo generar el encoding facial")
                return None
                
        except Exception as e:
            print(f"❌ Error al generar encoding: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def comparar_encodings(encoding_nuevo, encoding_guardado, tolerancia=None):
        """
        Compara dos encodings faciales para verificar si son la misma persona
        
        Args:
            encoding_nuevo: Encoding del rostro a verificar
            encoding_guardado: Encoding almacenado en la BD
            tolerancia: Umbral de tolerancia (opcional)
            
        Returns:
            tuple: (coincide: bool, distancia: float)
        """
        try:
            if tolerancia is None:
                tolerancia = ControlBiometria.TOLERANCIA
            
            # Calcular distancia euclidiana entre encodings
            distancia = face_recognition.face_distance([encoding_guardado], encoding_nuevo)[0]
            
            # Verificar si está dentro del umbral
            coincide = distancia <= tolerancia
            
            # Calcular porcentaje de similitud (para mostrar al usuario)
            similitud = max(0, (1 - distancia) * 100)
            
            print(f"📊 Distancia: {distancia:.4f} | Similitud: {similitud:.1f}% | Coincide: {coincide}")
            
            return coincide, distancia, similitud
            
        except Exception as e:
            print(f"❌ Error al comparar encodings: {e}")
            return False, 1.0, 0.0
    
    @staticmethod
    def serializar_encoding(encoding):
        """
        Serializa un encoding numpy array a bytes para almacenar en PostgreSQL
        
        Args:
            encoding: numpy.ndarray de 128 dimensiones
            
        Returns:
            bytes: Encoding serializado con pickle
        """
        try:
            return pickle.dumps(encoding)
        except Exception as e:
            print(f"❌ Error al serializar encoding: {e}")
            return None
    
    @staticmethod
    def deserializar_encoding(encoding_bytes):
        """
        Deserializa bytes a un encoding numpy array
        
        Args:
            encoding_bytes: bytes o memoryview del encoding
            
        Returns:
            numpy.ndarray: Encoding de 128 dimensiones
        """
        try:
            # Si es memoryview, convertir a bytes
            if isinstance(encoding_bytes, memoryview):
                encoding_bytes = bytes(encoding_bytes)
            return pickle.loads(encoding_bytes)
        except Exception as e:
            print(f"❌ Error al deserializar encoding: {e}")
            return None
    
    @staticmethod
    def registrar_rostro(id_usuario, imagen_base64):
        """
        Registra el rostro de un usuario en la base de datos
        MODO PERMISIVO: Acepta incluso si la detección no es perfecta
        
        Args:
            id_usuario: ID del usuario
            imagen_base64: Imagen del rostro en formato base64
            
        Returns:
            dict: {'exito': bool, 'mensaje': str}
        """
        try:
            print(f"🔄 Iniciando registro facial para usuario {id_usuario}")
            
            # Convertir base64 a imagen
            imagen = ControlBiometria.base64_a_imagen(imagen_base64)
            if imagen is None:
                return {'exito': False, 'mensaje': 'Error al procesar la imagen'}
            
            print(f"✓ Imagen convertida: {imagen.shape}")
            
            # MODO PERMISIVO: Intentar generar encoding directamente sin validación estricta
            print("🔍 Intentando generar encoding (modo permisivo)...")
            encoding = ControlBiometria.generar_encoding(imagen)
            
            if encoding is None:
                # Si falla, intentar con la imagen original sin mejoras
                print("⚠️ Falló con mejoras, intentando con imagen original...")
                imagen_original = ControlBiometria.base64_a_imagen_sin_mejoras(imagen_base64)
                if imagen_original is not None:
                    encoding = ControlBiometria.generar_encoding(imagen_original)
            
            if encoding is None:
                return {'exito': False, 'mensaje': 'No se pudo detectar ningún rostro en la imagen. Intenta con mejor iluminación o usa tu teléfono.'}
            
            print("✓ Encoding generado exitosamente")
            
            # Serializar encoding
            encoding_bytes = ControlBiometria.serializar_encoding(encoding)
            if encoding_bytes is None:
                return {'exito': False, 'mensaje': 'Error al procesar el encoding facial'}
            
            # Guardar en base de datos
            conexion = get_connection()
            if not conexion:
                return {'exito': False, 'mensaje': 'Error de conexión a la base de datos'}
            
            try:
                sql = """
                    UPDATE USUARIO 
                    SET encoding_facial = %s,
                        tiene_biometria = TRUE,
                        fecha_registro_facial = NOW()
                    WHERE id_usuario = %s
                """
                
                with conexion.cursor() as cursor:
                    cursor.execute(sql, (encoding_bytes, id_usuario))
                    conexion.commit()
                
                print(f"✅ Rostro registrado exitosamente para usuario {id_usuario}")
                return {'exito': True, 'mensaje': 'Rostro registrado exitosamente'}
                
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al registrar rostro: {e}")
            import traceback
            traceback.print_exc()
            return {'exito': False, 'mensaje': f'Error inesperado: {str(e)}'}
    
    @staticmethod
    def base64_a_imagen_sin_mejoras(base64_string):
        """Convierte base64 a imagen SIN mejoras de procesamiento"""
        try:
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            imagen_bytes = base64.b64decode(base64_string)
            imagen_pil = Image.open(BytesIO(imagen_bytes))
            if imagen_pil.mode != 'RGB':
                imagen_pil = imagen_pil.convert('RGB')
            imagen_np = np.array(imagen_pil)
            # Asegurar uint8 y C-contiguous (CRÍTICO)
            imagen_np = np.ascontiguousarray(imagen_np.astype(np.uint8))
            return imagen_np
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    @staticmethod
    def verificar_rostro(correo, contrasena, imagen_base64):
        """
        Verifica las credenciales y el rostro de un usuario para el login
        
        Args:
            correo: Correo electrónico del usuario
            contrasena: Contraseña del usuario
            imagen_base64: Imagen del rostro en formato base64
            
        Returns:
            dict: {'exito': bool, 'mensaje': str, 'usuario': dict or None}
        """
        try:
            # Primero verificar credenciales
            conexion = get_connection()
            if not conexion:
                return {'exito': False, 'mensaje': 'Error de conexión a la base de datos', 'usuario': None}
            
            try:
                sql = """
                    SELECT id_usuario, nombre, ape_pat, ape_mat, correo, 
                           id_rol, estado, encoding_facial, tiene_biometria
                    FROM USUARIO 
                    WHERE correo = %s AND contrasena = %s
                """
                
                with conexion.cursor() as cursor:
                    cursor.execute(sql, (correo, contrasena))
                    usuario = cursor.fetchone()
                
                if not usuario:
                    return {'exito': False, 'mensaje': 'Correo o contraseña incorrectos', 'usuario': None}
                
                # Mapear resultado a diccionario
                usuario_dict = {
                    'id_usuario': usuario[0],
                    'nombre': usuario[1],
                    'ape_pat': usuario[2],
                    'ape_mat': usuario[3],
                    'correo': usuario[4],
                    'id_rol': usuario[5],
                    'estado': usuario[6],
                    'encoding_facial': usuario[7],
                    'tiene_biometria': usuario[8]
                }
                
                # Verificar estado del usuario
                if not usuario_dict['estado']:
                    return {'exito': False, 'mensaje': 'Usuario inactivo. Contacte al administrador', 'usuario': None}
                
                # Verificar si tiene biometría registrada
                if not usuario_dict['tiene_biometria'] or usuario_dict['encoding_facial'] is None:
                    return {
                        'exito': False, 
                        'mensaje': 'No tiene rostro registrado. Por favor, registre su rostro primero.',
                        'usuario': None,
                        'requiere_registro': True,
                        'id_usuario': usuario_dict['id_usuario']
                    }
                
                # Convertir imagen base64 a numpy array
                imagen = ControlBiometria.base64_a_imagen(imagen_base64)
                if imagen is None:
                    return {'exito': False, 'mensaje': 'Error al procesar la imagen del rostro', 'usuario': None}
                
                # Detectar rostro en la imagen
                hay_rostro, cantidad, _ = ControlBiometria.detectar_rostro(imagen)
                
                if not hay_rostro:
                    return {'exito': False, 'mensaje': 'No se detectó ningún rostro. Asegúrese de estar frente a la cámara', 'usuario': None}
                
                if cantidad > 1:
                    return {'exito': False, 'mensaje': 'Se detectaron múltiples rostros. Solo debe aparecer un rostro', 'usuario': None}
                
                # Generar encoding del rostro capturado
                encoding_nuevo = ControlBiometria.generar_encoding(imagen)
                if encoding_nuevo is None:
                    return {'exito': False, 'mensaje': 'No se pudo procesar el rostro', 'usuario': None}
                
                # Deserializar encoding guardado
                encoding_guardado = ControlBiometria.deserializar_encoding(usuario_dict['encoding_facial'])
                if encoding_guardado is None:
                    return {'exito': False, 'mensaje': 'Error al recuperar datos biométricos', 'usuario': None}
                
                # Comparar encodings
                coincide, distancia, similitud = ControlBiometria.comparar_encodings(encoding_nuevo, encoding_guardado)
                
                if coincide:
                    # Limpiar datos sensibles antes de retornar
                    del usuario_dict['encoding_facial']
                    del usuario_dict['tiene_biometria']
                    
                    return {
                        'exito': True, 
                        'mensaje': f'Verificación exitosa (Similitud: {similitud:.1f}%)',
                        'usuario': usuario_dict,
                        'similitud': similitud
                    }
                else:
                    return {
                        'exito': False, 
                        'mensaje': f'El rostro no coincide con el usuario registrado (Similitud: {similitud:.1f}%)',
                        'usuario': None,
                        'similitud': similitud
                    }
                    
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error en verificar_rostro: {e}")
            import traceback
            traceback.print_exc()
            return {'exito': False, 'mensaje': f'Error inesperado: {str(e)}', 'usuario': None}
    
    @staticmethod
    def obtener_usuarios_sin_biometria():
        """
        Obtiene lista de usuarios que no tienen rostro registrado
        
        Returns:
            list: Lista de diccionarios con datos de usuarios sin biometría
        """
        try:
            conexion = get_connection()
            if not conexion:
                return []
            
            try:
                sql = """
                    SELECT id_usuario, nombre, ape_pat, ape_mat, correo
                    FROM USUARIO 
                    WHERE (tiene_biometria = FALSE OR tiene_biometria IS NULL)
                    AND estado = TRUE
                    ORDER BY nombre, ape_pat
                """
                
                with conexion.cursor() as cursor:
                    cursor.execute(sql)
                    usuarios = cursor.fetchall()
                
                return [
                    {
                        'id_usuario': u[0],
                        'nombre_completo': f"{u[1]} {u[2]} {u[3]}",
                        'correo': u[4]
                    }
                    for u in usuarios
                ]
                
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al obtener usuarios sin biometría: {e}")
            return []
    
    @staticmethod
    def tiene_biometria(id_usuario):
        """
        Verifica si un usuario tiene biometría registrada
        
        Args:
            id_usuario: ID del usuario
            
        Returns:
            bool: True si tiene biometría, False en caso contrario
        """
        try:
            conexion = get_connection()
            if not conexion:
                return False
            
            try:
                sql = """
                    SELECT tiene_biometria 
                    FROM USUARIO 
                    WHERE id_usuario = %s
                """
                
                with conexion.cursor() as cursor:
                    cursor.execute(sql, (id_usuario,))
                    resultado = cursor.fetchone()
                
                return resultado[0] if resultado else False
                
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al verificar biometría: {e}")
            return False
    
    @staticmethod
    def eliminar_biometria(id_usuario):
        """
        Elimina los datos biométricos de un usuario
        
        Args:
            id_usuario: ID del usuario
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            conexion = get_connection()
            if not conexion:
                return False
            
            try:
                sql = """
                    UPDATE USUARIO 
                    SET encoding_facial = NULL,
                        tiene_biometria = FALSE,
                        fecha_registro_facial = NULL
                    WHERE id_usuario = %s
                """
                
                with conexion.cursor() as cursor:
                    cursor.execute(sql, (id_usuario,))
                    conexion.commit()
                
                print(f"✅ Biometría eliminada para usuario {id_usuario}")
                return True
                
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al eliminar biometría: {e}")
            return False
    
    @staticmethod
    def verificar_solo_rostro(id_usuario, imagen_base64):
        """
        Verifica solo el rostro de un usuario (sin credenciales)
        Útil para re-autenticación o confirmación de identidad
        
        Args:
            id_usuario: ID del usuario
            imagen_base64: Imagen del rostro en formato base64
            
        Returns:
            dict: {'exito': bool, 'mensaje': str, 'similitud': float}
        """
        try:
            conexion = get_connection()
            if not conexion:
                return {'exito': False, 'mensaje': 'Error de conexión'}
            
            try:
                sql = """
                    SELECT encoding_facial, tiene_biometria 
                    FROM USUARIO 
                    WHERE id_usuario = %s
                """
                
                with conexion.cursor() as cursor:
                    cursor.execute(sql, (id_usuario,))
                    resultado = cursor.fetchone()
                
                if not resultado:
                    return {'exito': False, 'mensaje': 'Usuario no encontrado'}
                
                encoding_bytes, tiene_biometria = resultado
                
                if not tiene_biometria or encoding_bytes is None:
                    return {'exito': False, 'mensaje': 'Usuario sin biometría registrada'}
                
                # Procesar imagen
                imagen = ControlBiometria.base64_a_imagen(imagen_base64)
                if imagen is None:
                    return {'exito': False, 'mensaje': 'Error al procesar imagen'}
                
                # Detectar y generar encoding
                hay_rostro, cantidad, _ = ControlBiometria.detectar_rostro(imagen)
                if not hay_rostro:
                    return {'exito': False, 'mensaje': 'No se detectó rostro'}
                
                encoding_nuevo = ControlBiometria.generar_encoding(imagen)
                if encoding_nuevo is None:
                    return {'exito': False, 'mensaje': 'Error al procesar rostro'}
                
                # Comparar
                encoding_guardado = ControlBiometria.deserializar_encoding(encoding_bytes)
                coincide, _, similitud = ControlBiometria.comparar_encodings(encoding_nuevo, encoding_guardado)
                
                if coincide:
                    return {'exito': True, 'mensaje': 'Rostro verificado', 'similitud': similitud}
                else:
                    return {'exito': False, 'mensaje': 'Rostro no coincide', 'similitud': similitud}
                    
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'exito': False, 'mensaje': str(e)}

