-- Cambios segunda fase 2025-10-15
CREATE TABLE pronosticos
(
    idPronostico INT AUTO_INCREMENT PRIMARY KEY,
    tipo_equipo VARCHAR(15) NOT NULL,
    Transformadores_idTransformadores INT NULL,
    Interruptores_idInterruptores INT NULL,
    tiempo_apertura DECIMAL(10, 2) NOT NULL COMMENT 'Tiempo en milisegundos',
    tiempo_cierre DECIMAL(10, 2) NOT NULL COMMENT 'Tiempo en milisegundos',
    numero_operaciones INT NOT NULL,
    corriente_falla DECIMAL(10, 2) NOT NULL COMMENT 'Corriente en kA',
    resistencia_contactos DECIMAL(30, 20) NOT NULL COMMENT 'Resistencia en µΩ',
    fecha_mantenimiento DATE NOT NULL,
    fecha_creacion DATETIME(6) NOT NULL,
    probabilidad_mantenimiento DECIMAL(5, 2) NULL COMMENT 'Probabilidad estimada de requerir mantenimiento (%)',
    fecha_programada DATE NULL COMMENT 'Fecha programada (cada 3 años)',
    fecha_optima_sugerida DATE NULL COMMENT 'Fecha óptima sugerida según condición del equipo',
    CONSTRAINT pronosticos_transformador_fk FOREIGN KEY (Transformadores_idTransformadores) REFERENCES transformadores (idTransformadores) ON DELETE CASCADE,
    CONSTRAINT pronosticos_interruptor_fk FOREIGN KEY (Interruptores_idInterruptores) REFERENCES interruptores (idInterruptores) ON DELETE CASCADE
)
CHARSET = utf8mb4;