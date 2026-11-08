-- Dueño y permisos de lo que hay en los schemas de los flujos: todos salvo public, sys y los del
-- sistema (information_schema y pg_*, que incluye los de las tablas temporales).
--   - Todo lo que se crea en ellos (schemas, tablas, vistas y funciones) pasa a ser de omnis_airflow,
--     lo cree quien lo cree: el engine, un database_admin o el superusuario. Así el engine siempre
--     puede alterarlo o reemplazarlo, y un database_admin, como miembro suyo, también.
--   - database_user puede leer todos los schemas y sus tablas y vistas, raw incluido.
--   - visualization solo puede leer el schema publish.
-- Lo hace un event trigger cuando se crea cada objeto, porque las tablas las crean los flujos en su
-- primera ejecución, y al final de este fichero un barrido de lo que ya existía. Se usa en lugar de
-- ALTER DEFAULT PRIVILEGES porque esos solo cubren lo que crea un rol concreto, y los de publish
-- exigirían que el schema ya existiera.

CREATE SCHEMA IF NOT EXISTS sys;
-- El event trigger corre con el rol de quien crea el objeto, sea cual sea
GRANT USAGE ON SCHEMA sys TO PUBLIC;

CREATE OR REPLACE FUNCTION sys.is_flow_schema(schema_oid oid) RETURNS boolean
LANGUAGE sql STABLE AS $$
    SELECT nspname NOT IN ('public', 'sys', 'information_schema') AND nspname NOT LIKE 'pg\_%'
    FROM pg_namespace
    WHERE oid = schema_oid
$$;

-- Los permisos se dan antes de cambiar el dueño, mientras quien crea el objeto aún es su dueño: al
-- cambiarlo, pasan a constar como dados por omnis_airflow. El dueño solo se cambia si no lo es ya,
-- porque ALTER ... OWNER bloquea el objeto aunque no cambie nada, y el barrido corre en cada arranque
CREATE OR REPLACE FUNCTION sys.claim_schema(schema_oid oid) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    schema_name name;
    owner oid;
BEGIN
    SELECT nspname, nspowner INTO schema_name, owner FROM pg_namespace WHERE oid = schema_oid;
    IF NOT sys.is_flow_schema(schema_oid) THEN
        RETURN;
    END IF;
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO database_user', schema_name);
    IF schema_name = 'publish' THEN
        EXECUTE format('GRANT USAGE ON SCHEMA %I TO visualization', schema_name);
    END IF;
    IF owner <> 'omnis_airflow'::regrole THEN
        EXECUTE format('ALTER SCHEMA %I OWNER TO omnis_airflow', schema_name);
    END IF;
END
$$;

CREATE OR REPLACE FUNCTION sys.claim_relation(relation regclass) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    schema_oid oid;
    kind "char";
    owner oid;
BEGIN
    SELECT relnamespace, relkind, relowner INTO schema_oid, kind, owner FROM pg_class WHERE oid = relation;
    -- Tablas (también las particionadas), vistas y vistas materializadas
    IF NOT sys.is_flow_schema(schema_oid) OR kind NOT IN ('r', 'p', 'v', 'm') THEN
        RETURN;
    END IF;
    EXECUTE format('GRANT SELECT ON %s TO database_user', relation);
    IF (SELECT nspname FROM pg_namespace WHERE oid = schema_oid) = 'publish' THEN
        EXECUTE format('GRANT SELECT ON %s TO visualization', relation);
    END IF;
    IF owner <> 'omnis_airflow'::regrole THEN
        EXECUTE format(
            'ALTER %s %s OWNER TO omnis_airflow',
            CASE kind WHEN 'v' THEN 'VIEW' WHEN 'm' THEN 'MATERIALIZED VIEW' ELSE 'TABLE' END,
            relation
        );
    END IF;
END
$$;

-- Las funciones ya las puede ejecutar cualquiera (PUBLIC), así que solo cambia su dueño
CREATE OR REPLACE FUNCTION sys.claim_routine(routine regprocedure) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
    schema_oid oid;
    owner oid;
BEGIN
    SELECT pronamespace, proowner INTO schema_oid, owner FROM pg_proc WHERE oid = routine;
    IF sys.is_flow_schema(schema_oid) AND owner <> 'omnis_airflow'::regrole THEN
        EXECUTE format('ALTER ROUTINE %s OWNER TO omnis_airflow', routine);
    END IF;
END
$$;

CREATE OR REPLACE FUNCTION sys.claim_created() RETURNS event_trigger
LANGUAGE plpgsql AS $$
DECLARE
    created record;
BEGIN
    FOR created IN SELECT objid, object_type FROM pg_event_trigger_ddl_commands() WHERE NOT in_extension LOOP
        IF created.object_type = 'schema' THEN
            PERFORM sys.claim_schema(created.objid);
        ELSIF created.object_type IN ('table', 'view', 'materialized view') THEN
            PERFORM sys.claim_relation(created.objid);
        ELSIF created.object_type IN ('function', 'procedure') THEN
            PERFORM sys.claim_routine(created.objid);
        END IF;
    END LOOP;
END
$$;

-- Solo al crear: sus propios ALTER ... OWNER y GRANT no lo vuelven a disparar
DROP EVENT TRIGGER IF EXISTS sys_claim_created;
CREATE EVENT TRIGGER sys_claim_created ON ddl_command_end
    WHEN TAG IN (
        'CREATE SCHEMA', 'CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO', 'CREATE VIEW',
        'CREATE MATERIALIZED VIEW', 'CREATE FUNCTION', 'CREATE PROCEDURE'
    )
    EXECUTE FUNCTION sys.claim_created();

-- Barrido de lo que ya existía: lo creado antes de este init, o con el event trigger desactivado.
-- Se salta lo que pertenece a una extensión, que es de la extensión
DO $$
DECLARE
    object_oid oid;
BEGIN
    FOR object_oid IN SELECT oid FROM pg_namespace WHERE sys.is_flow_schema(oid) LOOP
        PERFORM sys.claim_schema(object_oid);
    END LOOP;
    FOR object_oid IN
        SELECT c.oid FROM pg_class c
        WHERE sys.is_flow_schema(c.relnamespace)
          AND NOT EXISTS (
              SELECT FROM pg_depend d
              WHERE d.classid = 'pg_class'::regclass AND d.objid = c.oid AND d.deptype = 'e'
          )
    LOOP
        PERFORM sys.claim_relation(object_oid);
    END LOOP;
    FOR object_oid IN
        SELECT p.oid FROM pg_proc p
        WHERE sys.is_flow_schema(p.pronamespace)
          AND NOT EXISTS (
              SELECT FROM pg_depend d
              WHERE d.classid = 'pg_proc'::regclass AND d.objid = p.oid AND d.deptype = 'e'
          )
    LOOP
        PERFORM sys.claim_routine(object_oid);
    END LOOP;
END
$$;
