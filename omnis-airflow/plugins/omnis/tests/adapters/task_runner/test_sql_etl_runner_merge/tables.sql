-- The origin is text, like a raw table; the destination is typed, like an orig table
CREATE SCHEMA src;
CREATE TABLE src.origin (id TEXT, fecha TEXT, peso TEXT);

CREATE SCHEMA dst;
CREATE TABLE dst.destination (id INTEGER, fecha DATE, peso FLOAT);
