/**
 * Quick connectivity check for the database + pgvector.
 * Uses the `pg` driver directly (the Prisma client is TypeScript and needs a
 * TS runner; this script verifies the underlying connection and extension).
 * Run with: node scripts/db/check-connection.mjs
 */
import "dotenv/config";
import pg from "pg";

const { Client } = pg;

const client = new Client({ connectionString: process.env.DATABASE_URL });

try {
  await client.connect();

  const ok = await client.query("SELECT 1 AS ok");
  console.log("DB connection OK:", JSON.stringify(ok.rows));

  const ext = await client.query(
    "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector'",
  );
  console.log("pgvector:", JSON.stringify(ext.rows));

  const vec = await client.query("SELECT '[1,2,3]'::vector AS v");
  console.log("vector cast OK:", JSON.stringify(vec.rows));
} catch (err) {
  console.error("DB check FAILED:", err.message);
  process.exitCode = 1;
} finally {
  await client.end();
}
