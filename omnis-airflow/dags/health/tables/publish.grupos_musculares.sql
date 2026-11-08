CREATE SCHEMA IF NOT EXISTS publish;

CREATE TABLE IF NOT EXISTS publish.grupos_musculares(
    grupo   VARCHAR,
    nombre  VARCHAR NOT NULL,
    zona    VARCHAR NOT NULL,
    orden   INTEGER NOT NULL,
    PRIMARY KEY(grupo)
);
