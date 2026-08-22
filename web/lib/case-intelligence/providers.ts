import { sortAndFilterByDistance } from "./distance";
import type { ProviderSearchInput, ResourceProvider, ResourceResult } from "./types";
import courtDirectory from "@/data/legal/courts.json";
import advocateDirectory from "@/data/legal/advocates.json";

function isSafeUrl(value: unknown): value is string {
  if (typeof value !== "string") return false;
  try {
    const url = new URL(value);
    return url.protocol === "https:";
  } catch {
    return false;
  }
}

function validateResults(value: unknown, type: "court" | "advocate"): ResourceResult[] {
  if (!Array.isArray(value)) return [];
  return value.flatMap((item, index) => {
    if (!item || typeof item !== "object" || typeof (item as { name?: unknown }).name !== "string") return [];
    const row = item as Record<string, unknown>;
    const source = row.source as Record<string, unknown> | undefined;
    return [
      {
        id: typeof row.id === "string" ? row.id : `${type}-${index}`,
        name: String(row.name).slice(0, 200),
        type,
        practice_areas: Array.isArray(row.practice_areas)
          ? row.practice_areas.filter((x): x is string => typeof x === "string").slice(0, 20)
          : undefined,
        court_type: typeof row.court_type === "string" ? row.court_type : null,
        address: typeof row.address === "string" ? row.address : null,
        city: typeof row.city === "string" ? row.city : null,
        state: typeof row.state === "string" ? row.state : null,
        latitude: typeof row.latitude === "number" ? row.latitude : null,
        longitude: typeof row.longitude === "number" ? row.longitude : null,
        phone: typeof row.phone === "string" ? row.phone : null,
        profile_url: isSafeUrl(row.profile_url) ? row.profile_url : null,
        official_url: isSafeUrl(row.official_url) ? row.official_url : null,
        source_url: isSafeUrl(source?.source_url) ? source.source_url : null,
        source_type: typeof source?.source_type === "string" ? source.source_type : "Provider unavailable",
        verification_status: source?.verification_status === "verified" ? "verified" : "unverified",
        retrieved_at: new Date().toISOString(),
      },
    ];
  });
}

function matchesLocation(row: ResourceResult, input: ProviderSearchInput): boolean {
  const city = input.location.city?.toLowerCase().trim();
  const state = input.location.state?.toLowerCase().trim();
  if (!city && !state) return true;
  const rowCity = row.city?.toLowerCase() || "";
  const rowState = row.state?.toLowerCase() || "";
  const rowName = row.name.toLowerCase();
  if (state && (rowState.includes(state) || rowName.includes(state) || !row.state)) {
    if (!city) return true;
    return rowCity.includes(city) || rowName.includes(city) || !row.city;
  }
  if (city && (rowCity.includes(city) || rowName.includes(city))) return true;
  // Keep national portals when location is set.
  return !row.city && !row.state;
}

function matchesPractice(row: ResourceResult, practiceArea?: string | null, caseCategory?: string | null): boolean {
  const needle = (practiceArea || caseCategory || "").toLowerCase().trim();
  if (!needle) return true;
  // Courts are jurisdiction venues — keep location matches even when category tokens differ.
  if (row.type === "court") return true;
  const areas = (row.practice_areas || []).map((item) => item.toLowerCase());
  const haystack = [row.name, ...areas].join(" ").toLowerCase();
  const aliases = needle
    .replace(/\//g, " ")
    .split(/\s+/)
    .filter((token) => token.length > 2);
  if (aliases.some((token) => /property|tenancy|rent|landlord/.test(token))) {
    aliases.push("civil", "property", "family");
  }
  if (aliases.some((token) => /consumer|refund|product/.test(token))) {
    aliases.push("consumer");
  }
  if (aliases.some((token) => /criminal|fir|arrest|police/.test(token))) {
    aliases.push("criminal");
  }
  return aliases.some((token) => haystack.includes(token));
}

class LocalDirectoryProvider implements ResourceProvider {
  constructor(
    private readonly type: "court" | "advocate",
    private readonly rows: ResourceResult[],
  ) {}

  async search(input: ProviderSearchInput): Promise<ResourceResult[]> {
    const filtered = this.rows.filter(
      (row) => matchesLocation(row, input) && matchesPractice(row, input.practiceArea, input.caseCategory),
    );
    const withDistance = sortAndFilterByDistance(filtered, input.location, input.radiusKm);
    // If distance filter emptied everything (no coords on query), fall back to text-matched rows.
    if (withDistance.length === 0 && filtered.length > 0) {
      return filtered.slice(0, 20);
    }
    return withDistance.length ? withDistance : this.rows.filter((row) => !row.city && !row.state).slice(0, 10);
  }
}

class ConfiguredProvider implements ResourceProvider {
  constructor(
    private readonly type: "court" | "advocate",
    private readonly endpoint: string | undefined,
    private readonly fallback: ResourceProvider,
  ) {}

  async search(input: ProviderSearchInput) {
    if (!this.endpoint) return this.fallback.search(input);
    try {
      const response = await fetch(this.endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(input),
        cache: "no-store",
        signal: AbortSignal.timeout(10_000),
      });
      if (!response.ok) throw new Error(`Provider returned ${response.status}`);
      const remote = sortAndFilterByDistance(
        validateResults(await response.json(), this.type),
        input.location,
        input.radiusKm,
      );
      return remote.length ? remote : this.fallback.search(input);
    } catch {
      return this.fallback.search(input);
    }
  }
}

const localCourts = new LocalDirectoryProvider("court", validateResults(courtDirectory, "court"));
const localAdvocates = new LocalDirectoryProvider("advocate", validateResults(advocateDirectory, "advocate"));

export const courtProvider: ResourceProvider = new ConfiguredProvider(
  "court",
  process.env.COURT_PROVIDER_URL,
  localCourts,
);
export const advocateProvider: ResourceProvider = new ConfiguredProvider(
  "advocate",
  process.env.ADVOCATE_PROVIDER_URL,
  localAdvocates,
);
