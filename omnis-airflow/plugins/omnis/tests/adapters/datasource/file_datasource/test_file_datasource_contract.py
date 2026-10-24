"""
The file operations every FileDataSource implements, checked the same on each storage: whatever
works on the local filesystem must work on S3. Each storage is set up and checked directly, not
through the adapter under test.

Every test runs once per storage: the test id ends in [local] or [s3] and says which one fails.
"""
from pathlib import Path

import boto3
import pytest

from omnis.adapters import LocalDataSource, S3DataSource


class LocalStorage:
    def __init__(self, root: Path):
        self.root = root
        self.datasource = LocalDataSource(root)

    def put(self, path: str, content: bytes) -> None:
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_bytes(content)

    def files(self) -> dict[str, bytes]:
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}


class S3Storage:
    def __init__(self, client_arguments: dict, bucket: str):
        self.client = boto3.client(**client_arguments)
        self.bucket = bucket
        self.datasource = S3DataSource(**client_arguments, bucket=bucket)

    def put(self, path: str, content: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=path, Body=content)

    def files(self) -> dict[str, bytes]:
        objects = self.client.list_objects_v2(Bucket=self.bucket).get("Contents", [])
        return {
            obj["Key"]: self.client.get_object(Bucket=self.bucket, Key=obj["Key"])["Body"].read()
            for obj in objects
        }


@pytest.fixture(params=["local", pytest.param("s3", marks=pytest.mark.integration)])
def storage(request, tmp_path):
    if request.param == "local":
        return LocalStorage(tmp_path)
    return S3Storage(*request.getfixturevalue("s3_bucket"))


def test_lists_every_file_under_a_prefix(storage):
    """
    Checks: listing a prefix returns the full path of every file under it, subfolders included,
    and nothing from other prefixes. A prefix with no files gives an empty list, not an error.

    If it fails: this storage lists files differently from the others. The raw load would load the
    wrong CSVs (or none) and repositories would miss artifacts. An empty raw/new would crash the run.
    """
    storage.put("raw/new/t/a.csv", b"a")
    storage.put("raw/new/t/old/b.csv", b"b")
    storage.put("raw/new/other/c.csv", b"c")

    assert sorted(storage.datasource.list_files("raw/new/t/")) == ["raw/new/t/a.csv", "raw/new/t/old/b.csv"]
    assert storage.datasource.list_files("raw/his/") == []


def test_tells_whether_a_file_exists(storage):
    """
    Checks: exists() is True for a file that is there and False for one that isn't, without raising.

    If it fails: read() could not tell a missing artifact from an error, and the archive could not
    skip files already moved, so retrying it would crash.
    """
    storage.put("raw/new/t/a.csv", b"a")

    assert storage.datasource.exists("raw/new/t/a.csv") is True
    assert storage.datasource.exists("raw/new/t/b.csv") is False


def test_reads_a_file_byte_for_byte(storage):
    """
    Checks: a file is read exactly as written: BOM, accents, Windows line ends and all.

    If it fails: this storage alters the bytes (encoding, line ends). Raw CSVs would be loaded with
    corrupted text, or their header would not be recognised.
    """
    content = "﻿fecha,ejercicio\n2026-01-01,Press banca ñ\r\n".encode("utf-8")
    storage.put("raw/new/t/a.csv", content)

    assert storage.datasource.read_file("raw/new/t/a.csv") == content


def test_moves_a_file_replacing_what_is_at_the_new_path(storage):
    """
    Checks: moving a file leaves it only at the new path, with its content, replacing a file that
    was there, and touches no other file.

    If it fails: the archive could leave a copy behind (the file would be loaded again on the next
    run), lose it, or fail when raw/his already has a file with that name.
    """
    storage.put("raw/new/t/a.csv", b"new")
    storage.put("raw/his/t/a.csv", b"old")
    storage.put("raw/new/t/b.csv", b"b")

    storage.datasource.move_file("raw/new/t/a.csv", "raw/his/t/a.csv")

    assert storage.files() == {"raw/his/t/a.csv": b"new", "raw/new/t/b.csv": b"b"}


def test_moves_a_file_to_a_folder_that_does_not_exist_yet(storage):
    """
    Checks: a file can be moved to a folder that doesn't exist yet.

    If it fails: the first archive of every entity (when raw/his/<entity>/ doesn't exist) would
    fail, and on that storage nothing would ever be archived.
    """
    storage.put("raw/new/t/a.csv", b"a")

    storage.datasource.move_file("raw/new/t/a.csv", "raw/his/t/a.csv")

    assert storage.files() == {"raw/his/t/a.csv": b"a"}
