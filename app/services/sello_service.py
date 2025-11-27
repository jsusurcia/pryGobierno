"""
Servicio para gestionar sellos institucionales de usuarios
Los sellos se suben a Cloudinary como imágenes
"""
import cloudinary
import cloudinary.uploader
from datetime import datetime
from werkzeug.utils import secure_filename

class SelloService:
    """Servicio para subir y gestionar sellos institucionales"""
    
    @staticmethod
    def subir_sello(archivo_imagen, id_usuario):
        """
        Sube un sello institucional a Cloudinary
        
        Args:
            archivo_imagen: Archivo de imagen (FileStorage de Flask)
            id_usuario: ID del usuario propietario del sello
            
        Returns:
            str: URL del sello en Cloudinary o None si falla
        """
        try:
            # Validar que sea imagen
            extensiones_validas = ['png', 'jpg', 'jpeg', 'gif']
            nombre_archivo = secure_filename(archivo_imagen.filename)
            extension = nombre_archivo.rsplit('.', 1)[1].lower() if '.' in nombre_archivo else ''
            
            if extension not in extensiones_validas:
                print(f"❌ Extensión no válida: {extension}")
                return None
            
            # Leer el archivo
            archivo_imagen.seek(0)
            
            # Public ID único para el sello
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            public_id = f"sellos/usuario_{id_usuario}_{timestamp}"
            
            # Subir a Cloudinary
            print(f"📤 Subiendo sello a Cloudinary: {public_id}")
            resultado = cloudinary.uploader.upload(
                archivo_imagen,
                public_id=public_id,
                folder="sellos_institucionales",
                resource_type="image",
                overwrite=False,
                transformation=[
                    {'width': 500, 'height': 500, 'crop': 'limit'},  # Limitar tamaño
                    {'quality': 'auto'}  # Optimizar calidad
                ]
            )
            
            url = resultado.get('secure_url')
            print(f"✅ Sello subido exitosamente")
            print(f"   URL: {url}")
            return url
            
        except Exception as e:
            print(f"❌ Error al subir sello: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def actualizar_sello_usuario(id_usuario, url_sello):
        """
        Actualiza la URL del sello en la BD
        
        Args:
            id_usuario: ID del usuario
            url_sello: URL del sello en Cloudinary
            
        Returns:
            bool: True si se actualizó correctamente
        """
        try:
            from ConexionBD import get_connection
            
            conexion = get_connection()
            if not conexion:
                return False
            
            sql = "UPDATE USUARIO SET url_sello = %s WHERE id_usuario = %s"
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (url_sello, id_usuario))
                conexion.commit()
            
            conexion.close()
            
            print(f"✅ Sello actualizado para usuario {id_usuario}")
            return True
            
        except Exception as e:
            print(f"❌ Error al actualizar sello en BD: {e}")
            return False
    
    @staticmethod
    def obtener_sello_usuario(id_usuario):
        """
        Obtiene la URL del sello de un usuario
        
        Args:
            id_usuario: ID del usuario
            
        Returns:
            str: URL del sello o None si no tiene
        """
        try:
            from ConexionBD import get_connection
            
            conexion = get_connection()
            if not conexion:
                return None
            
            sql = "SELECT url_sello FROM USUARIO WHERE id_usuario = %s"
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                resultado = cursor.fetchone()
            
            conexion.close()
            
            return resultado[0] if resultado and resultado[0] else None
            
        except Exception as e:
            print(f"❌ Error al obtener sello: {e}")
            return None
    
    @staticmethod
    def eliminar_sello_cloudinary(url_sello):
        """
        Elimina un sello de Cloudinary (opcional)
        
        Args:
            url_sello: URL del sello en Cloudinary
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            # Extraer public_id de la URL
            # URL formato: https://res.cloudinary.com/.../sellos_institucionales/sello_xxx.png
            if 'cloudinary.com' in url_sello:
                partes = url_sello.split('/')
                # Encontrar el índice de 'upload'
                idx_upload = partes.index('upload')
                # El public_id está después de 'upload' y la versión
                public_id_parts = partes[idx_upload + 2:]  # Saltar 'upload' y versión
                public_id = '/'.join(public_id_parts).rsplit('.', 1)[0]  # Sin extensión
                
                resultado = cloudinary.uploader.destroy(public_id)
                print(f"🗑️ Sello eliminado de Cloudinary: {public_id}")
                return resultado.get('result') == 'ok'
            
            return False
            
        except Exception as e:
            print(f"❌ Error al eliminar sello: {e}")
            return False

