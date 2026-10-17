CREATE SCHEMA IF NOT EXISTS orig;

CREATE TABLE IF NOT EXISTS orig.sesiones_carrera(
    fecha       DATE,
    num         INTEGER,
    categoria   VARCHAR,
    modalidad   VARCHAR,
    distancia   FLOAT   NOT NULL,
    tiempo      FLOAT   NOT NULL,
    cals        FLOAT   NOT NULL,
    fc_avg     FLOAT,
    fc_max     FLOAT,
    por_z1    FLOAT   NOT NULL,
    por_z2    FLOAT   NOT NULL,
    por_z3    FLOAT   NOT NULL,
    por_z4    FLOAT   NOT NULL,
    por_z5    FLOAT   NOT NULL,
    CHECK((tiempo >= 0)),
    CHECK((distancia >= 0)),
    CHECK((cals >= 0)),
    CHECK((fc_avg IS NULL OR (0 <= fc_avg AND fc_avg <= 220))),
    CHECK((fc_max IS NULL OR (0 <= fc_max AND fc_max <= 220))),
    CHECK(((0 <= por_z1) AND (por_z1 <= 1))),
    CHECK(((0 <= por_z2) AND (por_z2 <= 1))),
    CHECK(((0 <= por_z3) AND (por_z3 <= 1))),
    CHECK(((0 <= por_z4) AND (por_z4 <= 1))),
    CHECK(((0 <= por_z5) AND (por_z5 <= 1))),
    PRIMARY KEY(fecha, num)
);
