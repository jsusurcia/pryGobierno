-- ============================================================================
-- Script para Limpiar Datos de Biometría Facial
-- ============================================================================
-- Este script resetea los datos biométricos de los usuarios
-- Útil para hacer pruebas o volver a registrar rostros
-- ============================================================================

-- Opción 1: Limpiar biometría de TODOS los usuarios
-- ⚠️ CUIDADO: Esto borrará todos los rostros registrados
UPDATE USUARIO 
SET encoding_facial = NULL,
    tiene_biometria = FALSE,
    fecha_registro_facial = NULL;

-- Opción 2: Limpiar biometría de un usuario específico por correo
-- UPDATE USUARIO 
-- SET encoding_facial = NULL,
--     tiene_biometria = FALSE,
--     fecha_registro_facial = NULL
-- WHERE correo = 'usuario@ejemplo.com';

-- Opción 3: Limpiar biometría de un usuario específico por ID
-- UPDATE USUARIO 
-- SET encoding_facial = NULL,
--     tiene_biometria = FALSE,
--     fecha_registro_facial = NULL
-- WHERE id_usuario = 1;

-- ============================================================================
-- Verificar que se limpiaron correctamente
-- ============================================================================
SELECT 
    id_usuario,
    nombre,
    ape_pat,
    correo,
    tiene_biometria,
    fecha_registro_facial,
    CASE 
        WHEN encoding_facial IS NULL THEN 'Sin encoding'
        ELSE 'Con encoding'
    END as estado_encoding
FROM USUARIO
ORDER BY id_usuario;

