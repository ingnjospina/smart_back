script de base de datos


ALTER TABLE medicionesinterruptores
DROP FOREIGN KEY medicionesinterrupto_Interruptores_idInte_9f6783ac_fk_interrupt;

ALTER TABLE interruptores
MODIFY idInterruptores INT AUTO_INCREMENT;

ALTER TABLE interruptores
AUTO_INCREMENT = 1;

ALTER TABLE medicionesinterruptores
ADD CONSTRAINT medicionesinterrupto_Interruptores_idInte_9f6783ac_fk_interrupt
FOREIGN KEY (Interruptores_idInterruptores) REFERENCES interruptores (idInterruptores);

ALTER TABLE interruptores
ADD COLUMN deleted BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE transformadores
ADD COLUMN deleted BOOLEAN NOT NULL DEFAULT FALSE;
