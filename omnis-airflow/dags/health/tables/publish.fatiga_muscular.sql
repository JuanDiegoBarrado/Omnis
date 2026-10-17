CREATE SCHEMA IF NOT EXISTS publish;

CREATE TABLE IF NOT EXISTS publish.fatiga_muscular(
    id_fatiga      VARCHAR,
    fecha           DATE    NOT NULL,
    grupo_muscular  VARCHAR,
    si            FLOAT   NOT NULL,
    CHECK((si >= 0)),
    PRIMARY KEY(id_fatiga, grupo_muscular)
);
