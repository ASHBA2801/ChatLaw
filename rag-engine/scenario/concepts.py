"""Deterministic legal concept and synonym dictionary.

Maps informal, colloquial, and scenario-based language to formal Indian legal
terminology, statutory concepts, and domain synonyms without calling an LLM.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class ConceptMapping:
    concept_id: str
    canonical_term: str
    domain: str
    triggers: tuple[str, ...]
    expanded_terms: tuple[str, ...]


# Extensible legal concept mappings
CONCEPT_MAPPINGS: tuple[ConceptMapping, ...] = (
    # --- Consumer Protection / E-Commerce ---
    ConceptMapping(
        concept_id="defective_goods",
        canonical_term="defective goods",
        domain="consumer",
        triggers=(
            "defective product", "defective item", "defective phone", "defective goods",
            "defect in goods", "product defect", "defect", "bad product", "faulty product",
            "faulty item", "broken product", "not working", "damaged product", "arrived damaged",
            "damaged item", "damaged on delivery", "flawed product", "substandard goods",
            "خराब", "खराब सामान", "दोषपूर्ण",
        ),
        expanded_terms=(
            "defect in goods", "defective goods", "product defect", "substandard goods",
            "product liability", "manufacturing defect", "replacement of goods", "repair of defect",
        ),
    ),
    ConceptMapping(
        concept_id="refund_return_dispute",
        canonical_term="refund and return dispute",
        domain="consumer",
        triggers=(
            "refused refund", "refuses to refund", "refused to refund", "no refund",
            "refused return", "refuses to return", "refused to return", "refused a return",
            "refused returns", "won't replace", "wont replace", "refused replacement",
            "seller refused", "refund dispute", "return dispute", "return refusal",
            "denied refund", "reject return", "not returning money",
            "रिफंड नहीं", "पैसे वापस नहीं", "वापसी से इनकार",
        ),
        expanded_terms=(
            "refund of price", "return of goods", "refusal of refund", "consumer redressal",
            "consumer grievance", "reimbursement", "compensation for loss", "unfair trade practice",
        ),
    ),
    ConceptMapping(
        concept_id="ecommerce_transaction",
        canonical_term="e-commerce transaction",
        domain="consumer",
        triggers=(
            "e-commerce", "ecommerce", "online shopping", "online shop", "online store",
            "bought online", "purchased online", "e-commerce website", "online order",
            "online marketplace", "shopping app", "amazon", "flipkart", "meesho",
            "marketplace", "e-commerce platform", "online purchase", "digital commerce", "online",
            "ऑनलाइन खरीदारी", "ई-कॉमर्स",
        ),
        expanded_terms=(
            "e-commerce entity", "electronic commerce", "online marketplace",
            "direct selling", "duties of e-commerce entity", "marketplace platform liability",
        ),
    ),
    ConceptMapping(
        concept_id="wrong_product_delivery",
        canonical_term="wrong or different goods delivered",
        domain="consumer",
        triggers=(
            "different product", "wrong product", "wrong item", "different item",
            "received different", "sent wrong", "sent completely different", "incorrect item",
            "गलत सामान", "अलग सामान",
        ),
        expanded_terms=(
            "non-conforming goods", "deficiency in service", "unfair trade practice",
            "misleading advertisement", "replacement of goods", "full refund",
        ),
    ),
    ConceptMapping(
        concept_id="non_delivery_goods",
        canonical_term="non-delivery of purchased goods",
        domain="consumer",
        triggers=(
            "never delivered", "not delivered", "did not deliver", "delivery delayed",
            "order not received", "delivery failed", "failed delivery", "undelivered",
            "डिलीवरी नहीं हुई", "सामान नहीं मिला",
        ),
        expanded_terms=(
            "non-delivery", "failure to deliver", "deficiency in service",
            "unfair trade practice", "refund of purchase amount", "delay in supply",
        ),
    ),
    ConceptMapping(
        concept_id="warranty_guarantee_breach",
        canonical_term="breach of warranty or guarantee",
        domain="consumer",
        triggers=(
            "warranty", "guarantee", "refuses to honour", "refuses to honor",
            "warranty rejected", "warranty denied", "under warranty", "warranty period",
            "गारंटी", "वारंटी",
        ),
        expanded_terms=(
            "express warranty", "implied warranty", "product liability",
            "manufacturer liability", "service provider liability", "breach of warranty",
        ),
    ),
    ConceptMapping(
        concept_id="misleading_advertisement",
        canonical_term="misleading advertisement and unfair trade practice",
        domain="consumer",
        triggers=(
            "advertised a product with features", "false advertising", "misleading ad",
            "misleading advertisement", "fake promises", "false claim", "exaggerated claim",
            "features that it does not have", "does not actually have", "fake specification",
            "भ्रामक विज्ञापन", "झूठा प्रचार",
        ),
        expanded_terms=(
            "misleading advertisement", "unfair trade practice", "false representation",
            "deceptive marketing", "consumer protection act", "central consumer protection authority",
        ),
    ),
    ConceptMapping(
        concept_id="double_charging_unauthorized_payment",
        canonical_term="unauthorized payment or duplicate deduction",
        domain="banking",
        triggers=(
            "charged twice", "charged money twice", "debited twice", "double charged",
            "deducted twice", "double payment", "money deducted no order", "extra charge",
            "दो बार कट गया", "दोहरा भुगतान",
        ),
        expanded_terms=(
            "unauthorized debit", "duplicate transaction", "deficiency in banking service",
            "wrongful deduction", "reversal of transaction", "banking ombudsman",
        ),
    ),
    # --- Criminal Law / Cheating / Cyber ---
    ConceptMapping(
        concept_id="criminal_cheating_fraud",
        canonical_term="cheating and dishonest inducement",
        domain="criminal",
        triggers=(
            "cheated", "cheating", "defrauded", "scammed", "fraud", "fraudulent",
            "took my money", "duped", "conned", "swindled", "trick",
            "धोखाधड़ी", "धोखा दिया", "ठगी",
        ),
        expanded_terms=(
            "cheating", "dishonest inducement", "criminal breach of trust",
            "fraudulent misrepresentation", "section 318 bns", "punishment for cheating",
        ),
    ),
    ConceptMapping(
        concept_id="cyber_fraud_online_theft",
        canonical_term="cyber fraud and digital crime",
        domain="cyber",
        triggers=(
            "online fraud", "cyber fraud", "scammed online", "took my money online",
            "phishing", "fake link", "apk scam", "otp fraud", "cyber crime", "cybercrime",
            "ऑनलाइन धोखाधड़ी", "साइबर अपराध",
        ),
        expanded_terms=(
            "cyber crime", "information technology act", "identity theft",
            "cheating by personation", "digital evidence", "cyber fraud reporting",
        ),
    ),
    ConceptMapping(
        concept_id="theft_stealing",
        canonical_term="theft and dishonest misappropriation",
        domain="criminal",
        triggers=(
            "theft", "stolen", "stealing", "thief", "robbery", "stole", "pickpocket",
            "section 303", "sec 303", "sec. 303", "303 bns", "bns 303", "bns section 303",
            "चोरी", "चोरी की सजा",
        ),
        expanded_terms=(
            "theft", "dishonest taking of property", "section 303 bns",
            "punishment for theft", "movable property",
        ),
    ),
    # --- Tenancy / Property ---
    ConceptMapping(
        concept_id="tenancy_deposit_dispute",
        canonical_term="tenancy security deposit dispute",
        domain="tenancy",
        triggers=(
            "security deposit", "deposit refund", "landlord won't return deposit",
            "withholding deposit", "deposit deducted", "rent deposit",
            "सिक्योरिटी डिपॉजिट", "मकान मालिक",
        ),
        expanded_terms=(
            "refund of security deposit", "tenant rights", "landlord obligation",
            "rent agreement", "unlawful deduction", "rent court",
        ),
    ),
    ConceptMapping(
        concept_id="unlawful_eviction",
        canonical_term="unlawful eviction of tenant",
        domain="tenancy",
        triggers=(
            "evict", "eviction", "forced out", "kick out of house", "threatened eviction",
            "evict immediately", "unlawful eviction", "bezabta",
            "बेदखल", "घर से निकालना",
        ),
        expanded_terms=(
            "eviction notice", "unlawful eviction", "due process of law",
            "tenancy protection", "rent control",
        ),
    ),
    # --- Employment / Labour ---
    ConceptMapping(
        concept_id="unpaid_salary_wages",
        canonical_term="unpaid salary and delayed wages",
        domain="employment",
        triggers=(
            "unpaid salary", "salary withheld", "not paying salary", "pending salary",
            "wages not paid", "delayed salary", "unpaid wages",
            "वेतन नहीं मिला", "पगार नहीं दी",
        ),
        expanded_terms=(
            "payment of wages act", "recovery of unpaid salary", "labour commissioner",
            "employment contract breach", "non-payment of wages",
        ),
    ),
    ConceptMapping(
        concept_id="unlawful_termination",
        canonical_term="unlawful termination of employment",
        domain="employment",
        triggers=(
            "fired without notice", "terminated without cause", "wrongful termination",
            "illegal dismissal", "fired suddenly", "terminated employment",
            "बिना नोटिस निकाले", "नौकरी से हटाया",
        ),
        expanded_terms=(
            "wrongful dismissal", "notice period requirement", "severance pay",
            "industrial disputes act", "reinstatement", "labour court",
        ),
    ),
    # --- Contract ---
    ConceptMapping(
        concept_id="breach_of_contract",
        canonical_term="breach of contract and damages",
        domain="contract",
        triggers=(
            "breach of contract", "broke agreement", "violated contract", "contract dispute",
            "did not fulfill agreement", "agreement violated", "terms not met",
            "समझौता तोड़ा", "अनुबंध का उल्लंघन",
        ),
        expanded_terms=(
            "breach of contract", "specific performance", "liquidated damages",
            "compensation for breach", "indian contract act", "discharge of contract",
        ),
    ),
    # --- Motor Vehicle ---
    ConceptMapping(
        concept_id="motor_accident_claim",
        canonical_term="motor vehicle accident and insurance claim",
        domain="motor_vehicle",
        triggers=(
            "car accident", "bike accident", "road accident", "hit and run",
            "motor accident", "challan", "traffic fine", "vehicle insurance claim",
            "सड़क दुर्घटना", "चालान",
        ),
        expanded_terms=(
            "motor vehicles act", "mact claim", "third party insurance",
            "compensation for accident", "rash and negligent driving",
        ),
    ),
    # --- Railways ---
    ConceptMapping(
        concept_id="railway_accident_claim",
        canonical_term="railway accident untoward incident and passenger compensation",
        domain="railways",
        triggers=(
            "train accident", "railway accident", "untoward incident", "derailment",
            "fell from train", "railway compensation", "railway claims tribunal",
            "रेल दुर्घटना", "ट्रेन हादसा",
        ),
        expanded_terms=(
            "railways act 1989", "section 124 railways act", "section 124a untoward incident",
            "railway claims tribunal act", "compensation for train accident",
        ),
    ),
    # --- Family Law ---
    ConceptMapping(
        concept_id="matrimonial_maintenance",
        canonical_term="matrimonial maintenance and alimony",
        domain="family",
        triggers=(
            "divorce", "maintenance claim", "alimony", "child custody", "domestic dispute",
            "spousal support", "wife maintenance", "child support",
            "तलाक", "गुजारा भत्ता",
        ),
        expanded_terms=(
            "maintenance under section 144 bnss", "hindu marriage act",
            "interim maintenance", "permanent alimony", "custody of children",
        ),
    ),
)


# Entity/Actor synonym mappings
ENTITY_SYNONYMS: dict[str, tuple[str, ...]] = {
    "customer": ("consumer", "complainant", "buyer", "purchaser", "user"),
    "consumer": ("consumer", "buyer", "customer", "complainant"),
    "buyer": ("consumer", "purchaser", "buyer"),
    "seller": ("trader", "service provider", "vendor", "merchant", "retailer", "e-commerce entity"),
    "trader": ("seller", "merchant", "dealer", "distributor"),
    "manufacturer": ("producer", "maker", "manufacturing entity", "product seller"),
    "e-commerce": ("electronic commerce", "online marketplace", "digital platform", "e-commerce entity"),
    "landlord": ("lessor", "property owner", "house owner"),
    "tenant": ("lessee", "renter", "occupant"),
    "employer": ("company", "organization", "management", "master"),
    "employee": ("workman", "staff", "servant"),
}


def normalize_string(text: str | None) -> str:
    """Normalize unicode and whitespace."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text).lower()
    return " ".join(re.sub(r"[^\w\s-]", " ", normalized, flags=re.UNICODE).split())


def extract_matching_concepts(query: str) -> list[ConceptMapping]:
    """Identify matching legal concepts from a user query deterministically."""
    norm_query = normalize_string(query)
    matches: list[ConceptMapping] = []
    for mapping in CONCEPT_MAPPINGS:
        for trigger in mapping.triggers:
            norm_trigger = normalize_string(trigger)
            if not norm_trigger:
                continue
            # Match word boundary or exact substring
            if re.search(rf"\b{re.escape(norm_trigger)}\b", norm_query) or norm_trigger in norm_query:
                matches.append(mapping)
                break
    return matches


def get_synonyms_for_term(term: str) -> list[str]:
    """Retrieve legal synonyms for an entity or concept term."""
    norm = normalize_string(term)
    synonyms = list(ENTITY_SYNONYMS.get(norm, ()))
    for mapping in CONCEPT_MAPPINGS:
        if norm in normalize_string(mapping.canonical_term) or norm in [normalize_string(t) for t in mapping.triggers]:
            synonyms.extend(mapping.expanded_terms)
    return list(dict.fromkeys(synonyms))
