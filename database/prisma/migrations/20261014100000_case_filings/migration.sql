-- AlterTable
ALTER TABLE "cases" ADD COLUMN     "district" TEXT,
ADD COLUMN     "filingProfile" JSONB,
ADD COLUMN     "latitude" DOUBLE PRECISION,
ADD COLUMN     "locality" TEXT,
ADD COLUMN     "longitude" DOUBLE PRECISION,
ADD COLUMN     "pincode" TEXT;

-- CreateTable
CREATE TABLE "case_filings" (
    "id" TEXT NOT NULL,
    "caseId" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "kind" TEXT NOT NULL,
    "forum" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "subject" TEXT NOT NULL,
    "addressee" TEXT NOT NULL,
    "body" TEXT NOT NULL,
    "recipients" JSONB NOT NULL,
    "cc" JSONB,
    "sections" JSONB NOT NULL,
    "citations" JSONB NOT NULL,
    "warnings" JSONB NOT NULL,
    "placeholders" JSONB NOT NULL,
    "filing" JSONB NOT NULL,
    "emailBody" TEXT NOT NULL,
    "language" TEXT NOT NULL DEFAULT 'en',
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "generation" JSONB,
    "sentAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "case_filings_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "authority_contacts" (
    "lookupKey" TEXT NOT NULL,
    "kind" TEXT NOT NULL,
    "state" TEXT,
    "district" TEXT,
    "locality" TEXT,
    "status" TEXT NOT NULL,
    "offices" JSONB NOT NULL,
    "checkedAt" TIMESTAMP(3) NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "authority_contacts_pkey" PRIMARY KEY ("lookupKey")
);

-- CreateTable
CREATE TABLE "drafting_templates" (
    "id" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "kind" TEXT NOT NULL,
    "forum" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "documentType" TEXT NOT NULL,
    "courtSubject" TEXT,
    "sources" JSONB NOT NULL,
    "content" TEXT NOT NULL,
    "contentHash" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "drafting_templates_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "drafting_template_chunks" (
    "id" TEXT NOT NULL,
    "templateId" TEXT NOT NULL,
    "chunkIndex" INTEGER NOT NULL,
    "heading" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "embedding" vector(768),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "drafting_template_chunks_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "case_filings_caseId_createdAt_idx" ON "case_filings"("caseId", "createdAt");

-- CreateIndex
CREATE INDEX "case_filings_userId_updatedAt_idx" ON "case_filings"("userId", "updatedAt");

-- CreateIndex
CREATE INDEX "authority_contacts_kind_state_district_idx" ON "authority_contacts"("kind", "state", "district");

-- CreateIndex
CREATE UNIQUE INDEX "drafting_templates_slug_key" ON "drafting_templates"("slug");

-- CreateIndex
CREATE INDEX "drafting_templates_kind_idx" ON "drafting_templates"("kind");

-- CreateIndex
CREATE INDEX "drafting_template_chunks_templateId_idx" ON "drafting_template_chunks"("templateId");

-- AddForeignKey
ALTER TABLE "case_filings" ADD CONSTRAINT "case_filings_caseId_fkey" FOREIGN KEY ("caseId") REFERENCES "cases"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "case_filings" ADD CONSTRAINT "case_filings_userId_fkey" FOREIGN KEY ("userId") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "drafting_template_chunks" ADD CONSTRAINT "drafting_template_chunks_templateId_fkey" FOREIGN KEY ("templateId") REFERENCES "drafting_templates"("id") ON DELETE CASCADE ON UPDATE CASCADE;
