/**
 * Development database reset.
 *
 * Drops and recreates the target database, then applies all migrations.
 * This is DESTRUCTIVE — it deletes all data in the configured database.
 *
 * It refuses to run when NODE_ENV is "production" to protect production data.
 *
 * Usage:
 *   npm run db:reset
 *   node scripts/db/reset.mjs
 */

import "dotenv/config";
import { execSync } from "node:child_process";
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
  if (process.env.NODE_ENV === "production") {
    console.error(
      "Refusing to reset the database: NODE_ENV is 'production'. This script is for development only.",
    );
    process.exit(1);
  }

  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error("DATABASE_URL is not set. Copy .env.example to .env first.");
    process.exit(1);
  }

  const { database, ...admin } = parseUrl(url);

  const client = new Client({ ...admin, database: "postgres" });
  await client.connect();

  console.log(`Dropping database "${database}"...`);
  await client.query(`DROP DATABASE IF EXISTS "${database.replace(/"/g, '""')}" WITH (FORCE)`);
  console.log(`Creating database "${database}"...`);
  await client.query(`CREATE DATABASE "${database.replace(/"/g, '""')}"`);
  await client.end();

  console.log("Applying migrations...");
  execSync("npx prisma migrate deploy", { stdio: "inherit" });

  console.log("Database reset complete.");
}

main().catch((err) => {
  console.error("Database reset failed:", err.message);
  process.exit(1);
});
