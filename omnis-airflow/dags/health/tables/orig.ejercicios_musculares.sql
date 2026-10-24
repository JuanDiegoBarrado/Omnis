-- Reference table: share of each muscle group worked by each exercise, read by clean.
-- This file is its only source: every run replaces its rows with the ones below, so edit them here.
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

DELETE FROM orig.ejercicios_musculares;

INSERT INTO orig.ejercicios_musculares (
    ejercicio, categoria,
    pectoral, triceps, dorsal, trapecio, biceps, isquios, cuadriceps, aductores, gluteos, gemelos,
    abdominales, deltoides_anterior, deltoides_posterior, deltoides_lateral
) VALUES
--   ejercicio                              categoria          pect  tric  dors  trap  bice  isqu  cuad  aduc  glut  geme  abdo  dAnt  dPos  dLat
    ('Curl araña',                          'Biceps',           0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Curl de biceps con mancuerna',        'Biceps',           0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Curl de biceps en barra',             'Biceps',           0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Curl en banco inclinado',             'Biceps',           0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Curl en banco scott',                 'Biceps',           0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Deltoides posterior en maquina',      'Deltoides',        0.00, 0.00, 0.10, 0.30, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.15),
    ('Elevaciones laterales con mancuerna', 'Deltoides',        0.00, 0.00, 0.00, 0.25, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00),
    ('Press militar',                       'Deltoides',        0.00, 0.25, 0.00, 0.25, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.10, 0.25),
    ('Remo al menton con barra',            'Deltoides',        0.00, 0.00, 0.00, 0.75, 0.25, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00),
    ('Dominadas',                           'Dorsal',           0.00, 0.00, 1.00, 0.45, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00),
    ('Jalon al pecho',                      'Dorsal',           0.00, 0.00, 1.00, 0.45, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00),
    ('Pull over',                           'Dorsal',           0.45, 0.15, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00),
    ('Remo bajo en maquina',                'Dorsal',           0.00, 0.00, 1.00, 0.50, 0.20, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.20, 0.00),
    ('Remo con mancuerna unilateral',       'Dorsal',           0.00, 0.00, 1.00, 0.50, 0.20, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.20, 0.00),
    ('Remo en barra libre',                 'Dorsal',           0.00, 0.00, 1.00, 0.55, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00),
    ('Remo en punta',                       'Dorsal',           0.00, 0.00, 1.00, 0.45, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00),
    ('Remo gironda',                        'Dorsal',           0.00, 0.00, 1.00, 0.55, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00),
    ('Flies en banco',                      'Pectoral',         1.00, 0.00, 0.00, 0.00, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00, 0.00),
    ('Flies en maquina',                    'Pectoral',         1.00, 0.00, 0.00, 0.00, 0.10, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00, 0.00),
    ('Fondos en paralelas',                 'Pectoral',         1.00, 0.70, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00, 0.00),
    ('Pecho en polea alta',                 'Pectoral',         1.00, 0.15, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00, 0.00),
    ('Pecho en polea baja',                 'Pectoral',         1.00, 0.15, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00, 0.00),
    ('Press banca',                         'Pectoral',         1.00, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.30, 0.00, 0.00),
    ('Press banca inclinado',               'Pectoral',         1.00, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.30, 0.00, 0.00),
    ('Press de banca con mancuernas',       'Pectoral',         1.00, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.30, 0.00, 0.00),
    ('Press de banca declinado',            'Pectoral',         1.00, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 0.00, 0.00),
    ('Press en maquina',                    'Pectoral',         1.00, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.35, 0.00, 0.00),
    ('Press inclinado con mancuernas',      'Pectoral',         1.00, 0.35, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.30, 0.00, 0.00),
    ('Aduccion en maquina',                 'Pierna anterior',  0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.15, 1.00, 0.15, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Extension de cuadriceps',             'Pierna anterior',  0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Sentadilla en jaca',                  'Pierna anterior',  0.00, 0.00, 0.00, 0.00, 0.00, 0.25, 1.00, 0.00, 0.45, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Curl de biceps femoral',              'Pierna posterior', 0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.25, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Peso muerto rumano',                  'Pierna posterior', 0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.55, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Caminata del granjero',               'Trapecio',         0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Encogimientos',                       'Trapecio',         0.00, 0.00, 0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.10, 0.00),
    ('Face pull',                           'Trapecio',         0.00, 0.00, 0.00, 0.45, 0.25, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00),
    ('Snatch',                              'Trapecio',         0.00, 0.00, 0.00, 0.75, 0.00, 0.45, 0.35, 0.00, 0.00, 0.00, 0.00, 1.00, 0.00, 1.00),
    ('Extensiones de codo en polea',        'Triceps',          0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00),
    ('Extensiones katana con mancuerna',    'Triceps',          0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.20, 0.00),
    ('Press frances',                       'Triceps',          0.00, 1.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00);
