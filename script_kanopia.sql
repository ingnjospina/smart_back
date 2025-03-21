-- 🔹 Eliminar clave foránea en medicionesinterruptores antes de modificar la tabla
ALTER TABLE medicionesinterruptores
    DROP FOREIGN KEY medicionesinterrupto_Interruptores_idInte_9f6783ac_fk_interrupt;

-- 🔹 Modificar la tabla interruptores para que su ID sea AUTO_INCREMENT
ALTER TABLE interruptores
    MODIFY idInterruptores INT AUTO_INCREMENT;

-- 🔹 Reiniciar el contador de AUTO_INCREMENT en interruptores
ALTER TABLE interruptores
    AUTO_INCREMENT = 1;

-- 🔹 Restaurar la clave foránea en medicionesinterruptores
ALTER TABLE medicionesinterruptores
    ADD CONSTRAINT medicionesinterrupto_Interruptores_idInte_9f6783ac_fk_interrupt
        FOREIGN KEY (Interruptores_idInterruptores) REFERENCES interruptores (idInterruptores);

-- 🔹 Agregar la columna "deleted" a interruptores para manejo de eliminación lógica
ALTER TABLE interruptores
    ADD COLUMN deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- 🔹 Agregar la columna "deleted" a transformadores para eliminación lógica
ALTER TABLE transformadores
    ADD COLUMN deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- 🔹 Eliminar clave foránea en alertas antes de modificar la tabla
ALTER TABLE alertas
    DROP FOREIGN KEY alertas_MedicionesInterrupto_b83186a3_fk_medicione;

-- 🔹 Modificar la tabla medicionesinterruptores para que su ID sea AUTO_INCREMENT
ALTER TABLE medicionesinterruptores
    MODIFY idMediciones_Interruptores INT AUTO_INCREMENT;

-- 🔹 Reiniciar el contador de AUTO_INCREMENT en medicionesinterruptores
ALTER TABLE medicionesinterruptores
    AUTO_INCREMENT = 1;

-- 🔹 Restaurar la clave foránea en alertas
ALTER TABLE alertas
    ADD CONSTRAINT alertas_MedicionesInterrupto_b83186a3_fk_medicione
        FOREIGN KEY (MedicionesInterruptores_idMediciones_Interruptores)
            REFERENCES medicionesinterruptores (idMediciones_Interruptores);

-- 🔹 Crear la tabla mediciones_interruptores si no existe
CREATE TABLE IF NOT EXISTS mediciones_interruptores
(
    idMediciones_Interruptores    INT AUTO_INCREMENT PRIMARY KEY,
    numero_operaciones            INT UNSIGNED  NOT NULL,
    tiempo_apertura               DECIMAL(6, 3) NOT NULL,
    tiempo_cierre                 DECIMAL(6, 3) NOT NULL,
    corriente_falla               DECIMAL(8, 3) NOT NULL,
    resistencia_contactos         DECIMAL(6, 3) NOT NULL,
    Interruptores_idInterruptores INT           NOT NULL,
    CONSTRAINT fk_interruptores FOREIGN KEY (Interruptores_idInterruptores)
        REFERENCES interruptores (idInterruptores)
)
    CHARACTER SET utf8mb4;


CREATE TABLE alertas_interruptores
(
    id              INT AUTO_INCREMENT PRIMARY KEY,
    idInterruptores INT          NOT NULL,
    valor_medicion  VARCHAR(255) NOT NULL,
    tipo_alerta     VARCHAR(255) NOT NULL,
    condicion       TEXT         NOT NULL,
    recomendacion   TEXT         NULL,
    fecha_medicion  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idInterruptores) REFERENCES interruptores (idInterruptores) ON DELETE CASCADE
)
    CHARACTER SET utf8mb4;


-- ###################################### NUEVO ######################################
ALTER TABLE interruptores
    ADD COLUMN niveles_tension VARCHAR(50)  NOT NULL,
    ADD COLUMN subestacion     VARCHAR(100) NOT NULL;
