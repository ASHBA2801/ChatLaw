"""Deterministic document-drafting intent, multi-entity extraction, and progressive clarification."""

from __future__ import annotations

import calendar
import datetime
import re
from dataclasses import dataclass
from typing import Any

from documents.templates import TEMPLATES, get_template
from documents.validation import validate_values

MAX_ROUNDS = 8

# City to Indian State / Union Territory mapping
_CITY_TO_REGION: dict[str, str] = {
    "chennai": "Tamil Nadu",
    "coimbatore": "Tamil Nadu",
    "madurai": "Tamil Nadu",
    "salem": "Tamil Nadu",
    "trichy": "Tamil Nadu",
    "tiruchirappalli": "Tamil Nadu",
    "tirupur": "Tamil Nadu",
    "tirunelveli": "Tamil Nadu",
    "vellore": "Tamil Nadu",
    "erode": "Tamil Nadu",
    "bengaluru": "Karnataka",
    "bangalore": "Karnataka",
    "mysuru": "Karnataka",
    "mysore": "Karnataka",
    "hubballi": "Karnataka",
    "hubli": "Karnataka",
    "mumbai": "Maharashtra",
    "pune": "Maharashtra",
    "nagpur": "Maharashtra",
    "nashik": "Maharashtra",
    "thane": "Maharashtra",
    "delhi": "Delhi",
    "new delhi": "Delhi",
    "hyderabad": "Telangana",
    "secunderabad": "Telangana",
    "warangal": "Telangana",
    "kolkata": "West Bengal",
    "calcutta": "West Bengal",
    "howrah": "West Bengal",
    "ahmedabad": "Gujarat",
    "surat": "Gujarat",
    "vadodara": "Gujarat",
    "rajkot": "Gujarat",
    "jaipur": "Rajasthan",
    "jodhpur": "Rajasthan",
    "udaipur": "Rajasthan",
    "lucknow": "Uttar Pradesh",
    "kanpur": "Uttar Pradesh",
    "noida": "Uttar Pradesh",
    "varanasi": "Uttar Pradesh",
    "chandigarh": "Chandigarh",
    "gurugram": "Haryana",
    "gurgaon": "Haryana",
    "faridabad": "Haryana",
    "patna": "Bihar",
    "bhopal": "Madhya Pradesh",
    "indore": "Madhya Pradesh",
    "thiruvananthapuram": "Kerala",
    "kochi": "Kerala",
    "cochin": "Kerala",
    "kozhikode": "Kerala",
}

_REGION_HINTS = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa", "Gujarat",
    "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Puducherry", "Chandigarh", "Jammu and Kashmir", "Ladakh",
]

# Ordered patterns: specific patterns match before generic ones.
_INTENT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "rental_agreement_tamil_nadu",
        re.compile(
            r"(?:\b(?:tamil\s*nadu\s+(?:rental|lease|tenancy)|rental\s+agreement\s+in\s+tamil\s*nadu"
            r"|rental\s+agreement\s+in\s+(?:chennai|coimbatore|madurai|salem|trichy|tirupur))\b|வாடகை\s+ஒப்பந்தம்)",
            re.I,
        ),
    ),
    (
        "special_power_of_attorney",
        re.compile(r"(?:\b(?:special\s+power\s+of\s+attorney|spa|specific\s+power\s+of\s+attorney)\b|குறிப்பிட்ட\s+அதிகார\s+ஆவணம்)", re.I),
    ),
    (
        "general_power_of_attorney",
        re.compile(r"(?:\b(?:general\s+power\s+of\s+attorney|gpa|power\s+of\s+attorney)\b|பொது\s+அதிகார\s+ஆவணம்)", re.I),
    ),
    (
        "sale_deed",
        re.compile(r"(?:\b(?:sale\s+deed|deed\s+of\s+sale|absolute\s+sale\s+deed)\b|கிரைய\s+பத்திரம்|बिक्री\s*नामा|విక్రయ\s*పత్రం)", re.I),
    ),
    (
        "gift_deed",
        re.compile(r"(?:\b(?:gift\s+deed|deed\s+of\s+gift)\b|தான\s+செட்டில்மென்ட்|தானப்\s+பத்திரம்)", re.I),
    ),
    (
        "release_deed",
        re.compile(r"(?:\b(?:release\s+deed|relinquishment\s+deed|deed\s+of\s+release)\b|விடுதலைப்\s+பத்திரம்)", re.I),
    ),
    (
        "partition_deed",
        re.compile(r"(?:\b(?:partition\s+deed|deed\s+of\s+partition)\b|பாகப்பிரிவினை\s+பத்திரம்)", re.I),
    ),
    (
        "commercial_lease",
        re.compile(r"\b(?:commercial\s+(?:lease|rent(?:al)?|tenancy)\b|office\s+lease\b|shop\s+lease\b|warehouse\s+lease\b)", re.I),
    ),
    (
        "leave_license",
        re.compile(r"\b(?:leave\s+(?:and|&)\s+license(?:\s+agreement)?|leave\s+license)\b", re.I),
    ),
    (
        "founder_agreement",
        re.compile(r"\b(?:co[\s-]?founders?\s+agreement|founders?\s+agreement|shareholders?\s+agreement)\b", re.I),
    ),
    (
        "loan_agreement",
        re.compile(r"\b(?:loan\s+agreement|personal\s+loan\s+agreement|inter[\s-]?corporate\s+loan\s+agreement|money\s+lending\s+agreement)\b", re.I),
    ),
    (
        "payment_demand_notice",
        re.compile(r"\b(?:138\s+(?:ni\s+act\s+)?notice|cheque\s+bounce\s+notice|section\s+138\s+notice|demand\s+notice\s+for\s+cheque)\b", re.I),
    ),
    (
        "eviction_notice",
        re.compile(r"\b(?:eviction\s+notice|notice\s+to\s+vacate|notice\s+to\s+quit|section\s+106\s+notice|tenant\s+eviction\s+notice)\b", re.I),
    ),
    (
        "breach_notice",
        re.compile(r"\b(?:breach\s+notice|notice\s+of\s+breach|cure\s+notice)\b", re.I),
    ),
    (
        "rti_application",
        re.compile(r"\b(?:rti\s+application|right\s+to\s+information(?:\s+act)?\s+application|form\s+a\s+rti|file\s+(?:an?\s+)?rti)\b", re.I),
    ),
    (
        "legal_aid_application",
        re.compile(r"\b(?:legal\s+aid\s+application|nalsa\s+application|free\s+legal\s+services?\s+application|dlsa\s+application)\b", re.I),
    ),
    (
        "name_change_affidavit",
        re.compile(r"\b(?:name\s+change\s+affidavit|affidavit\s+for\s+change\s+of\s+name|change\s+of\s+name\s+affidavit)\b", re.I),
    ),
    (
        "indemnity_bond",
        re.compile(r"\b(?:indemnity\s+bond|bond\s+of\s+indemnity)\b", re.I),
    ),
    ("nda", re.compile(r"\b(?:nda|non[\s-]?disclosure|confidentiality agreement)\b", re.I)),
    ("employment_agreement", re.compile(r"\b(?:employment|employee|employer)\s+agreement\b|\bcontract of employment\b|\bjob\s+contract\b", re.I)),
    ("partnership_agreement", re.compile(r"\bpartnership\s+(?:agreement|deed)\b|\bpartners?\s+agreement\b", re.I)),
    ("sale_agreement", re.compile(r"\bsale\s+(?:of\s+)?(?:goods\s+)?agreement\b|\bagreement\s+(?:to\s+)?sell\b|\bpurchase\s+agreement\b", re.I)),
    ("mou", re.compile(r"\b(?:mou|memorandum of understanding)\b", re.I)),
    ("rent_lease", re.compile(r"(?:\b(?:rent(?:al)?|lease)\s+agreement\b|\btenancy\s+agreement\b|किराया\s*अनुबंध|किरायानामा|అద్దె\s*ఒప్పందం)", re.I)),
    ("service_agreement", re.compile(r"\bservice\s+agreement\b|\bservices?\s+contract\b", re.I)),
    ("affidavit", re.compile(r"\baffidavit\b", re.I)),
    ("authorization_letter", re.compile(r"\bauthorization\s+letter\b|\bletter of authority\b|\bauthorisation\s+letter\b", re.I)),
    ("legal_notice", re.compile(r"\blegal\s+notice\b|\bdemand\s+notice\b", re.I)),
    ("consumer_complaint", re.compile(r"\bconsumer\s+complaint\b", re.I)),
    ("complaint", re.compile(r"\b(?:police\s+)?complaint\b|\bfir\b", re.I)),
]

_UNSUPPORTED = re.compile(
    r"\b(?:will\b|testament\b|divorce\s+petition\b|bail\s+application\b|writ\s+petition\b|probate\b)",
    re.I,
)

_DRAFT_VERB = re.compile(
    r"\b(?:draft|generate|create|prepare|write|make|need|want|help(?:\s+me)?)\b.{0,40}\b(?:agreement|contract|nda|affidavit|notice|letter|mou|complaint|deed|application|bond)\b"
    r"|\b(?:agreement|contract|nda|affidavit|notice|letter|mou|complaint|deed|application|bond)\b.{0,30}\b(?:draft|generate|create|prepare|write|needed|required)\b",
    re.I,
)
_DRAFT_LOOSE = re.compile(r"\b(?:draft|generate|create|prepare|write|make)\b", re.I)


@dataclass(frozen=True)
class DocumentDraftResult:
    action: str  # "pass" | "unsupported" | "clarify" | "ready"
    message: str
    state: dict[str, Any]


def detect_template_id(message: str) -> str | None:
    text = message or ""
    lowered = text.lower()
    # Check Tamil Nadu rental specifically if rental/lease is requested with a TN location or Tamil term
    if re.search(r"\b(?:rent(?:al)?|lease|tenancy)\s+agreement\b|\b(?:flat|house|room|property|premises)\s+(?:for\s+)?rent\b", lowered):
        if re.search(r"\b(?:tamil\s*nadu|chennai|coimbatore|madurai|salem|trichy|tirupur|vellore|erode)\b|வாடகை", lowered):
            return "rental_agreement_tamil_nadu"
    for template_id, pattern in _INTENT_PATTERNS:
        if pattern.search(text):
            return template_id
    return None


def looks_like_document_request(message: str) -> bool:
    text = message or ""
    if _UNSUPPORTED.search(text) and _DRAFT_LOOSE.search(text):
        return True
    matched_id = detect_template_id(text)
    if matched_id:
        if _DRAFT_VERB.search(text):
            return True
        if re.search(r"\b(?:need|want|help(?:\s+me)?|for|in)\b", text, re.I):
            return True
        # Multilingual request cues in Tamil, Hindi, Telugu
        if re.search(r"(?:வேண்டும்|உருவாக்க|செய்ய|தயாரிக்க|ஒப்பந்தம்|பத்திரம்|चाहिए|बनाना|तैयार|काవాలి|చేయండి)", text):
            return True
    return bool(_DRAFT_VERB.search(text))


def _empty_state(template_id: str | None = None, original_query: str = "") -> dict[str, Any]:
    return {
        "mode": "document_drafting",
        "template_id": template_id,
        "values": {"jurisdiction_country": "IN"},
        "asked": [],
        "round": 0,
        "max_rounds": MAX_ROUNDS,
        "original_query": original_query,
        "unsupported": False,
    }


def drafting_state_from_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata or not isinstance(metadata, dict):
        return None
    draft = metadata.get("document_draft")
    if isinstance(draft, dict) and draft.get("mode") == "document_drafting":
        return {
            "mode": "document_drafting",
            "template_id": draft.get("template_id"),
            "values": dict(draft.get("values") or {"jurisdiction_country": "IN"}),
            "asked": list(draft.get("asked") or []),
            "round": int(draft.get("round") or 0),
            "max_rounds": int(draft.get("max_rounds") or MAX_ROUNDS),
            "original_query": draft.get("original_query") or "",
            "unsupported": bool(draft.get("unsupported")),
            "pending_field": draft.get("pending_field"),
            "pending_fields": list(draft.get("pending_fields") or []),
        }
    if metadata.get("kind") in {"document_clarification", "document_ready"} and isinstance(metadata.get("document_draft"), dict):
        return drafting_state_from_metadata({"document_draft": metadata["document_draft"]})
    return None


def _required_fields(template_id: str) -> list[dict[str, Any]]:
    template = get_template(template_id)
    return [field for field in template["fields"] if field.get("requirement") == "required"]


def _missing_required(template_id: str, values: dict[str, Any]) -> list[dict[str, Any]]:
    validation = validate_values(get_template(template_id), values)
    blocking_ids = {issue["field_id"] for issue in validation["blocking"]}
    return [field for field in _required_fields(template_id) if field["id"] in blocking_ids]


def _optional_missing(template_id: str, values: dict[str, Any]) -> list[str]:
    template = get_template(template_id)
    missing = []
    for field in template["fields"]:
        if field.get("requirement") not in {"recommended", "optional"}:
            continue
        raw = values.get(field["id"])
        if raw in (None, "", False):
            missing.append(field["id"])
    return missing


def _extract_region(text: str) -> str | None:
    lowered = text.lower()
    for region in _REGION_HINTS:
        if region.lower() in lowered:
            return region
    for city, region in _CITY_TO_REGION.items():
        if re.search(r"\b" + re.escape(city) + r"\b", lowered):
            return region
    return None


def _extract_city_seat(text: str) -> str | None:
    lowered = text.lower()
    for city in _CITY_TO_REGION:
        if re.search(r"\b" + re.escape(city) + r"\b", lowered):
            return city.title()
    return None


def _parse_currency_amount(val_str: str, multiplier_word: str | None = None) -> float:
    clean = val_str.replace(",", "").strip()
    base = float(clean)
    if multiplier_word:
        m = multiplier_word.lower()
        if "lakh" in m or "lac" in m:
            base *= 100000
        elif "crore" in m:
            base *= 10000000
        elif "k" in m or "thousand" in m:
            base *= 1000
    return base


def extract_entities_from_text(template_id: str, text: str, values: dict[str, Any]) -> None:
    """Intelligently extract parties, financials, dates, and locations from free-form text."""
    if not text:
        return

    # 1. Region & Dispute Seat
    region = _extract_region(text)
    if region and "jurisdiction_region" not in values:
        values["jurisdiction_region"] = region
    city = _extract_city_seat(text)
    if city and "governing_law_seat" not in values:
        values["governing_law_seat"] = city

    # 2. Financials: Rent, Deposit, Consideration, Salary, Loan, Claim
    rent_m = re.search(
        r"\b(?:rent|monthly rent)(?:\s*(?:is|of|amount|:|=))?\s*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d+)?)\s*(k|thousand|lakhs?|lac)?\b",
        text,
        re.I,
    )
    if rent_m and "rent_amount" not in values:
        values["rent_amount"] = _parse_currency_amount(rent_m.group(1), rent_m.group(2))
    elif "monthly_rent" not in values and rent_m:
        values["monthly_rent"] = _parse_currency_amount(rent_m.group(1), rent_m.group(2))

    deposit_m = re.search(
        r"\b(?:security\s+)?deposit(?:\s*(?:is|of|amount|:|=))?\s*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d+)?)\s*(k|thousand|lakhs?|lac|crores?)?\b",
        text,
        re.I,
    )
    if deposit_m and "deposit_amount" not in values:
        values["deposit_amount"] = _parse_currency_amount(deposit_m.group(1), deposit_m.group(2))

    sale_m = re.search(
        r"\b(?:sale\s+)?(?:consideration|price)(?:\s*(?:is|of|amount|:|=))?\s*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d+)?)\s*(k|thousand|lakhs?|lac|crores?)?\b",
        text,
        re.I,
    )
    if sale_m:
        val = _parse_currency_amount(sale_m.group(1), sale_m.group(2))
        if "sale_consideration" not in values:
            values["sale_consideration"] = val
        if "price_amount" not in values:
            values["price_amount"] = val

    salary_m = re.search(
        r"\b(?:salary|ctc|stipend|wages?)(?:\s*(?:is|of|amount|:|=))?\s*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d+)?)\s*(k|thousand|lakhs?|lac|crores?)?\b",
        text,
        re.I,
    )
    if salary_m and "salary_amount" not in values:
        values["salary_amount"] = _parse_currency_amount(salary_m.group(1), salary_m.group(2))

    cheque_m = re.search(
        r"\b(?:cheque\s+(?:amount|of)|amount\s+of)\s*(?:rs\.?|inr|₹)?\s*([\d,]+(?:\.\d+)?)\s*(k|thousand|lakhs?|lac|crores?)?\b",
        text,
        re.I,
    )
    if cheque_m and "cheque_amount" not in values:
        values["cheque_amount"] = _parse_currency_amount(cheque_m.group(1), cheque_m.group(2))

    # 3. Durations
    month_m = re.search(r"\b(?:for\s+)?(\d{1,2})\s*months?\b", text, re.I)
    if month_m:
        months_val = int(month_m.group(1))
        if "duration_months" not in values:
            values["duration_months"] = months_val

    year_m = re.search(r"\b(?:for\s+)?(\d{1,2})\s*years?\b", text, re.I)
    if year_m:
        years_val = int(year_m.group(1))
        if "lease_years" not in values:
            values["lease_years"] = years_val
        if "duration_months" not in values:
            values["duration_months"] = years_val * 12

    notice_m = re.search(r"\b(\d{1,3})\s*days?(?:\s+notice)?\b", text, re.I)
    if notice_m:
        days_val = int(notice_m.group(1))
        if "termination_notice_days" not in values:
            values["termination_notice_days"] = days_val
        if "compliance_days" not in values:
            values["compliance_days"] = days_val

    # 4. Dates
    iso_date_m = re.search(r"\b(20\d\d-\d{2}-\d{2})\b", text)
    if iso_date_m:
        d_val = iso_date_m.group(1)
        for date_k in ["effective_date", "start_date"]:
            if date_k not in values:
                values[date_k] = d_val

    # 5. Parties extraction
    # Landlord
    landlord_m = re.search(
        r"\b(?:landlord|lessor|owner)\s+(?:is|name\s+is|:)?\s*([A-Z][a-zA-Z\s\.\']{2,35}?)(?=[,\.\n]|\band\b|\bfor\b|\bwith\b|\bfrom\b|\btenant\b|\brent\b|\bdeposit\b|$)",
        text,
    )
    if landlord_m and "landlord_name" not in values:
        name = landlord_m.group(1).strip()
        if len(name) > 2 and name.lower() not in {"the", "a", "an", "is"}:
            values["landlord_name"] = name
            values.setdefault("landlord_type", "individual")

    # Tenant
    tenant_m = re.search(
        r"\b(?:tenant|lessee|renter)\s+(?:is|name\s+is|:)?\s*([A-Z][a-zA-Z\s\.\']{2,35}?)(?=[,\.\n]|\band\b|\bfor\b|\bwith\b|\bto\b|\blandlord\b|\brent\b|\bdeposit\b|$)",
        text,
    )
    if tenant_m and "tenant_name" not in values:
        name = tenant_m.group(1).strip()
        if len(name) > 2 and name.lower() not in {"the", "a", "an", "is"}:
            values["tenant_name"] = name
            values.setdefault("tenant_type", "individual")

    # Employer / Employee
    employer_m = re.search(
        r"\b(?:employer|company)\s+(?:is|name\s+is|:)?\s*([A-Z][a-zA-Z0-9\s\.\']{2,35}?)(?=[,\.\n]|\band\b|\bfor\b|\bwith\b|\bemployee\b|\bsalary\b|$)",
        text,
    )
    if employer_m and "employer_name" not in values:
        values["employer_name"] = employer_m.group(1).strip()
        values.setdefault("employer_type", "company")

    employee_m = re.search(
        r"\b(?:employee|candidate)\s+(?:is|name\s+is|:)?\s*([A-Z][a-zA-Z\s\.\']{2,35}?)(?=[,\.\n]|\band\b|\bfor\b|\bwith\b|\bemployer\b|\bsalary\b|$)",
        text,
    )
    if employee_m and "employee_name" not in values:
        values["employee_name"] = employee_m.group(1).strip()
        values.setdefault("employee_type", "individual")

    # Seller / Buyer
    seller_m = re.search(
        r"\b(?:seller|vendor)\s+(?:is|name\s+is|:)?\s*([A-Z][a-zA-Z\s\.\']{2,35}?)(?=[,\.\n]|\band\b|\bfor\b|\bwith\b|\bbuyer\b|\bpurchaser\b|$)",
        text,
    )
    if seller_m:
        s_name = seller_m.group(1).strip()
        if "seller_name" not in values:
            values["seller_name"] = s_name
            values.setdefault("seller_type", "individual")
        if "vendor_name" not in values:
            values["vendor_name"] = s_name
            values.setdefault("vendor_type", "individual")

    buyer_m = re.search(
        r"\b(?:buyer|purchaser)\s+(?:is|name\s+is|:)?\s*([A-Z][a-zA-Z\s\.\']{2,35}?)(?=[,\.\n]|\band\b|\bfor\b|\bwith\b|\bseller\b|\bvendor\b|$)",
        text,
    )
    if buyer_m:
        b_name = buyer_m.group(1).strip()
        if "buyer_name" not in values:
            values["buyer_name"] = b_name
            values.setdefault("buyer_type", "individual")
        if "purchaser_name" not in values:
            values["purchaser_name"] = b_name
            values.setdefault("purchaser_type", "individual")

    # 6. Property use and address
    if re.search(r"\bresidential\b", text, re.I):
        values.setdefault("property_use", "residential")
    elif re.search(r"\bcommercial\b", text, re.I):
        values.setdefault("property_use", "commercial")

    flat_m = re.search(r"\b(?:flat|house|apartment|property|office|shop)\s+(?:in|at)\s+([A-Za-z0-9\s,\.-]+?)(?=[,\.\n]|\brent\b|\bdeposit\b|\bfor\b|$)", text, re.I)
    if flat_m and "property_address" not in values:
        loc = flat_m.group(1).strip()
        if len(loc) > 3:
            values["property_address"] = f"{flat_m.group(0).split()[0].title()} in {loc}"

    # Auto-calculate end_date if effective_date and duration_months are known
    if "effective_date" in values and "duration_months" in values and "end_date" not in values:
        try:
            start = datetime.date.fromisoformat(values["effective_date"])
            d_months = int(values["duration_months"])
            new_month = start.month + d_months
            new_year = start.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1
            max_days = calendar.monthrange(new_year, new_month)[1]
            end_d = min(start.day, max_days)
            end_date = datetime.date(new_year, new_month, end_d) - datetime.timedelta(days=1)
            values["end_date"] = end_date.isoformat()
        except Exception:
            pass


def _question_for_field(field: dict[str, Any], language: str = "en") -> str:
    lang = (language or "en").lower().split("-")[0]
    field_id = field.get("id", "")

    if field_id == "jurisdiction_region":
        if lang == "ta":
            return "இந்த வரைவு எந்த இந்திய மாநிலத்திற்கு பொருந்தும்? (எ.கா. தமிழ்நாடு)"
        if lang == "hi":
            return "यह कानूनी प्रारूप किस भारतीय राज्य या केंद्र शासित प्रदेश के लिए है? (उदा. दिल्ली, उत्तर प्रदेश)"
        if lang == "te":
            return "ఈ చట్టపరమైన డ్రాఫ్ట్ ఏ భారతీయ రాష్ట్రానికి వర్తిస్తుంది? (ఉదా. తెలంగాణ, ఆంధ్రప్రదేశ్)"
        return "Which Indian state or union territory should govern this draft? I will not guess the jurisdiction."

    if "rent" in field_id or "monthly_rent" in field_id:
        if lang == "ta":
            return "மாத வாடகை தொகை எவ்வளவு?"
        if lang == "hi":
            return "मासिक किराया कितना है?"
        if lang == "te":
            return "నెలవారీ అద్దె ఎంత?"

    if "deposit" in field_id:
        if lang == "ta":
            return "பாதுகாப்பு வைப்புத் தொகை (Security Deposit) எவ்வளவு?"
        if lang == "hi":
            return "सुरक्षा जमा राशि (Security Deposit) कितनी है?"
        if lang == "te":
            return "సెక్యూరిటీ డిపాజిట్ మొత్తం ఎంత?"

    help_text = (field.get("help") or "").strip()
    base = f"To draft this document, what is the {field['label'].lower()}?"
    if field["type"] == "select" and field.get("options"):
        options = ", ".join(option["label"] for option in field["options"][:8])
        base = f"Please choose {field['label'].lower()} ({options})."
    if help_text:
        return f"{base} {help_text}"
    return base


def _assign_answer(field: dict[str, Any], message: str, values: dict[str, Any]) -> None:
    text = (message or "").strip()
    if not text:
        return
    field_id = field["id"]
    field_type = field["type"]
    if field_id == "jurisdiction_region":
        region = _extract_region(text)
        if region:
            values[field_id] = region
            return
        for option in field.get("options") or []:
            if option["value"].lower() == text.lower() or option["label"].lower() == text.lower():
                values[field_id] = option["value"]
                return
        values[field_id] = text
        return
    if field_type == "checkbox":
        values[field_id] = text.lower() in {"yes", "y", "true", "mutual", "include", "ok"}
        return
    if field_type == "select":
        for option in field.get("options") or []:
            if option["value"].lower() == text.lower() or option["label"].lower() in text.lower():
                values[field_id] = option["value"]
                return
        values[field_id] = text
        return
    if field_type in {"number", "currency"}:
        match = re.search(r"[\d,.]+", text.replace(",", ""))
        if match:
            try:
                values[field_id] = float(match.group(0)) if "." in match.group(0) else int(match.group(0))
            except ValueError:
                values[field_id] = text
        else:
            values[field_id] = text
        return
    if field_type == "date":
        match = re.search(r"\d{4}-\d{2}-\d{2}", text)
        values[field_id] = match.group(0) if match else text
        return
    values[field_id] = text


def _seed_from_message(template_id: str, message: str, values: dict[str, Any]) -> None:
    extract_entities_from_text(template_id, message, values)
    values.setdefault("jurisdiction_country", "IN")

    # Soft seed purpose-like free text from the original request when present.
    purpose_fields = [
        field
        for field in get_template(template_id)["fields"]
        if field["id"] in {"purpose", "facts", "duties", "business_nature", "goods_description", "scope", "specific_queries"}
    ]
    if purpose_fields and purpose_fields[0]["id"] not in values:
        cleaned = re.sub(r"\s+", " ", message).strip()
        if len(cleaned) > 40:
            values[purpose_fields[0]["id"]] = cleaned[:500]


def _build_clarification_prompt(
    template: dict[str, Any],
    values: dict[str, Any],
    missing: list[dict[str, Any]],
    language: str = "en",
) -> str:
    """Build a conversational, grouped clarification response summarizing understood facts."""
    lang = (language or "en").lower().split("-")[0]
    title = template["title"]

    if lang == "ta":
        lines = [f"உங்களுக்கு **{title}** ஆவணம் தேவை என்பதை அடையாளம் கண்டுள்ளேன்."]
    elif lang == "hi":
        lines = [f"मैंने पहचाना है कि आपको **{title}** की आवश्यकता है।"]
    elif lang == "te":
        lines = [f"మీకు **{title}** అవసరమని గుర్తించాను."]
    else:
        lines = [f"I have identified that you need a **{title}**."]

    # Summarize recorded facts
    recorded_items = []
    field_map = {f["id"]: f["label"] for f in template.get("fields", [])}
    for k, v in values.items():
        if k in {"jurisdiction_country", "document_title"}:
            continue
        if k in field_map and v:
            label = field_map[k]
            if isinstance(v, (int, float)) and ("amount" in k or "rent" in k or "deposit" in k or "salary" in k or "price" in k):
                recorded_items.append(f"• {label}: ₹{v:,.0f}")
            else:
                recorded_items.append(f"• {label}: {v}")

    if recorded_items:
        if lang == "ta":
            lines.append("\n**இதுவரை பதிவு செய்யப்பட்ட விவரங்கள்:**")
        elif lang == "hi":
            lines.append("\n**अब तक दर्ज किए गए विवरण:**")
        elif lang == "te":
            lines.append("\n**ఇప్పటివరకు నమోదు చేయబడిన వివరాలు:**")
        else:
            lines.append("\n**Here is what I have recorded so far:**")
        lines.extend(recorded_items[:12])

    # Numbered missing questions (top 3-4 items)
    if lang == "ta":
        lines.append("\n**உங்கள் சட்ட ஆவண வரைவை முடிக்க, தயவுசெய்து பின்வரும் விவரங்களை கூறவும்:**")
    elif lang == "hi":
        lines.append("\n**आपके कानूनी दस्तावेज़ को पूरा करने के लिए, कृपया निम्नलिखित विवरण प्रदान करें:**")
    elif lang == "te":
        lines.append("\n**మీ చట్టపరమైన డ్రాఫ్ట్‌ను పూర్తి చేయడానికి, దయచేసి క్రింది వివరాలను అందించండి:**")
    else:
        lines.append("\n**To complete your legal draft, please provide:**")

    for i, field in enumerate(missing[:4], 1):
        q = _question_for_field(field, language)
        lines.append(f"{i}. {q}")

    return "\n".join(lines)


def process_document_turn(
    message: str,
    prior: dict[str, Any] | None = None,
    language: str = "en",
) -> DocumentDraftResult:
    """Deterministic document-drafting engine with multi-entity extraction and grouped clarification."""
    prior = prior if isinstance(prior, dict) and prior.get("mode") == "document_drafting" else None

    if prior and prior.get("unsupported"):
        return DocumentDraftResult("pass", "", {})

    if prior is None:
        if not looks_like_document_request(message):
            return DocumentDraftResult("pass", "", {})
        if _UNSUPPORTED.search(message) and not detect_template_id(message):
            state = _empty_state(None, message)
            state["unsupported"] = True
            return DocumentDraftResult(
                "unsupported",
                "ChatLaw can draft from its supported templates (for example NDA, rental agreements, sale deeds, "
                "powers of attorney, employment agreements, partnership deeds, consumer complaints, RTI applications, "
                "legal notices, and affidavits). That document type is not supported yet.",
                state,
            )
        template_id = detect_template_id(message)
        if template_id is None or template_id not in TEMPLATES:
            state = _empty_state(None, message)
            state["unsupported"] = True
            return DocumentDraftResult(
                "unsupported",
                "I recognized a document request, but not a supported template. "
                "Try naming a supported type such as Rental Agreement, Sale Deed, Power of Attorney, "
                "NDA, Employment Agreement, Consumer Complaint, RTI Application, or Legal Notice.",
                state,
            )
        state = _empty_state(template_id, message)
        _seed_from_message(template_id, message, state["values"])
    else:
        state = {
            "mode": "document_drafting",
            "template_id": prior.get("template_id"),
            "values": dict(prior.get("values") or {"jurisdiction_country": "IN"}),
            "asked": list(prior.get("asked") or []),
            "round": int(prior.get("round") or 0),
            "max_rounds": int(prior.get("max_rounds") or MAX_ROUNDS),
            "original_query": prior.get("original_query") or "",
            "unsupported": False,
            "pending_field": prior.get("pending_field"),
            "pending_fields": list(prior.get("pending_fields") or []),
        }
        template_id = state["template_id"]
        if not template_id or template_id not in TEMPLATES:
            return DocumentDraftResult("pass", "", {})

        # Run multi-entity extraction on this turn's message as well
        extract_entities_from_text(template_id, message, state["values"])

        # Also support single-field targeted answers
        pending_id = state.get("pending_field")
        if pending_id:
            fields = {field["id"]: field for field in get_template(template_id)["fields"]}
            field = fields.get(pending_id)
            if field and pending_id not in state["values"]:
                _assign_answer(field, message, state["values"])

    assert template_id
    template = get_template(template_id)
    missing = _missing_required(template_id, state["values"])

    lang = (language or "en").lower().split("-")[0]
    if not missing or state["round"] >= state["max_rounds"]:
        # If still missing jurisdiction after max rounds, keep asking for it.
        still = _missing_required(template_id, state["values"])
        jurisdiction_missing = [field for field in still if field["id"] in {"jurisdiction_region", "jurisdiction_country"}]
        if jurisdiction_missing:
            field = jurisdiction_missing[0]
            state["pending_field"] = field["id"]
            state["pending_fields"] = [field["id"]]
            if field["id"] not in state["asked"]:
                state["asked"].append(field["id"])
            state["round"] = int(state["round"]) + 1
            title = template["title"]
            q_text = _question_for_field(field, language)
            return DocumentDraftResult(
                "clarify",
                f"Drafting a {title}. {q_text}",
                state,
            )
        state["pending_field"] = None
        state["pending_fields"] = []
        state["missing_optional"] = _optional_missing(template_id, state["values"])
        title = template["title"]
        if lang == "ta":
            ready_msg = f"{title} வரைவுக்கு தேவையான விவரங்கள் பெறப்பட்டன. ஆவணத்தை உருவாக்க இப்போது திறக்கப்படுகிறது."
        elif lang == "hi":
            ready_msg = f"{title} प्रारूप के लिए आवश्यक विवरण प्राप्त हो गए हैं। दस्तावेज़ तैयार किया जा रहा है।"
        elif lang == "te":
            ready_msg = f"{title} డ్రాఫ్ట్ కోసం అవసరమైన వివరాలు పొందబడ్డాయి. పత్రం రూపొందించబడుతోంది."
        else:
            ready_msg = f"I have the required details for a {title} draft. Opening your document workspace to generate it now."
        return DocumentDraftResult(
            "ready",
            ready_msg,
            state,
        )

    # Pick the next pending field(s)
    field = missing[0]
    state["pending_field"] = field["id"]
    state["pending_fields"] = [f["id"] for f in missing[:4]]
    if field["id"] not in state["asked"]:
        state["asked"].append(field["id"])
    state["round"] = int(state["round"]) + 1

    # Return grouped conversational clarification
    clarification_msg = _build_clarification_prompt(template, state["values"], missing, language=language)
    return DocumentDraftResult(
        "clarify",
        clarification_msg,
        state,
    )
