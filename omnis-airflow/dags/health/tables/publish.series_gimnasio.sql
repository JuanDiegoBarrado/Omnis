CREATE SCHEMA IF NOT EXISTS publish;

CREATE TABLE IF NOT EXISTS publish.series_gimnasio(
    id_serie   VARCHAR,
    fecha       DATE    NOT NULL,
    ejercicio   VARCHAR NOT NULL,
    categoria   VARCHAR NOT NULL,
    peso        FLOAT   NOT NULL,
    por_rm    FLOAT,      -- NULL when peso is 0
    reps        INTEGER NOT NULL,
    rir       FLOAT   NOT NULL,
    rpe       FLOAT   NOT NULL,
    rm        FLOAT   NOT NULL,
    si        FLOAT   NOT NULL,
    CHECK((peso >= 0)),
    CHECK(((0 <= por_rm) AND (por_rm <= 1))),
    CHECK((reps >= 0)),
    CHECK((rir >= 0)),
    CHECK(((0 <= rpe) AND (rpe <= 10))),
    CHECK((rm >= 0)),
    CHECK(((0 <= si) AND (si <= 2))),
    PRIMARY KEY(id_serie)
);
