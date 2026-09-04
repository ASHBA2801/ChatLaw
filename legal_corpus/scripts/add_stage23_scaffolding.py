#!/usr/bin/env python3
"""Append Stage 2 (rules/notifications) and Stage 3 (State) catalog scaffolding.

These entries are catalog-only for this phase: no PDF ingest required.
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO / "legal_corpus" / "acts" / "catalog.json"

STAGE2_ENTRIES = [
    {
        "act_id": "CGSTRULES2017",
        "official_title": "Central Goods and Services Tax Rules, 2017",
        "short_title": "CGST Rules, 2017",
        "year": 2017,
        "act_number": "CGST Rules 2017",
        "category": "Tax / GST Rules",
        "domain": "tax",
        "domains": ["tax", "gst"],
        "gst_component": "cgst_rules",
        "sub_domains": ["gst_rules", "returns", "registration"],
        "jurisdiction_level": "CENTRAL",
        "jurisdiction": "India",
        "document_type": "RULE",
        "source_authority": "Central Board of Indirect Taxes and Customs",
        "official_url": "https://cbic-gst.gov.in/",
        "source_type": "ministry_notification",
        "status": "in_force",
        "effective_from": "2017-07-01",
        "parent_act_id": "CGST2017",
        "priority": "tier_2",
        "ingestion_stage": "stage_2",
        "aliases": ["cgst rules", "cgst rules 2017"],
        "ingestion_status": "catalog_only",
    },
    {
        "act_id": "GSTNOTIFICATIONS",
        "official_title": "GST Rate and Exemption Notifications (Central)",
        "short_title": "GST Notifications",
        "year": 2017,
        "act_number": "GST Notifications",
        "category": "Tax / GST Notifications",
        "domain": "tax",
        "domains": ["tax", "gst"],
        "gst_component": "notifications",
        "sub_domains": ["rate_notifications", "exemptions"],
        "jurisdiction_level": "CENTRAL",
        "jurisdiction": "India",
        "document_type": "NOTIFICATION",
        "source_authority": "CBIC / Ministry of Finance",
        "official_url": "https://cbic-gst.gov.in/",
        "source_type": "ministry_notification",
        "status": "in_force",
        "effective_from": "2017-07-01",
        "parent_act_id": "CGST2017",
        "priority": "tier_3",
        "ingestion_stage": "stage_2",
        "aliases": ["gst notifications", "gst rate notifications"],
        "ingestion_status": "catalog_only",
    },
    {
        "act_id": "UTGST2017",
        "official_title": "The Union Territory Goods and Services Tax Act, 2017",
        "short_title": "UTGST Act, 2017",
        "year": 2017,
        "act_number": "14 of 2017",
        "category": "Tax / GST",
        "domain": "tax",
        "domains": ["tax", "gst"],
        "gst_component": "utgst",
        "sub_domains": ["utgst"],
        "jurisdiction_level": "CENTRAL",
        "jurisdiction": "India",
        "document_type": "STATUTE",
        "source_authority": "Parliament of India / Ministry of Finance",
        "official_url": "https://www.indiacode.gov.in/",
        "source_type": "official_gazette",
        "status": "in_force",
        "effective_from": "2017-07-01",
        "priority": "tier_2",
        "ingestion_stage": "stage_2",
        "aliases": ["utgst", "utgst act", "utgst 2017"],
        "ingestion_status": "catalog_only",
    },
    {
        "act_id": "GSTCOMP2017",
        "official_title": "The Goods and Services Tax (Compensation to States) Act, 2017",
        "short_title": "GST Compensation Act, 2017",
        "year": 2017,
        "act_number": "15 of 2017",
        "category": "Tax / GST",
        "domain": "tax",
        "domains": ["tax", "gst"],
        "gst_component": "compensation",
        "sub_domains": ["compensation_cess"],
        "jurisdiction_level": "CENTRAL",
        "jurisdiction": "India",
        "document_type": "STATUTE",
        "source_authority": "Parliament of India / Ministry of Finance",
        "official_url": "https://www.indiacode.gov.in/",
        "source_type": "official_gazette",
        "status": "in_force",
        "effective_from": "2017-07-01",
        "priority": "tier_2",
        "ingestion_stage": "stage_2",
        "aliases": ["gst compensation act", "compensation to states act"],
        "ingestion_status": "catalog_only",
    },
    {
        "act_id": "ECOMRULES2020",
        "official_title": "Consumer Protection (E-Commerce) Rules, 2020",
        "short_title": "E-Commerce Rules, 2020",
        "year": 2020,
        "act_number": "E-Commerce Rules 2020",
        "category": "Consumer / Rules",
        "domain": "consumer_protection",
        "domains": ["consumer_protection"],
        "sub_domains": ["e_commerce", "marketplace"],
        "jurisdiction_level": "CENTRAL",
        "jurisdiction": "India",
        "document_type": "RULE",
        "source_authority": "Ministry of Consumer Affairs",
        "official_url": "https://consumeraffairs.gov.in/",
        "source_type": "ministry_notification",
        "status": "in_force",
        "effective_from": "2020-07-23",
        "parent_act_id": "CPA2019",
        "priority": "tier_2",
        "ingestion_stage": "stage_2",
        "aliases": ["e-commerce rules", "consumer protection e-commerce rules"],
        "ingestion_status": "catalog_only",
    },
    {
        "act_id": "ENVNOTIFICATIONS",
        "official_title": "Environment Protection Rules and Notifications (Central)",
        "short_title": "EPA Rules/Notifications",
        "year": 1986,
        "act_number": "EPA Rules",
        "category": "Environment / Rules",
        "domain": "environment",
        "domains": ["environment"],
        "sub_domains": ["rules", "notifications", "standards"],
        "jurisdiction_level": "CENTRAL",
        "jurisdiction": "India",
        "document_type": "RULE",
        "source_authority": "MoEFCC",
        "official_url": "https://moef.gov.in/",
        "source_type": "ministry_notification",
        "status": "in_force",
        "effective_from": "1986-11-19",
        "parent_act_id": "EPA1986",
        "priority": "tier_3",
        "ingestion_stage": "stage_2",
        "aliases": ["environment protection rules", "epa rules"],
        "ingestion_status": "catalog_only",
    },
]

STAGE3_STATE_ENTRIES = [
    {
        "act_id": "STATE_RENT_PLACEHOLDER",
        "official_title": "State Rent Control / Tenancy Acts (placeholder)",
        "short_title": "State Rent/Tenancy Acts",
        "year": 0,
        "act_number": "STATE",
        "category": "Property / State",
        "domain": "property",
        "domains": ["property"],
        "sub_domains": ["rent_control", "tenancy"],
        "jurisdiction_level": "STATE",
        "jurisdiction": None,
        "state": None,
        "document_type": "STATUTE",
        "source_authority": "State Legislature",
        "official_url": None,
        "source_type": "state_gazette",
        "status": "catalog_scaffold",
        "effective_from": None,
        "priority": "tier_3",
        "ingestion_stage": "stage_3",
        "aliases": ["state rent act", "state tenancy act"],
        "ingestion_status": "catalog_only",
        "notes": "Scaffold only — per-state corpora to be added in Stage 3.",
    },
    {
        "act_id": "STATE_RERA_PLACEHOLDER",
        "official_title": "State RERA Rules (placeholder)",
        "short_title": "State RERA Rules",
        "year": 0,
        "act_number": "STATE",
        "category": "Property / State",
        "domain": "property",
        "domains": ["property"],
        "sub_domains": ["rera"],
        "jurisdiction_level": "STATE",
        "jurisdiction": None,
        "state": None,
        "document_type": "RULE",
        "source_authority": "State Government / RERA Authority",
        "official_url": None,
        "source_type": "state_gazette",
        "status": "catalog_scaffold",
        "effective_from": None,
        "priority": "tier_3",
        "ingestion_stage": "stage_3",
        "aliases": ["state rera rules"],
        "ingestion_status": "catalog_only",
        "notes": "Scaffold only — Central RERA Act may be Stage 1; State rules are Stage 3.",
    },
    {
        "act_id": "STATE_LABOUR_PLACEHOLDER",
        "official_title": "State Labour Rules under Labour Codes (placeholder)",
        "short_title": "State Labour Rules",
        "year": 0,
        "act_number": "STATE",
        "category": "Labour / State",
        "domain": "labour_employment",
        "domains": ["labour_employment"],
        "sub_domains": ["state_rules", "labour_codes"],
        "jurisdiction_level": "STATE",
        "jurisdiction": None,
        "state": None,
        "document_type": "RULE",
        "source_authority": "State Labour Department",
        "official_url": None,
        "source_type": "state_gazette",
        "status": "catalog_scaffold",
        "effective_from": None,
        "priority": "tier_3",
        "ingestion_stage": "stage_3",
        "aliases": ["state labour rules"],
        "ingestion_status": "catalog_only",
        "notes": "Scaffold only — Central labour codes ingested separately; State rules Stage 3.",
    },
    {
        "act_id": "STATE_FAMILY_PLACEHOLDER",
        "official_title": "State Family Court / Personal Law Rules (placeholder)",
        "short_title": "State Family Rules",
        "year": 0,
        "act_number": "STATE",
        "category": "Family / State",
        "domain": "family_law",
        "domains": ["family_law", "personal_law"],
        "sub_domains": ["family_courts", "personal_law_rules"],
        "jurisdiction_level": "STATE",
        "jurisdiction": None,
        "state": None,
        "document_type": "RULE",
        "source_authority": "State High Court / State Government",
        "official_url": None,
        "source_type": "state_gazette",
        "status": "catalog_scaffold",
        "effective_from": None,
        "priority": "tier_3",
        "ingestion_stage": "stage_3",
        "aliases": ["state family rules"],
        "ingestion_status": "catalog_only",
        "notes": "Scaffold only — personal-law statutes remain Central; State rules Stage 3.",
    },
    {
        "act_id": "STATE_LAND_PLACEHOLDER",
        "official_title": "State Land Revenue / Land Reform Acts (placeholder)",
        "short_title": "State Land Acts",
        "year": 0,
        "act_number": "STATE",
        "category": "Property / State",
        "domain": "property",
        "domains": ["property"],
        "sub_domains": ["land_revenue", "land_reforms"],
        "jurisdiction_level": "STATE",
        "jurisdiction": None,
        "state": None,
        "document_type": "STATUTE",
        "source_authority": "State Legislature",
        "official_url": None,
        "source_type": "state_gazette",
        "status": "catalog_scaffold",
        "effective_from": None,
        "priority": "tier_3",
        "ingestion_stage": "stage_3",
        "aliases": ["state land act", "land revenue act"],
        "ingestion_status": "catalog_only",
        "notes": "Scaffold only — State land corpora Stage 3.",
    },
]


def build_by_domain(acts: list[dict]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for act in acts:
        for domain in act.get("domains", [act.get("domain", "general_legal")]):
            if domain and act["act_id"] not in index[domain]:
                index[domain].append(act["act_id"])
    return dict(sorted(index.items()))


def main() -> int:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    acts = list(data.get("acts", []))
    existing = {a["act_id"] for a in acts}
    added = []
    for entry in STAGE2_ENTRIES + STAGE3_STATE_ENTRIES:
        if entry["act_id"] not in existing:
            acts.append(entry)
            existing.add(entry["act_id"])
            added.append(entry["act_id"])

    data["version"] = "2.1"
    data["last_updated"] = date.today().isoformat()
    data["acts"] = acts
    data["by_domain"] = build_by_domain(acts)
    data["stage_notes"] = {
        "stage_2": "Rules/notifications/circulars catalogued; mass ingest deferred pending cost gate.",
        "stage_3": "State corpora scaffolding only (jurisdiction_level=STATE, empty corpora).",
    }
    CATALOG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"added": added, "total_acts": len(acts)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
