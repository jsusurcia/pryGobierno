"""
Servicio para subir archivos PDF a Catbox
Catbox es un servicio gratuito de hosting de archivos
API: https://catbox.moe/user/api.php
"""
import requests
import os

class CatboxService:
    """Servicio para interactuar con la API de Catbox"""
    
    UPLOAD_URL = "https://catbox.moe/user/api.php"
    
    @staticmethod
    def subir_pdf(archivo_path):
        """
        Sube un archivo PDF a Catbox y retorna la URL
        
        Args:
            archivo_path: Ruta al archivo PDF en disco
            
        Returns:
            str: URL del archivo subido en Catbox o None si falla
        """
        try:
            if not os.path.exists(archivo_path):
                print(f"❌ El archivo no existe: {archivo_path}")
                return None
            
            # Verificar que sea un PDF
            if not archivo_path.lower().endswith('.pdf'):
                print(f"❌ El archivo no es un PDF: {archivo_path}")
                return None
            
            # Leer el archivo
            with open(archivo_path, 'rb') as file:
                files = {
                    'fileToUpload': (os.path.basename(archivo_path), file, 'application/pdf')
                }
                data = {
                    'reqtype': 'fileupload'
                }
                
                print(f"📤 Subiendo PDF a Catbox: {os.path.basename(archivo_path)}")
                response = requests.post(
                    CatboxService.UPLOAD_URL,
                    files=files,
                    data=data,
                    timeout=60  # 60 segundos timeout
                )
                
                if response.status_code == 200:
                    url = response.text.strip()
                    if url.startswith('http'):
                        print(f"✅ PDF subido exitosamente a Catbox")
                        print(f"   URL: {url}")
                        return url
                    else:
                        print(f"❌ Respuesta inválida de Catbox: {url}")
                        return None
                else:
                    print(f"❌ Error al subir a Catbox. Status: {response.status_code}")
                    print(f"   Respuesta: {response.text}")
                    return None
                    
        except requests.exceptions.Timeout:
            print("❌ Timeout al subir archivo a Catbox (>60s)")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión con Catbox: {e}")
            return None
        except Exception as e:
            print(f"❌ Error al subir PDF a Catbox: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def subir_desde_bytes(contenido_pdf, nombre_archivo):
        """
        Sube un PDF desde bytes en memoria a Catbox
        
        Args:
            contenido_pdf: Bytes del PDF
            nombre_archivo: Nombre del archivo (ej: "contrato_firmado.pdf")
            
        Returns:
            str: URL del archivo subido en Catbox o None si falla
        """
        try:
            if not nombre_archivo.lower().endswith('.pdf'):
                nombre_archivo += '.pdf'
            
            files = {
                'fileToUpload': (nombre_archivo, contenido_pdf, 'application/pdf')
            }
            data = {
                'reqtype': 'fileupload'
            }
            
            print(f"📤 Subiendo PDF a Catbox desde memoria: {nombre_archivo}")
            response = requests.post(
                CatboxService.UPLOAD_URL,
                files=files,
                data=data,
                timeout=60
            )
            
            if response.status_code == 200:
                url = response.text.strip()
                if url.startswith('http'):
                    print(f"✅ PDF subido exitosamente a Catbox")
                    print(f"   URL: {url}")
                    return url
                else:
                    print(f"❌ Respuesta inválida de Catbox: {url}")
                    return None
            else:
                print(f"❌ Error al subir a Catbox. Status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error al subir PDF a Catbox desde bytes: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def descargar_pdf(url):
        """
        Descarga un PDF desde una URL (Catbox u otra)
        
        Args:
            url: URL del archivo PDF
            
        Returns:
            bytes: Contenido del PDF o None si falla
        """
        try:
            print(f"📥 Descargando PDF desde: {url}")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ PDF descargado exitosamente ({len(response.content)} bytes)")
                return response.content
            else:
                print(f"❌ Error al descargar PDF. Status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error al descargar PDF: {e}")
            return None

