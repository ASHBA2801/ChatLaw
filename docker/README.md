# Docker

One Compose file runs everything: PostgreSQL (pgvector), Redis, Prisma migrations, the RAG engine and the web app.

```bash
cp .env.example .env     # set AUTH_SECRET, RAG_API_SECRET, GEMINI_API_KEY
docker compose up --build
```

| Service | Address |
| --- | --- |
| Web app | http://localhost:3000 |
| RAG engine | http://localhost:8000/health |
| PostgreSQL + pgvector | `localhost:5433` |
| Redis | `localhost:6379` |

Startup order: `postgres` healthy, `migrate` completes, `rag-engine` healthy, then `web`. Compose reads settings from the root `.env` and sets `DATABASE_URL` and `RAG_API_URL` to the service network (`postgres`, `rag-engine`), so `web/.env` and `rag-engine/.env` are only for running the apps on the host.

Add `-d` to run in the background and `docker compose down` to stop (data volumes are kept; `-v` deletes them).

## Dev mode (hot reload)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

`docker-compose.dev.yml` layers on the main file (same ports, env and startup order) and bind-mounts the source so edits show up without rebuilding:

- `web` runs `next dev` on `./web`.
- `rag-engine` runs `uvicorn --reload` on `./rag-engine`.

Rebuild (`--build`) only when dependencies change (`web/package.json`, `package-lock.json`, `rag-engine/requirements.prod.txt`). Dev `web` uses its own case-documents volume (`chatlaw_case_documents_dev`) and runs as `DEV_UID`/`DEV_GID` (default 1000) so files it writes to the mount belong to you. On Docker Desktop, set `WATCHPACK_POLLING=true` and `WATCHFILES_FORCE_POLLING=true` in `.env` if changes are not picked up.

The RAG image installs `rag-engine/requirements.prod.txt`. Local tests keep using `rag-engine/requirements.txt`, which includes pytest, and run on the host (`npm test`, `pytest`).

`docker/postgres/compose.yml` and `docker/redis/compose.yml` start only a database or cache for host development. For Railway, see `docs/railway.md`.
