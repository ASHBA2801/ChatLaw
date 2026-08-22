import { NextResponse } from "next/server";
import { z } from "zod";

import { requireSessionUser } from "@/lib/auth/session";
import { prisma } from "@/lib/db/client";
import { isLanguageCode } from "@/lib/i18n/languages";

const bodySchema = z.object({
  language: z.string().min(2).max(16),
});

export async function POST(request: Request) {
  const user = await requireSessionUser().catch(() => null);
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const parsed = bodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success || !isLanguageCode(parsed.data.language)) {
    return NextResponse.json({ error: "Invalid language" }, { status: 400 });
  }

  await prisma.user.update({
    where: { id: user.id },
    data: { preferredLanguage: parsed.data.language },
  });

  return NextResponse.json({ language: parsed.data.language });
}
