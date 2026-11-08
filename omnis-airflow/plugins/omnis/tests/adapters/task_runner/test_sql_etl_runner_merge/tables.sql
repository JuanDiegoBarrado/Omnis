-- The origin is text, like a raw table, with the file each row came from. The destination is typed
-- and keeps the file of the last change of each row, like an orig table
CREATE SCHEMA src;
CREATE TABLE src.origin (id TEXT, fecha TEXT, peso TEXT, source_file TEXT);

CREATE SCHEMA dst;
CREATE TABLE dst.destination (id INTEGER, fecha DATE, peso FLOAT, sys_source_file TEXT);
