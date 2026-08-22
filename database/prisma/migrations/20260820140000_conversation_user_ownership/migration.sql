-- Phase 21: bind conversations to owning users for case-ask authorization.
ALTER TABLE "conversations" ADD COLUMN "userId" TEXT;

CREATE INDEX "conversations_userId_caseId_idx" ON "conversations"("userId", "caseId");

ALTER TABLE "conversations"
  ADD CONSTRAINT "conversations_userId_fkey"
  FOREIGN KEY ("userId") REFERENCES "users"("id")
  ON DELETE SET NULL ON UPDATE CASCADE;
