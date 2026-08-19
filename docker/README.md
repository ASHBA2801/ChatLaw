# Docker

Container definitions for ChatLaw's shared infrastructure.

| Path | Service | Purpose |
| --- | --- | --- |
| `postgres/compose.yml` | PostgreSQL + pgvector | Shared database (host port 5433) |
| `redis/compose.yml` | Redis | Optional cache / queue (host port 6379) |

Run individually:

```bash
docker compose -f docker/postgres/compose.yml up -d
docker compose -f docker/redis/compose.yml up -d
```

Or start everything from the repo root:

```bash
docker compose up -d
```
