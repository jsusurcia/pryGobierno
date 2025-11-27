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
    
    # Posiciones predefinidas para las firmas (en puntos, desde abajo-izquierda)
    POSICIONES_FIRMA = {
        1: {'x': 50, 'y': 50, 'ancho': 150, 'alto': 60},    # Primera firma: abajo izquierda
        2: {'x': 250, 'y': 50, 'ancho': 150, 'alto': 60},   # Segunda firma: abajo centro
        3: {'x': 450, 'y': 50, 'ancho': 150, 'alto': 60},   # Tercera firma: abajo derecha
        4: {'x': 50, 'y': 120, 'ancho': 150, 'alto': 60},   # Cuarta firma: segunda fila izquierda
        5: {'x': 250, 'y': 120, 'ancho': 150, 'alto': 60},  # Quinta firma: segunda fila centro
        6: {'x': 450, 'y': 120, 'ancho': 150, 'alto': 60},  # Sexta firma: segunda fila derecha
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
    def agregar_firma_a_pdf(pdf_bytes, firma_base64, nombre_firmante, orden_firma):
        """
        Añade una firma visual a un PDF existente
        
        Args:
            pdf_bytes: Bytes del PDF original
            firma_base64: Imagen de la firma en base64
            nombre_firmante: Nombre completo del firmante
            orden_firma: Orden de esta firma (1, 2, 3...)
            
        Returns:
            bytes: PDF con la firma añadida o None si falla
        """
        try:
            # Convertir firma base64 a imagen
            firma_imagen = FirmaService.base64_a_imagen(firma_base64)
            if not firma_imagen:
                print("❌ No se pudo procesar la imagen de la firma")
                return None
            
            # Obtener posición para esta firma
            posicion = FirmaService.POSICIONES_FIRMA.get(orden_firma)
            if not posicion:
                print(f"⚠️ No hay posición definida para firma #{orden_firma}, usando posición por defecto")
                posicion = {'x': 50, 'y': 50 + ((orden_firma - 1) * 70), 'ancho': 150, 'alto': 60}
            
            # Leer el PDF original
            pdf_reader = PdfReader(BytesIO(pdf_bytes))
            pdf_writer = PdfWriter()
            
            # Crear una página con la firma usando ReportLab
            packet = BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            
            # Guardar la imagen de la firma temporalmente
            firma_buffer = BytesIO()
            firma_imagen.save(firma_buffer, format='PNG')
            firma_buffer.seek(0)
            
            # Dibujar la firma en el canvas
            can.drawImage(
                ImageReader(firma_buffer),
                posicion['x'],
                posicion['y'],
                width=posicion['ancho'],
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
            
            print(f"✅ Firma de '{nombre_firmante}' añadida al PDF (orden #{orden_firma})")
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

