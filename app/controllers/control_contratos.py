"""
Controlador para gestión de contratos y firmas electrónicas
"""
from ConexionBD import get_connection
from services.catbox_service import CatboxService
from services.firma_service import FirmaService
from controllers.control_notificaciones import ControlNotificaciones
from controllers.control_Usuarios import controlUsuarios
from datetime import datetime

class ControlContratos:
    """Controlador para gestión de contratos con firmas electrónicas"""
    
    @staticmethod
    def crear_contrato(titulo, descripcion, pdf_bytes, firmantes_data, id_usuario_creador):
        """
        Crea un nuevo contrato con lista de firmantes
        
        Args:
            titulo: Título del contrato
            descripcion: Descripción del contrato
            pdf_bytes: Bytes del PDF original (sin firmar)
            firmantes_data: Lista de dicts con {'id_usuario': int, 'orden': int}
            id_usuario_creador: ID del usuario que crea el contrato
            
        Returns:
            dict: {'success': bool, 'id_contrato': int, 'message': str}
        """
        try:
            # Validar PDF
            if not FirmaService.verificar_pdf_valido(pdf_bytes):
                return {'success': False, 'message': 'El archivo no es un PDF válido'}
            
            # Subir PDF original a Catbox
            print("📤 Subiendo PDF original a Catbox...")
            nombre_archivo = f"contrato_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            pdf_temporal = FirmaService.guardar_pdf_temporal(pdf_bytes, nombre_archivo)
            
            if not pdf_temporal:
                return {'success': False, 'message': 'Error al guardar PDF temporal'}
            
            url_catbox = CatboxService.subir_pdf(pdf_temporal)
            
            # Limpiar archivo temporal
            import os
            try:
                os.remove(pdf_temporal)
            except:
                pass
            
            if not url_catbox:
                return {'success': False, 'message': 'Error al subir PDF a Catbox'}
            
            # Insertar en la BD
            conexion = get_connection()
            if not conexion:
                return {'success': False, 'message': 'Error de conexión a la BD'}
            
            with conexion.cursor() as cursor:
                # Insertar contrato
                sql_contrato = """
                    INSERT INTO CONTRATO (titulo, descripcion, url_archivo, estado, fecha_creacion)
                    VALUES (%s, %s, %s, 'P', NOW())
                    RETURNING id_contrato
                """
                cursor.execute(sql_contrato, (titulo, descripcion, url_catbox))
                id_contrato = cursor.fetchone()[0]
                
                # Insertar firmantes con su orden
                sql_firmante = """
                    INSERT INTO CONTRATO_FIRMA_PENDIENTE 
                    (id_contrato, id_usuario, orden, firmado)
                    VALUES (%s, %s, %s, FALSE)
                """
                for firmante in firmantes_data:
                    cursor.execute(sql_firmante, (
                        id_contrato,
                        firmante['id_usuario'],
                        firmante['orden']
                    ))
                
                conexion.commit()
            
            conexion.close()
            
            # Notificar al primer firmante (orden = 1)
            primer_firmante = next((f for f in firmantes_data if f['orden'] == 1), None)
            if primer_firmante:
                ControlNotificaciones.crear_notificacion(
                    id_usuario=primer_firmante['id_usuario'],
                    titulo=f"Nuevo Contrato para Firmar: {titulo}",
                    mensaje=f"Tienes un nuevo contrato pendiente de firma. Eres el primer firmante.",
                    tipo="contrato",
                    id_referencia=id_contrato
                )
            
            print(f"✅ Contrato creado exitosamente (ID: {id_contrato})")
            return {
                'success': True,
                'id_contrato': id_contrato,
                'message': 'Contrato creado exitosamente'
            }
            
        except Exception as e:
            print(f"❌ Error al crear contrato: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    @staticmethod
    def obtener_contratos_pendientes_usuario(id_usuario):
        """
        Obtiene los contratos pendientes de firma para un usuario
        
        Returns:
            list: Lista de contratos pendientes
        """
        try:
            sql = """
                SELECT 
                    c.id_contrato,
                    c.titulo,
                    c.descripcion,
                    c.url_archivo,
                    c.fecha_creacion,
                    cfp.orden,
                    cfp.id_firma
                FROM CONTRATO c
                INNER JOIN CONTRATO_FIRMA_PENDIENTE cfp 
                    ON c.id_contrato = cfp.id_contrato
                WHERE c.estado = 'P'
                    AND cfp.id_usuario = %s
                    AND cfp.firmado = FALSE
                    AND cfp.rechazo = FALSE
                ORDER BY c.fecha_creacion DESC
            """
            
            conexion = get_connection()
            if not conexion:
                return []
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_usuario,))
                resultados = cursor.fetchall()
            
            conexion.close()
            
            contratos = []
            for row in resultados:
                # Verificar si es el turno de este usuario (todos los anteriores ya firmaron)
                es_su_turno = ControlContratos.es_turno_de_firmar(row[0], id_usuario)
                
                contratos.append({
                    'id_contrato': row[0],
                    'titulo': row[1],
                    'descripcion': row[2],
                    'url_archivo': row[3],
                    'fecha_creacion': row[4],
                    'orden': row[5],
                    'id_firma': row[6],
                    'es_su_turno': es_su_turno
                })
            
            return contratos
            
        except Exception as e:
            print(f"❌ Error al obtener contratos pendientes: {e}")
            return []
    
    @staticmethod
    def es_turno_de_firmar(id_contrato, id_usuario):
        """
        Verifica si es el turno de un usuario para firmar
        (Todos los firmantes con orden menor ya deben haber firmado)
        
        Returns:
            bool: True si es su turno
        """
        try:
            sql = """
                SELECT orden FROM CONTRATO_FIRMA_PENDIENTE
                WHERE id_contrato = %s AND id_usuario = %s
            """
            
            conexion = get_connection()
            if not conexion:
                return False
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_contrato, id_usuario))
                resultado = cursor.fetchone()
                
                if not resultado:
                    conexion.close()
                    return False
                
                orden_usuario = resultado[0]
                
                # Verificar que todos los anteriores hayan firmado
                sql_anteriores = """
                    SELECT COUNT(*) FROM CONTRATO_FIRMA_PENDIENTE
                    WHERE id_contrato = %s 
                        AND orden < %s 
                        AND (firmado = FALSE OR rechazo = TRUE)
                """
                cursor.execute(sql_anteriores, (id_contrato, orden_usuario))
                pendientes_anteriores = cursor.fetchone()[0]
            
            conexion.close()
            
            # Es su turno si no hay pendientes anteriores
            return pendientes_anteriores == 0
            
        except Exception as e:
            print(f"❌ Error al verificar turno de firma: {e}")
            return False
    
    @staticmethod
    def firmar_contrato(id_contrato, id_usuario, firma_base64):
        """
        Firma un contrato: añade la firma visual al PDF y actualiza la BD
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Verificar que sea el turno del usuario
            if not ControlContratos.es_turno_de_firmar(id_contrato, id_usuario):
                return {'success': False, 'message': 'Aún no es tu turno para firmar'}
            
            # Obtener datos del contrato y del usuario
            contrato = ControlContratos.obtener_contrato_por_id(id_contrato)
            if not contrato:
                return {'success': False, 'message': 'Contrato no encontrado'}
            
            usuario = controlUsuarios.buscar_por_ID(id_usuario)
            if not usuario:
                return {'success': False, 'message': 'Usuario no encontrado'}
            
            nombre_completo = f"{usuario['nombre']} {usuario['ape_pat']} {usuario['ape_mat']}"
            
            # Descargar el PDF actual desde Catbox
            print(f"📥 Descargando PDF actual...")
            pdf_bytes = CatboxService.descargar_pdf(contrato['url_archivo'])
            if not pdf_bytes:
                return {'success': False, 'message': 'Error al descargar el PDF'}
            
            # Obtener el orden de esta firma
            orden_firma = ControlContratos.obtener_orden_firma(id_contrato, id_usuario)
            if not orden_firma:
                return {'success': False, 'message': 'No se pudo determinar el orden de firma'}
            
            # Añadir la firma visual al PDF
            print(f"✍️ Añadiendo firma de {nombre_completo}...")
            pdf_firmado = FirmaService.agregar_firma_a_pdf(
                pdf_bytes,
                firma_base64,
                nombre_completo,
                orden_firma
            )
            
            if not pdf_firmado:
                return {'success': False, 'message': 'Error al añadir la firma al PDF'}
            
            # Subir el PDF firmado a Catbox
            print(f"📤 Subiendo PDF firmado a Catbox...")
            nombre_archivo = f"contrato_{id_contrato}_firma_{orden_firma}.pdf"
            url_firmado = CatboxService.subir_desde_bytes(pdf_firmado, nombre_archivo)
            
            if not url_firmado:
                return {'success': False, 'message': 'Error al subir el PDF firmado'}
            
            # Actualizar la BD
            conexion = get_connection()
            if not conexion:
                return {'success': False, 'message': 'Error de conexión a la BD'}
            
            with conexion.cursor() as cursor:
                # Actualizar URL del contrato
                sql_update_contrato = """
                    UPDATE CONTRATO SET url_archivo = %s WHERE id_contrato = %s
                """
                cursor.execute(sql_update_contrato, (url_firmado, id_contrato))
                
                # Marcar como firmado
                sql_update_firma = """
                    UPDATE CONTRATO_FIRMA_PENDIENTE
                    SET firmado = TRUE, fecha_firma = NOW()
                    WHERE id_contrato = %s AND id_usuario = %s
                """
                cursor.execute(sql_update_firma, (id_contrato, id_usuario))
                
                # Verificar si hay más firmantes
                sql_siguiente = """
                    SELECT id_usuario, orden FROM CONTRATO_FIRMA_PENDIENTE
                    WHERE id_contrato = %s AND orden > %s AND firmado = FALSE
                    ORDER BY orden ASC LIMIT 1
                """
                cursor.execute(sql_siguiente, (id_contrato, orden_firma))
                siguiente_firmante = cursor.fetchone()
                
                # Si no hay más firmantes, marcar contrato como firmado completo
                if not siguiente_firmante:
                    sql_finalizar = """
                        UPDATE CONTRATO SET estado = 'F' WHERE id_contrato = %s
                    """
                    cursor.execute(sql_finalizar, (id_contrato,))
                    
                    # Notificar a todos los firmantes
                    sql_todos_firmantes = """
                        SELECT DISTINCT id_usuario FROM CONTRATO_FIRMA_PENDIENTE
                        WHERE id_contrato = %s
                    """
                    cursor.execute(sql_todos_firmantes, (id_contrato,))
                    todos_firmantes = cursor.fetchall()
                    
                    conexion.commit()
                    
                    for (id_firmante,) in todos_firmantes:
                        ControlNotificaciones.crear_notificacion(
                            id_usuario=id_firmante,
                            titulo=f"✅ Contrato Completado: {contrato['titulo']}",
                            mensaje=f"Todos los firmantes han firmado el contrato. El proceso está completo.",
                            tipo="contrato",
                            id_referencia=id_contrato
                        )
                    
                    mensaje_resultado = 'Contrato firmado completamente'
                else:
                    # Notificar al siguiente firmante
                    conexion.commit()
                    
                    ControlNotificaciones.crear_notificacion(
                        id_usuario=siguiente_firmante[0],
                        titulo=f"Tu Turno para Firmar: {contrato['titulo']}",
                        mensaje=f"{nombre_completo} ha firmado el contrato. Ahora es tu turno (Firma #{siguiente_firmante[1]}).",
                        tipo="contrato",
                        id_referencia=id_contrato
                    )
                    
                    mensaje_resultado = f'Firma registrada. Notificando al siguiente firmante.'
            
            conexion.close()
            
            print(f"✅ Contrato firmado exitosamente por {nombre_completo}")
            return {'success': True, 'message': mensaje_resultado}
            
        except Exception as e:
            print(f"❌ Error al firmar contrato: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    @staticmethod
    def rechazar_contrato(id_contrato, id_usuario, motivo):
        """
        Rechaza un contrato y registra el motivo
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        try:
            # Verificar que sea el turno del usuario
            if not ControlContratos.es_turno_de_firmar(id_contrato, id_usuario):
                return {'success': False, 'message': 'No puedes rechazar este contrato ahora'}
            
            contrato = ControlContratos.obtener_contrato_por_id(id_contrato)
            if not contrato:
                return {'success': False, 'message': 'Contrato no encontrado'}
            
            usuario = controlUsuarios.buscar_por_ID(id_usuario)
            nombre_completo = f"{usuario['nombre']} {usuario['ape_pat']}" if usuario else "Usuario"
            
            conexion = get_connection()
            if not conexion:
                return {'success': False, 'message': 'Error de conexión a la BD'}
            
            with conexion.cursor() as cursor:
                # Obtener id_firma
                sql_get_firma = """
                    SELECT id_firma FROM CONTRATO_FIRMA_PENDIENTE
                    WHERE id_contrato = %s AND id_usuario = %s
                """
                cursor.execute(sql_get_firma, (id_contrato, id_usuario))
                resultado_firma = cursor.fetchone()
                id_firma = resultado_firma[0] if resultado_firma else None
                
                # Marcar contrato como rechazado
                sql_update_contrato = """
                    UPDATE CONTRATO SET estado = 'R' WHERE id_contrato = %s
                """
                cursor.execute(sql_update_contrato, (id_contrato,))
                
                # Marcar la firma como rechazada
                sql_update_firma = """
                    UPDATE CONTRATO_FIRMA_PENDIENTE
                    SET rechazo = TRUE, comentario_rechazo = %s
                    WHERE id_contrato = %s AND id_usuario = %s
                """
                cursor.execute(sql_update_firma, (motivo, id_contrato, id_usuario))
                
                # Registrar en historial de rechazos
                sql_rechazo = """
                    INSERT INTO CONTRATO_RECHAZO 
                    (id_contrato, id_usuario, motivo, id_firma_pendiente)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql_rechazo, (id_contrato, id_usuario, motivo, id_firma))
                
                # Obtener todos los firmantes para notificarlos
                sql_firmantes = """
                    SELECT DISTINCT id_usuario FROM CONTRATO_FIRMA_PENDIENTE
                    WHERE id_contrato = %s AND id_usuario != %s
                """
                cursor.execute(sql_firmantes, (id_contrato, id_usuario))
                firmantes = cursor.fetchall()
                
                conexion.commit()
                
                # Notificar a todos los demás firmantes
                for (id_firmante,) in firmantes:
                    ControlNotificaciones.crear_notificacion(
                        id_usuario=id_firmante,
                        titulo=f"❌ Contrato Rechazado: {contrato['titulo']}",
                        mensaje=f"{nombre_completo} ha rechazado el contrato. Motivo: {motivo}",
                        tipo="contrato",
                        id_referencia=id_contrato
                    )
            
            conexion.close()
            
            print(f"⚠️ Contrato rechazado por {nombre_completo}")
            return {'success': True, 'message': 'Contrato rechazado exitosamente'}
            
        except Exception as e:
            print(f"❌ Error al rechazar contrato: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    @staticmethod
    def obtener_contrato_por_id(id_contrato):
        """Obtiene un contrato por su ID"""
        try:
            sql = """
                SELECT id_contrato, titulo, descripcion, url_archivo, 
                       estado, fecha_creacion
                FROM CONTRATO WHERE id_contrato = %s
            """
            
            conexion = get_connection()
            if not conexion:
                return None
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_contrato,))
                row = cursor.fetchone()
            
            conexion.close()
            
            if not row:
                return None
            
            return {
                'id_contrato': row[0],
                'titulo': row[1],
                'descripcion': row[2],
                'url_archivo': row[3],
                'estado': row[4],
                'fecha_creacion': row[5]
            }
            
        except Exception as e:
            print(f"❌ Error al obtener contrato: {e}")
            return None
    
    @staticmethod
    def obtener_orden_firma(id_contrato, id_usuario):
        """Obtiene el orden de firma de un usuario en un contrato"""
        try:
            sql = """
                SELECT orden FROM CONTRATO_FIRMA_PENDIENTE
                WHERE id_contrato = %s AND id_usuario = %s
            """
            
            conexion = get_connection()
            if not conexion:
                return None
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (id_contrato, id_usuario))
                resultado = cursor.fetchone()
            
            conexion.close()
            
            return resultado[0] if resultado else None
            
        except Exception as e:
            print(f"❌ Error al obtener orden de firma: {e}")
            return None
    
    @staticmethod
    def obtener_historial_contrato(id_contrato):
        """
        Obtiene el historial completo de un contrato
        
        Returns:
            dict con listas de firmantes y rechazos
        """
        try:
            conexion = get_connection()
            if not conexion:
                return None
            
            with conexion.cursor() as cursor:
                # Obtener firmantes
                sql_firmantes = """
                    SELECT 
                        cfp.orden,
                        u.nombre,
                        u.ape_pat,
                        u.ape_mat,
                        cfp.firmado,
                        cfp.fecha_firma,
                        cfp.rechazo,
                        cfp.comentario_rechazo
                    FROM CONTRATO_FIRMA_PENDIENTE cfp
                    INNER JOIN USUARIO u ON cfp.id_usuario = u.id_usuario
                    WHERE cfp.id_contrato = %s
                    ORDER BY cfp.orden ASC
                """
                cursor.execute(sql_firmantes, (id_contrato,))
                firmantes_rows = cursor.fetchall()
                
                # Obtener rechazos
                sql_rechazos = """
                    SELECT 
                        u.nombre,
                        u.ape_pat,
                        cr.motivo,
                        cr.fecha_rechazo
                    FROM CONTRATO_RECHAZO cr
                    INNER JOIN USUARIO u ON cr.id_usuario = u.id_usuario
                    WHERE cr.id_contrato = %s
                    ORDER BY cr.fecha_rechazo DESC
                """
                cursor.execute(sql_rechazos, (id_contrato,))
                rechazos_rows = cursor.fetchall()
            
            conexion.close()
            
            firmantes = []
            for row in firmantes_rows:
                firmantes.append({
                    'orden': row[0],
                    'nombre_completo': f"{row[1]} {row[2]} {row[3]}",
                    'firmado': row[4],
                    'fecha_firma': row[5],
                    'rechazo': row[6],
                    'comentario_rechazo': row[7]
                })
            
            rechazos = []
            for row in rechazos_rows:
                rechazos.append({
                    'nombre_completo': f"{row[0]} {row[1]}",
                    'motivo': row[2],
                    'fecha': row[3]
                })
            
            return {
                'firmantes': firmantes,
                'rechazos': rechazos
            }
            
        except Exception as e:
            print(f"❌ Error al obtener historial: {e}")
            return None
    
    @staticmethod
    def obtener_todos_contratos(limite=50):
        """
        Obtiene todos los contratos (para administradores)
        
        Returns:
            list: Lista de contratos
        """
        try:
            sql = """
                SELECT 
                    c.id_contrato,
                    c.titulo,
                    c.descripcion,
                    c.estado,
                    c.fecha_creacion,
                    COUNT(CASE WHEN cfp.firmado = TRUE THEN 1 END) as firmados,
                    COUNT(cfp.id_firma) as total_firmantes
                FROM CONTRATO c
                LEFT JOIN CONTRATO_FIRMA_PENDIENTE cfp ON c.id_contrato = cfp.id_contrato
                GROUP BY c.id_contrato, c.titulo, c.descripcion, c.estado, c.fecha_creacion
                ORDER BY c.fecha_creacion DESC
                LIMIT %s
            """
            
            conexion = get_connection()
            if not conexion:
                return []
            
            with conexion.cursor() as cursor:
                cursor.execute(sql, (limite,))
                rows = cursor.fetchall()
            
            conexion.close()
            
            contratos = []
            for row in rows:
                contratos.append({
                    'id_contrato': row[0],
                    'titulo': row[1],
                    'descripcion': row[2],
                    'estado': row[3],
                    'fecha_creacion': row[4],
                    'firmados': row[5],
                    'total_firmantes': row[6]
                })
            
            return contratos
            
        except Exception as e:
            print(f"❌ Error al obtener contratos: {e}")
            return []

