/**
 * Deterministic legal speech normalizer for Text-to-Speech synthesis.
 * Converts section numbers, Indian currency amounts, abbreviations, and citations
 * into natural spoken prose without changing the legal meaning.
 */

const ONES: readonly string[] = [
  "",
  "one",
  "two",
  "three",
  "four",
  "five",
  "six",
  "seven",
  "eight",
  "nine",
  "ten",
  "eleven",
  "twelve",
  "thirteen",
  "fourteen",
  "fifteen",
  "sixteen",
  "seventeen",
  "eighteen",
  "nineteen",
];

const TENS: readonly string[] = [
  "",
  "",
  "twenty",
  "thirty",
  "forty",
  "fifty",
  "sixty",
  "seventy",
  "eighty",
  "ninety",
];

/** Convert an integer up to 999 into words. */
function convertThreeDigits(num: number): string {
  if (num === 0) return "";
  let result = "";
  const hundreds = Math.floor(num / 100);
  const remainder = num % 100;

  if (hundreds > 0) {
    result += `${ONES[hundreds]} hundred`;
    if (remainder > 0) {
      result += " ";
    }
  }

  if (remainder < 20) {
    result += ONES[remainder];
  } else {
    const tens = Math.floor(remainder / 10);
    const units = remainder % 10;
    result += TENS[tens];
    if (units > 0) {
      result += ` ${ONES[units]}`;
    }
  }

  return result.trim();
}

/**
 * Convert a positive integer into words using the Indian numbering system
 * (crores, lakhs, thousands, hundreds).
 */
export function numberToIndianWords(num: number): string {
  if (!Number.isFinite(num) || num < 0) return "";
  if (num === 0) return "zero";

  const crore = Math.floor(num / 10_000_000);
  let rem = num % 10_000_000;

  const lakh = Math.floor(rem / 100_000);
  rem %= 100_000;

  const thousand = Math.floor(rem / 1_000);
  rem %= 1_000;

  const parts: string[] = [];

  if (crore > 0) {
    parts.push(`${convertThreeDigits(crore)} crore`);
  }
  if (lakh > 0) {
    parts.push(`${convertThreeDigits(lakh)} lakh`);
  }
  if (thousand > 0) {
    parts.push(`${convertThreeDigits(thousand)} thousand`);
  }
  if (rem > 0) {
    parts.push(convertThreeDigits(rem));
  }

  return parts.join(" ").trim();
}

/**
 * Normalize Indian currency expressions (e.g. ₹18,000, Rs. 2,50,000, ₹1 Lakh).
 */
export function normalizeCurrency(text: string): string {
  let result = text;

  // Pattern for ₹ / Rs. followed by written Lakh/Crore, e.g., ₹1 Lakh, Rs 2.5 Crore
  result = result.replace(
    /(?:₹|Rs\.?|INR)\s*(\d+(?:\.\d+)?)\s*(lakhs?|crores?)/gi,
    (_, amountStr: string, unitStr: string) => {
      const val = parseFloat(amountStr);
      const unit = unitStr.toLowerCase().startsWith("cr") ? "crore" : "lakh";
      const words = Number.isInteger(val)
        ? numberToIndianWords(val)
        : `${val}`;
      return `${words} ${unit} rupees`;
    },
  );

  // Pattern for ₹18,000 or Rs. 2,50,000 or ₹ 500 with optional per month / p.a.
  result = result.replace(
    /(?:₹|Rs\.?|INR)\s*([\d,]+)(?:\/mo|\/month)?/gi,
    (match, numStr: string) => {
      const isPerMonth = /\/mo(?:nth)?/i.test(match);
      const cleanNum = parseInt(numStr.replace(/,/g, ""), 10);
      if (Number.isNaN(cleanNum)) return match;
      const spoken = numberToIndianWords(cleanNum);
      if (!spoken) return match;
      return `${spoken} rupees${isPerMonth ? " per month" : ""}`;
    },
  );

  return result;
}

/**
 * Normalize section references such as:
 * Section 303(2) -> Section 303, sub-section 2
 * Section 303(2)(a) -> Section 303, sub-section 2, clause a
 * Sec. 138 -> Section 138
 * Article 21(1) -> Article 21, clause 1
 * Order 39 Rule 1 -> Order 39, Rule 1
 */
export function normalizeLegalSections(text: string): string {
  let result = text;

  // Expand Sec. / Sec to Section
  result = result.replace(/\bSec\.\s*(\d+)/gi, "Section $1");
  result = result.replace(/\bsec\s+(\d+)/gi, "Section $1");

  // Section 303(2)(a) -> Section 303, sub-section 2, clause a
  result = result.replace(
    /\b(Section|Sec\.?)\s+(\d+)\s*\(\s*(\d+)\s*\)\s*\(\s*([a-zA-Z])\s*\)/gi,
    "Section $2, sub-section $3, clause $4",
  );

  // Section 303(2) -> Section 303, sub-section 2
  result = result.replace(
    /\b(Section|Sec\.?)\s+(\d+)\s*\(\s*(\d+)\s*\)/gi,
    "Section $2, sub-section $3",
  );

  // Article 21(1) -> Article 21, clause 1
  result = result.replace(
    /\bArticle\s+(\d+[A-Z]?)\s*\(\s*(\d+)\s*\)/gi,
    "Article $1, clause $2",
  );

  // Order 39 Rule 1 / Order 39, Rule 2
  result = result.replace(
    /\bOrder\s+(\d+)\s+Rule\s+(\d+)/gi,
    "Order $1, Rule $2",
  );

  return result;
}

/**
 * Expand statutory abbreviations so TTS sounds natural and authoritative.
 */
export function normalizeLegalAbbreviations(text: string): string {
  const replacements: Array<[RegExp, string]> = [
    [/\bBNS\b/g, "Bharatiya Nyaya Sanhita"],
    [/\bBNSS\b/g, "Bharatiya Nagarik Suraksha Sanhita"],
    [/\bBSA\b/g, "Bharatiya Sakshya Adhiniyam"],
    [/\bIPC\b/g, "Indian Penal Code"],
    [/\bCr\.?P\.?C\.?\b/gi, "Code of Criminal Procedure"],
    [/\bC\.?P\.?C\.?\b/gi, "Code of Civil Procedure"],
    [/\bN\.?I\.?\s*Act\b/gi, "Negotiable Instruments Act"],
    [/\bCPA\s+2019\b/gi, "Consumer Protection Act 2019"],
    [/\bRTI\s+Act\b/gi, "Right to Information Act"],
    [/\bFIR\b/g, "First Information Report"],
    [/\bGPA\b/g, "General Power of Attorney"],
    [/\bSPA\b/g, "Special Power of Attorney"],
    [/\bNDA\b/g, "Non-Disclosure Agreement"],
    [/\bp\.a\.\b/gi, "per annum"],
  ];

  let result = text;
  for (const [pattern, expansion] of replacements) {
    result = result.replace(pattern, expansion);
  }
  return result;
}

/**
 * Remove citations, technical bracketed markers, and URLs.
 */
export function stripCitationsAndTechnicalMarkers(text: string): string {
  return text
    .replace(/\[SOURCE\s+\d+\]/gi, "")
    .replace(/\[\d+\]/g, "")
    .replace(/https?:\/\/[^\s]+/gi, "")
    .replace(/www\.[^\s]+/gi, "");
}

/**
 * Convert markdown to clean, readable prose.
 */
export function stripMarkdownFormatting(text: string): string {
  return text
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/\*\*([^*]+)\*\*/g, "$1")
    .replace(/\*([^*]+)\*/g, "$1")
    .replace(/__([^_]+)__/g, "$1")
    .replace(/_([^_]+)_/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/^\s*>\s+/gm, "")
    .replace(/\|/g, " ")
    .replace(/-{3,}/g, " ");
}

/**
 * Clean up residual punctuation artifacts caused by stripping citations
 * (e.g., "punishable under .", "stated in and .", excessive commas).
 */
export function cleanPunctuationArtifacts(text: string): string {
  return text
    .replace(/\s+([.,;:?!])/g, "$1")
    .replace(/([.,;:?!])\s*\1+/g, "$1")
    .replace(/\bin and\b/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

/**
 * Comprehensive normalizer for legal answers before speech synthesis.
 */
export function normalizeTextForSpeech(text: string): string {
  if (!text || !text.trim()) return "";

  let processed = text;
  processed = stripCitationsAndTechnicalMarkers(processed);
  processed = stripMarkdownFormatting(processed);
  processed = normalizeLegalSections(processed);
  processed = normalizeCurrency(processed);
  processed = normalizeLegalAbbreviations(processed);
  processed = cleanPunctuationArtifacts(processed);

  return processed;
}
