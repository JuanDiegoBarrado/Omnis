-- Trazabilidad de las filas de los schemas de los flujos, salvo raw: sus tablas son una copia de los
-- ficheros que se recrea en cada carga, y el fichero de cada fila ya está en ellas (source_file).
-- Cada tabla lleva tres columnas que mantiene la propia base de datos, escriba quien escriba:
--   - sys_fec_insert: hora de la transacción que insertó la fila. No cambia nunca.
--   - sys_fec_mod: hora de la transacción que la cambió por última vez (al insertarla, la misma).
--   - sys_blame: quién la cambió por última vez (sys.current_blame).
-- Un trigger de filas las rellena al insertar y al modificar, ignorando lo que traiga la sentencia, y
-- se salta los updates que no cambian nada. Un event trigger se lo pone a cada tabla nueva y, al final
-- de este fichero, un barrido a las que ya existían.

-- Quién escribe: el login de la sesión (session_user, que SET ROLE no cambia y que no se puede falsear
-- sin su contraseña), más el detalle que haya fijado quien escribe en omnis.blame para su transacción,
-- como <login>:<detalle>. El engine fija <flujo>/<run_id>: omnis.blame es el BLAME_SETTING de
-- PostgresDatabase, y los dos deben llamarse igual. El nullif hace falta porque una sesión que ya lo
-- fijó alguna vez ve '' en lugar de NULL cuando termina esa transacción
CREATE OR REPLACE FUNCTION sys.current_blame() RETURNS text
LANGUAGE sql STABLE AS $$
    SELECT session_user || coalesce(':' || nullif(current_setting('omnis.blame', true), ''), '')
$$;

CREATE OR REPLACE FUNCTION sys.track_changes() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    system_columns text[];
BEGIN
    IF TG_OP = 'UPDATE' THEN
        -- Una fila que no cambia más que en sus columnas de sistema no se reescribe: el update de esa
        -- fila no se hace ni se cuenta, y la fila lo conserva todo, sys_source_file incluido
        system_columns := ARRAY(
            SELECT column_name FROM jsonb_object_keys(to_jsonb(NEW)) AS column_name
            WHERE column_name LIKE 'sys\_%'
        );
        IF to_jsonb(OLD) - system_columns = to_jsonb(NEW) - system_columns THEN
            RETURN NULL;
        END IF;
        NEW.sys_fec_insert := OLD.sys_fec_insert;
    ELSE
        NEW.sys_fec_insert := now();
    END IF;
    NEW.sys_fec_mod := now();
    NEW.sys_blame := sys.current_blame();
    RETURN NEW;
END
$$;

-- Las tablas de los schemas de los flujos salvo raw. Las particiones heredan de su tabla particionada
-- las columnas y el trigger, así que no se cuentan aparte
CREATE OR REPLACE FUNCTION sys.is_tracked_table(relation oid) RETURNS boolean
LANGUAGE sql STABLE AS $$
    SELECT sys.is_flow_schema(c.relnamespace) AND n.nspname <> 'raw'
       AND c.relkind IN ('r', 'p') AND NOT c.relispartition
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.oid = relation
$$;

-- Las filas que la tabla ya tenga reciben como fechas la hora de esta transacción y como sys_blame
-- existing_rows_blame: quien la crea, si la crea con filas (CREATE TABLE AS), o 'unknown' en el
-- barrido, porque esas filas las escribió alguien antes de que se registrara quién. No hace nada si
-- la tabla ya lo tiene todo, porque ALTER TABLE la bloquea aunque no cambie nada, y el barrido corre
-- en cada arranque
CREATE OR REPLACE FUNCTION sys.add_tracking(relation regclass, existing_rows_blame text) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
    IF (
        SELECT count(*) FROM pg_attribute
        WHERE attrelid = relation AND NOT attisdropped
          AND attname IN ('sys_fec_insert', 'sys_fec_mod', 'sys_blame')
    ) = 3 AND EXISTS (SELECT FROM pg_trigger WHERE tgrelid = relation AND tgname = 'sys_track_changes') THEN
        RETURN;
    END IF;
    EXECUTE format(
        'ALTER TABLE %s'
        ' ADD COLUMN IF NOT EXISTS sys_fec_insert timestamptz NOT NULL DEFAULT now(),'
        ' ADD COLUMN IF NOT EXISTS sys_fec_mod timestamptz NOT NULL DEFAULT now(),'
        ' ADD COLUMN IF NOT EXISTS sys_blame text NOT NULL DEFAULT %L',
        relation, existing_rows_blame
    );
    -- Lo que entre con el trigger desactivado no dice quién lo escribió
    EXECUTE format('ALTER TABLE %s ALTER COLUMN sys_blame SET DEFAULT %L', relation, 'unknown');
    EXECUTE format(
        'CREATE OR REPLACE TRIGGER sys_track_changes BEFORE INSERT OR UPDATE ON %s'
        ' FOR EACH ROW EXECUTE FUNCTION sys.track_changes()',
        relation
    );
END
$$;

CREATE OR REPLACE FUNCTION sys.track_created() RETURNS event_trigger
LANGUAGE plpgsql AS $$
DECLARE
    created record;
BEGIN
    FOR created IN
        SELECT objid FROM pg_event_trigger_ddl_commands() WHERE object_type = 'table' AND NOT in_extension
    LOOP
        IF sys.is_tracked_table(created.objid) THEN
            PERFORM sys.add_tracking(created.objid, sys.current_blame());
        END IF;
    END LOOP;
END
$$;

-- Solo al crear una tabla: sus propios ALTER TABLE y CREATE TRIGGER no lo vuelven a disparar. Corre
-- después de sys_claim_created (los event triggers se ejecutan por orden de nombre), con la tabla ya
-- de omnis_airflow, y quien la crea puede alterarla por ser omnis_airflow o miembro suyo
DROP EVENT TRIGGER IF EXISTS sys_track_created;
CREATE EVENT TRIGGER sys_track_created ON ddl_command_end
    WHEN TAG IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
    EXECUTE FUNCTION sys.track_created();

-- Barrido de las tablas que ya existían, salvo las que pertenecen a una extensión
DO $$
DECLARE
    table_oid oid;
BEGIN
    FOR table_oid IN
        SELECT c.oid FROM pg_class c
        WHERE c.relkind IN ('r', 'p') AND sys.is_tracked_table(c.oid)
          AND NOT EXISTS (
              SELECT FROM pg_depend d
              WHERE d.classid = 'pg_class'::regclass AND d.objid = c.oid AND d.deptype = 'e'
          )
    LOOP
        PERFORM sys.add_tracking(table_oid, 'unknown');
    END LOOP;
END
$$;
