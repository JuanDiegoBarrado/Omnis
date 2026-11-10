"""
Tests of omnis-storage, the landing zone the producers deliver the raw files to. Each test starts the
server in this process, on a free port and an empty folder of its own, and calls it over HTTP as a
producer would. They are independent of the engine.
"""
import base64
import importlib.util
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "storage_server", Path(__file__).parents[1] / "server" / "storage_server.py"
)
storage_server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(storage_server)

USERS = {"jd": "secret", "gym-app": "other"}
CSV = "fecha,num,ejercicio\n2026-10-01,1,Curl\n".encode()


class Client:
    def __init__(self, url: str):
        self.url = url

    def request(self, method: str, path: str, body: bytes | None = None, user: str | None = "jd",
                password: str = "secret", headers: dict | None = None) -> tuple[int, dict]:
        request = urllib.request.Request(self.url + path, data=body, method=method, headers=headers or {})
        if user is not None:
            token = base64.b64encode(f"{user}:{password}".encode()).decode()
            request.add_header("Authorization", f"Basic {token}")
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def deliver(self, entity: str, body: bytes = CSV, **arguments) -> tuple[int, dict]:
        return self.request("POST", f"/raw/{entity}", body, **arguments)


@pytest.fixture
def client(tmp_path) -> Client:
    server = storage_server.make_server(tmp_path, USERS, host="127.0.0.1", port=0)
    # A short poll interval, so shutdown() doesn't wait half a second per test
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield Client(f"http://127.0.0.1:{server.server_address[1]}")
    server.shutdown()
    server.server_close()


def files(root: Path) -> dict[str, bytes]:
    """Every file under root but the ones being written, by path relative to it."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and storage_server.INCOMING not in p.parts
    }


def test_keeps_a_delivered_file_where_the_raw_load_reads_it(client, tmp_path, monkeypatch):
    """
    Checks: a file delivered for an entity is kept, byte for byte, as
    raw/new/<entity>/<entity>_<YYYYMMDDHHMMSS>.csv, and the answer (201) says that path. Nothing is
    left in .incoming/, where it was written.

    If it fails: the raw loads would not find the delivered files (their source is
    raw/new/<entity>/), or would load them altered, and a producer couldn't tell where its file went.
    """
    monkeypatch.setattr(storage_server, "_timestamp", lambda: "20261109140512")

    status, body = client.deliver("series_gimnasio")

    assert (status, body) == (201, {"file": "raw/new/series_gimnasio/series_gimnasio_20261109140512.csv"})
    assert files(tmp_path) == {"raw/new/series_gimnasio/series_gimnasio_20261109140512.csv": CSV}
    assert list((tmp_path / storage_server.INCOMING).iterdir()) == []


def test_two_files_in_the_same_second_are_both_kept(client, tmp_path, monkeypatch):
    """
    Checks: two files of the same entity delivered in the same second are both kept: the second one
    gets the suffix _2, and a third _3.

    If it fails: a file would overwrite the one delivered just before it, and its rows would be lost
    without any error, for the producer or for the flow.
    """
    monkeypatch.setattr(storage_server, "_timestamp", lambda: "20261109140512")

    names = [client.deliver("series_gimnasio", f"fecha\n{i}\n".encode())[1]["file"] for i in range(3)]

    assert names == [
        "raw/new/series_gimnasio/series_gimnasio_20261109140512.csv",
        "raw/new/series_gimnasio/series_gimnasio_20261109140512_2.csv",
        "raw/new/series_gimnasio/series_gimnasio_20261109140512_3.csv",
    ]
    assert [files(tmp_path)[name] for name in names] == [b"fecha\n0\n", b"fecha\n1\n", b"fecha\n2\n"]


@pytest.mark.parametrize(
    "credentials",
    [
        pytest.param({"user": None}, id="no credentials"),
        pytest.param({"user": "jd", "password": "wrong"}, id="wrong password"),
        pytest.param({"user": "gym-app", "password": "secret"}, id="password of another user"),
        pytest.param({"user": "nobody", "password": "secret"}, id="unknown user"),
    ],
)
def test_rejects_a_file_without_a_user_and_its_password(client, tmp_path, credentials):
    """
    Checks: a delivery without credentials, with a wrong password, with another user's password or
    with a user that isn't in STORAGE_USERS (the test id says which) is answered 401, and nothing is
    kept.

    If it fails: anyone who can reach the port could put files in the landing zone, and their rows
    would end up in the warehouse as if a producer had sent them.
    """
    status, _ = client.deliver("series_gimnasio", **credentials)

    assert status == 401
    assert files(tmp_path) == {}


def test_every_user_can_deliver_with_its_own_password(client, tmp_path):
    """
    Checks: each user of STORAGE_USERS delivers with its own password.

    If it fails: only one of the users configured would work, so producers sharing the landing zone
    with their own passwords would be locked out.
    """
    assert client.deliver("series_gimnasio", user="jd", password="secret")[0] == 201
    assert client.deliver("sesiones_carrera", user="gym-app", password="other")[0] == 201
    assert len(files(tmp_path)) == 2


@pytest.mark.parametrize("entity", ["Series", "series-gimnasio", "..", "%2e%2e", "series%2Fgimnasio"])
def test_rejects_an_entity_that_is_not_a_plain_name(client, tmp_path, entity):
    """
    Checks: an entity with anything but lowercase letters, digits and _ (uppercase, a dash, a path
    like .., or one hidden in URL escapes; the test id says which) is answered 400, and nothing is
    kept.

    If it fails: a producer could write outside raw/new/, over files of other entities or of the
    archive, or into folders no raw load reads, where its files would be lost.
    """
    status, _ = client.deliver(entity)

    assert status == 400
    assert files(tmp_path) == {}


@pytest.mark.parametrize("path", ["/", "/raw", "/raw/series_gimnasio/extra", "/files/series_gimnasio"])
def test_only_raw_entity_paths_take_files(client, tmp_path, path):
    """
    Checks: a POST to anything but /raw/<entity> (the test id says which path) is answered 404, and
    nothing is kept.

    If it fails: a mistyped URL would still keep the file somewhere no raw load reads, and the
    producer would think it was delivered.
    """
    status, _ = client.request("POST", path, CSV)

    assert status == 404
    assert files(tmp_path) == {}


@pytest.mark.parametrize(
    "content, expected",
    [
        pytest.param(b"", 400, id="empty"),
        pytest.param("fecha,ejercicio\n2026-10-01,Curl de bíceps\n".encode("latin-1"), 400, id="not utf-8"),
    ],
)
def test_rejects_a_file_the_raw_load_could_not_read(client, tmp_path, content, expected):
    """
    Checks: an empty file, or one that isn't UTF-8 (the test id says which), is answered 400, and
    nothing is kept.

    If it fails: an empty file would stay in raw/new/ forever (it loads no rows, so it is never
    archived), and one that isn't UTF-8 would fail the raw load, and with it the run, which pauses
    the flow until someone removes the file by hand.
    """
    status, _ = client.deliver("series_gimnasio", content)

    assert status == expected
    assert files(tmp_path) == {}


def test_rejects_a_file_larger_than_the_limit(client, tmp_path, monkeypatch):
    """
    Checks: a file larger than MAX_FILE_BYTES is answered 413 without being read, and nothing is
    kept. One of exactly the limit is kept.

    If it fails: a producer's mistake (or anyone with a password) could fill the disk of the machine,
    which the warehouse and Airflow share.
    """
    monkeypatch.setattr(storage_server, "MAX_FILE_BYTES", len(CSV))

    assert client.deliver("series_gimnasio", CSV + b"x")[0] == 413
    assert files(tmp_path) == {}
    assert client.deliver("series_gimnasio", CSV)[0] == 201


def test_answers_its_health_without_credentials(client):
    """
    Checks: GET /health answers 200 with no credentials.

    If it fails: the healthcheck of the compose would mark the service unhealthy, although it works.
    """
    assert client.request("GET", "/health", user=None) == (200, {"status": "ok"})


@pytest.mark.parametrize(
    "value, expected",
    [
        pytest.param("jd:secret", {"jd": "secret"}, id="one user"),
        pytest.param("jd:secret, gym-app:a:b", {"jd": "secret", "gym-app": "a:b"}, id="several, a colon in a password"),
    ],
)
def test_reads_the_users_of_storage_users(value, expected):
    """
    Checks: STORAGE_USERS is read as name:password pairs separated by commas, spaces around them
    ignored, and a password may contain a colon (only the first one separates).

    If it fails: users written as the README says would not be able to deliver, or a password would
    be cut at its first colon.
    """
    assert storage_server.parse_users(value) == expected


@pytest.mark.parametrize("value", ["", "jd", "jd:", ":secret", "jd:secret,", "jd:a,jd:b"])
def test_a_wrong_storage_users_stops_the_server(value):
    """
    Checks: an empty STORAGE_USERS, a user without password or name, a trailing comma or a repeated
    user (the test id says which) fails with an error, so the server doesn't start.

    If it fails: the server would start with no users (nobody could deliver, and nothing would say
    why) or with a user whose password is empty.
    """
    with pytest.raises(ValueError, match="STORAGE_USERS"):
        storage_server.parse_users(value)
