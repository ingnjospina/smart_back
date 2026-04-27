-- ============================================================
-- Script de cambios en BD - Proyecto Nelson
-- Aplicar en orden cronológico
-- ============================================================

-- [17/04/2026] Añadir índices calculados a mediciones_interruptores
-- I_DM: Índice Mecánico, I_EE: Índice Eléctrico, I_M: Índice de Salud
ALTER TABLE mediciones_interruptores
    ADD COLUMN I_DM DECIMAL(6,2) NULL,
    ADD COLUMN I_EE DECIMAL(6,2) NULL,
    ADD COLUMN I_M  DECIMAL(6,2) NULL;

-- [17/04/2026] Rediseño tabla pronosticos para interruptores
-- Eliminar campos de medición redundantes y agregar resultados calculados del modelo
ALTER TABLE pronosticos DROP FOREIGN KEY fk_pronostico_trans;
ALTER TABLE pronosticos
    DROP COLUMN tiempo_apertura,
    DROP COLUMN tiempo_cierre,
    DROP COLUMN numero_operaciones,
    DROP COLUMN corriente_falla,
    DROP COLUMN resistencia_contactos,
    DROP COLUMN probabilidad_mantenimiento,
    DROP COLUMN fecha_programada,
    DROP COLUMN fecha_optima_sugerida,
    DROP COLUMN tipo_equipo,
    DROP COLUMN Transformadores_idTransformadores;
ALTER TABLE pronosticos
    ADD COLUMN I_DM      DECIMAL(8,4) NULL COMMENT 'Índice de Desgaste Mecánico',
    ADD COLUMN I_EE      DECIMAL(8,4) NULL COMMENT 'Índice de Estrés Eléctrico',
    ADD COLUMN I_M       DECIMAL(8,4) NULL COMMENT 'Índice General de Mantenimiento actual',
    ADD COLUMN I_M_prev  DECIMAL(8,4) NULL COMMENT 'IM(t-1) - 0 si equipo nuevo',
    ADD COLUMN delta_IM  DECIMAL(8,4) NULL COMMENT 'ΔH(t) = IM(t) - IM(t-1)',
    ADD COLUMN Pmant     DECIMAL(5,4) NULL COMMENT 'Probabilidad de mantenimiento [0-1]';

-- [17/04/2026] Rediseño tabla alertas: reemplazar campo mensaje por campos detallados
-- Se eliminó 'mensaje' (texto genérico) y se añadieron campos específicos para el resultado del análisis
ALTER TABLE alertas DROP COLUMN mensaje;
ALTER TABLE alertas
    ADD COLUMN color_alerta      VARCHAR(200) NOT NULL,
    ADD COLUMN mensaje_condicion VARCHAR(200) NOT NULL,
    ADD COLUMN recomendacion     VARCHAR(200) NOT NULL,
    ADD COLUMN vida_util_remanente VARCHAR(200) NOT NULL;

-- [17/04/2026] Añadir fecha de último mantenimiento a alertas_interruptores
ALTER TABLE alertas_interruptores
    ADD COLUMN fecha_mantenimiento DATE NULL COMMENT 'Fecha del último mantenimiento ingresada en la medición';

-- [21/04/2026] Añadir fecha recomendada de mantenimiento a pronosticos
-- Calculada automáticamente según Pmant: ≥75%→1mes, ≥50%→3meses, ≥25%→6meses, <25%→12meses
ALTER TABLE pronosticos
    ADD COLUMN fecha_recomendada DATE NULL COMMENT 'Fecha recomendada para el próximo mantenimiento';
