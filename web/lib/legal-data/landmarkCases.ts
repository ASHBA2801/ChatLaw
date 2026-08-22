import catalog from "@/data/legal/landmark-cases.json";

export type LandmarkCase = {
  id: string;
  title: string;
  citation: string;
  court: string;
  year: number;
  topics: string[];
  relevant_sections: string[];
  summary: string;
  why_relevant: string;
  source_url: string;
  source_type: string;
  verification_status: string;
};

export const LANDMARK_CASES = catalog as LandmarkCase[];

export function searchLandmarkCases(query: string, limit = 12): LandmarkCase[] {
  const tokens = query
    .toLowerCase()
    .split(/[^a-z0-9]+/i)
    .map((token) => token.trim())
    .filter((token) => token.length > 2);
  if (tokens.length === 0) return LANDMARK_CASES.slice(0, limit);

  const scored = LANDMARK_CASES.map((item) => {
    const haystack = [
      item.title,
      item.citation,
      item.court,
      item.summary,
      item.why_relevant,
      ...item.topics,
      ...item.relevant_sections,
    ]
      .join(" ")
      .toLowerCase();
    const score = tokens.reduce((total, token) => total + (haystack.includes(token) ? 1 : 0), 0);
    return { item, score };
  })
    .filter((row) => row.score > 0)
    .sort((a, b) => b.score - a.score || b.item.year - a.item.year);

  return scored.slice(0, limit).map((row) => row.item);
}
