import { z } from "zod";

/**
 * Environment contract for the database and Gemini integrations.
 *
 * DATABASE_URL is required for any database-backed operation (migrations,
 * the Prisma client, and vector search). It is optional here so that pure
 * UI-only builds (e.g. `next build` without a live DB) still type-check.
 */
export const envSchema = z.object({
  DATABASE_URL: z.string().url().optional(),
  GEMINI_API_KEY: z.string().optional(),
  GEMINI_MODEL: z.string().optional(),
  GEMINI_EMBEDDING_MODEL: z.string().optional(),
});

export type Env = z.infer<typeof envSchema>;

/** Parse and validate process.env against the schema. */
export function loadEnv(source: NodeJS.ProcessEnv = process.env): Env {
  const parsed = envSchema.safeParse(source);
  if (!parsed.success) {
    throw new Error(
      `Invalid environment configuration: ${parsed.error.issues
        .map((i) => `${i.path.join(".")}: ${i.message}`)
        .join("; ")}`,
    );
  }
  return parsed.data;
}
