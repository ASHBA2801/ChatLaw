-- AlterTable
ALTER TABLE "user_documents" ADD COLUMN IF NOT EXISTS "conversationId" TEXT;

-- CreateIndex
CREATE INDEX IF NOT EXISTS "user_documents_conversationId_idx" ON "user_documents"("conversationId");

-- AddForeignKey
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'user_documents_conversationId_fkey'
  ) THEN
    ALTER TABLE "user_documents"
      ADD CONSTRAINT "user_documents_conversationId_fkey"
      FOREIGN KEY ("conversationId") REFERENCES "conversations"("id")
      ON DELETE SET NULL ON UPDATE CASCADE;
  END IF;
END $$;
