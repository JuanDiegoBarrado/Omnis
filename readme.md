docker-compose --profile airflow start
docker-compose --profile airflow stop
docker-compose --profile airflow restart

pip install apache-airflow==3.1.0 --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.1.0/constraints-3.11.txt"

## Modes

The root `docker-compose.yaml` runs the stack with the default resources of each service. `docker_compose_modes/` holds
the same stack in each mode it can run in:

- `docker-compose.default.yaml`: the same as the root one.
- `docker-compose.raspberry.yaml`: tuned for a Raspberry Pi 5 shared with other services. It uses as little memory and
  CPU as it can, gives each long-running service a `mem_limit` and has no triggerer.

Run a mode from the repo root with `--project-directory .`, so it reads the root `.env` and keeps the containers and
volumes of the root compose:

```bash
docker compose --project-directory . -f docker_compose_modes/docker-compose.raspberry.yaml up -d
```

Switching from the default mode leaves the triggerer running: `--remove-orphans` stops it.

### Raspberry Pi

Docker only applies the `mem_limit`s if the kernel has the memory cgroup enabled, which Raspberry Pi OS leaves disabled:
if `docker info` warns `No memory limit support`, add `cgroup_enable=memory` to the end of the single line of
`/boot/firmware/cmdline.txt` and reboot.

`docker stats` shows what each container uses, to tighten the limits.
