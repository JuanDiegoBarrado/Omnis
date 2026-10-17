CREATE SCHEMA IF NOT EXISTS orig;

CREATE TABLE IF NOT EXISTS orig.series_gimnasio(
    fecha       DATE,
    num         INTEGER,
    ejercicio   VARCHAR NOT NULL,
    peso        FLOAT   NOT NULL,
    reps        FLOAT   NOT NULL,
    rir       FLOAT   NOT NULL,
    rpe       FLOAT   NOT NULL,
    CHECK((peso >= 0)),
    CHECK((reps >= 0)),
    CHECK((rir >= 0)),
    CHECK(((0 <= rpe) AND (rpe <= 10))),
    PRIMARY KEY(fecha, num)
);
