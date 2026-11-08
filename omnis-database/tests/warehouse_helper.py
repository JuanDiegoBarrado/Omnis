from dataclasses import dataclass
from pathlib import Path

import psycopg2

# The SQL postgres_init.sh applies, in its order
INIT_SQL = sorted((Path(__file__).parents[1] / "init" / "sql").glob("*.sql"))

# The roles the tests act as. The superuser stands for the image's (POSTGRES_USER in the stack). The
# engine's role is created as postgres_init.sh does, and there is a login of each group, as the
# README says to create them. Every login's password is its name
SUPERUSER = "superuser"
ENGINE = "omnis_airflow"
ADMIN = "an_admin"
USER = "a_user"
VIEWER = "a_viewer"
LOGINS = {ADMIN: "database_admin", USER: "database_user", VIEWER: "visualization"}


@dataclass(frozen=True)
class Server:
    """Where the throwaway Postgres of the session listens, and its superuser."""

    host: str
    port: int
    superuser: str
    password: str
    database: str

    def connect(self, database: str, role: str = SUPERUSER):
        user, password = (self.superuser, self.password) if role == SUPERUSER else (role, role)
        return psycopg2.connect(host=self.host, port=self.port, dbname=database, user=user, password=password)


class Warehouse:
    """
    A database of the server, used as any of the roles above. Each call opens a connection as the
    role, runs its SQL in one transaction and commits it, through psycopg2 directly.
    """

    def __init__(self, server: Server, name: str):
        self.server = server
        self.name = name

    def connect(self, role: str):
        """A connection as the role, for a test that needs several transactions in one session."""
        return self.server.connect(self.name, role)

    def execute(self, role: str, query: str, params=None) -> int:
        """Run the SQL and return the rows its last statement affected."""
        connection = self.connect(role)
        try:
            with connection, connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
        finally:
            connection.close()

    def fetch(self, role: str, query: str, params=None) -> list[tuple]:
        """Run the SQL and return the rows of its last statement."""
        connection = self.connect(role)
        try:
            with connection, connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        finally:
            connection.close()

    def apply_init(self) -> None:
        """Apply the init's SQL as the superuser, each file in one transaction, as postgres_init.sh does."""
        for path in INIT_SQL:
            self.execute(SUPERUSER, path.read_text(encoding="utf-8"))

    def owner(self, kind: str, name: str) -> str:
        """The owner of a `schema`, a `relation` (table or view) or a `routine` (by signature, `raw.f(text)`)."""
        query = {
            "schema": "SELECT nspowner::regrole::text FROM pg_namespace WHERE nspname = %s",
            "relation": "SELECT relowner::regrole::text FROM pg_class WHERE oid = %s::regclass",
            "routine": "SELECT proowner::regrole::text FROM pg_proc WHERE oid = %s::regprocedure",
        }[kind]
        [(owner,)] = self.fetch(SUPERUSER, query, (name,))
        return owner

    def tracking(self, table: str) -> tuple[list[str], bool]:
        """The system columns that the warehouse keeps of a table, and whether its trigger is on it."""
        columns = self.fetch(
            SUPERUSER,
            "SELECT attname::text FROM pg_attribute WHERE attrelid = %s::regclass AND attname::text"
            " IN ('sys_fec_insert', 'sys_fec_mod', 'sys_blame') AND NOT attisdropped ORDER BY attnum",
            (table,),
        )
        [(has_trigger,)] = self.fetch(
            SUPERUSER,
            "SELECT EXISTS (SELECT FROM pg_trigger WHERE tgrelid = %s::regclass AND tgname = 'sys_track_changes')",
            (table,),
        )
        return [column for (column,) in columns], has_trigger
