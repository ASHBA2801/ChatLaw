# Docker Infrastructure - Phase 21

Container definitions for ChatLaw's shared infrastructure, supporting Phase 21 (Case Workspace) persistence and vector storage.

| Path | Service | Purpose |
| --- | --- | --- |
| `postgres/compose.yml` | PostgreSQL + pgvector | Shared database (Postgres 17+, host 5433) |
| `redis/compose.yml` | Redis | Caching and session state (host 6379) |

## Quick Start

Start all required services from the root:

```bash
docker compose up -d
```

### Individual Services

If you need only specific services:

```bash
docker compose -f docker/postgres/compose.yml up -d
docker compose -f docker/redis/compose.yml up -d
```

## Maintenance

Ensure your local Postgres instance is running to enable the Prisma migration (`npm run db:migrate`) and application startup. Logs are available via:

```bash
docker compose logs -f
```
```
