-- =====================================================================
-- LIMPIEZA DE DATOS DE INTERRUPTORES
-- Fecha: 2026-08-25
--
-- MOTIVO
--   Se corrigieron las fórmulas de cálculo en InterruptorPotencia.py:
--     - Unidades de corriente de falla   (A, I_F_max = 40000)
--     - Unidades de resistencia contactos (Ω, R_C_ref = 0.00005)
--     - Ponderaciones alpha_0/1/2 = 0.5/0.25/0.25
--     - Referencia T_C_ref = 50 ms (antes 60)
--     - I_M = (γ1·(1−I_DM) + γ2·(1−I_EE)) · 100   -> escala de salud 0-100
--
--   Todos los registros existentes fueron calculados con la fórmula
--   anterior y quedaron en una escala incompatible con la nueva.
--   Mezclarlos produce deltas y tendencias sin sentido.
--
-- ALCANCE
--   Se vacían 3 tablas. NO se tocan 'interruptores' ni 'transformadores'
--   (los equipos se conservan), ni nada relativo a transformadores.
--
--     mediciones_interruptores  -> mediciones y sus índices I_DM/I_EE/I_M
--     alertas_interruptores     -> alertas derivadas de esas mediciones
--     pronosticos               -> pronósticos de interruptores, que
--                                  consumen las mediciones y además se
--                                  retroalimentan vía Pmant / I_M_prev
--
-- NOTA SOBRE INTEGRIDAD
--   Ninguna FK apunta a mediciones_interruptores, por lo que el borrado
--   no rompe restricciones. El vínculo alerta<->medición es lógico
--   (se crean juntas en la vista), no está declarado en la BD.
--
-- ADVERTENCIA: ESTE SCRIPT BORRA DATOS DE FORMA PERMANENTE.
--              Ejecutar el PASO 0 (respaldo) antes que nada.
-- =====================================================================


-- ---------------------------------------------------------------------
-- PASO 0 — RESPALDO  (ejecutar en la terminal, NO en el cliente SQL)
-- ---------------------------------------------------------------------
-- mysqldump -u <usuario> -p tg_nelson \
--     mediciones_interruptores alertas_interruptores pronosticos \
--     > respaldo_interruptores_20260825.sql
--
-- Restauración, si hiciera falta:
-- mysql -u <usuario> -p tg_nelson < respaldo_interruptores_20260825.sql
-- ---------------------------------------------------------------------


USE tg_nelson;


-- ---------------------------------------------------------------------
-- PASO 1 — INVENTARIO PREVIO
-- Dejar constancia de cuántos registros se van a eliminar.
-- ---------------------------------------------------------------------
SELECT 'ANTES DE BORRAR' AS momento;

SELECT 'mediciones_interruptores' AS tabla, COUNT(*) AS filas FROM mediciones_interruptores
UNION ALL
SELECT 'alertas_interruptores',           COUNT(*) FROM alertas_interruptores
UNION ALL
SELECT 'pronosticos',                     COUNT(*) FROM pronosticos;

-- Detalle de lo que se elimina (para el registro de la operación)
SELECT m.idMediciones_Interruptores AS id,
       i.nombre                     AS interruptor,
       m.numero_operaciones,
       m.tiempo_apertura_A,
       m.tiempo_cierre_A,
       m.corriente_falla,
       m.resistencia_contactos_R,
       m.I_DM, m.I_EE, m.I_M
FROM mediciones_interruptores m
LEFT JOIN interruptores i ON i.idInterruptores = m.Interruptores_idInterruptores
ORDER BY m.idMediciones_Interruptores;


-- ---------------------------------------------------------------------
-- PASO 2 — BORRADO
-- Se ejecuta dentro de una transacción: si algo falla, no queda a medias.
-- ---------------------------------------------------------------------
START TRANSACTION;

-- Orden: primero lo derivado, al final las mediciones de origen.
DELETE FROM pronosticos;
DELETE FROM alertas_interruptores;
DELETE FROM mediciones_interruptores;

COMMIT;


-- ---------------------------------------------------------------------
-- PASO 3 — REINICIAR CONTADORES
-- Para que los próximos registros arranquen en id = 1.
-- Omitir este paso si se prefiere conservar la numeración histórica.
-- ---------------------------------------------------------------------
ALTER TABLE mediciones_interruptores AUTO_INCREMENT = 1;
ALTER TABLE alertas_interruptores    AUTO_INCREMENT = 1;
ALTER TABLE pronosticos              AUTO_INCREMENT = 1;


-- ---------------------------------------------------------------------
-- PASO 4 — VERIFICACIÓN
-- Las tres tablas deben quedar en 0. Los equipos deben seguir intactos.
-- ---------------------------------------------------------------------
SELECT 'DESPUES DE BORRAR' AS momento;

SELECT 'mediciones_interruptores' AS tabla, COUNT(*) AS filas FROM mediciones_interruptores
UNION ALL
SELECT 'alertas_interruptores',           COUNT(*) FROM alertas_interruptores
UNION ALL
SELECT 'pronosticos',                     COUNT(*) FROM pronosticos;

-- Control: los interruptores NO deben haberse tocado.
SELECT idInterruptores, nombre, niveles_tension, subestacion
FROM interruptores
WHERE deleted = 0
ORDER BY idInterruptores;
