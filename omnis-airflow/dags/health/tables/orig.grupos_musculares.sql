-- Reference table: the muscle groups of orig.ejercicios_musculares and the zone each one belongs to, read by publish.
-- `grupo` is the name of its column in orig.ejercicios_musculares, and `zona` takes the values of its `categoria`
-- (plus "Core", which no exercise has as categoria), so a report can go from one to the other.
-- This file is its only source: every run replaces its rows with the ones below, so edit them here.
CREATE SCHEMA IF NOT EXISTS orig;

CREATE TABLE IF NOT EXISTS orig.grupos_musculares (
    grupo VARCHAR,
    nombre VARCHAR NOT NULL,
    zona VARCHAR NOT NULL,
    orden INTEGER NOT NULL,
    PRIMARY KEY ("grupo")
);

DELETE FROM orig.grupos_musculares;

INSERT INTO orig.grupos_musculares (grupo, nombre, zona, orden) VALUES
--   grupo                    nombre                   zona                orden
    ('pectoral',              'Pectoral',              'Pectoral',          1),
    ('dorsal',                'Dorsal',                'Dorsal',            2),
    ('trapecio',              'Trapecio',              'Trapecio',          3),
    ('deltoides_anterior',    'Deltoides anterior',    'Deltoides',         4),
    ('deltoides_lateral',     'Deltoides lateral',     'Deltoides',         5),
    ('deltoides_posterior',   'Deltoides posterior',   'Deltoides',         6),
    ('biceps',                'Bíceps',                'Biceps',            7),
    ('triceps',               'Tríceps',               'Triceps',           8),
    ('cuadriceps',            'Cuádriceps',            'Pierna anterior',   9),
    ('aductores',             'Aductores',             'Pierna anterior',  10),
    ('isquios',               'Isquiotibiales',        'Pierna posterior', 11),
    ('gluteos',               'Glúteos',               'Pierna posterior', 12),
    ('gemelos',               'Gemelos',               'Pierna posterior', 13),
    ('abdominales',           'Abdominales',           'Core',             14);
