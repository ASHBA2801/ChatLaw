import { NextResponse } from "next/server";
import { z } from "zod";
import { requireSessionUser, AuthRequiredError } from "@/lib/auth/session";
import { classifyCase } from "@/lib/case-intelligence/classify";
import { advocateProvider, courtProvider } from "@/lib/case-intelligence/providers";

export const dynamic = "force-dynamic";
const requestSchema = z.object({ query: z.string().trim().min(1).max(12000), resourceType: z.enum(["court", "advocate"]).optional(), location: z.object({ city: z.string().trim().max(120).optional(), state: z.string().trim().max(120).optional(), country: z.string().trim().max(120).optional(), latitude: z.number().finite().min(-90).max(90).optional(), longitude: z.number().finite().min(-180).max(180).optional() }).nullable().optional(), practiceArea: z.string().trim().max(120).optional(), radiusKm: z.number().finite().min(1).max(200).default(25) });

export async function POST(request: Request) {
  try {
    await requireSessionUser();
    const parsed = requestSchema.safeParse(await request.json());
    if (!parsed.success) return NextResponse.json({ error: "Invalid case intelligence request." }, { status: 422 });
    const { query, resourceType, location, practiceArea, radiusKm } = parsed.data;
    const intelligence = classifyCase(query, location ?? null);
    if (!resourceType) return NextResponse.json({ intelligence, results: [], providerStatus: "not_requested" });
    if (!location?.city && typeof location?.latitude !== "number") return NextResponse.json({ intelligence, results: [], providerStatus: "location_required" });
    try {
      const provider = resourceType === "court" ? courtProvider : advocateProvider;
      const results = await provider.search({ location, jurisdiction: intelligence.jurisdiction, caseCategory: intelligence.case_category, practiceArea, radiusKm });
      return NextResponse.json({ intelligence, results, providerStatus: "ok" });
    } catch {
      return NextResponse.json({ intelligence, results: [], providerStatus: "unavailable" });
    }
  } catch (error) {
    if (error instanceof AuthRequiredError) return NextResponse.json({ error: error.message }, { status: 401 });
    return NextResponse.json({ error: "Case intelligence is temporarily unavailable." }, { status: 500 });
  }
}