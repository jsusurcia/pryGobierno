"""
Controlador de Biometría Facial - VERSIÓN SIMPLE SIN DLIB
===========================================================
Sistema de reconocimiento facial usando SOLO OpenCV.
Guarda los rostros y hace comparación por histogramas.
"""

import numpy as np
import cv2
import base64
import pickle
from io import BytesIO
from PIL import Image
from ConexionBD import get_connection


class ControlBiometria:
    """Controlador para gestión de biometría facial - SOLO OpenCV"""
    
    # Umbral de similitud (0-1, donde 1 es idéntico)
    UMBRAL_SIMILITUD = 0.65  # 65% de similitud mínima
    
    @staticmethod
    def base64_a_imagen(base64_string):
        """
        Convierte una imagen en base64 a un array numpy (RGB)
        
        Args:
            base64_string: String en formato base64
            
        Returns:
            numpy.ndarray: Imagen en formato RGB, o None si hay error
        """
        try:
            # Remover el prefijo data:image si existe
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decodificar base64
            imagen_bytes = base64.b64decode(base64_string)
            
            # Convertir a imagen PIL
            imagen_pil = Image.open(BytesIO(imagen_bytes))
            
            # Convertir a RGB
            if imagen_pil.mode != 'RGB':
                imagen_pil = imagen_pil.convert('RGB')
            
            # Convertir a numpy array
            imagen_np = np.array(imagen_pil, dtype=np.uint8)
            
            return imagen_np
            
        except Exception as e:
            print(f"❌ Error al convertir base64 a imagen: {e}")
            return None
    
    @staticmethod
    def detectar_rostro(imagen_rgb):
        """
        Detecta y recorta el rostro en una imagen usando OpenCV Haar Cascade
        
        Args:
            imagen_rgb: Imagen en formato RGB (numpy array)
            
        Returns:
            numpy.ndarray: Imagen del rostro recortado y redimensionado, o None
        """
        try:
            print("🔍 Detectando rostro con OpenCV Haar Cascade...")
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(imagen_rgb, cv2.COLOR_RGB2GRAY)
            
            # Cargar clasificador Haar Cascade
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            
            # Detectar rostros (configuración permisiva)
            rostros = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            if len(rostros) == 0:
                print("❌ No se detectó ningún rostro")
                return None
            
            print(f"✅ Detectados {len(rostros)} rostro(s)")
            
            # Si hay múltiples rostros, usar el más grande
            if len(rostros) > 1:
                rostro = max(rostros, key=lambda r: r[2] * r[3])
            else:
                rostro = rostros[0]
            
            # Recortar rostro con margen
            x, y, w, h = rostro
            margen = int(w * 0.2)
            x1 = max(0, x - margen)
            y1 = max(0, y - margen)
            x2 = min(imagen_rgb.shape[1], x + w + margen)
            y2 = min(imagen_rgb.shape[0], y + h + margen)
            
            rostro_recortado = imagen_rgb[y1:y2, x1:x2]
            
            # Redimensionar a tamaño estándar para comparación
            rostro_estandar = cv2.resize(rostro_recortado, (200, 200))
            
            print(f"✅ Rostro recortado y redimensionado: {rostro_estandar.shape}")
            
            return rostro_estandar
            
        except Exception as e:
            print(f"❌ Error al detectar rostro: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def calcular_histograma(rostro):
        """
        Calcula el histograma de un rostro para comparación
        
        Args:
            rostro: Imagen del rostro (RGB)
            
        Returns:
            numpy.ndarray: Histograma normalizado
        """
        try:
            # Convertir a HSV para mejor representación de color
            hsv = cv2.cvtColor(rostro, cv2.COLOR_RGB2HSV)
            
            # Calcular histograma 3D (Hue, Saturation, Value)
            hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
            
            # Normalizar
            hist = cv2.normalize(hist, hist).flatten()
            
            return hist
            
        except Exception as e:
            print(f"❌ Error al calcular histograma: {e}")
            return None
    
    @staticmethod
    def comparar_rostros(rostro1, rostro2):
        """
        Compara dos rostros usando histogramas
        
        Args:
            rostro1: Primer rostro (numpy array RGB 200x200)
            rostro2: Segundo rostro (numpy array RGB 200x200)
            
        Returns:
            float: Similitud (0-1, donde 1 es idéntico)
        """
        try:
            hist1 = ControlBiometria.calcular_histograma(rostro1)
            hist2 = ControlBiometria.calcular_histograma(rostro2)
            
            if hist1 is None or hist2 is None:
                return 0.0
            
            # Comparar usando correlación (rango -1 a 1, ajustamos a 0-1)
            similitud = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            similitud = max(0.0, similitud)  # Asegurar que esté entre 0 y 1
            
            print(f"📊 Similitud calculada: {similitud:.4f}")
            
            return similitud
            
        except Exception as e:
            print(f"❌ Error al comparar rostros: {e}")
            return 0.0
    
    @staticmethod
    def registrar_rostro(id_usuario, imagen_base64):
        """
        Registra el rostro de un usuario en la base de datos
        
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
            
            # Detectar y recortar rostro
            rostro = ControlBiometria.detectar_rostro(imagen)
            if rostro is None:
                return {'exito': False, 'mensaje': 'No se detectó ningún rostro en la imagen'}
            
            # Serializar el rostro
            rostro_serializado = pickle.dumps(rostro)
            
            # Guardar en base de datos
            conexion = get_connection()
            if not conexion:
                return {'exito': False, 'mensaje': 'Error de conexión a la base de datos'}
            
            try:
                with conexion.cursor() as cursor:
                    sql = """
                        UPDATE USUARIO 
                        SET encoding_facial = %s,
                            tiene_biometria = TRUE,
                            fecha_registro_facial = CURRENT_TIMESTAMP
                        WHERE id_usuario = %s
                    """
                    cursor.execute(sql, (rostro_serializado, id_usuario))
                    conexion.commit()
                    
                    print(f"✅ Rostro registrado exitosamente para usuario {id_usuario}")
                    return {'exito': True, 'mensaje': 'Rostro registrado exitosamente'}
                    
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al registrar rostro: {e}")
            import traceback
            traceback.print_exc()
            return {'exito': False, 'mensaje': f'Error al registrar rostro: {str(e)}'}
    
    @staticmethod
    def tiene_biometria(id_usuario):
        """
        Verifica si un usuario tiene biometría registrada
        
        Args:
            id_usuario: ID del usuario
            
        Returns:
            bool: True si tiene biometría, False si no
        """
        try:
            conexion = get_connection()
            if not conexion:
                return False
            
            try:
                with conexion.cursor() as cursor:
                    sql = "SELECT tiene_biometria FROM USUARIO WHERE id_usuario = %s"
                    cursor.execute(sql, (id_usuario,))
                    resultado = cursor.fetchone()
                    
                    if resultado:
                        return resultado[0] if resultado[0] is not None else False
                    return False
                    
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al verificar biometría: {e}")
            return False
    
    @staticmethod
    def verificar_rostro(correo, contrasena, imagen_base64):
        """
        Verifica las credenciales y el rostro de un usuario
        
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
                    WHERE correo = %s AND contrasena = %s AND estado = TRUE
                """
                
                with conexion.cursor() as cursor:
                    cursor.execute(sql, (correo, contrasena))
                    usuario = cursor.fetchone()
                    
                    if not usuario:
                        return {'exito': False, 'mensaje': 'Credenciales incorrectas', 'usuario': None}
                    
                    # Verificar si tiene biometría registrada
                    if not usuario[8]:  # tiene_biometria
                        return {'exito': False, 'mensaje': 'Usuario no tiene biometría registrada', 'usuario': None}
                    
                    # Obtener rostro almacenado
                    rostro_almacenado_bytes = usuario[7]  # encoding_facial
                    if not rostro_almacenado_bytes:
                        return {'exito': False, 'mensaje': 'Datos biométricos no encontrados', 'usuario': None}
                    
                    rostro_almacenado = pickle.loads(rostro_almacenado_bytes)
                    
                    # Detectar rostro en imagen actual
                    imagen = ControlBiometria.base64_a_imagen(imagen_base64)
                    if imagen is None:
                        return {'exito': False, 'mensaje': 'Error al procesar la imagen', 'usuario': None}
                    
                    rostro_actual = ControlBiometria.detectar_rostro(imagen)
                    if rostro_actual is None:
                        return {'exito': False, 'mensaje': 'No se detectó ningún rostro', 'usuario': None}
                    
                    # Comparar rostros
                    similitud = ControlBiometria.comparar_rostros(rostro_almacenado, rostro_actual)
                    
                    print(f"📊 Similitud: {similitud:.2%}, Umbral: {ControlBiometria.UMBRAL_SIMILITUD:.2%}")
                    
                    if similitud >= ControlBiometria.UMBRAL_SIMILITUD:
                        usuario_dict = {
                            'id_usuario': usuario[0],
                            'nombre': usuario[1],
                            'ape_pat': usuario[2],
                            'ape_mat': usuario[3],
                            'correo': usuario[4],
                            'id_rol': usuario[5],
                            'estado': usuario[6]
                        }
                        return {'exito': True, 'mensaje': 'Verificación biométrica exitosa', 'usuario': usuario_dict}
                    else:
                        return {'exito': False, 'mensaje': f'El rostro no coincide (similitud: {similitud:.2%})', 'usuario': None}
                    
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al verificar rostro: {e}")
            import traceback
            traceback.print_exc()
            return {'exito': False, 'mensaje': f'Error al verificar rostro: {str(e)}', 'usuario': None}

