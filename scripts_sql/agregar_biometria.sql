-- ============================================================
-- SCRIPT SQL: Agregar soporte de Biometría Facial
-- Base de datos: PostgreSQL (Gobierno2)
-- Fecha: 2025
-- ============================================================

-- 1. Agregar columna para almacenar el encoding facial
-- El encoding es un vector de 128 dimensiones (float64)
-- Lo almacenamos como BYTEA (datos binarios serializados con pickle)
ALTER TABLE USUARIO 
ADD COLUMN IF NOT EXISTS encoding_facial BYTEA;

-- 2. Agregar columna para saber si el usuario tiene rostro registrado
ALTER TABLE USUARIO 
ADD COLUMN IF NOT EXISTS tiene_biometria BOOLEAN DEFAULT FALSE;

-- 3. Agregar columna para la fecha de registro del rostro
ALTER TABLE USUARIO 
ADD COLUMN IF NOT EXISTS fecha_registro_facial TIMESTAMP;

-- 4. Crear índice para búsquedas más rápidas de usuarios con biometría
CREATE INDEX IF NOT EXISTS idx_usuario_biometria 
ON USUARIO(tiene_biometria) 
WHERE tiene_biometria = TRUE;

-- ============================================================
-- VERIFICACIÓN: Ejecutar para confirmar que se agregaron las columnas
-- ============================================================
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'usuario' 
-- AND column_name IN ('encoding_facial', 'tiene_biometria', 'fecha_registro_facial');

-- ============================================================
-- NOTA: Para revertir los cambios (si es necesario):
-- ============================================================
-- ALTER TABLE USUARIO DROP COLUMN IF EXISTS encoding_facial;
-- ALTER TABLE USUARIO DROP COLUMN IF EXISTS tiene_biometria;
-- ALTER TABLE USUARIO DROP COLUMN IF EXISTS fecha_registro_facial;
-- DROP INDEX IF EXISTS idx_usuario_biometria;

