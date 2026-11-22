omnis-storage is the landing zone of the raw files (see README.md).

- server/: the HTTP server producers deliver files to (POST /raw/<entity>), and the gym's Excels
  for now (POST /temp/<kind>, kept in data/temp/<kind>/).
- data/: where it keeps them, mounted as /data in omnis-storage and as the raw files of Airflow.
  New files are in data/raw/new/<entity>/, archived ones in data/raw/his/<entity>/.
  Only the folder is in the repo, never what is in it.
- scripts/: the monthly backup of data/raw/ into backups/.
- tests/: the tests of the server.
