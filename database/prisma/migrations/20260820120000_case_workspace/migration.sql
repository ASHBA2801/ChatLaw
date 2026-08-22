ALTER TABLE "conversations" ADD COLUMN "caseId" TEXT;

CREATE TABLE "cases" (
  "id" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "description" TEXT,
  "category" TEXT,
  "subCategory" TEXT,
  "jurisdiction" TEXT,
  "city" TEXT,
  "state" TEXT,
  "country" TEXT,
  "status" TEXT NOT NULL DEFAULT 'ACTIVE',
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  "archivedAt" TIMESTAMP(3),
  CONSTRAINT "cases_pkey" PRIMARY KEY ("id")
);
CREATE TABLE "case_documents" (
  "id" TEXT NOT NULL,
  "caseId" TEXT NOT NULL,
  "userId" TEXT NOT NULL,
  "fileName" TEXT NOT NULL,
  "fileType" TEXT NOT NULL,
  "fileSize" INTEGER NOT NULL,
  "storageKey" TEXT NOT NULL,
  "checksum" TEXT NOT NULL,
  "extractedTextStatus" TEXT NOT NULL DEFAULT 'PENDING',
  "extractedText" TEXT,
  "pageCount" INTEGER,
  "metadata" JSONB,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  "deletedAt" TIMESTAMP(3),
  CONSTRAINT "case_documents_pkey" PRIMARY KEY ("id")
);
CREATE TABLE "case_timeline_events" (
  "id" TEXT NOT NULL,
  "caseId" TEXT NOT NULL,
  "type" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "description" TEXT,
  "occurredAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "case_timeline_events_pkey" PRIMARY KEY ("id")
);
CREATE TABLE "case_important_dates" (
  "id" TEXT NOT NULL,
  "caseId" TEXT NOT NULL,
  "title" TEXT NOT NULL,
  "description" TEXT,
  "date" TIMESTAMP(3) NOT NULL,
  "reminderPreference" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "case_important_dates_pkey" PRIMARY KEY ("id")
);
CREATE UNIQUE INDEX "case_documents_userId_checksum_key" ON "case_documents"("userId", "checksum");
CREATE INDEX "conversations_caseId_idx" ON "conversations"("caseId");
CREATE INDEX "cases_userId_updatedAt_idx" ON "cases"("userId", "updatedAt");
CREATE INDEX "cases_userId_status_idx" ON "cases"("userId", "status");
CREATE INDEX "case_documents_caseId_createdAt_idx" ON "case_documents"("caseId", "createdAt");
CREATE INDEX "case_documents_userId_deletedAt_idx" ON "case_documents"("userId", "deletedAt");
CREATE INDEX "case_timeline_events_caseId_occurredAt_idx" ON "case_timeline_events"("caseId", "occurredAt");
CREATE INDEX "case_important_dates_caseId_date_idx" ON "case_important_dates"("caseId", "date");
ALTER TABLE "conversations" ADD CONSTRAINT "conversations_caseId_fkey" FOREIGN KEY ("caseId") REFERENCES "cases"("id") ON DELETE SET NULL ON UPDATE CASCADE;
ALTER TABLE "cases" ADD CONSTRAINT "cases_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "case_documents" ADD CONSTRAINT "case_documents_caseId_fkey" FOREIGN KEY ("caseId") REFERENCES "cases"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "case_documents" ADD CONSTRAINT "case_documents_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "case_timeline_events" ADD CONSTRAINT "case_timeline_events_caseId_fkey" FOREIGN KEY ("caseId") REFERENCES "cases"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "case_important_dates" ADD CONSTRAINT "case_important_dates_caseId_fkey" FOREIGN KEY ("caseId") REFERENCES "cases"("id") ON DELETE CASCADE ON UPDATE CASCADE;