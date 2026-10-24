# Image of the backup services: pg_dump of the same major version as omnis-database, mc to copy the
# data bucket, and Python (standard library only) to e-mail a failed copy
FROM postgres:16
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY --from=quay.io/minio/mc:latest /usr/bin/mc /usr/bin/mc
COPY notify_failure.py /usr/local/bin/notify_failure.py
