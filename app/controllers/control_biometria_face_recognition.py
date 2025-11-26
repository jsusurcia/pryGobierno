"""
Controlador de Biometría Facial - Adaptado del video de YouTube
================================================================
Enrolamiento: Captura foto → Detecta rostro → Codifica → Guarda en BD
Login: Video streaming → Compara cada frame con encoding de BD
"""

import numpy as np
import cv2
import base64
import pickle
import face_recognition
from ConexionBD import get_connection


class ControlBiometriaFR:
    """Controlador de biometría facial simple y directo"""
    
    # Umbral de distancia (0.6 es el recomendado por face_recognition)
    UMBRAL_DISTANCIA = 0.6
    
    # Número de frames consecutivos requeridos para login
    FRAMES_REQUERIDOS = 50
    
    @staticmethod
    def base64_a_array(base64_string):
        """
        Convierte base64 a array numpy (simple y directo)
        """
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
            print(f"❌ Error en base64_a_array: {e}")
            return None
    
    @staticmethod
    def registrar_rostro(id_usuario, imagen_base64):
        """
        Registra el encoding facial de un usuario
        (Adaptado de la primera imagen del video de YouTube)
        
        Args:
            id_usuario: ID del usuario
            imagen_base64: Imagen capturada en base64
            
        Returns:
            dict: {'exito': bool, 'mensaje': str}
        """
        try:
            print(f"🔄 Registrando rostro para usuario {id_usuario}")
            
            # Convertir base64 a imagen (BGR)
            image = ControlBiometriaFR.base64_a_array(imagen_base64)
            
            if image is None:
                return {'exito': False, 'mensaje': 'Error al procesar la imagen'}
            
            # IMPORTANTE: Convertir BGR (OpenCV) a RGB (face_recognition)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            print(f"✓ Convertido a RGB: {image.shape}")
            
            # PASO 1: Detectar ubicación del rostro (como en el video)
            print("🔍 Detectando rostro...")
            face_loc = face_recognition.face_locations(image)
            
            if len(face_loc) == 0:
                print("❌ No se detectó rostro")
                return {'exito': False, 'mensaje': 'No se detectó ningún rostro'}
            
            # Tomar el primer rostro [0]
            face_loc = face_loc[0]
            print(f"✅ Rostro detectado en: {face_loc}")
            
            # PASO 2: Codificar el rostro (como en el video)
            print("🔐 Codificando rostro a 128-d...")
            face_image_encodings = face_recognition.face_encodings(
                image, 
                known_face_locations=[face_loc]
            )[0]
            
            print(f"✅ Encoding generado: shape {face_image_encodings.shape}")
            
            # PASO 3: Guardar en base de datos
            encoding_bytes = pickle.dumps(face_image_encodings)
            
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
                    cursor.execute(sql, (encoding_bytes, id_usuario))
                    conexion.commit()
                    
                    print(f"✅ Encoding guardado en BD para usuario {id_usuario}")
                    return {'exito': True, 'mensaje': 'Rostro registrado exitosamente'}
                    
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al registrar rostro: {e}")
            import traceback
            traceback.print_exc()
            return {'exito': False, 'mensaje': f'Error: {str(e)}'}
    
    @staticmethod
    def obtener_encoding_usuario(correo, contrasena):
        """
        Obtiene el encoding guardado de un usuario
        
        Returns:
            dict: {'exito': bool, 'encoding': array, 'usuario': dict, 'mensaje': str}
        """
        try:
            conexion = get_connection()
            if not conexion:
                return {
                    'exito': False,
                    'encoding': None,
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
                            'encoding': None,
                            'usuario': None,
                            'mensaje': 'Credenciales incorrectas'
                        }
                    
                    if not usuario[8]:  # tiene_biometria
                        return {
                            'exito': False,
                            'encoding': None,
                            'usuario': None,
                            'mensaje': 'Usuario no tiene biometría registrada'
                        }
                    
                    # Deserializar encoding
                    encoding_bytes = usuario[7]
                    if not encoding_bytes:
                        return {
                            'exito': False,
                            'encoding': None,
                            'usuario': None,
                            'mensaje': 'Datos biométricos no encontrados'
                        }
                    
                    encoding = pickle.loads(encoding_bytes)
                    
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
                        'encoding': encoding,
                        'usuario': usuario_dict,
                        'mensaje': 'OK'
                    }
                    
            finally:
                conexion.close()
                
        except Exception as e:
            print(f"❌ Error al obtener encoding: {e}")
            return {
                'exito': False,
                'encoding': None,
                'usuario': None,
                'mensaje': str(e)
            }
    
    @staticmethod
    def verificar_frame(encoding_guardado, frame_base64):
        """
        Verifica un frame del video contra el encoding guardado
        (Adaptado de la segunda imagen del video de YouTube)
        
        Args:
            encoding_guardado: Encoding del usuario (desde BD)
            frame_base64: Frame actual del video en base64
            
        Returns:
            dict: {'coincide': bool, 'distancia': float, 'face_location': tuple, 'mensaje': str}
        """
        try:
            # Convertir frame base64 a imagen (BGR)
            frame = ControlBiometriaFR.base64_a_array(frame_base64)
            
            if frame is None:
                return {
                    'coincide': False,
                    'distancia': 1.0,
                    'face_location': None,
                    'mensaje': 'Error al procesar frame'
                }
            
            # Convertir BGR a RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar rostros en el frame (como en el video)
            face_locations = face_recognition.face_locations(frame)
            
            if len(face_locations) == 0:
                return {
                    'coincide': False,
                    'distancia': 1.0,
                    'face_location': None,
                    'mensaje': 'No se detectó rostro'
                }
            
            # Tomar el primer rostro
            face_location = face_locations[0]
            
            # Codificar el rostro del frame (como en el video)
            face_frame_encodings = face_recognition.face_encodings(
                frame,
                known_face_locations=[face_location]
            )[0]
            
            # Comparar con el encoding guardado (como en el video: compare_faces)
            result = face_recognition.compare_faces(
                [encoding_guardado], 
                face_frame_encodings,
                tolerance=ControlBiometriaFR.UMBRAL_DISTANCIA
            )
            
            # Calcular distancia
            distancia = face_recognition.face_distance([encoding_guardado], face_frame_encodings)[0]
            
            coincide = result[0]
            
            return {
                'coincide': coincide,
                'distancia': float(distancia),
                'face_location': face_location,
                'mensaje': 'Match' if coincide else 'No match'
            }
            
        except Exception as e:
            print(f"❌ Error al verificar frame: {e}")
            return {
                'coincide': False,
                'distancia': 1.0,
                'face_location': None,
                'mensaje': str(e)
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
