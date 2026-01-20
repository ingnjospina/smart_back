-- =====================================================
-- Script: Crear tabla pronosticos_transformadores
-- Fecha: 2026-01-17
-- Descripcion: Tabla para almacenar pronosticos de
--              transformadores con calculo de HI y RM
-- =====================================================

-- Crear la tabla pronosticos_transformadores
CREATE TABLE IF NOT EXISTS pronosticos_transformadores (
    idpronostico_transformador INT AUTO_INCREMENT PRIMARY KEY,

    -- Relacion con transformador
    Transformadores_idTransformadores INT NOT NULL,

    -- Fecha del ultimo mantenimiento (input del usuario)
    fecha_ultimo_mantenimiento DATE NOT NULL,

    -- =====================================================
    -- DATOS DE ENTRADA - INDICE FUNCIONAL
    -- =====================================================
    -- Relacion de transformacion (% error TTR)
    relacion_transformacion DECIMAL(6,3) NOT NULL,
    -- Resistencia de devanados (% error)
    resistencia_devanados DECIMAL(6,3) NOT NULL,
    -- Corriente de excitacion (patron: 4=correcto, 0=incorrecto)
    corriente_excitacion TINYINT NOT NULL,

    -- =====================================================
    -- DATOS DE ENTRADA - GASES DISUELTOS (DGA)
    -- =====================================================
    hidrogeno DECIMAL(10,2) NOT NULL,
    metano DECIMAL(10,2) NOT NULL,
    etano DECIMAL(10,2) NOT NULL,
    etileno DECIMAL(10,2) NOT NULL,
    acetileno DECIMAL(10,2) NOT NULL,
    dioxido_carbono DECIMAL(10,2) NOT NULL,
    monoxido_carbono DECIMAL(10,2) NOT NULL,

    -- =====================================================
    -- DATOS DE ENTRADA - INDICE DIELECTRICO
    -- =====================================================
    -- Factor de potencia (%)
    factor_potencia DECIMAL(6,3) NOT NULL,
    -- Rigidez dielectrica (KV)
    rigidez_dielectrica DECIMAL(10,2) NOT NULL,
    -- Tension interfacial (mN/m)
    tension_interfacial DECIMAL(10,2) NOT NULL,
    -- Numero de acidez (mg KOH/g)
    numero_acidez DECIMAL(6,4) NOT NULL,
    -- Contenido de humedad (mg/kg o ppm)
    contenido_humedad DECIMAL(10,2) NOT NULL,
    -- Color
    color DECIMAL(4,2) NOT NULL,
    -- Factor de potencia liquido 25%
    factor_potencia_liquido DECIMAL(6,4) NOT NULL,
    -- Inhibidor de oxidacion (%)
    inhibidor_oxidacion DECIMAL(6,4) NOT NULL,
    -- Grado de polimerizacion (DP) - segun Tabla 16 documento
    grado_polimerizacion DECIMAL(10,2) NOT NULL,

    -- =====================================================
    -- VALORES HIF CALCULADOS - INDICE FUNCIONAL
    -- =====================================================
    hif_relacion_transformacion TINYINT DEFAULT NULL COMMENT 'HIF 0-4',
    hif_resistencia_devanados TINYINT DEFAULT NULL COMMENT 'HIF 0-4',
    hif_corriente_excitacion TINYINT DEFAULT NULL COMMENT 'HIF 0 o 4',
    dgaf_porcentaje DECIMAL(6,2) DEFAULT NULL COMMENT '%DGAF calculado',
    hif_gases_disueltos TINYINT DEFAULT NULL COMMENT 'HIF 0-4 basado en %DGAF',

    -- =====================================================
    -- VALORES HIF CALCULADOS - INDICE DIELECTRICO
    -- =====================================================
    hif_factor_potencia TINYINT DEFAULT NULL COMMENT 'HIF 0-4',
    oqf_porcentaje DECIMAL(6,2) DEFAULT NULL COMMENT '%OQF calculado',
    hif_calidad_aceite TINYINT DEFAULT NULL COMMENT 'HIF 0-4 basado en %OQF',
    hif_inhibidor_oxidacion TINYINT DEFAULT NULL COMMENT 'HIF 0-4',
    hif_grado_polimerizacion TINYINT DEFAULT NULL COMMENT 'HIF 0-4',

    -- =====================================================
    -- INDICES DE SALUD CALCULADOS
    -- =====================================================
    hi_funcional DECIMAL(6,2) DEFAULT NULL COMMENT 'HI Funcional (0-100)',
    hi_dielectrico DECIMAL(6,2) DEFAULT NULL COMMENT 'HI Dielectrico (0-100)',
    hi_total DECIMAL(6,2) DEFAULT NULL COMMENT 'HI Total = 0.5*HI_func + 0.5*HI_diel',

    -- =====================================================
    -- DATOS TERMICOS Y ESTRES
    -- =====================================================
    faa_p95 DECIMAL(10,4) DEFAULT NULL COMMENT 'FAA Percentil 95',
    estres_termico DECIMAL(6,4) DEFAULT NULL COMMENT 'TS normalizado 0-1',

    -- =====================================================
    -- INDICE DE RIESGO DE MANTENIMIENTO
    -- =====================================================
    rm_actual DECIMAL(6,4) DEFAULT NULL COMMENT 'RM = 0.5*HI + 0.35*TS + 0.15*tendencia',
    tendencia_hi DECIMAL(8,6) DEFAULT NULL COMMENT 'Pendiente de HI (puntos/dia)',

    -- =====================================================
    -- FECHAS DE MANTENIMIENTO
    -- =====================================================
    fecha_cruce_rm DATETIME DEFAULT NULL COMMENT 'Fecha estimada cruce umbral RM (0.70)',
    fecha_programada DATE DEFAULT NULL COMMENT 'Fecha por intervalo (ultima_mant + 3 anios)',
    fecha_optima_sugerida DATE DEFAULT NULL COMMENT 'min(fecha_cruce - 21 dias, fecha_programada)',
    criterio_fecha VARCHAR(20) DEFAULT NULL COMMENT 'condicion o tiempo',

    -- =====================================================
    -- CLASIFICACION Y ALERTA
    -- =====================================================
    condicion_hi VARCHAR(20) DEFAULT NULL COMMENT 'Muy Bueno/Bueno/Regular/Pobre/Muy Pobre',
    vida_util_remanente VARCHAR(50) DEFAULT NULL,
    recomendacion TEXT DEFAULT NULL,
    color_alerta VARCHAR(20) DEFAULT NULL COMMENT 'verde/amarillo/naranja/rojo',

    -- =====================================================
    -- METADATA
    -- =====================================================
    tiene_archivos BOOLEAN DEFAULT FALSE,
    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- =====================================================
    -- FOREIGN KEY
    -- =====================================================
    CONSTRAINT fk_pronostico_transformador
        FOREIGN KEY (Transformadores_idTransformadores)
        REFERENCES transformadores(idTransformadores)
        ON DELETE CASCADE
        ON UPDATE CASCADE

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Indices para mejorar rendimiento de consultas
-- =====================================================
CREATE INDEX idx_pronostico_transf_transformador
    ON pronosticos_transformadores(Transformadores_idTransformadores);

CREATE INDEX idx_pronostico_transf_fecha_creacion
    ON pronosticos_transformadores(fecha_creacion);

CREATE INDEX idx_pronostico_transf_hi_total
    ON pronosticos_transformadores(hi_total);

CREATE INDEX idx_pronostico_transf_rm
    ON pronosticos_transformadores(rm_actual);

CREATE INDEX idx_pronostico_transf_fecha_optima
    ON pronosticos_transformadores(fecha_optima_sugerida);


-- =====================================================
-- Verificar creacion
-- =====================================================
DESCRIBE pronosticos_transformadores;

-- =====================================================
-- NOTA: La tabla 'pronosticos' existente se mantiene
-- para interruptores. Esta nueva tabla es especifica
-- para transformadores y contiene todos los campos
-- necesarios para calcular HI (Indice de Salud) y
-- RM (Indice de Riesgo de Mantenimiento) segun la
-- metodologia del documento Word y el notebook.
-- =====================================================
