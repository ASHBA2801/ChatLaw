-- AlterTable
ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "preferredLanguage" TEXT DEFAULT 'en';
