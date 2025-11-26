"""
Controlador de Biometría Facial - Solo OpenCV (Sin dlib)
=========================================================
Sistema simple y funcional usando únicamente OpenCV.
Enrolamiento: Captura foto → Detecta rostro → Guarda imagen en BD
Login: Video streaming → Compara cada frame con imagen guardada
"""

import numpy as np
import cv2
import base64
import pickle
from ConexionBD import get_connection


class ControlBiometriaOpenCV:
    """Controlador de biometría facial usando solo OpenCV"""
    
    # Umbral de similitud para ORB matcher (menor = más similar)
    UMBRAL_SIMILITUD = 40  # Distancia promedio máxima
    
    # Número de frames consecutivos requeridos para login
    FRAMES_REQUERIDOS = 30  # Reducido porque OpenCV es más rápido
    
    @staticmethod
    def base64_a_imagen(base64_string):
        """Convierte base64 a imagen OpenCV (BGR)"""
        try:
            # Remover prefijo data:image
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decodificar base64
            img_bytes = base64.b64decode(base64_string)
            
            # Convertir a numpy array
            nparr = np.frombuffer(img_bytes, np.uint8)
            
            # Decodificar con OpenCV (BGR)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                print("❌ Error al decodificar imagen")
                return None
            
            print(f"✓ Imagen decodificada: {img.shape}")
            return img
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    @staticmethod
    def detectar_rostro(imagen_bgr):
        """
        Detecta y recorta el rostro principal en una imagen
        
        Returns:
            numpy.ndarray: Imagen del rostro recortado, o None si no se detecta
        """
        try:
            print("🔍 Detectando rostro con OpenCV...")
            
            # Convertir a escala de grises
            gray = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2GRAY)
            
            # Cargar clasificador Haar Cascade
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            # Detectar rostros
            rostros = face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100)
            )
            
            if len(rostros) == 0:
                print("❌ No se detectó ningún rostro")
                return None
            
            print(f"✅ Detectados {len(rostros)} rostro(s)")
            
            # Si hay múltiples rostros, tomar el más grande
            if len(rostros) > 1:
                rostro = max(rostros, key=lambda r: r[2] * r[3])
            else:
                rostro = rostros[0]
            
            # Recortar rostro
            x, y, w, h = rostro
            rostro_img = imagen_bgr[y:y+h, x:x+w]
            
            # Redimensionar a tamaño estándar (importante para comparación)
            rostro_std = cv2.resize(rostro_img, (200, 200))
            
            print(f"✅ Rostro recortado: {rostro_std.shape}")
            
            return rostro_std
            
        except Exception as e:
            print(f"❌ Error al detectar rostro: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def comparar_rostros_orb(rostro1, rostro2):
        """
        Compara dos rostros usando ORB (Oriented FAST and Rotated BRIEF)
        Método robusto y rápido para matching de características
        
        Returns:
            tuple: (bool coincide, float distancia_promedio)
        """
        try:
            # Convertir a escala de grises
            gray1 = cv2.cvtColor(rostro1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(rostro2, cv2.COLOR_BGR2GRAY)
            
            # Crear detector ORB
            orb = cv2.ORB_create(nfeatures=500)
            
            # Detectar keypoints y descriptores
            kp1, des1 = orb.detectAndCompute(gray1, None)
            kp2, des2 = orb.detectAndCompute(gray2, None)
            
            if des1 is None or des2 is None:
                print("⚠️ No se encontraron características")
                return False, 100.0
            
            # Crear matcher BFMatcher
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
            
            # Emparejar descriptores
            matches = bf.match(des1, des2)
            
            if len(matches) < 10:
                print(f"⚠️ Muy pocas coincidencias: {len(matches)}")
                return False, 100.0
            
            # Calcular distancia promedio
            distancias = [m.distance for m in matches]
            distancia_promedio = sum(distancias) / len(distancias)
            
            # Determinar si coincide
            coincide = distancia_promedio <= ControlBiometriaOpenCV.UMBRAL_SIMILITUD
            
            print(f"📊 Matches: {len(matches)}, Distancia: {distancia_promedio:.2f}, Coincide: {coincide}")
            
            return coincide, float(distancia_promedio)
            
        except Exception as e:
            print(f"❌ Error al comparar: {e}")
            return False, 100.0
    
    @staticmethod
    def registrar_rostro(id_usuario, imagen_base64):
        """
        Registra el rostro de un usuario
        
        Args:
            id_usuario: ID del usuario
            imagen_base64: Imagen capturada en base64
            
        Returns:
            dict: {'exito': bool, 'mensaje': str}
        """
        try:
            print(f"🔄 Registrando rostro para usuario {id_usuario}")
            
            # Convertir base64 a imagen
            imagen = ControlBiometriaOpenCV.base64_a_imagen(imagen_base64)
            
            if imagen is None:
                return {'exito': False, 'mensaje': 'Error al procesar la imagen'}
            
            # Detectar y recortar rostro
            rostro = ControlBiometriaOpenCV.detectar_rostro(imagen)
            
            if rostro is None:
                return {'exito': False, 'mensaje': 'No se detectó ningún rostro'}
            
            # Serializar la imagen del rostro
            rostro_bytes = pickle.dumps(rostro)
            
            # Guardar en base de datos
            conexion = get_connection()
            if not conexion:
                return {'exito': False, 'mensaje': 'Error de conexión a BD'}
            
            try:
                with conexion.cursor() as cursor:
                    sql = """
                        UPDATE USUARIO 
                        SET encoding_facial = %s,
                            tiene_biometria = TRUE,
                            fecha_registro_facial = CURRENT_TIMESTAMP
                        WHERE id_usuario = %s
                    """
                    cursor.execute(sql, (rostro_bytes, id_usuario))
                    conexion.commit()
                    
                    print(f"✅ Rostro guardado en BD para usuario {id_usuario}")
                    return {'exito': True, 'mensaje': 'Rostro registrado exitosamente'}
                    
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al registrar rostro: {e}")
            import traceback
            traceback.print_exc()
            return {'exito': False, 'mensaje': f'Error: {str(e)}'}
    
    @staticmethod
    def obtener_rostro_usuario(correo, contrasena):
        """
        Obtiene el rostro guardado de un usuario
        
        Returns:
            dict: {'exito': bool, 'rostro': array, 'usuario': dict, 'mensaje': str}
        """
        try:
            conexion = get_connection()
            if not conexion:
                return {
                    'exito': False,
                    'rostro': None,
                    'usuario': None,
                    'mensaje': 'Error de conexión a BD'
                }
            
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
                        return {
                            'exito': False,
                            'rostro': None,
                            'usuario': None,
                            'mensaje': 'Credenciales incorrectas'
                        }
                    
                    if not usuario[8]:  # tiene_biometria
                        return {
                            'exito': False,
                            'rostro': None,
                            'usuario': None,
                            'mensaje': 'Usuario no tiene biometría registrada'
                        }
                    
                    # Deserializar imagen del rostro
                    rostro_bytes = usuario[7]
                    if not rostro_bytes:
                        return {
                            'exito': False,
                            'rostro': None,
                            'usuario': None,
                            'mensaje': 'Datos biométricos no encontrados'
                        }
                    
                    rostro = pickle.loads(rostro_bytes)
                    
                    usuario_dict = {
                        'id_usuario': usuario[0],
                        'nombre': usuario[1],
                        'ape_pat': usuario[2],
                        'ape_mat': usuario[3],
                        'correo': usuario[4],
                        'id_rol': usuario[5],
                        'estado': usuario[6]
                    }
                    
                    return {
                        'exito': True,
                        'rostro': rostro,
                        'usuario': usuario_dict,
                        'mensaje': 'OK'
                    }
                    
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al obtener rostro: {e}")
            return {
                'exito': False,
                'rostro': None,
                'usuario': None,
                'mensaje': str(e)
            }
    
    @staticmethod
    def verificar_frame(rostro_guardado, frame_base64):
        """
        Verifica un frame del video contra el rostro guardado
        
        Args:
            rostro_guardado: Imagen del rostro del usuario (desde BD)
            frame_base64: Frame actual del video en base64
            
        Returns:
            dict: {'coincide': bool, 'distancia': float, 'mensaje': str}
        """
        try:
            # Convertir frame base64 a imagen
            frame = ControlBiometriaOpenCV.base64_a_imagen(frame_base64)
            
            if frame is None:
                return {
                    'coincide': False,
                    'distancia': 100.0,
                    'mensaje': 'Error al procesar frame'
                }
            
            # Detectar rostro en el frame actual
            rostro_actual = ControlBiometriaOpenCV.detectar_rostro(frame)
            
            if rostro_actual is None:
                return {
                    'coincide': False,
                    'distancia': 100.0,
                    'mensaje': 'No se detectó rostro'
                }
            
            # Comparar usando ORB
            coincide, distancia = ControlBiometriaOpenCV.comparar_rostros_orb(
                rostro_guardado,
                rostro_actual
            )
            
            return {
                'coincide': coincide,
                'distancia': distancia,
                'mensaje': 'Match' if coincide else 'No match'
            }
            
        except Exception as e:
            print(f"❌ Error al verificar frame: {e}")
            return {
                'coincide': False,
                'distancia': 100.0,
                'mensaje': str(e)
            }
    
    @staticmethod
    def verificar_rostro(correo, contrasena, imagen_base64):
        """
        Verifica credenciales y rostro (para login tradicional)
        
        Returns:
            dict: {'exito': bool, 'mensaje': str, 'usuario': dict or None}
        """
        try:
            # Obtener rostro guardado del usuario
            resultado_usuario = ControlBiometriaOpenCV.obtener_rostro_usuario(correo, contrasena)
            
            if not resultado_usuario['exito']:
                return {
                    'exito': False,
                    'mensaje': resultado_usuario['mensaje'],
                    'usuario': None
                }
            
            rostro_guardado = resultado_usuario['rostro']
            usuario = resultado_usuario['usuario']
            
            # Convertir imagen actual
            imagen_actual = ControlBiometriaOpenCV.base64_a_imagen(imagen_base64)
            if imagen_actual is None:
                return {
                    'exito': False,
                    'mensaje': 'Error al procesar la imagen',
                    'usuario': None
                }
            
            # Detectar rostro en imagen actual
            rostro_actual = ControlBiometriaOpenCV.detectar_rostro(imagen_actual)
            if rostro_actual is None:
                return {
                    'exito': False,
                    'mensaje': 'No se detectó rostro en la imagen',
                    'usuario': None
                }
            
            # Comparar rostros
            coincide, distancia = ControlBiometriaOpenCV.comparar_rostros_orb(
                rostro_guardado,
                rostro_actual
            )
            
            if coincide:
                return {
                    'exito': True,
                    'mensaje': 'Verificación exitosa',
                    'usuario': usuario,
                    'distancia': distancia
                }
            else:
                return {
                    'exito': False,
                    'mensaje': f'El rostro no coincide (distancia: {distancia:.2f})',
                    'usuario': None
                }
                
        except Exception as e:
            print(f"❌ Error al verificar rostro: {e}")
            import traceback
            traceback.print_exc()
            return {
                'exito': False,
                'mensaje': str(e),
                'usuario': None
            }
    
    @staticmethod
    def tiene_biometria(id_usuario):
        """Verifica si un usuario tiene biometría registrada"""
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
            print(f"❌ Error: {e}")
            return False

