-- Script para agregar campo de sello/firma a la tabla USUARIO
-- Ejecutar este script en tu base de datos PostgreSQL

-- Agregar columna para URL del sello institucional
ALTER TABLE USUARIO 
ADD COLUMN url_sello TEXT;

-- Agregar comentario a la columna
COMMENT ON COLUMN USUARIO.url_sello IS 'URL de Cloudinary con el sello institucional del usuario';

-- Verificar que se agregó correctamente
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'usuario' AND column_name = 'url_sello';

-- Ejemplo de actualización (cambiar los valores según tus necesidades)
-- UPDATE USUARIO SET url_sello = 'https://res.cloudinary.com/tu-cloud/image/upload/v1234567890/sellos/sello_usuario_1.png' WHERE id_usuario = 1;

