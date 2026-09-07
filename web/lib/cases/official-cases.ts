import officialCatalog from "@/data/legal/official-judgments.json";
import {
  extractLegalIssues,
  extractTokens,
  type LegalCaseDomain,
  type LegalIssueRepresentation,
} from "./query-understanding";

export type CourtLevel = "SUPREME_COURT" | "HIGH_COURT" | "TRIBUNAL" | "DISTRICT_COURT";

export interface OfficialJudgmentRecord {
  id: string;
  title: string;
  court: string;
  court_level: CourtLevel;
  jurisdiction: string;
  case_number: string;
  case_type: string;
  judgment_date: string;
  bench: string | null;
  judge_names: string[];
  petitioner: string | null;
  respondent: string | null;
  citation: string | null;
  official_source: boolean;
  source_authority: string;
  source_url: string;
  source_type: string;
  domain: LegalCaseDomain;
  acts: string[];
  sections: string[];
  legal_topics: string[];
  primary_issue: string;
  facts_summary: string;
  holding: string;
  disposition: string | null;
  why_relevant: string;
  content_hash: string;
}

export type RelevanceLevel = "Highly relevant" | "Relevant" | "Potentially relevant";

export interface RankedCaseResult {
  id: string;
  title: string;
  court: string;
  court_level: CourtLevel;
  jurisdiction: string;
  judgment_date: string;
  case_number: string;
  case_type: string;
  citation: string;
  legal_issue: string;
  relevant_law: string;
  why_relevant: string;
  relevance_score: number; // 0 - 100
  relevance_level: RelevanceLevel;
  official_source: boolean;
  source_authority: string;
  source_url: string;
  source_type: string;
  bench: string | null;
  judge_names: string[];
  holding: string;
  acts: string[];
  sections: string[];
  content_hash: string;
}

export const OFFICIAL_JUDGMENTS = officialCatalog as OfficialJudgmentRecord[];

const RELEVANCE_MIN_THRESHOLD = 60;

function stemWord(word: string): string {
  if (word.length <= 4) return word;
  return word
    .replace(/(?:ingly|fully|tion|tions|ment|ments|edly|ing|ed|es|er|ers|s)$/, "")
    .trim();
}

function wordMatches(haystack: string, word: string): boolean {
  if (haystack.includes(word)) return true;
  const stem = stemWord(word);
  return stem.length >= 3 && haystack.includes(stem);
}

function computeIssueSimilarity(
  issueRep: LegalIssueRepresentation,
  item: OfficialJudgmentRecord,
): number {
  const queryIssues = issueRep.issues.join(" ").toLowerCase();
  const caseHolding = item.holding.toLowerCase();
  const casePrimaryIssue = item.primary_issue.toLowerCase();
  const caseTopics = item.legal_topics.join(" ").toLowerCase();

  const queryTokens = extractTokens(queryIssues);
  if (queryTokens.length === 0) return 0.5;

  let matches = 0;
  for (const token of queryTokens) {
    if (wordMatches(casePrimaryIssue, token)) {
      matches += 2.0; // Holding/Issue priority
    } else if (wordMatches(caseHolding, token)) {
      matches += 1.5;
    } else if (wordMatches(caseTopics, token)) {
      matches += 1.0;
    }
  }

  const maxPossible = queryTokens.length * 2.0;
  return Math.min(1.0, matches / Math.max(1, maxPossible));
}

function computeTopicMatch(
  issueRep: LegalIssueRepresentation,
  item: OfficialJudgmentRecord,
): number {
  if (issueRep.domain === "UNKNOWN") return 0.5;
  if (issueRep.domain !== item.domain) return 0.0;

  let score = 0.80;
  const caseTopics = item.legal_topics.map((t) => t.toLowerCase());
  const queryKeywords = issueRep.keywords;
  const topicOverlap = queryKeywords.some((kw) =>
    caseTopics.some((ct) => ct.includes(kw) || kw.includes(ct)),
  );
  if (topicOverlap) {
    score += 0.20;
  }
  return Math.min(1.0, score);
}

function computeStatuteMatch(
  issueRep: LegalIssueRepresentation,
  item: OfficialJudgmentRecord,
): number {
  if (issueRep.acts.length === 0 && issueRep.sections.length === 0) {
    return 0.5; // neutral if no statutory constraints
  }

  let actMatch = 0;
  const caseActs = item.acts.map((a) => a.toLowerCase());
  for (const queryAct of issueRep.acts) {
    const qTokens = extractTokens(queryAct);
    for (const ca of caseActs) {
      const cTokens = extractTokens(ca);
      const common = qTokens.filter((t) => cTokens.includes(t));
      if (common.length >= 2 || (qTokens.length === 1 && common.length === 1)) {
        actMatch = Math.max(actMatch, Math.min(1.0, common.length / Math.max(qTokens.length - 1, 1)));
      }
    }
  }

  let secMatch = 0;
  if (issueRep.sections.length > 0) {
    const caseSecs = item.sections.map((s) => s.toLowerCase());
    for (const qSec of issueRep.sections) {
      const secNorm = qSec.toLowerCase().replace(/[^a-z0-9]/g, "");
      if (caseSecs.some((cs) => cs.replace(/[^a-z0-9]/g, "").includes(secNorm))) {
        secMatch = 1.0;
        break;
      }
    }
  }

  if (issueRep.sections.length > 0) {
    return actMatch * 0.6 + secMatch * 0.4;
  }
  return actMatch;
}

function computeFactSimilarity(
  issueRep: LegalIssueRepresentation,
  item: OfficialJudgmentRecord,
): number {
  if (issueRep.facts.length === 0) return 0.5;

  const caseHaystack = `${item.facts_summary} ${item.holding}`.toLowerCase();
  let matches = 0;

  for (const fact of issueRep.facts) {
    const factTokens = extractTokens(fact);
    const matchedTokens = factTokens.filter((token) => wordMatches(caseHaystack, token));
    if (matchedTokens.length >= 1) {
      matches += matchedTokens.length / Math.max(1, factTokens.length);
    }
  }

  return Math.min(1.0, matches / Math.max(1, issueRep.facts.length));
}

function computeLexicalSimilarity(
  queryTokens: string[],
  item: OfficialJudgmentRecord,
): number {
  if (queryTokens.length === 0) return 0.5;

  const haystack = [
    item.title,
    item.citation,
    item.primary_issue,
    item.holding,
    ...item.legal_topics,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  const hitCount = queryTokens.filter((token) => wordMatches(haystack, token)).length;
  return Math.min(1.0, hitCount / Math.max(1, queryTokens.length));
}

function computeCourtAuthority(
  item: OfficialJudgmentRecord,
  queryJurisdiction: string | null,
): number {
  // If query specifies a state jurisdiction (e.g. TAMIL_NADU), boost High Court of that state
  if (queryJurisdiction && item.jurisdiction === queryJurisdiction) {
    return 1.0;
  }

  switch (item.court_level) {
    case "SUPREME_COURT":
      return 1.0;
    case "HIGH_COURT":
      return 0.88;
    case "TRIBUNAL":
      return 0.80;
    default:
      return 0.70;
  }
}

function computeRecencyScore(judgmentDate: string): number {
  try {
    const year = new Date(judgmentDate).getFullYear();
    if (isNaN(year)) return 0.75;
    if (year >= 2020) return 1.0;
    if (year >= 2010) return 0.90;
    if (year >= 2000) return 0.82;
    if (year >= 1980) return 0.75;
    return 0.65;
  } catch {
    return 0.75;
  }
}

function classifyRelevanceLevel(score: number): RelevanceLevel {
  if (score >= 90) return "Highly relevant";
  if (score >= 75) return "Relevant";
  return "Potentially relevant";
}

function formatRelevantLaw(acts: string[], sections: string[]): string {
  const parts: string[] = [];
  if (acts.length > 0) {
    parts.push(acts.join(", "));
  }
  if (sections.length > 0) {
    parts.push(sections.join(", "));
  }
  return parts.join(" — ") || "General Law";
}

/**
 * Hybrid retrieval, ranking, and relevance scoring for official Indian judgments.
 */
export function searchOfficialJudgments(
  query: string,
  options: {
    limit?: number;
    minThreshold?: number;
    requireDisputeOrIntent?: boolean;
    filterJurisdiction?: string | null;
  } = {},
): RankedCaseResult[] {
  const {
    limit = 5,
    minThreshold = RELEVANCE_MIN_THRESHOLD,
    filterJurisdiction = null,
  } = options;

  if (!query || !query.trim()) return [];

  const issueRep = extractLegalIssues(query);
  const activeJurisdiction = filterJurisdiction || issueRep.jurisdiction;

  // Deduplicate cases by content_hash or id
  const seenHashes = new Set<string>();
  const candidates: OfficialJudgmentRecord[] = [];

  for (const item of OFFICIAL_JUDGMENTS) {
    if (seenHashes.has(item.content_hash)) continue;
    seenHashes.add(item.content_hash);
    candidates.push(item);
  }

  const queryTokens = extractTokens(query);

  const scored = candidates.map((item) => {
    const issueSim = computeIssueSimilarity(issueRep, item);
    const statuteSim = computeStatuteMatch(issueRep, item);
    const topicSim = computeTopicMatch(issueRep, item);
    const factSim = computeFactSimilarity(issueRep, item);
    const lexicalSim = computeLexicalSimilarity(queryTokens, item);
    const courtAuth = computeCourtAuthority(item, activeJurisdiction);
    const recency = computeRecencyScore(item.judgment_date);

    // Domain mismatch penalty:
    // If the query clearly maps to a domain (e.g. CONSUMER, PROPERTY) and candidate belongs
    // to a different domain, apply heavy penalty (-50) to prevent superficial keyword false positives.
    let domainMismatchPenalty = 0;
    if (issueRep.domain !== "UNKNOWN" && item.domain !== issueRep.domain) {
      domainMismatchPenalty = 0.50;
    }

    // Transparent weighted score calculation (Section 10 of requirements)
    const rawWeighted =
      issueSim * 0.20 +
      statuteSim * 0.15 +
      topicSim * 0.15 +
      factSim * 0.20 +
      lexicalSim * 0.10 +
      courtAuth * 0.10 +
      recency * 0.10 -
      domainMismatchPenalty;

    // Scale to 0-100 integer
    const finalScore = Math.max(0, Math.min(100, Math.round(rawWeighted * 100)));

    return {
      item,
      score: finalScore,
    };
  });

  const validHits = scored
    .filter((row) => row.score >= minThreshold)
    .sort((a, b) => b.score - a.score);

  return validHits.slice(0, limit).map(({ item, score }): RankedCaseResult => {
    return {
      id: item.id,
      title: item.title,
      court: item.court,
      court_level: item.court_level,
      jurisdiction: item.jurisdiction,
      judgment_date: item.judgment_date,
      case_number: item.case_number,
      case_type: item.case_type,
      citation: item.citation || item.case_number,
      legal_issue: item.primary_issue,
      relevant_law: formatRelevantLaw(item.acts, item.sections),
      why_relevant: item.why_relevant,
      relevance_score: score,
      relevance_level: classifyRelevanceLevel(score),
      official_source: item.official_source,
      source_authority: item.source_authority,
      source_url: item.source_url,
      source_type: item.source_type,
      bench: item.bench,
      judge_names: item.judge_names,
      holding: item.holding,
      acts: item.acts,
      sections: item.sections,
      content_hash: item.content_hash,
    };
  });
}
