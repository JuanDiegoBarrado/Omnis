-- Raw values exported from spreadsheets use placeholders for "no value": turn them into NULL
CREATE SCHEMA IF NOT EXISTS raw;

CREATE OR REPLACE FUNCTION raw.null_if_placeholder(value TEXT) RETURNS TEXT
LANGUAGE sql IMMUTABLE AS $$
    SELECT CASE
        WHEN TRIM(value) IN ('', '-', '#VALOR!', '#DIV/0!', '#N/A') THEN NULL
        ELSE TRIM(value)
    END
$$;
