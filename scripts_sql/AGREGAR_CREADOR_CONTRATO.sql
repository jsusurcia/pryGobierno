-- Script para agregar campo de usuario creador en la tabla CONTRATO
-- Ejecutar este script en tu base de datos PostgreSQL

-- Agregar columna para ID del usuario que creó el contrato
ALTER TABLE CONTRATO 
ADD COLUMN id_usuario_creador INTEGER;

-- Agregar foreign key hacia USUARIO
ALTER TABLE CONTRATO
ADD CONSTRAINT fk_contrato_creador 
FOREIGN KEY (id_usuario_creador) REFERENCES USUARIO(id_usuario);

-- Agregar comentario a la columna
COMMENT ON COLUMN CONTRATO.id_usuario_creador IS 'ID del usuario (jefe) que creó el contrato';

-- Verificar que se agregó correctamente
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'contrato' AND column_name = 'id_usuario_creador';

-- Si ya tienes contratos existentes, puedes actualizarlos a un usuario por defecto
-- UPDATE CONTRATO SET id_usuario_creador = 1 WHERE id_usuario_creador IS NULL;

