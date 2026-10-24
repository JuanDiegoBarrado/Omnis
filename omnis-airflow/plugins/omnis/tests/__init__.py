"""
Tests of the omnis engine, shipped with it (like numpy or pandas): only what the engine itself
does, never a flow of dags/. The folders mirror the package.

Each test that needs data has it in a folder next to it, named after its module. Tests of the
adapters that talk to Postgres or S3 run them in throwaway containers (testcontainers, so Docker
must be running) and are marked `integration`: `pytest -m "not integration"` skips them.
"""
