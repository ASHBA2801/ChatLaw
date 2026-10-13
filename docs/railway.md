# Deploying ChatLaw on Railway

Railway builds each service from its own Dockerfile; it does not run `docker-compose.yml`.
Create one Railway project with five services, all built from the repository root.
Each service points at a config file via **Settings → Config-as-code → Railway Config File**.

| Service | Source | Config file | Notes |
| --- | --- | --- | --- |
| `postgres` | Image `pgvector/pgvector:pg18` | none | Add a volume at `/var/lib/postgresql`. Required: the schema uses the `vector` type, so Railway's stock Postgres will not work. |
| `migrate` | Repo | `/railway/migrate.json` | One-shot `prisma migrate deploy`. Redeploy it whenever migrations change. |
| `rag-engine` | Repo | `/railway/rag-engine.json` | FastAPI on `$PORT`. Private only; do not generate a public domain. |
| `web` | Repo | `/railway/web.json` | Next.js on `$PORT`. Generate a public domain. |
| `redis` (optional) | Railway Redis | none | Nothing in the code reads Redis yet. |

## Variables

`postgres`: `POSTGRES_USER`, `POSTGRES_PASSWORD` (URL-safe), `POSTGRES_DB=chatlaw`.

Define the connection string once on `postgres` and reference it elsewhere:

```
DATABASE_URL_BASE=postgresql://${{POSTGRES_USER}}:${{POSTGRES_PASSWORD}}@${{RAILWAY_PRIVATE_DOMAIN}}:5432/${{POSTGRES_DB}}
```

`migrate`: `DATABASE_URL=${{postgres.DATABASE_URL_BASE}}?schema=public`

`rag-engine`:

```
DATABASE_URL=${{postgres.DATABASE_URL_BASE}}
RAG_API_SECRET=<openssl rand -hex 32>
GEMINI_API_KEY=...
GEMINI_GENERATION_MODEL=gemini-3.8-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2-preview
EMBEDDING_PROVIDER=gemini
EMBEDDING_MODEL=gemini-embedding-2-preview   # must equal GEMINI_EMBEDDING_MODEL
EMBEDDING_DIMENSION=768
CHATLAW_FRONTEND_ORIGIN=https://${{web.RAILWAY_PUBLIC_DOMAIN}}
```

`web`:

```
DATABASE_URL=${{postgres.DATABASE_URL_BASE}}?schema=public
RAG_API_URL=http://${{rag-engine.RAILWAY_PRIVATE_DOMAIN}}:${{rag-engine.PORT}}
RAG_API_SECRET=${{rag-engine.RAG_API_SECRET}}
GEMINI_API_KEY=${{rag-engine.GEMINI_API_KEY}}
AUTH_SECRET=<openssl rand -base64 32>
AUTH_GOOGLE_ID=...
AUTH_GOOGLE_SECRET=...
AUTH_TRUST_HOST=true
AUTH_URL=https://${{web.RAILWAY_PUBLIC_DOMAIN}}   # stops redirects to 0.0.0.0:3000
CASE_STORAGE_ROOT=/data/case-documents
```

Set `PORT=8000` on `rag-engine` so the reference above resolves. Add a volume mounted at
`/data/case-documents` on `web` so uploaded case documents survive redeploys.

In Google Cloud Console, add `https://<your-web-domain>/api/auth/callback/google` as an
authorized redirect URI.

## Order

1. Deploy `postgres`.
2. Deploy `migrate` and wait for it to exit successfully.
3. Deploy `rag-engine`, then `web`.

The legal corpus embeddings live in Postgres. A new database starts empty; ingest with the
scripts in `rag-engine/scripts/` before expecting grounded answers.
