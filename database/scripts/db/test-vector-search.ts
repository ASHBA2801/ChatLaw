/**
 * End-to-end smoke test for the vector-search abstraction.
 *
 * Inserts a couple of legal chunks with embeddings, runs semanticSearch, and
 * verifies results are ranked by cosine similarity.
 *
 * NOTE: This script builds its own PrismaClient because web/lib/db/client.ts is
 * guarded with `server-only` (a Next.js boundary) and cannot run in a plain
 * Node process.
 *
 * Run with: npx tsx scripts/db/test-vector-search.ts
 */
import "dotenv/config";
import { PrismaPg } from "@prisma/adapter-pg";
import { PrismaClient } from "../../../web/lib/generated/prisma/client";
import { semanticSearch } from "../../lib/vector-search";

const adapter = new PrismaPg({ connectionString: process.env.DATABASE_URL });
const prisma = new PrismaClient({ adapter });

function makeEmbedding(base: number, dim = 768): number[] {
  const v = new Array(dim).fill(0);
  v[0] = base;
  v[1] = 1;
  return v;
}

async function main() {
  // Clean up any prior test data.
  await prisma.legalDocument.deleteMany({ where: { title: { startsWith: "[test]" } } });

  const doc = await prisma.legalDocument.create({
    data: {
      title: "[test] Vector Search Smoke Test",
      documentType: "act",
      authority: "Test Authority",
      language: "en",
    },
  });

  // The `embedding` column is a pgvector `vector(768)` type, which Prisma's
  // typed client cannot write (it is `Unsupported`). Insert chunks via raw SQL
  // so the vector values are stored correctly.
  const chunks = [
    {
      content: "Section 1: Right to equality before the law.",
      sectionNumber: "1",
      chapter: "Part III",
      chunkIndex: 0,
      embedding: makeEmbedding(1),
    },
    {
      content: "Section 2: Freedom of speech and expression.",
      sectionNumber: "2",
      chapter: "Part III",
      chunkIndex: 1,
      embedding: makeEmbedding(0.5),
    },
    {
      content: "Section 3: Protection in respect of conviction for offences.",
      sectionNumber: "3",
      chapter: "Part III",
      chunkIndex: 2,
      embedding: makeEmbedding(0.1),
    },
  ];

  for (const c of chunks) {
    await prisma.$executeRawUnsafe(
      `INSERT INTO "legal_chunks"
        ("id", "documentId", "content", "sectionNumber", "chapter", "chunkIndex", "embedding", "createdAt")
       VALUES ($1, $2, $3, $4, $5, $6, $7::vector, now())`,
      crypto.randomUUID(),
      doc.id,
      c.content,
      c.sectionNumber,
      c.chapter,
      c.chunkIndex,
      `[${c.embedding.join(",")}]`,
    );
  }

  // Query with an embedding closest to chunk 0 (base=1).
  const results = await semanticSearch(prisma, makeEmbedding(0.95), { limit: 3 });

  console.log("Semantic search results:");
  for (const r of results) {
    console.log(
      `  [${r.score.toFixed(4)}] ${r.chapter} / s.${r.sectionNumber}: ${r.content.slice(0, 60)}`,
    );
  }

  if (results.length === 0) {
    throw new Error("semanticSearch returned no results");
  }
  if (results[0].sectionNumber !== "1") {
    throw new Error(
      `Expected top result to be section 1, got section ${results[0].sectionNumber}`,
    );
  }

  console.log("\nVector search smoke test PASSED.");

  // Clean up test data.
  await prisma.legalDocument.deleteMany({ where: { title: { startsWith: "[test]" } } });
  await prisma.$disconnect();
}

main().catch(async (err) => {
  console.error("Vector search smoke test FAILED:", err.message);
  await prisma.$disconnect();
  process.exit(1);
});
