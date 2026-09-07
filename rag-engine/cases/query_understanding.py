"""Case-law query understanding and deterministic legal issue extraction."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class LegalIssueRepresentation:
    domain: str
    domain_display_name: str
    confidence: str
    issues: tuple[str, ...]
    acts: tuple[str, ...]
    sections: tuple[str, ...]
    facts: tuple[str, ...]
    jurisdiction: str | None
    keywords: tuple[str, ...]
    is_dispute_scenario: bool
    raw_query: str


DOMAIN_RULES = [
    {
        "domain": "CONSUMER",
        "display_name": "Consumer Protection",
        "priority_keywords": (
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
        ),
        "general_keywords": (
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
            "delivery",
        ),
        "default_acts": ("Consumer Protection Act, 2019", "Consumer Protection Act, 1986"),
    },
    {
        "domain": "EMPLOYMENT",
        "display_name": "Employment & Labour Law",
        "priority_keywords": (
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
        ),
        "general_keywords": (
            "employer",
            "employee",
            "termination",
            "fired",
            "workplace",
            "salary",
            "harassment",
        ),
        "default_acts": (
            "Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013",
            "Industrial Disputes Act, 1947",
        ),
    },
    {
        "domain": "PROPERTY",
        "display_name": "Property & Tenancy",
        "priority_keywords": (
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
        ),
        "general_keywords": (
            "landlord",
            "tenant",
            "rent",
            "deposit",
            "lease",
            "flat",
            "property",
            "possession",
            "eviction",
        ),
        "default_acts": ("Transfer of Property Act, 1882",),
    },
    {
        "domain": "CONTRACT",
        "display_name": "Contract & Commercial",
        "priority_keywords": (
            "breached the agreement",
            "breach of contract",
            "refused compensation",
            "liquidated damages",
            "forfeited earnest money",
            "commercial agreement",
        ),
        "general_keywords": (
            "contract",
            "agreement",
            "breach",
            "clause",
            "damages",
            "compensation",
            "forfeiture",
        ),
        "default_acts": ("Indian Contract Act, 1872", "Specific Relief Act, 1963"),
    },
    {
        "domain": "FAMILY",
        "display_name": "Family & Matrimonial",
        "priority_keywords": (
            "filed for divorce",
            "divorce rights",
            "child custody",
            "maintenance claim",
            "alimony",
            "matrimonial dispute",
        ),
        "general_keywords": (
            "divorce",
            "spouse",
            "wife",
            "husband",
            "marriage",
            "maintenance",
            "custody",
        ),
        "default_acts": ("Hindu Marriage Act, 1955", "Protection of Women from Domestic Violence Act, 2005"),
    },
    {
        "domain": "CYBER",
        "display_name": "Cyber Law & Data Privacy",
        "priority_keywords": (
            "personal information without permission",
            "used my personal information",
            "data privacy",
            "informational privacy",
            "unauthorized data",
            "data leak",
            "dpdp",
        ),
        "general_keywords": (
            "privacy",
            "personal data",
            "unauthorized",
            "permission",
            "data",
            "cyber",
        ),
        "default_acts": (
            "Digital Personal Data Protection Act, 2023",
            "Information Technology Act, 2000",
            "Constitution of India",
        ),
    },
    {
        "domain": "IP",
        "display_name": "Intellectual Property",
        "priority_keywords": (
            "using my registered trademark",
            "registered trademark",
            "trademark infringement",
            "deceptive similarity",
            "passing off",
            "brand name copied",
        ),
        "general_keywords": (
            "trademark",
            "trade mark",
            "brand",
            "logo",
            "infringement",
            "counterfeit",
        ),
        "default_acts": ("Trade Marks Act, 1999",),
    },
    {
        "domain": "TAX",
        "display_name": "Taxation & Revenue",
        "priority_keywords": (
            "tax demand",
            "calculation is wrong",
            "erroneous tax",
            "gst demand",
            "incorrect tax calculation",
        ),
        "general_keywords": (
            "tax",
            "taxes",
            "gst",
            "income tax",
            "demand",
            "revenue",
            "assessment",
        ),
        "default_acts": ("Central Goods and Services Act, 2017", "Income-tax Act, 1961"),
    },
    {
        "domain": "CRIMINAL",
        "display_name": "Criminal Law & Procedure",
        "priority_keywords": (
            "accused of theft",
            "police custody",
            "fir registration",
            "false fir",
            "anticipatory bail",
            "cognizable offence",
            "theft case",
        ),
        "general_keywords": (
            "theft",
            "accused",
            "police",
            "fir",
            "arrest",
            "bail",
            "crime",
            "stolen",
        ),
        "default_acts": (
            "Bharatiya Nyaya Sanhita, 2023",
            "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "Indian Penal Code, 1860",
            "Code of Criminal Procedure, 1973",
        ),
    },
    {
        "domain": "ENVIRONMENT",
        "display_name": "Environmental Law",
        "priority_keywords": (
            "factory is polluting",
            "polluting a nearby water source",
            "polluting water",
            "industrial effluent",
            "polluter pays",
        ),
        "general_keywords": (
            "polluting",
            "pollution",
            "factory",
            "water source",
            "effluent",
            "environment",
        ),
        "default_acts": (
            "Water (Prevention and Control of Pollution) Act, 1974",
            "Environment (Protection) Act, 1986",
        ),
    },
    {
        "domain": "CONSTITUTIONAL",
        "display_name": "Constitutional Law",
        "priority_keywords": (
            "basic structure",
            "article 21",
            "article 14",
            "fundamental right",
            "unconstitutional",
            "constitution bench",
        ),
        "general_keywords": (
            "constitution",
            "fundamental rights",
            "amendment",
            "due process",
        ),
        "default_acts": ("Constitution of India",),
    },
]

JURISDICTION_PATTERNS = [
    ("TAMIL_NADU", re.compile(r"\b(?:tamil\s*nadu|chennai|madras)\b", re.IGNORECASE)),
    ("DELHI", re.compile(r"\b(?:delhi|new\s*delhi|ncr)\b", re.IGNORECASE)),
    ("MAHARASHTRA", re.compile(r"\b(?:maharashtra|mumbai|bombay|pune)\b", re.IGNORECASE)),
    ("KARNATAKA", re.compile(r"\b(?:karnataka|bangalore|bengaluru)\b", re.IGNORECASE)),
    ("WEST_BENGAL", re.compile(r"\b(?:west\s*bengal|kolkata|calcutta)\b", re.IGNORECASE)),
    ("UTTAR_PRADESH", re.compile(r"\b(?:uttar\s*pradesh|lucknow|allahabad|kanpur|noida)\b", re.IGNORECASE)),
    ("KERALA", re.compile(r"\b(?:kerala|kochi|cochin|ernakulam|thiruvananthapuram)\b", re.IGNORECASE)),
    ("GUJARAT", re.compile(r"\b(?:gujarat|ahmedabad|gandhinagar|surat)\b", re.IGNORECASE)),
]

STOPWORDS = frozenset(
    "a about an and are as at be by can could did do does for from had has have he her him his how i if in into is it its me my no not of off on once or other our out over she should so some such than that the their them then there these they this those through to too under until up very was we were what when where which while who whom why will with would you your case cases court judgments precedent precedents".split()
)


def extract_legal_issues(query: str) -> LegalIssueRepresentation:
    normalized = unicodedata.normalize("NFKC", query or "").lower().strip()
    words = [re.sub(r"[^\w]", "", w) for w in re.split(r"\s+", normalized) if w]
    tokens = tuple(w for w in words if len(w) > 2 and w not in STOPWORDS)

    jurisdiction = None
    for j_id, pattern in JURISDICTION_PATTERNS:
        if pattern.search(normalized):
            jurisdiction = j_id
            break

    scored_domains = []
    for rule in DOMAIN_RULES:
        score = 0
        for kw in rule["priority_keywords"]:
            if kw in normalized:
                score += 8
        for kw in rule["general_keywords"]:
            if kw in normalized:
                score += 2
        scored_domains.append((rule, score))

    scored_domains.sort(key=lambda x: x[1], reverse=True)
    top_rule, top_score = scored_domains[0] if scored_domains else (None, 0)

    domain = top_rule["domain"] if top_rule and top_score > 0 else "UNKNOWN"
    display_name = top_rule["display_name"] if top_rule and top_score > 0 else "General Legal Matter"
    confidence = (
        "HIGH" if top_score >= 10
        else "MEDIUM" if top_score >= 4
        else "LOW" if top_score > 0
        else "NONE"
    )

    acts = tuple(top_rule["default_acts"][:2]) if top_rule and top_score >= 4 else ()
    
    issues = []
    if top_rule and top_score > 0:
        for kw in top_rule["priority_keywords"]:
            if kw in normalized:
                issues.append(kw)

    facts = []
    if re.search(r"\b(?:bought|purchased|ordered|online|e-commerce|website)\b", normalized):
        facts.append("commercial or e-commerce transaction")
    if re.search(r"\b(?:defective|damaged|broken|faulty|not working)\b", normalized):
        facts.append("product or service defect")
    if re.search(r"\b(?:refused|denied|declined|won't|wont)\b.{0,20}\b(?:refund|return|replace|pay|return deposit)\b", normalized):
        facts.append("refusal to refund or remediate")
    if re.search(r"\b(?:terminated|fired|dismissed)\b.{0,25}\b(?:after|complained|whistleblow|harassment)\b", normalized):
        facts.append("employment termination following complaint")
    if re.search(r"\b(?:security deposit|rent deposit)\b", normalized):
        facts.append("tenancy security deposit dispute")
    if re.search(r"\b(?:breached|violated)\b.{0,20}\b(?:agreement|contract)\b", normalized):
        facts.append("breach of contractual covenants")
    if re.search(r"\b(?:divorce|spouse filed)\b", normalized):
        facts.append("divorce proceedings initiated")
    if re.search(r"\b(?:personal information|privacy|without permission)\b", normalized):
        facts.append("unauthorized use of personal information")
    if re.search(r"\b(?:registered trademark|trademark)\b", normalized):
        facts.append("unauthorized use of registered trademark")
    if re.search(r"\b(?:tax demand|calculation is wrong)\b", normalized):
        facts.append("dispute over erroneous tax demand calculation")
    if re.search(r"\b(?:accused of theft|theft)\b", normalized):
        facts.append("allegation or charge of theft")
    if re.search(r"\b(?:factory|water source|polluting)\b", normalized):
        facts.append("industrial discharge polluting water body")

    is_dispute = bool(facts or re.search(r"\b(?:i bought|my employer|my landlord|accused of|factory is)\b", normalized))

    return LegalIssueRepresentation(
        domain=domain,
        domain_display_name=display_name,
        confidence=confidence,
        issues=tuple(issues) if issues else tokens[:3],
        acts=acts,
        sections=(),
        facts=tuple(facts),
        jurisdiction=jurisdiction,
        keywords=tokens,
        is_dispute_scenario=is_dispute,
        raw_query=query,
    )
