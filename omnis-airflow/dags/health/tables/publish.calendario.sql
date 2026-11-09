CREATE SCHEMA IF NOT EXISTS publish;

CREATE TABLE IF NOT EXISTS publish.calendario(
    fecha           DATE,
    anio            INTEGER NOT NULL,
    mes             INTEGER NOT NULL,
    inicio_semana   DATE    NOT NULL,   -- Monday of its ISO week
    anio_iso        INTEGER NOT NULL,   -- year of its ISO week, which differs from anio in some days of late December and early January
    semana_iso      INTEGER NOT NULL,
    dia_semana      INTEGER NOT NULL,   -- 1 (Monday) to 7 (Sunday)
    CHECK(((1 <= mes) AND (mes <= 12))),
    CHECK(((1 <= semana_iso) AND (semana_iso <= 53))),
    CHECK(((1 <= dia_semana) AND (dia_semana <= 7))),
    PRIMARY KEY(fecha)
);
