-- ============================================
-- VERIFICAR JEFES EN EL SISTEMA
-- ============================================
-- Este script ayuda a verificar qué usuarios son jefes
-- y pueden crear contratos en el sistema

-- 1. Ver todos los roles tipo 'J' (Jefe)
SELECT 
    r.id_rol,
    r.nombre as nombre_rol,
    r.tipo,
    a.nombre as area,
    COUNT(u.id_usuario) as cantidad_usuarios
FROM ROL r
LEFT JOIN AREA a ON r.id_area = a.id_area
LEFT JOIN USUARIO u ON r.id_rol = u.id_rol AND u.estado = true
WHERE r.tipo = 'J'
GROUP BY r.id_rol, r.nombre, r.tipo, a.nombre
ORDER BY a.nombre;

-- 2. Ver todos los usuarios que son jefes (activos)
SELECT 
    u.id_usuario,
    u.nombre || ' ' || u.ape_pat || ' ' || u.ape_mat as nombre_completo,
    u.correo,
    r.nombre as rol,
    a.nombre as area,
    CASE 
        WHEN r.tipo = 'J' THEN '✅ Puede crear contratos'
        ELSE '❌ No puede crear contratos'
    END as permisos_contrato
FROM USUARIO u
JOIN ROL r ON u.id_rol = r.id_rol
JOIN AREA a ON r.id_area = a.id_area
WHERE r.tipo = 'J' AND u.estado = true
ORDER BY a.nombre, u.nombre;

-- 3. Resumen por área
SELECT 
    a.nombre as area,
    COUNT(DISTINCT u.id_usuario) as total_jefes_activos
FROM AREA a
LEFT JOIN ROL r ON a.id_area = r.id_area AND r.tipo = 'J'
LEFT JOIN USUARIO u ON r.id_rol = u.id_rol AND u.estado = true
GROUP BY a.nombre
ORDER BY a.nombre;

-- 4. Ver TODOS los roles (para referencia)
SELECT 
    r.id_rol,
    r.nombre,
    r.tipo,
    CASE 
        WHEN r.tipo = 'J' THEN 'Jefe/Gerente'
        WHEN r.tipo = 'T' THEN 'Técnico'
        ELSE 'Otro'
    END as descripcion_tipo,
    a.nombre as area
FROM ROL r
JOIN AREA a ON r.id_area = a.id_area
ORDER BY a.nombre, r.tipo;

