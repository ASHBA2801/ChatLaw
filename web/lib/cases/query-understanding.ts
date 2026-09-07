/**
 * Deterministic legal issue extraction and query understanding engine.
 *
 * Infers legal concepts, domains, statutory provisions, factual disputes,
 * and jurisdictions without calling external LLM APIs.
 */

export type LegalCaseDomain =
  | "CONSUMER"
  | "EMPLOYMENT"
  | "PROPERTY"
  | "CONTRACT"
  | "FAMILY"
  | "CYBER"
  | "IP"
  | "TAX"
  | "CRIMINAL"
  | "ENVIRONMENT"
  | "CONSTITUTIONAL"
  | "UNKNOWN";

export interface LegalIssueRepresentation {
  domain: LegalCaseDomain;
  domainDisplayName: string;
  confidence: "HIGH" | "MEDIUM" | "LOW" | "NONE";
  issues: string[];
  acts: string[];
  sections: string[];
  facts: string[];
  jurisdiction: string | null;
  keywords: string[];
  isDisputeScenario: boolean;
  rawQuery: string;
}

interface DomainRule {
  domain: LegalCaseDomain;
  displayName: string;
  priorityKeywords: string[];
  generalKeywords: string[];
  defaultActs: string[];
}

const DOMAIN_RULES: DomainRule[] = [
  {
    domain: "CONSUMER",
    displayName: "Consumer Protection",
    priorityKeywords: [
      "defective product",
      "defective goods",
      "defective phone",
      "defective item",
      "refused refund",
      "refused return",
      "refund refusal",
      "e-commerce",
      "online shopping",
      "online purchase",
      "online store",
      "online order",
      "amazon",
      "flipkart",
      "deficiency in service",
      "unfair trade practice",
      "consumer dispute",
      "consumer forum",
      "consumer court",
      "ncdrc",
      "consumer rights",
      "warranty claim",
      "replacement refused",
    ],
    generalKeywords: [
      "refund",
      "return",
      "defective",
      "warranty",
      "replacement",
      "customer",
      "consumer",
      "seller",
      "buyer",
      "purchase",
      "bought",
      "ordered",
      "shipped",
      "delivery",
      "invoice",
      "receipt",
    ],
    defaultActs: ["Consumer Protection Act, 2019", "Consumer Protection Act, 1986"],
  },
  {
    domain: "EMPLOYMENT",
    displayName: "Employment & Labour Law",
    priorityKeywords: [
      "workplace harassment",
      "sexual harassment",
      "posh",
      "posh act",
      "internal complaints committee",
      "terminated me",
      "unlawful termination",
      "wrongful termination",
      "fired after",
      "retaliation",
      "hostile work environment",
      "employment dispute",
      "unpaid salary",
      "labour court",
    ],
    generalKeywords: [
      "employer",
      "employee",
      "termination",
      "fired",
      "job",
      "workplace",
      "office",
      "boss",
      "salary",
      "harassment",
      "resigned",
      "severance",
      "probation",
    ],
    defaultActs: [
      "Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013",
      "Industrial Disputes Act, 1947",
    ],
  },
  {
    domain: "PROPERTY",
    displayName: "Property & Tenancy",
    priorityKeywords: [
      "security deposit",
      "landlord refuses",
      "return my security deposit",
      "deposit refund",
      "rent deposit",
      "tenant",
      "landlord",
      "unlawful eviction",
      "eviction notice",
      "tenancy dispute",
      "lease agreement",
      "vacate premises",
      "rent control",
    ],
    generalKeywords: [
      "landlord",
      "tenant",
      "rent",
      "deposit",
      "lease",
      "flat",
      "house",
      "apartment",
      "property",
      "possession",
      "evict",
      "eviction",
      "premises",
    ],
    defaultActs: ["Transfer of Property Act, 1882"],
  },
  {
    domain: "CONTRACT",
    displayName: "Contract & Commercial",
    priorityKeywords: [
      "breached the agreement",
      "breach of contract",
      "refused compensation",
      "liquidated damages",
      "forfeited earnest money",
      "contractual dispute",
      "commercial agreement",
      "specific performance",
      "non-disclosure",
    ],
    generalKeywords: [
      "contract",
      "agreement",
      "breach",
      "clause",
      "damages",
      "compensation",
      "forfeiture",
      "sign",
      "signed",
      "vendor",
      "terms",
    ],
    defaultActs: ["Indian Contract Act, 1872", "Specific Relief Act, 1963"],
  },
  {
    domain: "FAMILY",
    displayName: "Family & Matrimonial",
    priorityKeywords: [
      "filed for divorce",
      "divorce rights",
      "child custody",
      "maintenance claim",
      "alimony",
      "triple talaq",
      "matrimonial dispute",
      "domestic violence",
      "spousal rights",
    ],
    generalKeywords: [
      "divorce",
      "spouse",
      "wife",
      "husband",
      "marriage",
      "matrimonial",
      "maintenance",
      "custody",
      "child",
      "alimony",
    ],
    defaultActs: [
      "Hindu Marriage Act, 1955",
      "Special Marriage Act, 1954",
      "Protection of Women from Domestic Violence Act, 2005",
    ],
  },
  {
    domain: "CYBER",
    displayName: "Cyber Law & Data Privacy",
    priorityKeywords: [
      "personal information without permission",
      "used my personal information",
      "data privacy",
      "informational privacy",
      "unauthorized data",
      "data leak",
      "identity theft",
      "right to be forgotten",
      "cyber crime",
      "dpdp",
    ],
    generalKeywords: [
      "privacy",
      "personal data",
      "information",
      "online account",
      "hacked",
      "unauthorized",
      "permission",
      "internet",
      "data",
      "cyber",
    ],
    defaultActs: [
      "Digital Personal Data Protection Act, 2023",
      "Information Technology Act, 2000",
      "Constitution of India",
    ],
  },
  {
    domain: "IP",
    displayName: "Intellectual Property",
    priorityKeywords: [
      "using my registered trademark",
      "registered trademark",
      "trademark infringement",
      "deceptive similarity",
      "passing off",
      "brand name copied",
      "patent infringement",
      "copyright infringement",
    ],
    generalKeywords: [
      "trademark",
      "trade mark",
      "brand",
      "logo",
      "patent",
      "copyright",
      "infringement",
      "counterfeit",
      "ipr",
    ],
    defaultActs: ["Trade Marks Act, 1999", "Copyright Act, 1957"],
  },
  {
    domain: "TAX",
    displayName: "Taxation & Revenue",
    priorityKeywords: [
      "tax demand",
      "calculation is wrong",
      "erroneous tax",
      "gst demand",
      "income tax demand",
      "assessment order",
      "tax notice",
      "incorrect tax calculation",
    ],
    generalKeywords: [
      "tax",
      "taxes",
      "gst",
      "income tax",
      "demand",
      "revenue",
      "assessment",
      "penalty",
      "notice",
      "audit",
    ],
    defaultActs: ["Central Goods and Services Tax Act, 2017", "Income-tax Act, 1961"],
  },
  {
    domain: "CRIMINAL",
    displayName: "Criminal Law & Procedure",
    priorityKeywords: [
      "accused of theft",
      "police custody",
      "fir registration",
      "false fir",
      "anticipatory bail",
      "arrest without warrant",
      "cognizable offence",
      "theft case",
      "cheating case",
    ],
    generalKeywords: [
      "theft",
      "accused",
      "police",
      "fir",
      "arrest",
      "bail",
      "crime",
      "stolen",
      "jail",
      "charge",
      "court trial",
      "bns",
      "ipc",
      "crpc",
      "bnss",
    ],
    defaultActs: [
      "Bharatiya Nyaya Sanhita, 2023",
      "Bharatiya Nagarik Suraksha Sanhita, 2023",
      "Indian Penal Code, 1860",
      "Code of Criminal Procedure, 1973",
    ],
  },
  {
    domain: "ENVIRONMENT",
    displayName: "Environmental Law",
    priorityKeywords: [
      "factory is polluting",
      "polluting a nearby water source",
      "polluting water",
      "industrial effluent",
      "toxic waste discharge",
      "polluter pays",
      "water contamination",
      "factory smoke",
    ],
    generalKeywords: [
      "polluting",
      "pollution",
      "factory",
      "water source",
      "river",
      "lake",
      "effluent",
      "hazardous",
      "environment",
      "contamination",
    ],
    defaultActs: [
      "Water (Prevention and Control of Pollution) Act, 1974",
      "Environment (Protection) Act, 1986",
      "National Green Tribunal Act, 2010",
    ],
  },
  {
    domain: "CONSTITUTIONAL",
    displayName: "Constitutional Law",
    priorityKeywords: [
      "basic structure",
      "article 21",
      "article 14",
      "article 19",
      "article 32",
      "fundamental right",
      "unconstitutional",
      "constitution bench",
      "writ of habeas corpus",
      "judicial review",
    ],
    generalKeywords: [
      "constitution",
      "fundamental rights",
      "amendment",
      "parliament power",
      "due process",
      "equality",
      "liberty",
    ],
    defaultActs: ["Constitution of India"],
  },
];

const JURISDICTION_PATTERNS: Array<{ id: string; name: string; regex: RegExp }> = [
  { id: "TAMIL_NADU", name: "Tamil Nadu", regex: /\b(?:tamil\s*nadu|chennai|madras)\b/i },
  { id: "DELHI", name: "Delhi", regex: /\b(?:delhi|new\s*delhi|ncr)\b/i },
  { id: "MAHARASHTRA", name: "Maharashtra", regex: /\b(?:maharashtra|mumbai|bombay|pune)\b/i },
  { id: "KARNATAKA", name: "Karnataka", regex: /\b(?:karnataka|bangalore|bengaluru)\b/i },
  { id: "WEST_BENGAL", name: "West Bengal", regex: /\b(?:west\s*bengal|kolkata|calcutta)\b/i },
  { id: "UTTAR_PRADESH", name: "Uttar Pradesh", regex: /\b(?:uttar\s*pradesh|lucknow|allahabad|kanpur|noida)\b/i },
  { id: "KERALA", name: "Kerala", regex: /\b(?:kerala|kochi|cochin|ernakulam|thiruvananthapuram)\b/i },
  { id: "GUJARAT", name: "Gujarat", regex: /\b(?:gujarat|ahmedabad|gandhinagar|surat)\b/i },
];

const ACT_PATTERNS: Array<{ act: string; regex: RegExp }> = [
  { act: "Consumer Protection Act, 2019", regex: /\b(?:consumer\s+protection\s+act|cpa\s*2019|cpa)\b/i },
  { act: "Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013", regex: /\b(?:posh(?:\s+act)?|sexual\s+harassment(?:\s+at\s+workplace)?(?:\s+act)?)\b/i },
  { act: "Transfer of Property Act, 1882", regex: /\b(?:transfer\s+of\s+property(?:\s+act)?|tpa)\b/i },
  { act: "Indian Contract Act, 1872", regex: /\b(?:contract\s+act|indian\s+contract\s+act|ica)\b/i },
  { act: "Trade Marks Act, 1999", regex: /\b(?:trade\s*marks?\s+act|trademark\s+act)\b/i },
  { act: "Digital Personal Data Protection Act, 2023", regex: /\b(?:dpdp(?:\s+act)?|data\s+protection\s+act)\b/i },
  { act: "Information Technology Act, 2000", regex: /\b(?:it\s+act|information\s+technology\s+act)\b/i },
  { act: "Central Goods and Services Tax Act, 2017", regex: /\b(?:cgst(?:\s+act)?|gst(?:\s+act)?)\b/i },
  { act: "Water (Prevention and Control of Pollution) Act, 1974", regex: /\b(?:water\s+act|water\s+pollution\s+act)\b/i },
  { act: "Environment (Protection) Act, 1986", regex: /\b(?:environment(?:\s+protection)?\s+act|epa)\b/i },
  { act: "Hindu Marriage Act, 1955", regex: /\b(?:hindu\s+marriage\s+act|hma)\b/i },
  { act: "Code of Criminal Procedure, 1973", regex: /\b(?:code\s+of\s+criminal\s+procedure|crpc)\b/i },
  { act: "Bharatiya Nagarik Suraksha Sanhita, 2023", regex: /\b(?:bharatiya\s+nagarik\s+suraksha\s+sanhita|bnss)\b/i },
  { act: "Bharatiya Nyaya Sanhita, 2023", regex: /\b(?:bharatiya\s+nyaya\s+sanhita|bns)\b/i },
  { act: "Indian Penal Code, 1860", regex: /\b(?:indian\s+penal\s+code|ipc)\b/i },
  { act: "Constitution of India", regex: /\b(?:constitution(?:\s+of\s+india)?)\b/i },
];

const SECTION_PATTERNS: RegExp[] = [
  /\b(?:section|sec\.?)\s*(\d+[a-z]?(?:\s*\(\s*\w+\s*\))*)/gi,
  /\b(?:article|art\.?)\s*(\d+[a-z]?)/gi,
  /\brule\s*(\d+[a-z]?)/gi,
];

const STOPWORDS = new Set([
  "a", "about", "an", "and", "are", "as", "at", "be", "by", "can", "could", "did", "do",
  "does", "for", "from", "had", "has", "have", "he", "her", "him", "his", "how", "i",
  "if", "in", "into", "is", "it", "its", "me", "my", "no", "not", "of", "off", "on",
  "once", "or", "other", "our", "out", "over", "she", "should", "so", "some", "such",
  "than", "that", "the", "their", "them", "then", "there", "these", "they", "this",
  "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were",
  "what", "when", "where", "which", "while", "who", "whom", "why", "will", "with",
  "would", "you", "your", "case", "cases", "court", "judgments", "precedent", "precedents",
]);

export function extractTokens(text: string): string[] {
  return (text || "")
    .toLowerCase()
    .split(/[^a-z0-9]+/i)
    .map((token) => token.trim())
    .filter((token) => token.length > 2 && !STOPWORDS.has(token));
}

export function extractLegalIssues(query: string): LegalIssueRepresentation {
  const text = (query || "").toLowerCase().trim();
  const tokens = extractTokens(text);

  // 1. Detect Jurisdiction (Never invent one)
  let jurisdiction: string | null = null;
  for (const item of JURISDICTION_PATTERNS) {
    if (item.regex.test(text)) {
      jurisdiction = item.id;
      break;
    }
  }

  // 2. Score Domains deterministically
  const scoredDomains = DOMAIN_RULES.map((rule) => {
    let score = 0;
    // Priority keywords have high weight
    for (const kw of rule.priorityKeywords) {
      if (text.includes(kw)) {
        score += 8;
      }
    }
    // General keywords contribute moderately
    for (const kw of rule.generalKeywords) {
      if (text.includes(kw)) {
        score += 2;
      }
    }
    return { rule, score };
  }).sort((a, b) => b.score - a.score);

  const topMatch = scoredDomains[0];
  const domain: LegalCaseDomain = topMatch && topMatch.score > 0 ? topMatch.rule.domain : "UNKNOWN";
  const domainDisplayName = topMatch && topMatch.score > 0 ? topMatch.rule.displayName : "General Legal Matter";
  const confidence =
    topMatch && topMatch.score >= 10
      ? "HIGH"
      : topMatch && topMatch.score >= 4
        ? "MEDIUM"
        : topMatch && topMatch.score > 0
          ? "LOW"
          : "NONE";

  // 3. Extract Specific Mentioned Acts
  const extractedActs: string[] = [];
  for (const item of ACT_PATTERNS) {
    if (item.regex.test(text)) {
      extractedActs.push(item.act);
    }
  }
  // If no explicit Act is mentioned, populate with default canonical Act of the identified domain
  if (extractedActs.length === 0 && topMatch && topMatch.score >= 4) {
    extractedActs.push(...topMatch.rule.defaultActs.slice(0, 2));
  }

  // 4. Extract Specific Mentioned Sections
  const extractedSections: string[] = [];
  for (const regex of SECTION_PATTERNS) {
    let match: RegExpExecArray | null;
    const re = new RegExp(regex.source, regex.flags);
    while ((match = re.exec(text)) !== null) {
      const sec = match[0].trim();
      if (!extractedSections.includes(sec)) {
        extractedSections.push(sec);
      }
    }
  }

  // 5. Extract Issues and Facts
  const issues: string[] = [];
  const facts: string[] = [];

  // Factual problem extraction based on matched priority keywords
  if (topMatch && topMatch.score > 0) {
    for (const kw of topMatch.rule.priorityKeywords) {
      if (text.includes(kw)) {
        issues.push(kw);
      }
    }
  }

  // Factual indicators
  if (/\b(?:bought|purchased|ordered|online|e-commerce|website)\b/i.test(text)) {
    facts.push("commercial or e-commerce transaction");
  }
  if (/\b(?:defective|damaged|broken|faulty|not working)\b/i.test(text)) {
    facts.push("product or service defect");
  }
  if (/\b(?:refused|denied|declined|won't|wont)\b.{0,20}\b(?:refund|return|replace|pay|return deposit)\b/i.test(text)) {
    facts.push("refusal to refund or remediate");
  }
  if (/\b(?:terminated|fired|dismissed)\b.{0,25}\b(?:after|complained|whistleblow|harassment)\b/i.test(text)) {
    facts.push("employment termination following complaint");
  }
  if (/\b(?:sexual harassment|workplace harassment|posh)\b/i.test(text)) {
    facts.push("allegation of workplace harassment");
  }
  if (/\b(?:landlord|tenant|security deposit|rent deposit)\b/i.test(text)) {
    facts.push("tenancy security deposit dispute");
  }
  if (/\b(?:breached|violated|failed to perform)\s+(?:agreement|contract)\b/i.test(text)) {
    facts.push("breach of contractual covenants");
  }
  if (/\b(?:divorce|spouse filed|matrimonial)\b/i.test(text)) {
    facts.push("divorce proceedings initiated");
  }
  if (/\b(?:personal information|privacy|without permission)\b/i.test(text)) {
    facts.push("unauthorized use of personal information");
  }
  if (/\b(?:registered trademark|trademark|brand name)\b/i.test(text)) {
    facts.push("unauthorized use of registered trademark");
  }
  if (/\b(?:tax demand|calculation is wrong|erroneous tax)\b/i.test(text)) {
    facts.push("dispute over erroneous tax demand calculation");
  }
  if (/\b(?:accused of theft|theft|stolen)\b/i.test(text)) {
    facts.push("allegation or charge of theft");
  }
  if (/\b(?:factory|water source|polluting|effluent)\b/i.test(text)) {
    facts.push("industrial discharge polluting water body");
  }

  const isDisputeScenario =
    /\b(?:i\s+bought|i\s+purchased|i\s+ordered|my\s+employer|my\s+landlord|my\s+spouse|accused\s+of|factory\s+is|refused\s+to|breached\s+the|dispute|complaint|notice)\b/i.test(text) ||
    facts.length > 0;

  return {
    domain,
    domainDisplayName,
    confidence,
    issues: issues.length > 0 ? issues : tokens.slice(0, 3),
    acts: extractedActs,
    sections: extractedSections,
    facts,
    jurisdiction,
    keywords: tokens,
    isDisputeScenario,
    rawQuery: query,
  };
}
