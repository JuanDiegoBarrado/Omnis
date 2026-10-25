CREATE SCHEMA IF NOT EXISTS clean;

CREATE TABLE IF NOT EXISTS clean.impacto_muscular(
    id_serie   VARCHAR,
    fecha       DATE    NOT NULL,
    grupo       VARCHAR,
    series      FLOAT   NOT NULL,
    si        FLOAT   NOT NULL,
    rpe       FLOAT   NOT NULL,
    rir       FLOAT   NOT NULL,
    CHECK((series > 0)),
    CHECK((si >= 0)),
    CHECK(((0 <= rpe) AND (rpe <= 10))),
    CHECK((rir >= 0)),
    PRIMARY KEY(id_serie, grupo)
);
