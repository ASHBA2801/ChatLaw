"""Offices and courts a complaint can go to, and which ones a matter calls for.

Everything here is deterministic. The model's reading of the facts (see
analysis.py) only fills in flags and a severity; the recommendation of where
to file is always made by these rules so that legal prerequisites (CBI
jurisdiction, Article 32 scope, CPGRAMS-only PMO grievances) are never skipped.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Sequence

SEVERITIES = ("low", "moderate", "serious", "grave")

FLAG_KEYS = (
    "cognizable_offence",   # facts describe a crime the police must register
    "public_servant",       # a government official is involved
    "central_government",   # the official/body is Central Government, a central PSU or bank
    "corruption",           # bribe demand or corrupt practice
    "police_inaction",      # police refused or failed to act
    "women",                # offence against a woman / domestic violence / dowry
    "child",                # victim is a child
    "cyber",                # online fraud, hacking, cyber harassment
    "custodial",            # custodial violence / illegal detention / police excess
    "threat_to_life",       # ongoing threat to life or safety
    "inter_state",          # facts span more than one State
    "land_revenue",         # land, encroachment, revenue records, certificates
    "consumer",             # defective goods or deficient service
    "family",               # marriage, maintenance, custody, domestic matters
    "civil_dispute",        # money, contract or property dispute between private parties
    "public_service",       # civic service or welfare delivery grievance
    "fundamental_rights",   # State action violating Part III rights
)


@dataclass(frozen=True)
class FilingKind:
    id: str
    forum: str            # "authority" | "court"
    label: str
    short_label: str
    description: str
    channel: str          # "email" | "portal" | "in_person" | "efiling"
    portal_url: str | None = None
    portal_label: str | None = None
    helpline: str | None = None
    court_subject: str | None = None  # civil | criminal | family | consumer | writ
    caveat: str | None = None
    lookup: str = "contacts"          # "nearby_police" | "nearby_court" | "contacts" | "curated"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


KINDS: dict[str, FilingKind] = {kind.id: kind for kind in (
    FilingKind(
        "police_station", "authority", "Local police station", "Police station",
        "Complaint to the Station House Officer asking for an FIR under Section 173 BNSS.",
        "email", lookup="nearby_police",
        caveat="A Zero FIR can be registered at any police station; it is then transferred to the station "
               "with jurisdiction (Section 173(1) BNSS).",
    ),
    FilingKind(
        "police_superior", "authority", "Commissioner of Police / Superintendent of Police", "SP / Commissioner",
        "Complaint to the district SP or city Commissioner, used when the police station does not act "
        "(Section 173(4) BNSS).", "email",
    ),
    FilingKind(
        "collector", "authority", "District Collector", "Collector",
        "Petition to the District Collector for land, revenue, certificate and public-service grievances.",
        "email",
    ),
    FilingKind(
        "vigilance", "authority", "State Vigilance / Anti-Corruption (DVAC / ACB)", "Vigilance (DVAC)",
        "Complaint about a bribe demand or corruption by a State Government official.", "email",
        caveat="State vigilance agencies act on complaints against State Government employees. "
               "Central Government officials are dealt with by the CBI or the Central Vigilance Commission.",
    ),
    FilingKind(
        "cm_cell", "authority", "Chief Minister's Special Cell", "CM cell",
        "Petition to the Chief Minister's grievance cell when district offices have not acted.", "email",
    ),
    FilingKind(
        "cbi", "authority", "Central Bureau of Investigation", "CBI",
        "Complaint about corruption or serious fraud by Central Government / PSU / bank officials, or "
        "offences spread across States.", "in_person",
        portal_url="https://cbi.gov.in/cbi-network", portal_label="Find the nearest CBI branch",
        caveat="The CBI investigates offences involving Central Government employees, central PSUs and "
               "banks, inter-State or international crime, or cases a court or the State Government "
               "refers to it. Other complaints go to the State police.",
        lookup="curated",
    ),
    FilingKind(
        "pmo", "authority", "Prime Minister's Office (CPGRAMS)", "PMO",
        "Grievance to the PMO, lodged on the CPGRAMS portal after other authorities have not resolved it.",
        "portal", portal_url="https://pgportal.gov.in/", portal_label="Open CPGRAMS",
        caveat="CPGRAMS states that grievances sent by email are not entertained; lodge this on the portal "
               "and attach the PDF.",
        lookup="curated",
    ),
    FilingKind(
        "women_commission", "authority", "Commission for Women (NCW / State)", "Women's commission",
        "Complaint about domestic violence, dowry, harassment or police inaction in a matter concerning a woman.",
        "email", portal_url="https://ncwapps.nic.in/onlinecomplaintsv2/frmPubRegistration.aspx",
        portal_label="NCW online complaint", helpline="14490", lookup="curated",
    ),
    FilingKind(
        "human_rights", "authority", "Human Rights Commission (NHRC / SHRC)", "Human rights",
        "Complaint about custodial violence, illegal detention or other rights violations by public servants.",
        "email", portal_url="https://www.hrcnet.nic.in/HRCNet/public/webcomplaint.aspx",
        portal_label="NHRC online complaint", helpline="14433", lookup="curated",
        caveat="The Commission does not take up matters older than one year or pending before a court "
               "(Section 36, Protection of Human Rights Act, 1993).",
    ),
    FilingKind(
        "cyber_crime", "authority", "Cyber Crime Police / National Cyber Crime Portal", "Cyber crime",
        "Complaint about online financial fraud, hacking, identity theft or cyber harassment.",
        "portal", portal_url="https://cybercrime.gov.in/", portal_label="Report on cybercrime.gov.in",
        helpline="1930",
        caveat="If money was lost, call 1930 at once — banks can freeze the funds only if reported quickly.",
    ),
    FilingKind(
        "magistrate", "court", "Judicial Magistrate (criminal)", "Magistrate",
        "Private complaint (Section 223 BNSS) with a request to direct the police to investigate "
        "(Section 175(3) BNSS).", "efiling", portal_url="https://efiling.ecourts.gov.in/",
        portal_label="eCourts e-filing", court_subject="criminal", lookup="nearby_court",
        caveat="Before asking the Magistrate to order an investigation you must have approached the police "
               "station and the SP (Section 173(4) BNSS), and the application needs an affidavit.",
    ),
    FilingKind(
        "civil_court", "court", "District civil court", "Civil court",
        "Plaint for money, property, injunction or declaration (Order VII Rule 1 CPC).",
        "efiling", portal_url="https://efiling.ecourts.gov.in/", portal_label="eCourts e-filing",
        court_subject="civil", lookup="nearby_court",
    ),
    FilingKind(
        "family_court", "court", "Family court", "Family court",
        "Petition for maintenance, custody, divorce or protection orders.", "efiling",
        portal_url="https://efiling.ecourts.gov.in/", portal_label="eCourts e-filing",
        court_subject="family", lookup="nearby_court",
    ),
    FilingKind(
        "consumer_commission", "court", "District Consumer Commission", "Consumer commission",
        "Consumer complaint for defective goods or deficient service (Section 35, Consumer Protection Act, 2019).",
        "efiling", portal_url="https://edaakhil.nic.in/", portal_label="Open e-Daakhil",
        court_subject="consumer", lookup="nearby_court",
        caveat="The complaint must be filed within two years of the cause of action (Section 69).",
    ),
    FilingKind(
        "high_court", "court", "High Court (Article 226)", "High Court",
        "Writ petition against action or inaction of the State or its officers.", "efiling",
        portal_url="https://efiling.ecourts.gov.in/", portal_label="eCourts e-filing",
        court_subject="writ", lookup="curated",
        caveat="Writ petitions are usually filed after a representation to the authority, and through an advocate.",
    ),
    FilingKind(
        "supreme_court", "court", "Supreme Court of India (Article 32)", "Supreme Court",
        "Writ petition for the enforcement of fundamental rights.", "efiling",
        portal_url="https://efiling.sci.gov.in/", portal_label="Supreme Court e-filing",
        court_subject="writ", lookup="curated",
        caveat="Article 32 is only for violations of fundamental rights; the Court ordinarily sends "
               "petitioners to the High Court first. Filing is through an Advocate-on-Record.",
    ),
)}

AUTHORITY_KINDS = tuple(k for k, v in KINDS.items() if v.forum == "authority")
COURT_KINDS = tuple(k for k, v in KINDS.items() if v.forum == "court")

# State / UT → High Court with jurisdiction and its principal seat.
HIGH_COURTS: dict[str, tuple[str, str]] = {
    "andhra pradesh": ("High Court of Andhra Pradesh", "Amaravati"),
    "arunachal pradesh": ("Gauhati High Court (Itanagar Bench)", "Guwahati"),
    "assam": ("Gauhati High Court", "Guwahati"),
    "bihar": ("Patna High Court", "Patna"),
    "chhattisgarh": ("High Court of Chhattisgarh", "Bilaspur"),
    "goa": ("Bombay High Court (Goa Bench)", "Panaji"),
    "gujarat": ("High Court of Gujarat", "Ahmedabad"),
    "haryana": ("High Court of Punjab and Haryana", "Chandigarh"),
    "himachal pradesh": ("High Court of Himachal Pradesh", "Shimla"),
    "jharkhand": ("Jharkhand High Court", "Ranchi"),
    "karnataka": ("High Court of Karnataka", "Bengaluru"),
    "kerala": ("High Court of Kerala", "Kochi"),
    "madhya pradesh": ("High Court of Madhya Pradesh", "Jabalpur"),
    "maharashtra": ("Bombay High Court", "Mumbai"),
    "manipur": ("High Court of Manipur", "Imphal"),
    "meghalaya": ("High Court of Meghalaya", "Shillong"),
    "mizoram": ("Gauhati High Court (Aizawl Bench)", "Guwahati"),
    "nagaland": ("Gauhati High Court (Kohima Bench)", "Guwahati"),
    "odisha": ("Orissa High Court", "Cuttack"),
    "punjab": ("High Court of Punjab and Haryana", "Chandigarh"),
    "rajasthan": ("Rajasthan High Court", "Jodhpur"),
    "sikkim": ("High Court of Sikkim", "Gangtok"),
    "tamil nadu": ("Madras High Court", "Chennai"),
    "telangana": ("High Court for the State of Telangana", "Hyderabad"),
    "tripura": ("High Court of Tripura", "Agartala"),
    "uttar pradesh": ("Allahabad High Court", "Prayagraj"),
    "uttarakhand": ("High Court of Uttarakhand", "Nainital"),
    "west bengal": ("Calcutta High Court", "Kolkata"),
    "andaman and nicobar islands": ("Calcutta High Court (Port Blair Circuit Bench)", "Kolkata"),
    "chandigarh": ("High Court of Punjab and Haryana", "Chandigarh"),
    "dadra and nagar haveli and daman and diu": ("Bombay High Court", "Mumbai"),
    "delhi": ("High Court of Delhi", "New Delhi"),
    "jammu and kashmir": ("High Court of Jammu & Kashmir and Ladakh", "Srinagar / Jammu"),
    "ladakh": ("High Court of Jammu & Kashmir and Ladakh", "Srinagar / Jammu"),
    "lakshadweep": ("High Court of Kerala", "Kochi"),
    "puducherry": ("Madras High Court", "Chennai"),
}
_STATE_ALIASES = {
    "orissa": "odisha", "pondicherry": "puducherry", "nct of delhi": "delhi", "new delhi": "delhi",
    "j&k": "jammu and kashmir", "jammu & kashmir": "jammu and kashmir", "tn": "tamil nadu",
    "andaman & nicobar islands": "andaman and nicobar islands", "up": "uttar pradesh",
}


def normalize_state(state: str | None) -> str | None:
    if not state:
        return None
    key = re.sub(r"\s+", " ", state.strip().lower().replace("&", "and")).strip()
    key = _STATE_ALIASES.get(state.strip().lower(), _STATE_ALIASES.get(key, key))
    return key if key in HIGH_COURTS else None


def high_court_for(state: str | None) -> tuple[str, str] | None:
    key = normalize_state(state)
    return HIGH_COURTS.get(key) if key else None


# ------------------------------------------------------------------- rules

@dataclass(frozen=True)
class Recommendation:
    kind: str
    priority: str   # "primary" | "escalation" | "optional"
    reason: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class RuleReading:
    """What the deterministic keyword pass sees in the facts."""
    category: str
    severity: str
    flags: dict[str, bool] = field(default_factory=dict)
    court_subjects: list[str] = field(default_factory=list)


_PATTERNS: dict[str, str] = {
    "corruption": r"\bbribe|\bbribery|\bcorrupt|kickback|illegal gratification|lanch|demanded (?:money|cash|payment) to\b|"
                  r"asked for money to (?:process|clear|approve|issue)",
    "police_inaction": r"police (?:refused|did not|didn't|are not|is not|declined|won't|will not)|"
                       r"(?:refused|refusing|not willing) to (?:register|file|lodge|take) (?:an |my |the )?(?:fir|complaint)|"
                       r"fir (?:was )?not (?:registered|filed)|no (?:fir|action) (?:was )?(?:taken|registered)",
    "women": r"\bdowry|domestic violence|my husband|in-laws|mother-in-law|harass(?:ed|ment) (?:me|her) as a woman|"
             r"\bstalk|molest|sexual(?:ly)? (?:harass|assault|abuse)|\brape|outrag(?:e|ing) (?:the )?modesty|eve.?teas",
    "child": r"\bchild\b|\bminor\b|\bpocso\b|my (?:son|daughter) (?:aged|is) \d|\bschool ?girl|\bschool ?boy",
    "cyber": r"\bupi\b|\botp\b|online fraud|cyber|hack(?:ed|ing)|phishing|fake (?:profile|account|website|app)|"
             r"sextort|morphed|instagram|whatsapp|facebook|telegram|loan app|kyc",
    "custodial": r"custod(?:y|ial)|lock-?up|police (?:beat|assaulted|tortured|detained)|illegal(?:ly)? detain|"
                 r"picked up by (?:the )?police",
    "threat_to_life": r"threat(?:en(?:ed|ing))? to kill|kill (?:me|us|my)|threat to (?:my |our )?life|"
                      r"life (?:is )?in danger|death threat",
    "inter_state": r"inter-?state|another state|other states|across states",
    "land_revenue": r"encroach|land ?grab|\bpatta\b|survey (?:no|number)|revenue record|\bchitta\b|\badangal\b|"
                    r"mutation|land records|boundary|\bcertificate\b|\bkhata\b|\bjamabandi\b",
    "consumer": r"refund|defective|warranty|guarantee|deficien(?:t|cy) (?:in )?service|e-?commerce|"
                r"(?:flipkart|amazon|swiggy|zomato)|courier|airline|insurance claim|builder|flat (?:possession|handover)",
    "family": r"divorce|maintenance|custody of (?:my|our|the) (?:child|son|daughter)|alimony|marriage|"
              r"separated|restitution|guardianship",
    "civil_dispute": r"(?:did not|didn't|refus\w* to) (?:repay|return|pay)|loan (?:not )?repaid|agreement|"
                     r"contract|breach|security deposit|rent|tenant|landlord|partition|recovery of",
    "public_service": r"ration|pension|water supply|electricity (?:connection|board)|road|street ?light|drainage|"
                      r"garbage|scholarship|welfare scheme|hospital|government school|bus service",
    "central_government": r"central government|union government|\brailway|\bbank\b|income.?tax|\bgst\b|customs|"
                          r"post office|\bepfo\b|passport|\bpsu\b|\bbsnl\b|\bonGC\b|\bLIC\b|\bcbdt\b|central excise",
    "public_servant": r"officer|official|\bvao\b|tahsildar|tehsildar|\bclerk\b|inspector|constable|"
                      r"sub-?inspector|\bsho\b|\bsi\b|panchayat (?:secretary|president)|registrar|\bbdo\b|"
                      r"government (?:employee|servant|staff)|municipal|corporation (?:staff|officer)|revenue",
    "fundamental_rights": r"fundamental right|article (?:14|19|21|32)|right to life|freedom of|discriminat",
}
_COGNIZABLE = (r"theft|stole|stolen|robbe|snatch|cheat|fraud|forg|assault|attack|beat(?:en)?\b|hurt|injur|"
               r"murder|kill|kidnap|abduct|missing|threat|extort|blackmail|rape|molest|dowry|"
               r"criminal breach|misappropriat|trespass|arson|set fire|acid|stalk|domestic violence")
_GRAVE = r"murder|kill(?:ed)?\b|rape|kidnap|abduct|acid attack|custodial death|died in custody|human trafficking"

_CATEGORY_ORDER = (
    ("custodial", "Police excess / custodial violence"),
    ("corruption", "Corruption by a public servant"),
    ("cyber", "Cyber crime"),
    ("women", "Offence against a woman"),
    ("child", "Offence against a child"),
    ("police_inaction", "Police inaction"),
    ("cognizable_offence", "Criminal offence"),
    ("family", "Family matter"),
    ("consumer", "Consumer dispute"),
    ("land_revenue", "Land / revenue grievance"),
    ("civil_dispute", "Civil dispute"),
    ("public_service", "Public service grievance"),
)


def read_facts(text: str) -> RuleReading:
    """Keyword reading of the facts. Conservative: it only raises flags the words support."""
    lowered = (text or "").lower()
    flags = {key: False for key in FLAG_KEYS}
    for key, pattern in _PATTERNS.items():
        flags[key] = bool(re.search(pattern, lowered, flags=re.IGNORECASE))
    flags["cognizable_offence"] = bool(re.search(_COGNIZABLE, lowered)) or flags["corruption"] or flags["custodial"]
    if flags["corruption"] or flags["custodial"] or flags["police_inaction"]:
        flags["public_servant"] = True
    if flags["central_government"] and not (flags["public_servant"] or flags["corruption"]):
        # "my bank" in a consumer complaint does not make a public servant a party
        flags["central_government"] = False
    category = next((label for key, label in _CATEGORY_ORDER if flags.get(key)), "General grievance")
    severity = "low"
    if flags["cognizable_offence"]:
        severity = "moderate"
    if any(flags[k] for k in ("corruption", "police_inaction", "women", "child", "cyber", "threat_to_life")):
        severity = "serious"
    if (flags["custodial"] or re.search(_GRAVE, lowered)
            or (flags["threat_to_life"] and flags["cognizable_offence"])
            or (flags["corruption"] and flags["central_government"])):
        severity = "grave"
    return RuleReading(category=category, severity=severity, flags=flags,
                       court_subjects=court_subjects_for(flags))


def court_subjects_for(flags: dict[str, bool]) -> list[str]:
    subjects: list[str] = []
    if flags.get("cognizable_offence") or flags.get("police_inaction"):
        subjects.append("criminal")
    if flags.get("civil_dispute") or flags.get("land_revenue"):
        subjects.append("civil")
    if flags.get("family"):
        subjects.append("family")
    if flags.get("consumer"):
        subjects.append("consumer")
    if flags.get("public_servant") or flags.get("custodial") or flags.get("fundamental_rights") \
            or flags.get("police_inaction") or flags.get("public_service"):
        subjects.append("writ")
    return subjects or ["civil"]


def merge_severity(*values: str | None) -> str:
    ranks = [SEVERITIES.index(v) for v in values if v in SEVERITIES]
    return SEVERITIES[max(ranks)] if ranks else "moderate"


def recommend(flags: dict[str, bool], severity: str, court_subjects: Sequence[str] = ()) -> list[Recommendation]:
    """Ordered recommendations of where to file. Every kind is still available to the user."""
    f = {key: bool(flags.get(key)) for key in FLAG_KEYS}
    recs: dict[str, Recommendation] = {}

    def add(kind: str, priority: str, reason: str) -> None:
        current = recs.get(kind)
        order = {"primary": 0, "escalation": 1, "optional": 2}
        if current is None or order[priority] < order[current.priority]:
            recs[kind] = Recommendation(kind, priority, reason)

    if f["police_inaction"]:
        add("police_superior", "primary", "The police station has not acted; Section 173(4) BNSS lets you send "
                                          "the complaint to the SP / Commissioner.")
        add("magistrate", "escalation", "After approaching the SP, the Magistrate can direct an investigation "
                                        "under Section 175(3) BNSS.")
        add("cm_cell", "optional", "The CM cell can call for a report from the police.")
    if f["cyber"]:
        add("cyber_crime", "primary", "Online fraud and cyber offences are reported on the National Cyber Crime "
                                      "Portal and to the cyber crime police.")
    if f["corruption"] and f["central_government"]:
        add("cbi", "primary", "Corruption by Central Government / PSU / bank officials is investigated by the CBI.")
        add("pmo", "optional", "A grievance can also be lodged with the PMO on CPGRAMS.")
    elif f["corruption"]:
        add("vigilance", "primary", "Bribe demands by State Government officials are handled by the State "
                                    "vigilance / anti-corruption agency.")
        add("cm_cell", "escalation", "Escalate to the CM cell if the vigilance agency does not act.")
    if f["women"]:
        add("women_commission", "primary" if f["police_inaction"] else "escalation",
            "The Commission for Women can call for a report from the police and assist the complainant.")
    if f["child"]:
        add("police_station", "primary", "Offences against children must be reported to the police "
                                         "(Special Juvenile Police Unit) — reporting is mandatory under POCSO.")
    if f["custodial"]:
        add("human_rights", "primary", "Custodial violence and illegal detention are within the Human Rights "
                                       "Commission's remit.")
        add("high_court", "escalation", "The High Court can be moved under Article 226 (including habeas corpus).")
        add("police_superior", "escalation", "Report the officers' conduct to the SP / Commissioner.")
    if f["threat_to_life"]:
        add("police_station", "primary", "A threat to life must be reported to the police at once (dial 112 in "
                                         "an emergency).")
        add("police_superior", "escalation", "Ask the SP / Commissioner for protection if the station does not act.")
    # Ordinary crimes go to the police first. Corruption and police excess go to the
    # bodies that oversee officials instead (handled above).
    if f["cognizable_offence"] and not (f["police_inaction"] or f["corruption"] or f["custodial"]):
        add("police_station", "primary", "The facts describe an offence the police must register as an FIR.")
        add("police_superior", "escalation", "If the police station does not register the FIR within a reasonable "
                                             "time, write to the SP / Commissioner under Section 173(4) BNSS.")
    if f["land_revenue"] or f["public_service"]:
        add("collector", "primary", "Land, revenue and public-service grievances are handled by the district "
                                    "administration.")
        add("cm_cell", "escalation", "Escalate to the CM cell if the Collector's office does not respond.")
        add("pmo", "optional", "Unresolved grievances can be lodged on CPGRAMS (PMO).")
    if f["consumer"]:
        add("consumer_commission", "primary", "Defective goods and deficient services are decided by the District "
                                              "Consumer Commission.")
    if f["family"]:
        add("family_court", "primary", "Maintenance, custody and matrimonial reliefs are decided by the Family Court.")
    if f["civil_dispute"] and not f["consumer"]:
        add("civil_court", "primary" if not f["cognizable_offence"] else "optional",
            "Recovery of money, property and contract disputes are decided by the civil court.")
    if f["public_servant"] or f["fundamental_rights"] or f["police_inaction"]:
        add("high_court", "escalation" if severity in ("serious", "grave") else "optional",
            "Persistent inaction or illegal action by the State can be challenged in a writ petition under "
            "Article 226.")
    if f["fundamental_rights"] and severity == "grave":
        add("supreme_court", "optional", "Article 32 is available for grave violations of fundamental rights.")
    if severity == "grave" and f["inter_state"]:
        add("cbi", "escalation", "Offences spread across States may be taken up by the CBI on a State "
                                 "reference or court order.")
    if severity in ("serious", "grave") and f["public_servant"]:
        add("cm_cell", "escalation", "The CM cell can intervene when officials do not act.")
    if not recs:
        add("collector", "primary", "A general grievance is usually addressed to the district administration first.")
        add("cm_cell", "escalation", "Escalate to the CM cell if the district office does not respond.")
        add("pmo", "optional", "Unresolved grievances can be lodged on CPGRAMS (PMO).")
    for subject in court_subjects:
        kind = {"criminal": "magistrate", "civil": "civil_court", "family": "family_court",
                "consumer": "consumer_commission", "writ": "high_court"}.get(subject)
        if kind and kind not in recs:
            add(kind, "optional", f"The matter has a {subject} side that a court can decide.")
    order = {"primary": 0, "escalation": 1, "optional": 2}
    # Stable sort: within a priority, the rule that matched first (the more specific one) leads.
    return sorted(recs.values(), key=lambda r: order[r.priority])


def kinds_payload(kinds: Iterable[str] | None = None) -> list[dict[str, Any]]:
    keys = list(kinds) if kinds is not None else list(KINDS)
    return [KINDS[key].as_dict() for key in keys if key in KINDS]
