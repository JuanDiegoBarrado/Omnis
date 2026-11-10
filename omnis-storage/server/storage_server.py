"""
omnis-storage: the landing zone of the raw files. Producers deliver each file over HTTP, and the
server keeps it in <data>/raw/new/<entity>/<entity>_<YYYYMMDDHHMMSS>.csv (UTC), where the raw
loads of the flows read it and the archives move it from.

    POST /raw/<entity>   the body is the CSV. HTTP Basic auth, with a user of STORAGE_USERS
                         201 {"file": "raw/new/<entity>/<name>.csv"}
    GET  /health         no auth, for the healthcheck

- The server names the file, so a producer can't overwrite another's or write outside its entity's
  folder. Two files of the same entity in the same second get a suffix (`_2`, `_3`...).
- A file is written under <data>/.incoming/ and renamed into place when complete, so a raw load
  never reads half a file. The raw load only reads `.csv` files directly under its prefix.
- A file must be UTF-8, not empty, and at most MAX_FILE_BYTES: a file the raw load can't read would
  fail the run and pause the flow. Nothing else of the CSV is checked here.
- STORAGE_USERS is `name:password,name:password...`: whoever runs Omnis chooses the users and their
  passwords (one per producer or shared), and the name only shows in the log. A password can't
  contain a comma.

Python's standard library only, so it runs on the official Python image with nothing installed.
"""
import base64
import binascii
import hmac
import json
import logging
import os
import re
import signal
import sys
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = 9000
MAX_FILE_BYTES = 50 * 1024 * 1024
ENTITY = re.compile(r"[a-z0-9_]+")
NEW_FILES = Path("raw", "new")
INCOMING = ".incoming"

logger = logging.getLogger("omnis-storage")


def parse_users(value: str) -> dict[str, str]:
    """The users of STORAGE_USERS (`name:password,...`), as {name: password}."""
    users = {}
    for entry in (part.strip() for part in value.split(",")):
        name, _, password = entry.partition(":")
        if not name or not password:
            raise ValueError("STORAGE_USERS must be name:password pairs separated by commas")
        if name in users:
            raise ValueError(f"STORAGE_USERS repeats the user {name!r}")
        users[name] = password
    return users


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


class Storage:
    """Where the delivered files are kept: <root>/raw/new/<entity>/."""

    def __init__(self, root: Path):
        self.root = root
        self._incoming = root / INCOMING
        self._incoming.mkdir(parents=True, exist_ok=True)
        (root / NEW_FILES).mkdir(parents=True, exist_ok=True)
        # Choosing a free name and renaming into it must not interleave between two requests
        self._naming = threading.Lock()

    def keep(self, entity: str, content: bytes) -> str:
        """Keep a delivered file of `entity`, and return its path relative to the root."""
        partial = self._incoming / f"{uuid.uuid4().hex}.part"
        with open(partial, "wb") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        folder = self.root / NEW_FILES / entity
        folder.mkdir(parents=True, exist_ok=True)
        with self._naming:
            stem = f"{entity}_{_timestamp()}"
            target, copy = folder / f"{stem}.csv", 1
            while target.exists():
                copy += 1
                target = folder / f"{stem}_{copy}.csv"
            os.replace(partial, target)
        return target.relative_to(self.root).as_posix()


def make_handler(storage: Storage, users: dict[str, str]) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "omnis-storage"

        def do_GET(self):
            if self.path == "/health":
                self._reply(200, {"status": "ok"})
            else:
                self._reply(404, {"error": "not found"})

        def do_POST(self):
            parts = self.path.strip("/").split("/")
            if len(parts) != 2 or parts[0] != "raw":
                return self._reply(404, {"error": "not found: deliver files with POST /raw/<entity>"})
            user = self._authenticated_user()
            if user is None:
                return self._reply(401, {"error": "wrong user or password"},
                                   {"WWW-Authenticate": 'Basic realm="omnis-storage"'})
            entity = parts[1]
            if not ENTITY.fullmatch(entity):
                return self._reply(400, {"error": "the entity must be lowercase letters, digits and _"})
            length = self.headers.get("Content-Length")
            if length is None or not length.isdigit():
                return self._reply(411, {"error": "Content-Length is required"})
            if int(length) > MAX_FILE_BYTES:
                return self._reply(413, {"error": f"the file is larger than {MAX_FILE_BYTES} bytes"})
            content = self.rfile.read(int(length))
            if not content:
                return self._reply(400, {"error": "the file is empty"})
            try:
                content.decode("utf-8")
            except UnicodeDecodeError:
                return self._reply(400, {"error": "the file is not UTF-8"})
            path = storage.keep(entity, content)
            logger.info("%s delivered %s (%d bytes)", user, path, len(content))
            self._reply(201, {"file": path})

        def _authenticated_user(self) -> str | None:
            scheme, _, credentials = (self.headers.get("Authorization") or "").partition(" ")
            if scheme.lower() != "basic":
                return None
            try:
                name, _, password = base64.b64decode(credentials, validate=True).decode("utf-8").partition(":")
            except (binascii.Error, UnicodeDecodeError):
                return None
            expected = users.get(name)
            # Compared in constant time, so the time of an answer gives no hint of the password
            if expected is None or not hmac.compare_digest(password.encode(), expected.encode()):
                return None
            return name

        def _reply(self, status: int, body: dict, headers: dict | None = None) -> None:
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            for name, value in (headers or {}).items():
                self.send_header(name, value)
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):
            logger.info("%s %s", self.address_string(), format % args)

    return Handler


def make_server(root: Path, users: dict[str, str], host: str = "0.0.0.0", port: int = PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(Storage(root), users))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stdout)
    users = parse_users(os.environ.get("STORAGE_USERS", ""))
    server = make_server(Path(os.environ.get("STORAGE_DATA_DIR", "/data")), users)
    # It is the container's main process: without this, docker stop would wait 10 s and kill it
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    logger.info("Listening on port %d with %d users", PORT, len(users))
    server.serve_forever()


if __name__ == "__main__":
    main()
