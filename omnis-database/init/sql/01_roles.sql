-- Roles del warehouse. omnis_airflow, el rol del engine, lo crea postgres_init.sh antes, porque
-- necesita la contraseña de .env.
--
-- Los grupos no tienen login: cada persona o aplicación entra con un login propio miembro de uno de
-- ellos (CREATE ROLE <login> LOGIN IN ROLE <grupo>, ver README.md), así que quien escribe queda
-- identificado y quitarle el acceso a alguien no afecta a los demás.
--   - database_admin: todo lo que el dueño de los objetos de los flujos (omnis_airflow), estructura
--     incluida, mientras no esté automatizado.
--   - database_user: lee todos los schemas de los flujos, raw incluido (02_access.sql).
--   - visualization: lee solo publish (02_access.sql).
DO $$
DECLARE
    group_name name;
BEGIN
    FOREACH group_name IN ARRAY ARRAY['database_admin', 'database_user', 'visualization'] LOOP
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = group_name) THEN
            EXECUTE format('CREATE ROLE %I NOLOGIN', group_name);
        END IF;
    END LOOP;
END
$$;

-- Ser miembro del dueño es lo único que deja cambiar la estructura de una tabla (ALTER TABLE) sin
-- ser superusuario
GRANT omnis_airflow TO database_admin;

-- El engine crea los schemas de cada flujo en su primera ejecución
DO $$
BEGIN
    EXECUTE format('GRANT CREATE ON DATABASE %I TO omnis_airflow', current_database());
END
$$;
