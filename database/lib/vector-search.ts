/**
 * Vector-search abstraction.
 *
 * The `embedding` column on `legal_chunks` is a pgvector `vector(768)` type,
 * which Prisma exposes as `Unsupported` — it cannot be queried through the
 * typed client. All vector operations therefore go through raw SQL here.
 *
 * To keep this module decoupled from Prisma (and from the `server-only`
 * guarded client in web/lib/db/client.ts), the query executor is passed in as
 * a dependency rather than imported. The application passes the shared Prisma
 * client; standalone scripts can pass their own.
 *
 * This module intentionally provides only the search primitive
 * (`semanticSearch`). The full retrieval pipeline (query embedding, hybrid
 * ranking, citation assembly) is a later phase.
 */

/** Minimal query surface this module needs from a database client. */
export type VectorSearchClient = {
  $queryRawUnsafe<T = unknown>(query: string, ...values: unknown[]): Promise<T>;
};

export type VectorSearchResult = {
  chunkId: string;
  documentId: string;
  content: string;
  sectionNumber: string | null;
  subsection: string | null;
  chapter: string | null;
  clause: string | null;
  pageNumber: number | null;
  chunkIndex: number;
  /** Cosine similarity in [0, 1]; higher is more similar. */
  score: number;
};

export type SemanticSearchOptions = {
  /** Number of results to return. */
  limit?: number;
  /** Optional filter to restrict results to a single document. */
  documentId?: string;
  /** Optional minimum similarity threshold in [0, 1]. */
  minScore?: number;
};

/**
 * Run a cosine-similarity search over `legal_chunks` embeddings.
 *
 * @param client    A database client exposing `$queryRawUnsafe` (e.g. the
 *                  shared Prisma client from lib/db/client.ts).
 * @param embedding The query embedding vector (must match the column dimension).
 * @param options   Search options (limit, filters).
 */
export async function semanticSearch(
  client: VectorSearchClient,
  embedding: number[],
  options: SemanticSearchOptions = {},
): Promise<VectorSearchResult[]> {
  const { limit = 10, documentId, minScore } = options;

  const vectorLiteral = `[${embedding.join(",")}]`;
  const where = documentId ? `WHERE lc."documentId" = $1` : "";

  // The vector literal is built only from numbers (safe to inline); the
  // documentId is passed as a bound parameter to prevent SQL injection.
  const params: unknown[] = documentId ? [documentId] : [];

  const rows = await client.$queryRawUnsafe<RawSearchRow[]>(
    `
    SELECT
      lc."id"            AS "chunkId",
      lc."documentId"    AS "documentId",
      lc."content"       AS "content",
      lc."sectionNumber" AS "sectionNumber",
      lc."subsection"    AS "subsection",
      lc."chapter"       AS "chapter",
      lc."clause"        AS "clause",
      lc."pageNumber"    AS "pageNumber",
      lc."chunkIndex"    AS "chunkIndex",
      1 - (lc."embedding" <=> '${vectorLiteral}'::vector) AS "score"
    FROM "legal_chunks" lc
    ${where}
    ORDER BY lc."embedding" <=> '${vectorLiteral}'::vector ASC
    LIMIT ${limit}
    `,
    ...params,
  );

  return rows
    .filter((row) => (minScore === undefined ? true : row.score >= minScore))
    .map((row) => ({
      chunkId: row.chunkId,
      documentId: row.documentId,
      content: row.content,
      sectionNumber: row.sectionNumber,
      subsection: row.subsection,
      chapter: row.chapter,
      clause: row.clause,
      pageNumber: row.pageNumber,
      chunkIndex: row.chunkIndex,
      score: row.score,
    }));
}

type RawSearchRow = {
  chunkId: string;
  documentId: string;
  content: string;
  sectionNumber: string | null;
  subsection: string | null;
  chapter: string | null;
  clause: string | null;
  pageNumber: number | null;
  chunkIndex: number;
  score: number;
};
