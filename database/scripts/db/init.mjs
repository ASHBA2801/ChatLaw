/**
 * Database initialization.
 *
 * Ensures the target database exists and that the pgvector extension is
 * enabled. Safe to run repeatedly (idempotent). This does NOT create or alter
 * tables — run `npm run db:migrate` (dev) or `npm run db:deploy` (deploy)
 * afterwards to apply the schema.
 *
 * Usage:
 *   npm run db:init
 *   node scripts/db/init.mjs
 */

import "dotenv/config";
import pg from "pg";

const { Client } = pg;

function parseUrl(url) {
  const u = new URL(url);
  return {
    database: u.pathname.replace(/^\//, "").split("?")[0] || "postgres",
    user: decodeURIComponent(u.username || "postgres"),
    password: decodeURIComponent(u.password || ""),
    host: u.hostname || "localhost",
    port: u.port ? Number(u.port) : 5432,
  };
}

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error("DATABASE_URL is not set. Copy .env.example to .env first.");
    process.exit(1);
  }

  const { database, ...admin } = parseUrl(url);

  // Connect to the maintenance database to create the target DB if needed.
  const adminClient = new Client({ ...admin, database: "postgres" });
  await adminClient.connect();

  const exists = await adminClient.query(
    "SELECT 1 FROM pg_database WHERE datname = $1",
    [database],
  );

  if (exists.rowCount === 0) {
    // Identifier cannot be parameterized; database name comes from our own URL.
    await adminClient.query(
      `CREATE DATABASE "${database.replace(/"/g, '""')}"`,
    );
    console.log(`Created database "${database}".`);
  } else {
    console.log(`Database "${database}" already exists.`);
  }
  await adminClient.end();

  // Enable pgvector on the target database.
  const dbClient = new Client({ ...admin, database });
  await dbClient.connect();
  await dbClient.query('CREATE EXTENSION IF NOT EXISTS vector');
  console.log("pgvector extension is enabled.");

  const ext = await dbClient.query(
    "SELECT extversion FROM pg_extension WHERE extname = 'vector'",
  );
  console.log(`pgvector version: ${ext.rows[0]?.extversion ?? "unknown"}`);

  await dbClient.end();
  console.log("Database initialization complete.");
}

main().catch((err) => {
  console.error("Database initialization failed:", err.message);
  process.exit(1);
});
