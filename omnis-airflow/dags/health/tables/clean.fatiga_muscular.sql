CREATE SCHEMA IF NOT EXISTS clean;

CREATE TABLE IF NOT EXISTS clean.fatiga_muscular(
    id_fatiga            VARCHAR,
    fecha                 DATE,
    pectoral              FLOAT NOT NULL,
    triceps               FLOAT NOT NULL,
    dorsal                FLOAT NOT NULL,
    trapecio              FLOAT NOT NULL,
    biceps                FLOAT NOT NULL,
    isquios               FLOAT NOT NULL,
    cuadriceps            FLOAT NOT NULL,
    aductores             FLOAT NOT NULL,
    gluteos               FLOAT NOT NULL,
    gemelos               FLOAT NOT NULL,
    abdominales           FLOAT NOT NULL,
    deltoides_anterior    FLOAT NOT NULL,
    deltoides_posterior   FLOAT NOT NULL,
    deltoides_lateral     FLOAT NOT NULL,
    CHECK((pectoral >= 0)), CHECK((triceps >= 0)), CHECK((dorsal >= 0)),
    CHECK((trapecio >= 0)), CHECK((biceps >= 0)), CHECK((isquios >= 0)),
    CHECK((cuadriceps >= 0)), CHECK((aductores >= 0)), CHECK((gluteos >= 0)),
    CHECK((gemelos >= 0)), CHECK((abdominales >= 0)),
    CHECK((deltoides_anterior >= 0)), CHECK((deltoides_posterior >= 0)), CHECK((deltoides_lateral >= 0)),
    PRIMARY KEY(id_fatiga)
);
