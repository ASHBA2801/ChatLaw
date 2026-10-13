-- CreateTable
CREATE TABLE "court_case_laws" (
    "id" TEXT NOT NULL,
    "caseId" TEXT NOT NULL,
    "lawKey" TEXT NOT NULL,
    "actId" TEXT NOT NULL,
    "sectionNumber" TEXT,
    "isLandmark" BOOLEAN NOT NULL DEFAULT false,
    "relevanceNote" TEXT,
    "origin" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "court_case_laws_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "research_law_lookups" (
    "lawKey" TEXT NOT NULL,
    "actId" TEXT NOT NULL,
    "sectionNumber" TEXT,
    "status" TEXT NOT NULL,
    "mode" TEXT NOT NULL,
    "caseCount" INTEGER NOT NULL DEFAULT 0,
    "proposedCount" INTEGER NOT NULL DEFAULT 0,
    "hitCount" INTEGER NOT NULL DEFAULT 0,
    "lastDiscoveredAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "research_law_lookups_pkey" PRIMARY KEY ("lawKey")
);

-- CreateTable
CREATE TABLE "research_queries" (
    "id" TEXT NOT NULL,
    "queryKey" TEXT NOT NULL,
    "query" TEXT NOT NULL,
    "lawKeys" JSONB NOT NULL,
    "caseIds" JSONB NOT NULL,
    "articulation" JSONB,
    "hitCount" INTEGER NOT NULL DEFAULT 1,
    "discoveredAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "research_queries_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "court_case_laws_caseId_lawKey_key" ON "court_case_laws"("caseId", "lawKey");

-- CreateIndex
CREATE INDEX "court_case_laws_lawKey_idx" ON "court_case_laws"("lawKey");

-- CreateIndex
CREATE INDEX "court_case_laws_actId_isLandmark_idx" ON "court_case_laws"("actId", "isLandmark");

-- CreateIndex
CREATE INDEX "research_law_lookups_actId_idx" ON "research_law_lookups"("actId");

-- CreateIndex
CREATE UNIQUE INDEX "research_queries_queryKey_key" ON "research_queries"("queryKey");

-- AddForeignKey
ALTER TABLE "court_case_laws" ADD CONSTRAINT "court_case_laws_caseId_fkey" FOREIGN KEY ("caseId") REFERENCES "court_cases"("id") ON DELETE CASCADE ON UPDATE CASCADE;
