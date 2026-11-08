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

    def execute(self, role: str, query: str, params=None) -> None:
        connection = self.server.connect(self.name, role)
        try:
            with connection, connection.cursor() as cursor:
                cursor.execute(query, params)
        finally:
            connection.close()

    def fetch(self, role: str, query: str, params=None) -> list[tuple]:
        connection = self.server.connect(self.name, role)
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
