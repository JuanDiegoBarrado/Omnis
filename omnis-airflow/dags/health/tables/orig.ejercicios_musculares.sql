-- Reference table: share of each muscle group worked by each exercise. Loaded by hand, read by clean.
CREATE SCHEMA IF NOT EXISTS orig;

CREATE TABLE IF NOT EXISTS orig.ejercicios_musculares (
    ejercicio VARCHAR,
    categoria VARCHAR NOT NULL,
    pectoral FLOAT NOT NULL,
    triceps FLOAT NOT NULL,
    dorsal FLOAT NOT NULL,
    trapecio FLOAT NOT NULL,
    biceps FLOAT NOT NULL,
    isquios FLOAT NOT NULL,
    cuadriceps FLOAT NOT NULL,
    aductores FLOAT NOT NULL,
    gluteos FLOAT NOT NULL,
    gemelos FLOAT NOT NULL,
    abdominales FLOAT NOT NULL,
    deltoides_anterior FLOAT NOT NULL,
    deltoides_posterior FLOAT NOT NULL,
    deltoides_lateral FLOAT NOT NULL,
    PRIMARY KEY ("ejercicio")
);
