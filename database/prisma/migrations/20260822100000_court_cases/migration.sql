-- CreateTable
CREATE TABLE "court_cases" (
    "id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "court" TEXT NOT NULL,
    "courtLevel" TEXT NOT NULL,
    "jurisdiction" TEXT NOT NULL,
    "caseNumber" TEXT NOT NULL,
    "caseType" TEXT NOT NULL,
    "judgmentDate" TIMESTAMP(3) NOT NULL,
    "bench" TEXT,
    "judgeNames" JSONB NOT NULL,
    "petitioner" TEXT,
    "respondent" TEXT,
    "citation" TEXT,
    "officialSource" BOOLEAN NOT NULL DEFAULT true,
    "sourceAuthority" TEXT NOT NULL,
    "sourceUrl" TEXT NOT NULL,
    "sourceType" TEXT NOT NULL DEFAULT 'JUDGMENT',
    "acts" JSONB NOT NULL,
    "sections" JSONB NOT NULL,
    "legalTopics" JSONB NOT NULL,
    "primaryIssue" TEXT NOT NULL,
    "factsSummary" TEXT NOT NULL,
    "holding" TEXT NOT NULL,
    "disposition" TEXT,
    "contentHash" TEXT NOT NULL,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "court_cases_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "court_case_chunks" (
    "id" TEXT NOT NULL,
    "caseId" TEXT NOT NULL,
    "chunkIndex" INTEGER NOT NULL,
    "chunkType" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "embedding" vector(768),
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "court_case_chunks_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "court_cases_contentHash_key" ON "court_cases"("contentHash");

-- CreateIndex
CREATE INDEX "court_cases_courtLevel_idx" ON "court_cases"("courtLevel");

-- CreateIndex
CREATE INDEX "court_cases_jurisdiction_idx" ON "court_cases"("jurisdiction");

-- CreateIndex
CREATE INDEX "court_cases_judgmentDate_idx" ON "court_cases"("judgmentDate");

-- CreateIndex
CREATE INDEX "court_cases_contentHash_idx" ON "court_cases"("contentHash");

-- CreateIndex
CREATE INDEX "court_case_chunks_caseId_idx" ON "court_case_chunks"("caseId");

-- CreateIndex
CREATE INDEX "court_case_chunks_chunkType_idx" ON "court_case_chunks"("chunkType");

-- CreateIndex
CREATE INDEX "court_case_chunks_chunkIndex_idx" ON "court_case_chunks"("chunkIndex");

-- AddForeignKey
ALTER TABLE "court_case_chunks" ADD CONSTRAINT "court_case_chunks_caseId_fkey" FOREIGN KEY ("caseId") REFERENCES "court_cases"("id") ON DELETE CASCADE ON UPDATE CASCADE;
