"""
Servicio para añadir firmas digitales visuales a archivos PDF
Utiliza PyPDF2 para leer PDFs y ReportLab para añadir la firma visual
"""
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from PIL import Image
from io import BytesIO
from datetime import datetime
import os
import base64

class FirmaService:
    """Servicio para añadir firmas visuales a PDFs"""
    
    # Configuración de posicionamiento de firmas
    FIRMA_BASE_Y = 120        # Altura inicial desde abajo (más alto = más arriba)
    FIRMA_ANCHO = 150         # Ancho de cada firma
    FIRMA_ALTO = 60           # Alto de cada firma
    FIRMA_MARGEN_X = 50       # Margen izquierdo
    FIRMA_ESPACIADO_X = 200   # Espacio horizontal entre firmas
    FIRMA_ESPACIADO_Y = 100   # Espacio vertical entre filas
    FIRMAS_POR_FILA = 3       # Número de firmas por fila
    
    @staticmethod
    def calcular_posicion_firma(orden_firma):
        """
        Calcula dinámicamente la posición de una firma basándose en su orden
        Las firmas se distribuyen en una cuadrícula de 3 columnas
        
        Args:
            orden_firma: Orden de la firma (0 = creador, 1+ = firmantes)
            
        Returns:
            dict: {'x': int, 'y': int, 'ancho': int, 'alto': int}
        """
        # Calcular fila y columna
        fila = orden_firma // FirmaService.FIRMAS_POR_FILA
        columna = orden_firma % FirmaService.FIRMAS_POR_FILA
        
        # Calcular posición X (de izquierda a derecha)
        x = FirmaService.FIRMA_MARGEN_X + (columna * FirmaService.FIRMA_ESPACIADO_X)
        
        # Calcular posición Y (de abajo hacia arriba)
        y = FirmaService.FIRMA_BASE_Y + (fila * FirmaService.FIRMA_ESPACIADO_Y)
        
        return {
            'x': x,
            'y': y,
            'ancho': FirmaService.FIRMA_ANCHO,
            'alto': FirmaService.FIRMA_ALTO
        }
    
    @staticmethod
    def base64_a_imagen(base64_string):
        """
        Convierte una cadena base64 a imagen PIL
        
        Args:
            base64_string: String en formato "data:image/png;base64,iVBORw0KG..."
            
        Returns:
            PIL.Image: Imagen PIL o None si falla
        """
        try:
            # Remover el prefijo "data:image/png;base64," si existe
            if 'base64,' in base64_string:
                base64_string = base64_string.split('base64,')[1]
            
            # Decodificar base64
            imagen_bytes = base64.b64decode(base64_string)
            imagen = Image.open(BytesIO(imagen_bytes))
            
            # Convertir a RGB si es RGBA (para compatibility)
            if imagen.mode == 'RGBA':
                # Crear fondo blanco
                fondo = Image.new('RGB', imagen.size, (255, 255, 255))
                fondo.paste(imagen, mask=imagen.split()[3])  # Usar canal alpha como máscara
                imagen = fondo
            
            return imagen
            
        except Exception as e:
            print(f"❌ Error al convertir base64 a imagen: {e}")
            return None
    
    @staticmethod
    def agregar_firma_a_pdf(pdf_bytes, firma_base64, nombre_firmante, orden_firma, sello_base64=None):
        """
        Añade una firma visual (y opcionalmente sello) a un PDF existente
        
        Args:
            pdf_bytes: Bytes del PDF original
            firma_base64: Imagen de la firma en base64
            nombre_firmante: Nombre completo del firmante
            orden_firma: Orden de esta firma (1, 2, 3...)
            sello_base64: Imagen del sello en base64 (opcional, solo para jefes)
            
        Returns:
            bytes: PDF con la firma (y sello) añadida o None si falla
        """
        try:
            # Convertir firma base64 a imagen
            firma_imagen = FirmaService.base64_a_imagen(firma_base64)
            if not firma_imagen:
                print("❌ No se pudo procesar la imagen de la firma")
                return None
            
            # Convertir sello base64 a imagen (si existe)
            sello_imagen = None
            if sello_base64:
                sello_imagen = FirmaService.base64_a_imagen(sello_base64)
                if not sello_imagen:
                    print("⚠️ No se pudo procesar la imagen del sello, continuando sin él")
            
            # Calcular posición dinámica para esta firma (evita superposiciones)
            posicion = FirmaService.calcular_posicion_firma(orden_firma)
            print(f"📍 Posición calculada para firma #{orden_firma}: x={posicion['x']}, y={posicion['y']}")
            
            # Leer el PDF original
            pdf_reader = PdfReader(BytesIO(pdf_bytes))
            pdf_writer = PdfWriter()
            
            # Crear una página con la firma usando ReportLab
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            
            # Si hay sello, dibujarlo primero (a la izquierda)
            if sello_imagen:
                print(f"🔐 Añadiendo sello institucional al PDF para {nombre_firmante}")
                sello_buffer = BytesIO()
                sello_imagen.save(sello_buffer, format='PNG')
                sello_buffer.seek(0)
                
                # Dibujar sello (tamaño mediano, a la izquierda)
                sello_size = 55  # Tamaño del sello en puntos
                can.drawImage(
                    ImageReader(sello_buffer),
                    posicion['x'],
                    posicion['y'] + 5,  # Alineado verticalmente con la firma
                    width=sello_size,
                    height=sello_size,
                    preserveAspectRatio=True,
                    mask='auto'
                )
                
                # Añadir borde alrededor del sello para destacarlo
                can.setStrokeColorRGB(0.7, 0.7, 0.7)  # Gris
                can.setLineWidth(0.5)
                can.rect(posicion['x'], posicion['y'] + 5, sello_size, sello_size, stroke=1, fill=0)
            
            # Guardar la imagen de la firma temporalmente
            firma_buffer = BytesIO()
            firma_imagen.save(firma_buffer, format='PNG')
            firma_buffer.seek(0)
            
            # Dibujar la firma en el canvas (al lado del sello si existe)
            firma_x_offset = 65 if sello_imagen else 0  # Espacio para el sello si existe
            firma_ancho_disponible = posicion['ancho'] - firma_x_offset
            
            print(f"✍️ Añadiendo firma al PDF para {nombre_firmante}")
            can.drawImage(
                ImageReader(firma_buffer),
                posicion['x'] + firma_x_offset,
                posicion['y'],
                width=firma_ancho_disponible,
                height=posicion['alto'],
                preserveAspectRatio=True,
                mask='auto'
            )
            
            # Añadir texto con el nombre y fecha
            can.setFont("Helvetica", 8)
            can.drawString(
                posicion['x'],
                posicion['y'] - 12,
                f"{nombre_firmante}"
            )
            can.drawString(
                posicion['x'],
                posicion['y'] - 22,
                f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            )
            
            can.save()
            
            # Mover al inicio del buffer
            packet.seek(0)
            
            # Leer la página con la firma
            firma_pdf = PdfReader(packet)
            firma_page = firma_pdf.pages[0]
            
            # Añadir la firma a la última página del PDF original
            for i, page in enumerate(pdf_reader.pages):
                if i == len(pdf_reader.pages) - 1:
                    # Última página: añadir la firma
                    page.merge_page(firma_page)
                pdf_writer.add_page(page)
            
            # Escribir el PDF resultante a bytes
            output_buffer = BytesIO()
            pdf_writer.write(output_buffer)
            output_buffer.seek(0)
            
            if sello_imagen:
                print(f"✅ FIRMA + SELLO de '{nombre_firmante}' añadidos al PDF (orden #{orden_firma})")
                print(f"   📐 Layout: [🔐 Sello 55x55] → [✍️ Firma {firma_ancho_disponible}x{posicion['alto']}]")
            else:
                print(f"✅ FIRMA de '{nombre_firmante}' añadida al PDF (orden #{orden_firma})")
                print(f"   📐 Layout: [✍️ Firma {posicion['ancho']}x{posicion['alto']}]")
            
            return output_buffer.getvalue()
            
        except Exception as e:
            print(f"❌ Error al agregar firma al PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def verificar_pdf_valido(pdf_bytes):
        """
        Verifica que los bytes correspondan a un PDF válido
        
        Args:
            pdf_bytes: Bytes del archivo
            
        Returns:
            bool: True si es un PDF válido
        """
        try:
            PdfReader(BytesIO(pdf_bytes))
            return True
        except Exception as e:
            print(f"❌ PDF inválido: {e}")
            return False
    
    @staticmethod
    def obtener_numero_paginas(pdf_bytes):
        """
        Obtiene el número de páginas de un PDF
        
        Args:
            pdf_bytes: Bytes del PDF
            
        Returns:
            int: Número de páginas o 0 si falla
        """
        try:
            pdf_reader = PdfReader(BytesIO(pdf_bytes))
            return len(pdf_reader.pages)
        except Exception as e:
            print(f"❌ Error al contar páginas: {e}")
            return 0
    
    @staticmethod
    def guardar_pdf_temporal(pdf_bytes, nombre_archivo):
        """
        Guarda un PDF en la carpeta temporal
        
        Args:
            pdf_bytes: Bytes del PDF
            nombre_archivo: Nombre del archivo
            
        Returns:
            str: Ruta del archivo guardado o None si falla
        """
        try:
            # Crear carpeta temporal si no existe
            temp_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'temp')
            os.makedirs(temp_folder, exist_ok=True)
            
            # Ruta completa
            filepath = os.path.join(temp_folder, nombre_archivo)
            
            # Guardar archivo
            with open(filepath, 'wb') as f:
                f.write(pdf_bytes)
            
            print(f"✅ PDF guardado temporalmente: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Error al guardar PDF temporal: {e}")
            return None
    
    @staticmethod
    def limpiar_archivos_temporales(max_edad_horas=24):
        """
        Limpia archivos temporales antiguos
        
        Args:
            max_edad_horas: Edad máxima en horas para mantener archivos
        """
        try:
            temp_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'temp')
            if not os.path.exists(temp_folder):
                return
            
            import time
            now = time.time()
            max_edad_segundos = max_edad_horas * 3600
            
            for filename in os.listdir(temp_folder):
                filepath = os.path.join(temp_folder, filename)
                if os.path.isfile(filepath):
                    edad = now - os.path.getmtime(filepath)
                    if edad > max_edad_segundos:
                        os.remove(filepath)
                        print(f"🗑️ Archivo temporal eliminado: {filename}")
                        
        except Exception as e:
            print(f"❌ Error al limpiar archivos temporales: {e}")

