"""Deterministic scenario understanding and factual slot extraction.

Identifies real-world legal situations expressed in natural language, extracts
grounded facts (actor, action, channel, problem, opposing action, potential issue)
without calling an LLM and without hallucinating unstated facts.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Mapping

from .concepts import extract_matching_concepts
from .domain import DOMAINS_REGISTRY, DomainRoutingResult, route_domain


@dataclass(frozen=True)
class ScenarioFacts:
    actor: str | None = None
    action: str | None = None
    channel: str | None = None
    problem: str | None = None
    opposing_action: str | None = None
    potential_legal_issue: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "actor": self.actor,
            "action": self.action,
            "channel": self.channel,
            "problem": self.problem,
            "opposing_action": self.opposing_action,
            "potential_legal_issue": self.potential_legal_issue,
        }

    def summary(self) -> str:
        parts = []
        if self.actor:
            parts.append(f"Actor: {self.actor}")
        if self.action:
            parts.append(f"Action: {self.action}")
        if self.channel:
            parts.append(f"Channel: {self.channel}")
        if self.problem:
            parts.append(f"Problem: {self.problem}")
        if self.opposing_action:
            parts.append(f"Opposing action: {self.opposing_action}")
        if self.potential_legal_issue:
            parts.append(f"Potential legal issue: {self.potential_legal_issue}")
        return "; ".join(parts)


@dataclass(frozen=True)
class ScenarioAnalysis:
    original_query: str
    is_scenario: bool
    is_legal_query: bool
    domain_routing: DomainRoutingResult
    facts: ScenarioFacts
    matched_concepts: tuple[str, ...]
    needs_clarification: bool = False
    clarification_question: str | None = None


# Patterns for direct statutory / legal lookup questions
_DIRECT_LOOKUP_PATTERNS = (
    r"\b(?:section|sec\.?)\s*\d+[a-z]?\b",
    r"\bwhat\s+is\s+(?:the\s+)?(?:punishment|definition|meaning|penalty|procedure)\s+(?:for|of)\b",
    r"\bwhich\s+(?:section|provision|act|article|clause)\s+(?:of|in|covers|deals|addresses)\b",
    r"\bunder\s+(?:the\s+)?(?:bns|bsa|bnss|ipc|crpc|cpc|constitution)\b",
    r"\b(?:bns|bsa|bnss|ipc|crpc|cpc)\s+(?:section|sec\.?)\b",
    r"\barticle\s+\d+\b",
)

# Common non-legal / irrelevant queries
_IRRELEVANT_PATTERNS = (
    r"\bcapital\s+of\s+[a-z]+\b",
    r"\brecipe\s+for\s+[a-z]+\b",
    r"\bweather\s+in\s+[a-z]+\b",
    r"\bwho\s+won\s+the\s+[a-z]+\b",
    r"\bhow\s+to\s+cook\b",
    r"\bhow\s+to\s+bake\b",
    r"\bjoke\b",
    r"\bscore\s+of\b",
)

# Scenario indicators (first-person narrative, factual story, dispute narrative)
_SCENARIO_INDICATORS = (
    r"\bi\s+(?:bought|purchased|ordered|paid|signed|received|hired|worked|live|rented|was)\b",
    r"\bmy\s+(?:order|landlord|employer|product|item|salary|deposit|tenant|wife|husband|car|bike|account)\b",
    r"\b(?:seller|landlord|employer|bank|company|shop|buyer)\s+(?:refused|won't|wont|denied|cheated|fired|deducted|threatened|sent|advertised|claimed)\b",
    r"\bwhen\s+i\s+received\b",
    r"\barrived\s+(?:damaged|broken|defective|wrong)\b",
    r"\brefused\s+(?:a\s+)?(?:refund|return|replacement|to\s+honour|to\s+honor)\b",
    r"\bcharged\s+(?:me\s+)?twice\b",
    r"\bnever\s+delivered\b",
    r"\btook\s+my\s+money\b",
    r"\b(?:advertised|features that it does not|false advertising|misleading advertisement)\b",
    r"\bsent\s+(?:me\s+)?(?:a\s+)?(?:completely\s+)?different\s+product\b",
)


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text or "").lower()
    return " ".join(re.sub(r"[^\w\s-]", " ", normalized, flags=re.UNICODE).split())


def is_direct_lookup(query: str) -> bool:
    norm = _normalize(query)
    return any(re.search(pat, norm, re.IGNORECASE) for pat in _DIRECT_LOOKUP_PATTERNS)


def is_irrelevant_query(query: str) -> bool:
    norm = _normalize(query)
    if any(re.search(pat, norm, re.IGNORECASE) for pat in _IRRELEVANT_PATTERNS):
        return True
    return False


def is_scenario_query(query: str) -> bool:
    norm = _normalize(query)
    if is_direct_lookup(query):
        return False
    if any(re.search(pat, norm, re.IGNORECASE) for pat in _SCENARIO_INDICATORS):
        return True
    # If it contains narrative pronouns and action verbs
    if re.search(r"\b(?:i|my|we|they|he|she|seller|landlord|employer)\b", norm) and len(norm.split()) >= 6:
        return True
    return False


def extract_scenario_facts(query: str, domain_result: DomainRoutingResult) -> ScenarioFacts:
    """Extract factual elements deterministically without hallucinating unstated facts."""
    norm = _normalize(query)

    # Actor extraction
    actor = None
    if re.search(r"\b(?:i\s+bought|i\s+purchased|i\s+ordered|customer|consumer|buyer)\b", norm):
        actor = "Consumer / Buyer"
    elif re.search(r"\b(?:tenant|renter|i\s+rented)\b", norm):
        actor = "Tenant"
    elif re.search(r"\b(?:landlord|house\s+owner|owner)\b", norm):
        actor = "Landlord"
    elif re.search(r"\b(?:employee|i\s+worked|worker|staff)\b", norm):
        actor = "Employee"
    elif re.search(r"\b(?:employer|company|boss)\b", norm):
        actor = "Employer"
    elif re.search(r"\b(?:accused|police\s+arrested|fir\s+against\s+me)\b", norm):
        actor = "Accused person"
    elif re.search(r"\b(?:victim|cheated|stolen|robbed|scammed)\b", norm):
        actor = "Aggrieved individual / Complainant"

    # Action extraction
    action = None
    if re.search(r"\b(?:bought|purchased|ordered)\s+(?:a\s+)?(?:product|item|phone|goods|something)\b", norm):
        action = "Purchased product"
    elif re.search(r"\b(?:paid|sent\s+money|transferred\s+money)\b", norm):
        action = "Paid money"
    elif re.search(r"\b(?:rented|leased|staying\s+in)\b", norm):
        action = "Rented property"
    elif re.search(r"\b(?:employed|working|job)\b", norm):
        action = "Employed at workplace"
    elif re.search(r"\b(?:signed|entered\s+into)\s+(?:contract|agreement)\b", norm):
        action = "Entered into agreement"

    # Channel extraction
    channel = None
    if re.search(r"\b(?:e-commerce|ecommerce|website|online\s+shop|online\s+store|online\s+order|online|amazon|flipkart|meesho|shopping\s+app|app)\b", norm):
        channel = "E-commerce website / Online marketplace"
    elif re.search(r"\b(?:shop|store|showroom|offline|market)\b", norm):
        channel = "Physical store / Offline retail"

    # Problem extraction
    problem = None
    if re.search(r"\b(?:defective|defect|faulty|not\s+working)\b", norm):
        problem = "Product defective / defect in goods"
    elif re.search(r"\b(?:damaged|broken|arrived\s+damaged)\b", norm):
        problem = "Product arrived damaged"
    elif re.search(r"\b(?:different\s+product|wrong\s+product|wrong\s+item|different\s+item)\b", norm):
        problem = "Wrong / non-conforming product delivered"
    elif re.search(r"\b(?:never\s+delivered|not\s+delivered|undelivered)\b", norm):
        problem = "Non-delivery of purchased item"
    elif re.search(r"\b(?:charged\s+twice|double\s+charge|debited\s+twice)\b", norm):
        problem = "Duplicate charge / unauthorized transaction"
    elif re.search(r"\b(?:advertised\s+a\s+product\s+with\s+features|does\s+not\s+actually\s+have|fake\s+claim)\b", norm):
        problem = "Misleading advertisement / false specification"
    elif re.search(r"\b(?:warranty|guarantee)\b", norm):
        problem = "Refusal to honour warranty"
    elif re.search(r"\b(?:cheated|scammed|took\s+my\s+money)\b", norm):
        problem = "Cheated / defrauded of money"
    elif re.search(r"\b(?:unpaid\s+salary|salary\s+withheld|wages)\b", norm):
        problem = "Unpaid salary / wages"
    elif re.search(r"\b(?:deposit|security\s+deposit)\b", norm):
        problem = "Security deposit withheld"

    # Opposing action
    opposing_action = None
    if re.search(r"\b(?:seller\s+refuses?|refuses?\s+(?:to\s+)?refund|refuses?\s+(?:a\s+)?refund|refuses?\s+returns?|refused\s+for\s+returns|no\s+refund|won't\s+replace|wont\s+replace|refuses?\s+replacement|denied\s+refund)\b", norm):
        opposing_action = "Seller refused return, replacement, or refund"
    elif re.search(r"\b(?:refuses?\s+to\s+honou?r|refused\s+warranty)\b", norm):
        opposing_action = "Seller/Manufacturer refused warranty claim"
    elif re.search(r"\b(?:landlord\s+refuses?|won't\s+return\s+deposit|withholding\s+deposit)\b", norm):
        opposing_action = "Landlord refused deposit return"
    elif re.search(r"\b(?:fired\s+without\s+notice|terminated)\b", norm):
        opposing_action = "Employer terminated employment without due process"

    # Potential legal issue
    potential_legal_issue = None
    if domain_result.primary_domain == "consumer_protection":
        potential_legal_issue = "Consumer grievance (defective goods, refund dispute, deficiency in service, unfair trade practice)"
    elif domain_result.primary_domain == "criminal_law":
        potential_legal_issue = "Criminal offence (cheating, dishonest inducement, theft)"
    elif domain_result.primary_domain == "cyber_law":
        potential_legal_issue = "Cyber fraud / online financial fraud"
    elif domain_result.primary_domain == "property":
        potential_legal_issue = "Tenancy / property dispute"
    elif domain_result.primary_domain == "labour_employment":
        potential_legal_issue = "Employment dispute (unpaid wages, wrongful termination)"
    elif domain_result.primary_domain == "contract":
        potential_legal_issue = "Breach of contract / non-performance"
    elif domain_result.primary_domain == "banking_finance":
        potential_legal_issue = "Banking deficiency / unauthorized debit"

    return ScenarioFacts(
        actor=actor,
        action=action,
        channel=channel,
        problem=problem,
        opposing_action=opposing_action,
        potential_legal_issue=potential_legal_issue,
    )


def analyze_scenario(query: str) -> ScenarioAnalysis:
    """Analyze a user query deterministically to extract scenario features and legal concepts."""
    trimmed = (query or "").strip()
    if not trimmed:
        return ScenarioAnalysis(
            original_query="",
            is_scenario=False,
            is_legal_query=False,
            domain_routing=route_domain(""),
            facts=ScenarioFacts(),
            matched_concepts=(),
        )

    is_irrelevant = is_irrelevant_query(trimmed)
    if is_irrelevant:
        return ScenarioAnalysis(
            original_query=trimmed,
            is_scenario=False,
            is_legal_query=False,
            domain_routing=route_domain(trimmed),
            facts=ScenarioFacts(),
            matched_concepts=(),
        )

    domain_routing = route_domain(trimmed)
    matched_mappings = extract_matching_concepts(trimmed)
    matched_concept_names = tuple(m.canonical_term for m in matched_mappings)

    is_scenario = is_scenario_query(trimmed)
    facts = extract_scenario_facts(trimmed, domain_routing) if is_scenario else ScenarioFacts()

    return ScenarioAnalysis(
        original_query=trimmed,
        is_scenario=is_scenario,
        is_legal_query=True,
        domain_routing=domain_routing,
        facts=facts,
        matched_concepts=matched_concept_names,
    )
