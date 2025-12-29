-- ============================================================
-- Script de migración para tabla mediciones_transformadores
-- ============================================================
-- Fecha: 2024-12-29
-- Descripción: Ampliar campo gases_disueltos para permitir
--              valores hasta 100.0000
-- ============================================================

-- BACKUP DEL ESTADO ANTERIOR:
-- gases_disueltos DECIMAL(6,4)
-- Permitía: 0.0001 a 99.9999 (máximo 2 dígitos enteros)

-- NUEVO ESTADO:
-- gases_disueltos DECIMAL(7,4)
-- Permite: 0.0001 a 999.9999 (máximo 3 dígitos enteros)

USE smart_db; -- Ajusta el nombre de tu base de datos si es necesario

-- Modificar el campo gases_disueltos
ALTER TABLE mediciones_transformadores
MODIFY COLUMN gases_disueltos DECIMAL(7, 4) NULL;

-- Verificar el cambio
DESCRIBE mediciones_transformadores;

-- ============================================================
-- ROLLBACK (en caso de necesitar revertir)
-- ============================================================
-- ALTER TABLE mediciones_transformadores
-- MODIFY COLUMN gases_disueltos DECIMAL(6, 4) NULL;
-- ============================================================
