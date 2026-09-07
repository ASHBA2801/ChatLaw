import "server-only";

import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "@/lib/generated/prisma/client";

import { loadEnv } from "@/lib/validation/env";

/**
 * Database boundary.
 *
 * A single PrismaClient is shared across the server runtime. In development
 * the client is cached on `globalThis` so hot-reloading does not exhaust the
 * connection pool. Construction is lazy so importing this module during
 * `next build` does not require DATABASE_URL until a query actually runs.
 *
 * Prisma 7 uses driver adapters: the connection string is supplied to the
 * adapter here (not via the datasource block), and the adapter is passed to
 * the PrismaClient constructor.
 */

const globalForPrisma = globalThis as unknown as {
  prisma?: PrismaClient;
};

function createClient(): PrismaClient {
  const { DATABASE_URL } = loadEnv();

  if (!DATABASE_URL) {
    throw new Error(
      "DATABASE_URL is not set. Copy .env.example to .env and configure a PostgreSQL connection.",
    );
  }

  const adapter = new PrismaPg({ connectionString: DATABASE_URL });
  return new PrismaClient({ adapter });
}

function getClient(): PrismaClient {
  globalForPrisma.prisma ??= createClient();
  return globalForPrisma.prisma;
}

export const prisma: PrismaClient = new Proxy({} as PrismaClient, {
  get(_target, property, receiver) {
    return Reflect.get(getClient(), property, receiver);
  },
});

/** Alias kept for callers that referenced the old boundary name. */
export const database = prisma;
