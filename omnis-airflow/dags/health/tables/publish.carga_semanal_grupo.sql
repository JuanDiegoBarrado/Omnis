CREATE SCHEMA IF NOT EXISTS publish;

CREATE TABLE IF NOT EXISTS publish.carga_semanal_grupo(
    inicio_semana   DATE,               -- Monday of its ISO week
    anio_iso        INTEGER NOT NULL,
    semana_iso      INTEGER NOT NULL,
    grupo           VARCHAR,
    series          FLOAT   NOT NULL,
    si              FLOAT   NOT NULL,
    rpe_medio       FLOAT,              -- NULL in a week without series of the group
    CHECK(((1 <= semana_iso) AND (semana_iso <= 53))),
    CHECK((series >= 0)),
    CHECK((si >= 0)),
    CHECK(((0 <= rpe_medio) AND (rpe_medio <= 10))),
    PRIMARY KEY(inicio_semana, grupo)
);
