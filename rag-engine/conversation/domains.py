"""Legal-domain definitions for the clarification interview.

Domains mirror web/lib/case-intelligence/classify.ts themes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Domain:
    id: str
    keywords: tuple[str, ...]
    slots: tuple[str, ...]
    required_slots: tuple[str, ...]
    slot_values: dict[str, tuple[str, ...]] = field(default_factory=dict)


# Keywords include English plus selected native-script terms (hi/ta/te/kn/ml/mr/bn).
DOMAINS: dict[str, Domain] = {
    "tenancy": Domain(
        id="tenancy",
        keywords=(
            "landlord", "tenant", "tenancy", "rent", "rented", "deposit", "security deposit", "evict",
            "eviction", "lease", "rental", "property", "house owner",
            "किराया", "मकान मालिक", "किरायेदार", "जमा",
            "வாடகை", "வீட்டு உரிமையாளர்", "குத்தகை",
            "అద్దె", "ఇంటి యజమాని",
            "ಬಾಡಿಗೆ", "ಮನೆ ಮಾಲೀಕ",
            "വാടക", "വീട്ടുടമ",
            "भाडे", "घरमालक",
            "ভাড়া", "বাড়িওয়ালা",
        ),
        slots=("party_role", "issue_type", "written_agreement", "location"),
        required_slots=("party_role", "issue_type"),
        slot_values={
            "party_role": ("landlord", "tenant", "owner", "renter", "मकान मालिक", "किरायेदार"),
            "issue_type": (
                "deposit", "security deposit", "rent", "evict", "eviction",
                "repair", "repairs", "notice", "जमा", "किराया",
            ),
            "written_agreement": ("yes", "no", "written", "agreement", "lease", "oral", "verbal"),
        },
    ),
    "employment": Domain(
        id="employment",
        keywords=(
            "salary", "wage", "wages", "employer", "employee", "termination",
            "fired", "dismissed", "workplace", "employment", "job", "pf", "esi",
            "वेतन", "नौकरी", "कर्मचारी", "नियोक्ता",
            "சம்பளம்", "வேலை",
            "జీతం", "ఉద్యోగం",
            "ಸಂಬಳ", "ಉದ್ಯೋಗ",
            "ശമ്പളം", "ജോലി",
            "पगार", "नोकरी",
            "বেতন", "চাকরি",
        ),
        slots=("party_role", "issue_type", "written_contract", "duration"),
        required_slots=("party_role", "issue_type"),
        slot_values={
            "party_role": ("employee", "employer", "worker", "staff", "कर्मचारी", "नियोक्ता"),
            "issue_type": (
                "salary", "wage", "termination", "fired", "dismissed",
                "harassment", "overtime", "pf", "gratuity", "वेतन",
            ),
            "written_contract": ("yes", "no", "written", "contract", "appointment", "oral"),
        },
    ),
    "consumer": Domain(
        id="consumer",
        keywords=(
            "refund", "consumer", "product", "service", "defective", "warranty",
            "complaint", "seller", "purchase", "delivery", "e-commerce",
            "रिफंड", "उपभोक्ता", "खराब",
            "திரும்பப்பெறுதல்", "நுகர்வோர்",
            "వినియోగదారు", "రిఫండ్",
            "ಗ್ರಾಹಕ", "ರಿಫಂಡ್",
            "ഉപഭോക്താവ്",
            "ग्राहक", "परतावा",
            "ভোক্তা", "রিফান্ড",
        ),
        slots=("purchase_type", "issue_type", "seller_contacted", "value"),
        required_slots=("purchase_type", "issue_type"),
        slot_values={
            "purchase_type": ("product", "service", "goods", "item", "online", "offline"),
            "issue_type": (
                "refund", "defect", "defective", "warranty", "delay",
                "poor service", "not delivered", "रिफंड",
            ),
            "seller_contacted": ("yes", "no", "complained", "complaint", "emailed", "called"),
        },
    ),
    "family": Domain(
        id="family",
        keywords=(
            "divorce", "maintenance", "custody", "marriage", "child", "alimony",
            "domestic", "spouse", "wife", "husband", "separation",
            "तलाक", "भरण-पोषण", "हिरासत", "शादी",
            "விவாகரத்து", "பராமரிப்பு",
            "విడాకులు", "పోషణ",
            "ವಿಚ್ಛೇದನ", "ಪೋಷಣೆ",
            "വിവാഹമോചനം", "ജീവനാംശം",
            "घटस्फोट", "निर्वाह",
            "বিবাহবিচ্ছেদ", "ভরণপোষণ",
        ),
        slots=("relationship", "issue_type", "location"),
        required_slots=("relationship", "issue_type"),
        slot_values={
            "relationship": (
                "spouse", "wife", "husband", "partner", "parent", "father",
                "mother", "child", "ex",
            ),
            "issue_type": (
                "divorce", "custody", "maintenance", "alimony", "domestic",
                "separation", "तलाक", "भरण-पोषण",
            ),
        },
    ),
    "contract": Domain(
        id="contract",
        keywords=(
            "agreement", "contract", "breach", "clause", "payment due",
            "non-payment", "obligation", "nda", "mou",
            "अनुबंध", "समझौता", "उल्लंघन",
            "ஒப்பந்தம்", "மீறல்",
            "ఒప్పందం", "ఉల్లంఘన",
            "ಒಪ್ಪಂದ", "ಉಲ್ಲಂಘನೆ",
            "കരാർ", "ലംഘനം",
            "करार", "भंग",
            "চুক্তি", "লঙ্ঘন",
        ),
        slots=("party_role", "issue_type", "written_agreement"),
        required_slots=("party_role", "issue_type"),
        slot_values={
            "party_role": ("party", "buyer", "seller", "client", "vendor", "signatory"),
            "issue_type": (
                "breach", "payment", "non-payment", "terms", "clause",
                "delay", "उल्लंघन",
            ),
            "written_agreement": ("yes", "no", "written", "signed", "oral", "verbal"),
        },
    ),
    "criminal": Domain(
        id="criminal",
        keywords=(
            "arrest", "police", "theft", "assault", "fraud", "crime", "fir",
            "bail", "charge", "accused", "complaint", "offence", "offense",
            "गिरफ्तारी", "पुलिस", "चोरी", "धोखाधड़ी",
            "கைது", "காவல்துறை", "திருட்டு",
            "అరెస్టు", "పోలీసు", "దొంగతనం",
            "ಬಂಧನ", "ಪೊಲೀಸ್", "ಕಳ್ಳತನ",
            "അറസ്റ്റ്", "പോലീസ്", "മോഷണം",
            "अटक", "पोलीस", "चोरी",
            "গ্রেপ্তার", "পুলিশ", "চুরি",
        ),
        slots=("party_role", "issue_type", "stage"),
        required_slots=("party_role", "issue_type"),
        slot_values={
            "party_role": (
                "complainant", "victim", "accused", "accused person",
                "witness", "defendant",
            ),
            "issue_type": (
                "theft", "assault", "fraud", "cheating", "harassment",
                "violence", "other", "चोरी", "धोखाधड़ी",
            ),
            "stage": ("fir", "arrest", "bail", "charge sheet", "court", "investigation"),
        },
    ),
}


def get_domain(domain_id: str | None) -> Domain | None:
    if not domain_id:
        return None
    return DOMAINS.get(str(domain_id).strip().lower())


def all_domains() -> tuple[Domain, ...]:
    return tuple(DOMAINS.values())
