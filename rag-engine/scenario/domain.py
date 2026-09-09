"""Lightweight deterministic legal domain routing and classification.

Supports at minimum the 16 legal domains required for Indian law queries,
calculating domain affinities without external API calls.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True)
class DomainDefinition:
    id: str
    display_name: str
    priority_keywords: tuple[str, ...]
    general_keywords: tuple[str, ...]
    acts_and_statutes: tuple[str, ...]


DOMAINS_REGISTRY: dict[str, DomainDefinition] = {
    "consumer_protection": DomainDefinition(
        id="consumer_protection",
        display_name="Consumer Protection",
        priority_keywords=(
            "consumer", "defective product", "defective goods", "defective", "defect",
            "refund", "return refusal", "refused refund", "e-commerce", "online shopping",
            "online shop", "online store", "online order", "unfair trade practice",
            "deficiency in service", "misleading advertisement", "advertised", "advertisement",
            "false advertising", "warranty", "replacement", "replace", "trader",
            "manufacturer liability", "consumer dispute", "consumer forum", "ncdrc",
            "dcdrc", "scdrc", "उपभोक्ता", "रिफंड", "दोषपूर्ण",
        ),
        general_keywords=(
            "seller", "buyer", "customer", "purchase", "delivery", "shopping", "store", "shop",
            "product", "goods", "item", "bad product", "broken product", "guarantee",
            "invoice", "bill", "flipkart", "amazon", "meesho",
        ),
        acts_and_statutes=("consumer protection act", "cpa 2019", "e-commerce rules"),
    ),
    "contract": DomainDefinition(
        id="contract",
        display_name="Contract",
        priority_keywords=(
            "contract", "agreement", "breach of contract", "liquidated damages", "specific performance",
            "indemnity", "guarantee", "consideration", "mou", "nda", "terms and conditions",
            "non-disclosure", "promissory note", "अनुबंध", "समझौता",
        ),
        general_keywords=(
            "sign", "signed", "clause", "obligation", "party", "breach", "violation of terms",
            "vendor agreement", "service agreement",
        ),
        acts_and_statutes=("indian contract act", "specific relief act"),
    ),
    "criminal_law": DomainDefinition(
        id="criminal_law",
        display_name="Criminal Law",
        priority_keywords=(
            "theft", "murder", "assault", "robbery", "dacoity", "cheating", "fraud",
            "criminal breach of trust", "criminal intimidation", "extortion", "kidnapping",
            "fir", "arrest", "bail", "bns", "ipc", "punishment", "offence", "offense",
            "चोरी", "धोखाधड़ी", "गिरफ्तारी", "सजा", "हत्या",
        ),
        general_keywords=(
            "police", "crime", "stolen", "victim", "accused", "jail", "culprit",
            "suspect", "charge", "complaint to police",
        ),
        acts_and_statutes=("bharatiya nyaya sanhita", "bns", "indian penal code", "ipc"),
    ),
    "property": DomainDefinition(
        id="property",
        display_name="Property",
        priority_keywords=(
            "landlord", "tenant", "tenancy", "house rent", "monthly rent", "rent arrears",
            "security deposit", "eviction",
            "lease", "property dispute", "title deed", "sale deed", "mortgage", "partition",
            "possession", "trespass", "encroachment", "stamp duty", "registration of property",
            "मकान मालिक", "किरायेदार", "किराया", "जमा", "संपत्ति",
        ),
        general_keywords=(
            "flat", "house", "apartment", "land", "plot", "rented", "owner", "builder",
            "possession delayed", "rera", "rent",
        ),
        acts_and_statutes=("transfer of property act", "rent control act", "rera"),
    ),
    "family_law": DomainDefinition(
        id="family_law",
        display_name="Family Law",
        priority_keywords=(
            "divorce", "maintenance", "alimony", "child custody", "marriage", "matrimonial",
            "domestic violence", "restitution of conjugal rights", "adoption", "guardianship",
            "inheritance", "succession", "ancestral property", "streedhan",
            "तलाक", "भरण-पोषण", "गुजारा भत्ता", "शादी",
        ),
        general_keywords=(
            "husband", "wife", "spouse", "children", "in-laws", "separation", "family court",
        ),
        acts_and_statutes=("hindu marriage act", "special marriage act", "guardians and wards act", "hindu succession act"),
    ),
    "personal_law": DomainDefinition(
        id="personal_law",
        display_name="Personal Law",
        priority_keywords=(
            "personal law", "hindu law", "muslim law", "christian marriage", "parsi marriage",
            "which marriage law", "applicable personal law", "succession under personal law",
            "triple talaq", "nikah", "hindu adoption",
        ),
        general_keywords=(
            "religion", "community", "custom", "personal status",
        ),
        acts_and_statutes=(
            "hindu marriage act", "hindu succession act", "special marriage act",
            "muslim women protection of rights on marriage act",
        ),
    ),
    "labour_employment": DomainDefinition(
        id="labour_employment",
        display_name="Labour/Employment",
        priority_keywords=(
            "salary", "unpaid salary", "wages", "employer", "employee", "termination",
            "wrongful termination", "fired", "dismissed", "provident fund", "pf", "gratuity",
            "esi", "labour court", "workplace harassment", "posh", "severance",
            "वेतन", "पगार", "नौकरी", "कर्मचारी", "नियोक्ता",
        ),
        general_keywords=(
            "workplace", "job", "office", "resignation", "notice period", "overtime",
            "working hours", "appointment letter",
        ),
        acts_and_statutes=("industrial disputes act", "payment of wages act", "payment of gratuity act", "posh act"),
    ),
    "cyber_law": DomainDefinition(
        id="cyber_law",
        display_name="Cyber Law",
        priority_keywords=(
            "cyber crime", "cyber fraud", "scammed online", "took my money online",
            "phishing", "identity theft", "hacking", "unauthorized access", "otp fraud",
            "fake website", "data privacy", "it act", "information technology act",
            "social media harassment", "deepfake", "साइबर अपराध", "ऑनलाइन धोखाधड़ी",
        ),
        general_keywords=(
            "online scam", "internet fraud", "digital", "apk scam", "whatsapp scam", "telegram scam",
            "money taken online", "hacked",
        ),
        acts_and_statutes=("information technology act", "it act 2000", "digital personal data protection act"),
    ),
    "motor_vehicle": DomainDefinition(
        id="motor_vehicle",
        display_name="Motor Vehicle",
        priority_keywords=(
            "motor vehicle", "car accident", "bike accident", "road accident", "traffic challan",
            "mact", "third party insurance", "driving license", "hit and run", "rash driving",
            "vehicle seizure", "सड़क दुर्घटना", "चालान",
        ),
        general_keywords=(
            "traffic fine", "insurance claim", "speeding", "drunk driving", "vehicle registration",
        ),
        acts_and_statutes=("motor vehicles act", "mva 1988"),
    ),
    "constitutional_law": DomainDefinition(
        id="constitutional_law",
        display_name="Constitutional Law",
        priority_keywords=(
            "fundamental rights", "article 21", "article 19", "article 14", "writ petition",
            "habeas corpus", "mandamus", "certiorari", "quowarranto", "prohibition",
            "constitutional validity", "supreme court", "high court jurisdiction", "public interest litigation", "pil",
            "मौलिक अधिकार", "संविधान",
        ),
        general_keywords=(
            "liberty", "equality", "discrimination", "freedom of speech", "state action",
        ),
        acts_and_statutes=("constitution of india",),
    ),
    "civil_procedure": DomainDefinition(
        id="civil_procedure",
        display_name="Civil Procedure",
        priority_keywords=(
            "cpc", "civil procedure", "plaint", "written statement", "injunction", "stay order",
            "interim injunction", "execution of decree", "res judicata", "limitation act",
            "court fee", "jurisdiction of civil court", "summons",
        ),
        general_keywords=(
            "civil suit", "decree", "plaintiff", "defendant", "affidavit", "interlocutory application",
        ),
        acts_and_statutes=("code of civil procedure", "cpc", "limitation act", "court fees act"),
    ),
    "criminal_procedure": DomainDefinition(
        id="criminal_procedure",
        display_name="Criminal Procedure",
        priority_keywords=(
            "bnss", "crpc", "criminal procedure", "anticipatory bail", "regular bail", "cognizable",
            "non-cognizable", "remand", "police custody", "judicial custody", "charge sheet",
            "investigation", "search warrant", "section 144", "zero fir",
            "जमानत", "रिमांड", "चार्जशीट",
        ),
        general_keywords=(
            "magistrate", "sessions court", "investigating officer", "inquest", "case diary",
        ),
        acts_and_statutes=("bharatiya nagarik suraksha sanhita", "bnss", "code of criminal procedure", "crpc"),
    ),
    "company_commercial_law": DomainDefinition(
        id="company_commercial_law",
        display_name="Company/Commercial Law",
        priority_keywords=(
            "companies act", "director liability", "shareholder", "insolvency", "bankruptcy",
            "ibc", "nclt", "nclat", "winding up", "incorporation", "merger", "amalgamation",
            "board of directors", "annual return", "roc",
        ),
        general_keywords=(
            "corporate", "company registration", "startup", "equity", "shares", "commercial dispute",
        ),
        acts_and_statutes=("companies act 2013", "insolvency and bankruptcy code", "ibc"),
    ),
    "intellectual_property": DomainDefinition(
        id="intellectual_property",
        display_name="Intellectual Property",
        priority_keywords=(
            "trademark", "copyright", "patent", "ip infringement", "passing off", "trade secret",
            "piracy", "design registration", "trademark objection", "licensing agreement",
            "logo copied", "software copied", "invented a machine", "geographical indication",
        ),
        general_keywords=(
            "brand name", "logo copied", "stolen design", "counterfeit", "intellectual property",
        ),
        acts_and_statutes=("trade marks act", "copyright act", "patents act", "designs act"),
    ),
    "environment": DomainDefinition(
        id="environment",
        display_name="Environmental Law",
        priority_keywords=(
            "pollution", "environment protection", "water pollution", "air pollution",
            "wildlife", "forest clearance", "ngt", "green tribunal", "river polluted",
            "environmental clearance", "hazardous waste", "biodiversity",
        ),
        general_keywords=(
            "factory discharge", "smoke", "effluent", "environment", "ecology",
        ),
        acts_and_statutes=(
            "environment protection act", "water act", "air act", "wild life protection act",
            "national green tribunal act",
        ),
    ),
    "evidence": DomainDefinition(
        id="evidence",
        display_name="Law of Evidence",
        priority_keywords=(
            "admissible evidence", "electronic evidence", "witness", "hearsay", "proof",
            "documentary evidence", "bsa", "indian evidence act", "examination of witness",
        ),
        general_keywords=(
            "evidence", "admission", "proof", "testimony", "affidavit evidence",
        ),
        acts_and_statutes=("bharatiya sakshya adhiniyam", "bsa", "indian evidence act"),
    ),
    "banking_finance": DomainDefinition(
        id="banking_finance",
        display_name="Banking/Finance",
        priority_keywords=(
            "cheque bounce", "section 138 ni act", "negotiable instruments", "banking ombudsman",
            "sarfaesi", "drt", "loan recovery", "emi dispute", "cibil score", "credit card dispute",
            "unauthorized transaction", "duplicate deduction", "rbi guidelines", "charged twice",
        ),
        general_keywords=(
            "bank", "loan", "bank account", "cheque", "mortgage loan", "interest rate",
        ),
        acts_and_statutes=("negotiable instruments act", "sarfaesi act", "rbi act", "banking regulation act"),
    ),
    "tax": DomainDefinition(
        id="tax",
        display_name="Tax",
        priority_keywords=(
            "income tax", "gst", "goods and services tax", "tax notice", "scrutiny",
            "it return", "tds", "input tax credit", "advance tax", "tax penalty",
            "assessment order", "itat", "gst tribunal", "cgst", "igst", "customs duty",
        ),
        general_keywords=(
            "taxation", "revenue", "tax deduction", "pan card", "audit", "tax refund",
        ),
        acts_and_statutes=(
            "income tax act", "income-tax act 2025", "central goods and services tax act", "cgst",
            "integrated goods and services tax act", "customs act",
        ),
    ),
    "railways": DomainDefinition(
        id="railways",
        display_name="Railways",
        priority_keywords=(
            "railway", "railways", "train accident", "untoward incident", "railway ticket",
            "train collision", "railway passenger", "railway administration", "railway claims tribunal",
            "railway property", "train delay", "railway refund", "रेल", "ट्रेन दुर्घटना", "रेलवे",
        ),
        general_keywords=(
            "train", "station", "locomotive", "railway track", "coach", "ticket examiner",
            "berth", "train fare", "freight train", "goods carriage", "demurrage", "wharfage",
        ),
        acts_and_statutes=("railways act", "railways act 1989", "the railways act, 1989", "indian railways act", "railway claims tribunal act"),
    ),
    "general_legal": DomainDefinition(
        id="general_legal",
        display_name="General Legal",
        priority_keywords=(
            "legal notice", "affidavit", "power of attorney", "notary", "court",
            "legal advice", "advocate", "jurisdiction",
        ),
        general_keywords=(
            "rights", "remedies", "law", "procedure", "dispute",
        ),
        acts_and_statutes=(),
    ),
}


@dataclass(frozen=True)
class DomainRoutingResult:
    primary_domain: str
    primary_domain_name: str
    confidence: float
    secondary_domains: tuple[str, ...]
    domain_scores: Mapping[str, float]


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text).lower()
    return " ".join(re.sub(r"[^\w\s-]", " ", normalized, flags=re.UNICODE).split())


def _matches_keyword(norm_kw: str, norm_query: str) -> bool:
    if not norm_kw:
        return False
    if norm_kw.isascii():
        return bool(re.search(rf"\b{re.escape(norm_kw)}\b", norm_query))
    return norm_kw in norm_query


def score_domain(query: str, domain: DomainDefinition) -> tuple[float, list[str]]:
    """Calculate match score for a given domain definition against query text."""
    norm_query = normalize_text(query)
    score = 0.0
    matched: list[str] = []

    for kw in domain.priority_keywords:
        norm_kw = normalize_text(kw)
        if _matches_keyword(norm_kw, norm_query):
            score += 2.0
            matched.append(kw)

    for kw in domain.general_keywords:
        norm_kw = normalize_text(kw)
        if _matches_keyword(norm_kw, norm_query):
            score += 1.0
            matched.append(kw)

    for act in domain.acts_and_statutes:
        norm_act = normalize_text(act)
        if _matches_keyword(norm_act, norm_query):
            score += 3.0
            matched.append(act)

    return score, matched


def route_domain(query: str) -> DomainRoutingResult:
    """Classify the query into primary and secondary domains deterministically."""
    scores: dict[str, float] = {}
    matches: dict[str, list[str]] = {}

    for domain_id, domain_def in DOMAINS_REGISTRY.items():
        score, matched = score_domain(query, domain_def)
        scores[domain_id] = score
        matches[domain_id] = matched

    sorted_domains = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_id, best_score = sorted_domains[0]

    if best_score <= 0.0:
        return DomainRoutingResult(
            primary_domain="general_legal",
            primary_domain_name=DOMAINS_REGISTRY["general_legal"].display_name,
            confidence=0.0,
            secondary_domains=(),
            domain_scores=scores,
        )

    # Compute normalized confidence
    total_positive = sum(s for s in scores.values() if s > 0)
    confidence = min(1.0, best_score / 6.0) if best_score < 6.0 else 1.0

    # Secondary domains with meaningful score
    secondary = tuple(
        d_id for d_id, s in sorted_domains[1:]
        if s >= 2.0 and s >= (best_score * 0.4) and d_id != "general_legal"
    )

    return DomainRoutingResult(
        primary_domain=best_id,
        primary_domain_name=DOMAINS_REGISTRY[best_id].display_name,
        confidence=confidence,
        secondary_domains=secondary,
        domain_scores=scores,
    )
