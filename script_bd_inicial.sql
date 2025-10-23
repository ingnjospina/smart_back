-- RECREAR TODAS LAS TABLAS DESDE CERO

DROP TABLE IF EXISTS usuario_user_permissions;
DROP TABLE IF EXISTS usuario_groups;
DROP TABLE IF EXISTS django_admin_log;
DROP TABLE IF EXISTS authtoken_token;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS pronosticos;
DROP TABLE IF EXISTS analisisgasesdisueltos;
DROP TABLE IF EXISTS analisisaceitefisicoquimico;
DROP TABLE IF EXISTS alertas;
DROP TABLE IF EXISTS mediciones_transformadores;
DROP TABLE IF EXISTS transformadores;
DROP TABLE IF EXISTS sys_config;
DROP TABLE IF EXISTS medicionesinterruptores;
DROP TABLE IF EXISTS mediciones_interruptores;
DROP TABLE IF EXISTS alertas_interruptores;
DROP TABLE IF EXISTS interruptores;
DROP TABLE IF EXISTS django_session;
DROP TABLE IF EXISTS django_migrations;
DROP TABLE IF EXISTS auth_group_permissions;
DROP TABLE IF EXISTS auth_permission;
DROP TABLE IF EXISTS django_content_type;
DROP TABLE IF EXISTS auth_group;
DROP TABLE IF EXISTS archivospruebas;

-- 🔽 Comienzan los CREATE TABLE 🔽

CREATE TABLE archivospruebas
(
    idArchivosPruebas INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    nombre_archivo    VARCHAR(255) NOT NULL,
    tipo_archivo      VARCHAR(5)   NOT NULL,
    ruta_archivo      VARCHAR(255) NOT NULL,
    fecha_carga       DATETIME(6)  NOT NULL
)
CHARSET = utf8mb4;

CREATE TABLE auth_group
(
    id   INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    CONSTRAINT name UNIQUE (name)
)
CHARSET = utf8mb4;

CREATE TABLE django_content_type
(
    id        INT AUTO_INCREMENT PRIMARY KEY,
    app_label VARCHAR(100) NOT NULL,
    model     VARCHAR(100) NOT NULL,
    CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model)
)
CHARSET = utf8mb4;

CREATE TABLE auth_permission
(
    id              INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    content_type_id INT NOT NULL,
    codename        VARCHAR(100) NOT NULL,
    CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename),
    CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES django_content_type (id)
)
CHARSET = utf8mb4;

CREATE TABLE auth_group_permissions
(
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    group_id      INT NOT NULL,
    permission_id INT NOT NULL,
    CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id),
    CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES auth_permission (id),
    CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group (id)
)
CHARSET = utf8mb4;

CREATE TABLE django_migrations
(
    id      BIGINT AUTO_INCREMENT PRIMARY KEY,
    app     VARCHAR(255) NOT NULL,
    name    VARCHAR(255) NOT NULL,
    applied DATETIME(6) NOT NULL
)
CHARSET = utf8mb4;

CREATE TABLE django_session
(
    session_key  VARCHAR(40) NOT NULL PRIMARY KEY,
    session_data LONGTEXT NOT NULL,
    expire_date  DATETIME(6) NOT NULL
)
CHARSET = utf8mb4;

CREATE INDEX django_session_expire_date_a5c62663 ON django_session (expire_date);

CREATE TABLE interruptores
(
    idInterruptores INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    descripcion     VARCHAR(200) NOT NULL,
    deleted         TINYINT(1) DEFAULT 0 NOT NULL,
    niveles_tension VARCHAR(50) NOT NULL,
    subestacion     VARCHAR(100) NOT NULL
)
CHARSET = utf8mb4;

CREATE TABLE alertas_interruptores
(
    id              INT AUTO_INCREMENT PRIMARY KEY,
    idInterruptores INT NOT NULL,
    valor_medicion  VARCHAR(255) NOT NULL,
    tipo_alerta     VARCHAR(255) NOT NULL,
    condicion       TEXT NOT NULL,
    recomendacion   TEXT NULL,
    fecha_medicion  DATETIME DEFAULT CURRENT_TIMESTAMP NULL,
    CONSTRAINT alertas_interruptores_ibfk_1 FOREIGN KEY (idInterruptores) REFERENCES interruptores (idInterruptores) ON DELETE CASCADE
)
CHARSET = utf8mb4;

CREATE INDEX idInterruptores ON alertas_interruptores (idInterruptores);

CREATE TABLE mediciones_interruptores
(
    idMediciones_Interruptores    INT AUTO_INCREMENT PRIMARY KEY,
    numero_operaciones            INT UNSIGNED NOT NULL,
    tiempo_apertura_A             DECIMAL(6, 3) NULL,
    tiempo_apertura_B             DECIMAL(6, 3) NULL,
    tiempo_apertura_C             DECIMAL(6, 3) NULL,
    tiempo_cierre_A               DECIMAL(6, 3) NULL,
    tiempo_cierre_B               DECIMAL(6, 3) NULL,
    tiempo_cierre_C               DECIMAL(6, 3) NULL,
    corriente_falla               DECIMAL(8, 3) NOT NULL,
    resistencia_contactos_R       DECIMAL(6, 3) NULL,
    resistencia_contactos_S       DECIMAL(6, 3) NULL,
    resistencia_contactos_T       DECIMAL(6, 3) NULL,
    Interruptores_idInterruptores INT NOT NULL,
    CONSTRAINT fk_interruptores FOREIGN KEY (Interruptores_idInterruptores) REFERENCES interruptores (idInterruptores)
)
CHARSET = utf8mb4;

CREATE TABLE medicionesinterruptores
(
    idMediciones_Interruptores    INT AUTO_INCREMENT PRIMARY KEY,
    fecha                         DATETIME(6) NOT NULL,
    corriente_nominal             DECIMAL(10, 2) NOT NULL,
    tension_operacion             DECIMAL(10, 2) NOT NULL,
    tiempo_operacion              DECIMAL(10, 2) NOT NULL,
    Interruptores_idInterruptores INT NULL,
    CONSTRAINT medicionesinterrupto_Interruptores_idInte_9f6783ac_fk_interrupt FOREIGN KEY (Interruptores_idInterruptores) REFERENCES interruptores (idInterruptores)
)
CHARSET = utf8mb4;

CREATE TABLE sys_config
(
    variable VARCHAR(128) NOT NULL PRIMARY KEY,
    value    VARCHAR(128) NULL,
    set_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NULL ON UPDATE CURRENT_TIMESTAMP,
    set_by   VARCHAR(128) NULL
)
CHARSET = utf8mb4;

CREATE TABLE transformadores
(
    idTransformadores INT AUTO_INCREMENT PRIMARY KEY,
    nombre            VARCHAR(100) NOT NULL,
    descripcion       VARCHAR(200) NOT NULL,
    deleted           TINYINT(1) DEFAULT 0 NOT NULL
)
CHARSET = utf8mb4;

CREATE TABLE mediciones_transformadores
(
    idMediciones_Transformadores      INT AUTO_INCREMENT PRIMARY KEY,
    relacion_transformacion           DECIMAL(4, 3) NOT NULL,
    resistencia_devanados             DECIMAL(4, 3) NOT NULL,
    corriente_excitacion              SMALLINT UNSIGNED NOT NULL,
    factor_potencia                   DECIMAL(4, 3) NOT NULL,
    inhibidor_oxidacion               DECIMAL(4, 3) NOT NULL,
    compuestos_furanicos              DECIMAL(7, 3) NOT NULL,
    Transformadores_idTransformadores INT NOT NULL,
    calidad_aceite_humedad            DECIMAL(8, 4) NULL,
    fecha_hora                        DATETIME(6) NOT NULL,
    gases_disueltos                   DECIMAL(6, 4) NULL,
    hi_calidad_aceite_humedad         DECIMAL(8, 4) NULL,
    hi_compuestos_furanicos           DECIMAL(4, 3) NULL,
    hi_dielectrico                    DECIMAL(4, 2) NULL,
    hi_factor_potencia                DECIMAL(4, 3) NULL,
    hi_funcional                      DECIMAL(4, 2) NULL,
    hi_inhibidor_oxidacion            DECIMAL(4, 3) NULL,
    hi_ponderado                      DECIMAL(4, 2) NULL,
    hif_corriente_excitacion          SMALLINT UNSIGNED NULL,
    hif_gases_disueltos               DECIMAL(6, 4) NULL,
    hif_relacion_transformacion       DECIMAL(4, 3) NULL,
    hif_resistencia_devanados         DECIMAL(4, 3) NULL,
    haveFiles                         TINYINT(1) NOT NULL,
    CONSTRAINT mediciones_transformadore_Transformadores_idTransfo_78a9c6f0_fk FOREIGN KEY (Transformadores_idTransformadores) REFERENCES transformadores (idTransformadores),
    CHECK (`hif_corriente_excitacion` >= 0),
    CONSTRAINT mediciones_transformadores_corriente_excitacion_4390cfa1_check CHECK (`corriente_excitacion` >= 0)
)
CHARSET = utf8mb4;

CREATE TABLE alertas
(
    idAlerta INT AUTO_INCREMENT PRIMARY KEY,
    color_alerta VARCHAR(200) NOT NULL,
    fecha_generacion DATETIME(6) NOT NULL,
    MedicionesInterruptores_idMediciones_Interruptores INT NULL,
    Mediciones_Transformadores_idMediciones_Transformadores INT NULL,
    mensaje_condicion VARCHAR(200) NOT NULL,
    recomendacion VARCHAR(200) NOT NULL,
    vida_util_remanente VARCHAR(200) NOT NULL,
    CONSTRAINT alertas_MedicionesInterrupto_b83186a3_fk_medicione FOREIGN KEY (MedicionesInterruptores_idMediciones_Interruptores) REFERENCES medicionesinterruptores (idMediciones_Interruptores),
    CONSTRAINT alertas_Mediciones_Transformadore_c32b8677_fk FOREIGN KEY (Mediciones_Transformadores_idMediciones_Transformadores) REFERENCES mediciones_transformadores (idMediciones_Transformadores)
)
CHARSET = utf8mb4;

CREATE TABLE analisisaceitefisicoquimico
(
    idAnalisisAceiteFisicoQuimico INT AUTO_INCREMENT PRIMARY KEY,
    rigidez_dieletrica DECIMAL(10, 2) NOT NULL,
    tension_interfacial DECIMAL(10, 2) NOT NULL,
    numero_acidez DECIMAL(10, 2) NOT NULL,
    contenido_humedad DECIMAL(10, 2) NOT NULL,
    factor_potencia_liquido DECIMAL(5, 2) NOT NULL,
    Mediciones_Transformadores_idMediciones_Transformadores INT NOT NULL,
    color DECIMAL(10, 2) NOT NULL,
    CONSTRAINT analisisaceitefisicoquimi_Mediciones_Transformadore_9068c793_fk FOREIGN KEY (Mediciones_Transformadores_idMediciones_Transformadores) REFERENCES mediciones_transformadores (idMediciones_Transformadores)
)
CHARSET = utf8mb4;

CREATE TABLE analisisgasesdisueltos
(
    idAnalisisGasesDisueltos INT AUTO_INCREMENT PRIMARY KEY,
    hidrogeno DECIMAL(10, 2) NOT NULL,
    metano DECIMAL(10, 2) NOT NULL,
    etano DECIMAL(10, 2) NOT NULL,
    etileno DECIMAL(10, 2) NOT NULL,
    acetileno DECIMAL(10, 2) NOT NULL,
    dioxido_carbono DECIMAL(10, 2) NOT NULL,
    monoxido_carbono DECIMAL(10, 2) NOT NULL,
    Mediciones_Transformadores_idMediciones_Transformadores INT NOT NULL,
    CONSTRAINT analisisgasesdisueltos_Mediciones_Transformadore_877d36a9_fk FOREIGN KEY (Mediciones_Transformadores_idMediciones_Transformadores) REFERENCES mediciones_transformadores (idMediciones_Transformadores)
)
CHARSET = utf8mb4;

CREATE TABLE usuario
(
    idUsuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL,
    correo VARCHAR(100) NOT NULL,
    rol VARCHAR(13) NOT NULL,
    fecha_creacion DATETIME(6) NOT NULL,
    estado VARCHAR(8) NOT NULL,
    is_active TINYINT(1) NOT NULL,
    is_staff TINYINT(1) NOT NULL,
    is_superuser TINYINT(1) NOT NULL,
    last_login DATETIME(6) NULL,
    password VARCHAR(128) NOT NULL,
    CONSTRAINT correo UNIQUE (correo)
)
CHARSET = utf8mb4;

CREATE TABLE authtoken_token
(
    `key` VARCHAR(40) NOT NULL PRIMARY KEY,
    created DATETIME(6) NOT NULL,
    user_id INT NOT NULL,
    CONSTRAINT user_id UNIQUE (user_id),
    CONSTRAINT authtoken_token_user_id_35299eff_fk_usuario_idUsuario FOREIGN KEY (user_id) REFERENCES usuario (idUsuario)
)
CHARSET = utf8mb4;

CREATE TABLE django_admin_log
(
    id INT AUTO_INCREMENT PRIMARY KEY,
    action_time DATETIME(6) NOT NULL,
    object_id LONGTEXT NULL,
    object_repr VARCHAR(200) NOT NULL,
    action_flag SMALLINT UNSIGNED NOT NULL,
    change_message LONGTEXT NOT NULL,
    content_type_id INT NULL,
    user_id INT NOT NULL,
    CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES django_content_type (id),
    CONSTRAINT django_admin_log_user_id_c564eba6_fk_usuario_idUsuario FOREIGN KEY (user_id) REFERENCES usuario (idUsuario),
    CHECK (`action_flag` >= 0)
)
CHARSET = utf8mb4;

CREATE TABLE usuario_groups
(
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    group_id INT NOT NULL,
    CONSTRAINT usuario_groups_usuario_id_group_id_2e3cd638_uniq UNIQUE (usuario_id, group_id),
    CONSTRAINT usuario_groups_group_id_c67c8651_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES auth_group (id),
    CONSTRAINT usuario_groups_usuario_id_161fc80c_fk_usuario_idUsuario FOREIGN KEY (usuario_id) REFERENCES usuario (idUsuario)
)
CHARSET = utf8mb4;

CREATE TABLE usuario_user_permissions
(
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    permission_id INT NOT NULL,
    CONSTRAINT usuario_user_permissions_usuario_id_permission_id_3db58b8c_uniq UNIQUE (usuario_id, permission_id),
    CONSTRAINT usuario_user_permiss_permission_id_a8893ce7_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES auth_permission (id),
    CONSTRAINT usuario_user_permiss_usuario_id_693d9c50_fk_usuario_i FOREIGN KEY (usuario_id) REFERENCES usuario (idUsuario)
)
CHARSET = utf8mb4;

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
