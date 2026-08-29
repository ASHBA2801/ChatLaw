export type CaseIntentType =
  | "NORMAL_LEGAL_QUESTION"
  | "CASE_DISCUSSION"
  | "SIMILAR_CASE_REQUEST"
  | "CASE_LAW_RESEARCH"
  | "PERSONAL_CASE_QUERY"
  | "NO_CASE_INTENT";

export function detectCaseIntent(message: string, isCasesWorkspace = false): {
  intent: CaseIntentType;
  requiresCases: boolean;
} {
  const text = (message || "").toLowerCase().trim();

  // Explicit case requests or research
  if (
    /\b(?:similar cases?|court cases?|judgments?|precedents?|case law|case laws?|cases related|cases about|previous cases?)\b/.test(text) ||
    /\b(?:find|show|give me|search)\b.{0,30}\b(?:cases?|judgments?|precedents?)\b/.test(text)
  ) {
    if (/\b(?:research|supreme court|high court|landmark)\b/.test(text)) {
      return { intent: "CASE_LAW_RESEARCH", requiresCases: true };
    }
    return { intent: "SIMILAR_CASE_REQUEST", requiresCases: true };
  }

  // Personal case discussion
  if (
    /\b(?:my case|against my employer|landlord has filed|consumer dispute|involved in a case|dispute with|refused to refund|my situation|i bought a defective)\b/.test(text)
  ) {
    return { intent: "PERSONAL_CASE_QUERY", requiresCases: isCasesWorkspace };
  }

  if (isCasesWorkspace) {
    return { intent: "CASE_DISCUSSION", requiresCases: true };
  }

  return { intent: "NORMAL_LEGAL_QUESTION", requiresCases: false };
}
