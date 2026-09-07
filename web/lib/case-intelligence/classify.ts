import type { CaseIntelligence, LegalDomain, LocationInput } from "./types";

const rules: Array<{ domain: LegalDomain; category: string; terms: string[]; topics: string[]; forums: string[]; documents: string[] }> = [
  { domain: "Property", category: "Property / Tenancy", terms: ["landlord", "tenant", "rent", "deposit", "evict", "property"], topics: ["tenancy", "property rights", "notice and remedies"], forums: ["Relevant local civil or tenancy forum"], documents: ["Agreement or title records", "Payment records", "Relevant communications"] },
  { domain: "Family", category: "Family dispute", terms: ["divorce", "maintenance", "custody", "marriage", "child"], topics: ["family law", "support obligations", "family procedure"], forums: ["Relevant family court or forum"], documents: ["Identity and relationship records", "Relevant financial records"] },
  { domain: "Employment", category: "Employment dispute", terms: ["salary", "employer", "termination", "workplace", "employee", "employment"], topics: ["employment rights", "contract terms", "workplace remedies"], forums: ["Relevant labour or civil forum"], documents: ["Employment agreement", "Payslips", "Workplace communications"] },
  { domain: "Consumer", category: "Consumer dispute", terms: ["refund", "consumer", "product", "service", "defective", "complaint"], topics: ["consumer protection", "refunds", "service deficiency"], forums: ["Relevant consumer forum"], documents: ["Invoice or receipt", "Warranty or service records", "Complaint correspondence"] },
  { domain: "Criminal", category: "Potential criminal matter", terms: ["arrest", "police", "theft", "assault", "fraud", "crime", "fir"], topics: ["criminal procedure", "offence classification", "evidence"], forums: ["Relevant criminal court or police forum"], documents: ["Notices or reports", "Available evidence", "Relevant communications"] },
  { domain: "Contract", category: "Contract dispute", terms: ["agreement", "contract", "breach", "clause", "payment due"], topics: ["contract formation", "breach", "remedies"], forums: ["Relevant civil or commercial forum"], documents: ["Signed agreement", "Payment records", "Notice and correspondence"] },
];

export function classifyCase(query: string, location: LocationInput | null = null): CaseIntelligence {
  const normalized = query.toLowerCase();
  const match = rules.map((rule) => ({ rule, score: rule.terms.filter((term) => normalized.includes(term)).length })).sort((a, b) => b.score - a.score)[0];
  const selected = match?.score ? match.rule : null;
  const urgent = /arrest|detain|deadline|tomorrow|imminent|evict immediately|threat/.test(normalized);
  return {
    case_category: selected?.category ?? "General legal question",
    legal_domain: selected?.domain ?? "Other",
    sub_category: selected ? selected.category : null,
    issue_summary: query.trim().slice(0, 240),
    relevant_legal_topics: selected?.topics ?? ["Applicable law", "Jurisdiction", "Available remedies"],
    jurisdiction: location?.state || location?.country || null,
    location,
    suggested_forum_types: selected?.forums ?? [],
    urgency: urgent ? "potentially_urgent" : "routine",
    required_documents: selected?.documents ?? [],
    confidence: match?.score >= 2 ? "high" : match?.score === 1 ? "medium" : "low",
    limitations: ["This is an orientation based on the question, not a legal conclusion.", "The potentially relevant forum depends on facts and jurisdiction.", ...(location ? [] : ["Add a city and state to search nearby resources."])],
  };
}