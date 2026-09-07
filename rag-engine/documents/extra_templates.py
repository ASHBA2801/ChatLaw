"""Additional agreement templates (employment, partnership, sale, MoU)."""

from __future__ import annotations

from .constants import DISPUTE_OPTIONS, INDIA_REGIONS, PARTY_TYPE_OPTIONS
from .types import FieldSpec, TemplateSpec

REGION_OPTIONS = [{"value": region, "label": region} for region in INDIA_REGIONS]


def _field(
    field_id: str,
    label: str,
    placeholder_label: str,
    field_type: str,
    requirement: str,
    step: str,
    help_text: str = "",
    **extra,
) -> FieldSpec:
    spec: FieldSpec = {
        "id": field_id,
        "label": label,
        "placeholder_label": placeholder_label,
        "type": field_type,  # type: ignore[typeddict-item]
        "requirement": requirement,  # type: ignore[typeddict-item]
        "step": step,
        "help": help_text,
    }
    spec.update(extra)  # type: ignore[typeddict-item]
    return spec


def _jurisdiction_fields(step: str = "jurisdiction") -> list[FieldSpec]:
    return [
        _field(
            "jurisdiction_country",
            "Jurisdiction",
            "JURISDICTION",
            "select",
            "required",
            step,
            "The generated draft retains this jurisdiction. Laws vary by place.",
            options=[{"value": "IN", "label": "India"}],
        ),
        _field(
            "jurisdiction_region",
            "State / Union Territory",
            "STATE OR UNION TERRITORY",
            "select",
            "required",
            step,
            "Required because contract and property rules can vary within India.",
            options=REGION_OPTIONS,
        ),
        _field(
            "governing_law_seat",
            "Seat / place for disputes",
            "DISPUTE SEAT",
            "text",
            "recommended",
            step,
            "City or district where disputes are to be heard, if the parties have agreed one.",
        ),
    ]

EMPLOYMENT_AGREEMENT_TEMPLATE: TemplateSpec = {
    "id": "employment_agreement",
    "category": "agreement",
    "title": "Employment Agreement",
    "description": "An employment contract draft between an employer and an employee in India based on Startup India model format.",
    "document_type": "Employment Agreement",
    "jurisdiction_country": "IN",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "Employment contracts across Indian establishments under the Industrial Relations Code / Contract Act.",
    "source": {
        "authority": "Startup India Model Contracts & Ministry of Labour and Employment",
        "url": "https://www.startupindia.gov.in/content/sih/en/model-contracts.html",
        "document_name": "Model Employment Agreement",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on appropriate non-judicial stamp paper as prescribed under State Stamp Act",
    ],
    "legal_query": "employment agreement contract of employment wages notice termination India labour",
    "parties": [
        {"id": "employer", "role": "Employer", "name_field": "employer_name",
         "type_field": "employer_type", "address_field": "employer_address"},
        {"id": "employee", "role": "Employee", "name_field": "employee_name",
         "type_field": "employee_type", "address_field": "employee_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the agreement you need.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Where employment is intended to operate.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Identify the employer and the employee.",
         "field_ids": ["employer_name", "employer_type", "employer_address", "employee_name", "employee_type", "employee_address"]},
        {"id": "role", "title": "Role and start", "description": "Job title, duties, and start date.",
         "field_ids": ["job_title", "duties", "place_of_work", "effective_date"]},
        {"id": "financial", "title": "Compensation", "description": "Record pay only if agreed.",
         "field_ids": ["salary_amount", "salary_currency", "salary_frequency", "probation_months"]},
        {"id": "duration", "title": "Hours and ending", "description": "Working hours and how employment may end.",
         "field_ids": ["working_hours", "termination_notice_days", "include_confidentiality"]},
        {"id": "conditions", "title": "Other terms", "description": "Disputes and extra agreed terms.",
         "field_ids": ["dispute_resolution", "special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("employer_name", "Employer name", "EMPLOYER NAME", "text", "required", "parties"),
        _field("employer_type", "Employer type", "EMPLOYER TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("employer_address", "Employer address", "EMPLOYER ADDRESS", "textarea", "required", "parties"),
        _field("employee_name", "Employee name", "EMPLOYEE NAME", "text", "required", "parties"),
        _field("employee_type", "Employee type", "EMPLOYEE TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("employee_address", "Employee address", "EMPLOYEE ADDRESS", "textarea", "required", "parties"),
        _field("job_title", "Job title", "JOB TITLE", "text", "required", "role"),
        _field("duties", "Duties / role description", "DUTIES", "textarea", "required", "role"),
        _field("place_of_work", "Place of work", "PLACE OF WORK", "text", "recommended", "role"),
        _field("effective_date", "Start date", "START DATE", "date", "required", "role"),
        _field("salary_amount", "Salary / wages", "SALARY AMOUNT", "currency", "recommended", "financial",
               "Leave blank if pay is still to be agreed.", min=0),
        _field("salary_currency", "Currency", "CURRENCY", "select", "optional", "financial",
               options=[{"value": "INR", "label": "INR"}]),
        _field("salary_frequency", "Pay frequency", "PAY FREQUENCY", "select", "optional", "financial",
               options=[{"value": "monthly", "label": "Monthly"}, {"value": "fortnightly", "label": "Fortnightly"},
                        {"value": "weekly", "label": "Weekly"}]),
        _field("probation_months", "Probation (months)", "PROBATION MONTHS", "number", "optional", "financial",
               min=0, max=24),
        _field("working_hours", "Working hours", "WORKING HOURS", "textarea", "recommended", "duration"),
        _field("termination_notice_days", "Notice period (days)", "NOTICE DAYS", "number", "recommended", "duration",
               min=1, max=365),
        _field("include_confidentiality", "Include confidentiality", "CONFIDENTIALITY", "checkbox", "recommended",
               "duration"),
        _field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions",
               options=list(DISPUTE_OPTIONS)),
        _field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional",
               "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "provision_class": "required", "body":
         "{document_title}\n\nThis Employment Agreement is made on {effective_date}."},
        {"id": "parties", "title": "Parties", "required": True, "provision_class": "required", "body":
         "BETWEEN:\n\n(1) {employer_name}, a {employer_type}, of {employer_address} (the \"Employer\"); and\n\n"
         "(2) {employee_name}, a {employee_type}, of {employee_address} (the \"Employee\")."},
        {"id": "recitals", "title": "Background", "required": True, "provision_class": "recommended", "body":
         "The Employer wishes to employ the Employee, and the Employee wishes to accept employment, "
         "on the terms set out in this Agreement."},
        {"id": "definitions", "title": "Definitions", "required": True, "provision_class": "recommended", "body":
         "In this Agreement, \"Employment\" means the employment of the Employee by the Employer under this Agreement. "
         "Headings are for convenience only."},
        {"id": "role", "title": "Position and duties", "required": True, "provision_class": "required", "body":
         "The Employee is employed as {job_title}. Duties: {duties}. Place of work: {place_of_work}. "
         "The Employee shall devote reasonable skill and attention to the Employment and follow lawful instructions."},
        {"id": "start", "title": "Commencement", "required": True, "provision_class": "required", "body":
         "Employment starts on {effective_date}. Probation, if any: {probation_months} months from the start date, "
         "during which either party may end employment on shorter notice if so agreed in writing and permitted by law."},
        {"id": "compensation", "title": "Remuneration", "required": False, "provision_class": "user_specific",
         "condition": {"has_value": "salary_amount"}, "body":
         "The Employer shall pay {salary_currency} {salary_amount} ({salary_frequency}), subject to statutory deductions. "
         "The draft does not invent allowances, bonuses, or benefits that were not supplied."},
        {"id": "hours", "title": "Working hours", "required": True, "provision_class": "recommended", "body":
         "Working hours: {working_hours}. Applicable working-time and leave rules must be checked for {jurisdiction_region}."},
        {"id": "obligations", "title": "Employee obligations", "required": True, "provision_class": "required", "body":
         "The Employee shall perform duties diligently, protect the Employer's property, and not engage in conflicting employment "
         "without prior written consent, except as permitted by applicable law."},
        {"id": "employer_obligations", "title": "Employer obligations", "required": True, "provision_class": "required", "body":
         "The Employer shall pay agreed remuneration, provide a safe workplace as required by law, and issue any documents "
         "required for the Employment that the parties have agreed to provide."},
        {"id": "confidentiality", "title": "Confidentiality", "required": False, "provision_class": "recommended",
         "condition": {"truthy": "include_confidentiality"}, "body":
         "The Employee shall keep the Employer's non-public business information confidential during Employment and afterwards, "
         "except for information that is public, independently known, or required to be disclosed by law."},
        {"id": "termination", "title": "Termination", "required": False, "provision_class": "recommended",
         "condition": {"has_value": "termination_notice_days"}, "body":
         "Either party may end Employment by giving {termination_notice_days} days' written notice, "
         "subject to any longer mandatory notice or procedure under applicable law. "
         "Summary termination for serious misconduct remains subject to applicable law."},
        {"id": "dispute_resolution", "title": "Dispute resolution", "required": True, "provision_class": "required", "body":
         "Disputes shall first be discussed in good faith. If arbitration is selected, unresolved disputes shall be referred "
         "to arbitration in India with the seat at {governing_law_seat}, except where a labour statute requires another forum. "
         "If courts are selected, or no method is stated, the courts at {governing_law_seat} have non-exclusive jurisdiction, "
         "subject to that limitation."},
        {"id": "governing_law", "title": "Governing law", "required": True, "provision_class": "required",
         "needs_legal_context": True, "body":
         "This Agreement is governed by the laws of India as applicable in {jurisdiction_region}. "
         "Shops and establishment, labour, social security, and tax formalities are not determined by this draft "
         "unless a verified legal source is attached."},
        {"id": "miscellaneous", "title": "General", "required": True, "provision_class": "user_specific", "body":
         "Amendments must be in writing and signed. If a provision is unenforceable, the rest remains in effect. "
         "Special conditions: {special_conditions}"},
        {"id": "signatures", "title": "Signatures", "required": True, "provision_class": "required",
         "include_signature": True, "body":
         "IN WITNESS WHEREOF the Parties have executed this Agreement on the date first written above."},
    ],
}

PARTNERSHIP_AGREEMENT_TEMPLATE: TemplateSpec = {
    "id": "partnership_agreement",
    "category": "agreement",
    "title": "Partnership Agreement",
    "description": "A partnership deed draft for partners carrying on business together under the Indian Partnership Act, 1932.",
    "document_type": "Partnership Agreement",
    "jurisdiction_country": "IN",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "General partnership firms governed by the Indian Partnership Act, 1932.",
    "source": {
        "authority": "Indian Partnership Act, 1932 & Startup India Model Contracts",
        "url": "https://www.startupindia.gov.in/content/sih/en/model-contracts.html",
        "document_name": "Model Partnership Deed",
        "reference_date": "1932 (as amended)",
    },
    "execution_requirements": [
        "Execution on non-judicial stamp paper as prescribed under State Stamp Act (Partnership Deed)",
        "Optional but recommended registration with the jurisdictional Registrar of Firms",
    ],
    "legal_query": "partnership deed partners profit sharing Indian Partnership Act",
    "parties": [
        {"id": "partner_a", "role": "Partner A", "name_field": "partner_a_name",
         "type_field": "partner_a_type", "address_field": "partner_a_address"},
        {"id": "partner_b", "role": "Partner B", "name_field": "partner_b_name",
         "type_field": "partner_b_type", "address_field": "partner_b_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the agreement you need.",
         "field_ids": ["document_title", "firm_name"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Where the firm is intended to operate.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Partners", "description": "Identify the partners.",
         "field_ids": ["partner_a_name", "partner_a_type", "partner_a_address",
                       "partner_b_name", "partner_b_type", "partner_b_address"]},
        {"id": "business", "title": "Business", "description": "Describe the firm and business.",
         "field_ids": ["business_nature", "principal_place", "effective_date"]},
        {"id": "financial", "title": "Capital and profit", "description": "Record contributions and sharing only if agreed.",
         "field_ids": ["capital_a", "capital_b", "profit_share_a", "profit_share_b", "capital_currency"]},
        {"id": "duration", "title": "Management and ending", "description": "Management, banking, and dissolution notice.",
         "field_ids": ["management_rules", "termination_notice_days", "include_confidentiality"]},
        {"id": "conditions", "title": "Other terms", "description": "Disputes and extra terms.",
         "field_ids": ["dispute_resolution", "special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        _field("firm_name", "Firm name", "FIRM NAME", "text", "required", "type"),
        *_jurisdiction_fields(),
        _field("partner_a_name", "Partner A name", "PARTNER A NAME", "text", "required", "parties"),
        _field("partner_a_type", "Partner A type", "PARTNER A TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("partner_a_address", "Partner A address", "PARTNER A ADDRESS", "textarea", "required", "parties"),
        _field("partner_b_name", "Partner B name", "PARTNER B NAME", "text", "required", "parties"),
        _field("partner_b_type", "Partner B type", "PARTNER B TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("partner_b_address", "Partner B address", "PARTNER B ADDRESS", "textarea", "required", "parties"),
        _field("business_nature", "Nature of business", "NATURE OF BUSINESS", "textarea", "required", "business"),
        _field("principal_place", "Principal place of business", "PRINCIPAL PLACE", "text", "required", "business"),
        _field("effective_date", "Commencement date", "COMMENCEMENT DATE", "date", "required", "business"),
        _field("capital_a", "Partner A capital contribution", "PARTNER A CAPITAL", "currency", "recommended",
               "financial", min=0),
        _field("capital_b", "Partner B capital contribution", "PARTNER B CAPITAL", "currency", "recommended",
               "financial", min=0),
        _field("capital_currency", "Currency", "CURRENCY", "select", "optional", "financial",
               options=[{"value": "INR", "label": "INR"}]),
        _field("profit_share_a", "Partner A profit share (%)", "PARTNER A PROFIT SHARE", "number", "recommended",
               "financial", min=0, max=100),
        _field("profit_share_b", "Partner B profit share (%)", "PARTNER B PROFIT SHARE", "number", "recommended",
               "financial", min=0, max=100),
        _field("management_rules", "Management / decision rules", "MANAGEMENT RULES", "textarea", "recommended",
               "duration"),
        _field("termination_notice_days", "Notice to dissolve / retire (days)", "NOTICE DAYS", "number",
               "recommended", "duration", min=1, max=365),
        _field("include_confidentiality", "Include confidentiality", "CONFIDENTIALITY", "checkbox", "recommended",
               "duration"),
        _field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions",
               options=list(DISPUTE_OPTIONS)),
        _field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional",
               "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "provision_class": "required", "body":
         "{document_title}\n\nThis Partnership Agreement for {firm_name} is made on {effective_date}."},
        {"id": "parties", "title": "Parties", "required": True, "provision_class": "required", "body":
         "BETWEEN:\n\n(1) {partner_a_name}, a {partner_a_type}, of {partner_a_address} (\"Partner A\"); and\n\n"
         "(2) {partner_b_name}, a {partner_b_type}, of {partner_b_address} (\"Partner B\").\n\n"
         "Together the \"Partners\"."},
        {"id": "recitals", "title": "Background", "required": True, "provision_class": "recommended", "body":
         "The Partners wish to carry on business in partnership under the name {firm_name} on the terms of this Agreement."},
        {"id": "definitions", "title": "Definitions", "required": True, "provision_class": "recommended", "body":
         "\"Firm\" means the partnership carried on under the name {firm_name}. \"Business\" means {business_nature}."},
        {"id": "business", "title": "Business and place", "required": True, "provision_class": "required", "body":
         "The Partners shall carry on the Business at {principal_place} and such other places as they agree in writing."},
        {"id": "commencement", "title": "Commencement", "required": True, "provision_class": "required", "body":
         "The partnership commences on {effective_date} and continues until dissolved in accordance with this Agreement or law."},
        {"id": "capital", "title": "Capital", "required": False, "provision_class": "user_specific",
         "condition": {"has_value": "capital_a"}, "body":
         "Initial capital: Partner A {capital_currency} {capital_a}; Partner B {capital_currency} {capital_b}. "
         "Further contributions require written agreement. The draft does not invent loans or interest."},
        {"id": "profit", "title": "Profit and loss", "required": False, "provision_class": "user_specific",
         "condition": {"has_value": "profit_share_a"}, "body":
         "Profits and losses are shared: Partner A {profit_share_a}%; Partner B {profit_share_b}%, "
         "unless the Partners agree otherwise in writing."},
        {"id": "management", "title": "Management", "required": True, "provision_class": "recommended", "body":
         "Management and decision-making: {management_rules}. Neither Partner shall bind the Firm beyond ordinary course "
         "without the other Partner's prior written consent, except as required by mandatory law."},
        {"id": "obligations", "title": "Partner obligations", "required": True, "provision_class": "required", "body":
         "Each Partner shall act in good faith toward the other, keep proper accounts of Firm dealings within their control, "
         "and not compete with the Firm using Firm opportunities without consent, subject to applicable law."},
        {"id": "confidentiality", "title": "Confidentiality", "required": False, "provision_class": "recommended",
         "condition": {"truthy": "include_confidentiality"}, "body":
         "Each Partner shall keep confidential the Firm's non-public business information, except where disclosure is required by law "
         "or agreed in writing."},
        {"id": "termination", "title": "Retirement and dissolution", "required": False, "provision_class": "recommended",
         "condition": {"has_value": "termination_notice_days"}, "body":
         "A Partner may retire or seek dissolution by giving {termination_notice_days} days' written notice, "
         "subject to any longer procedure required by law. Winding up and settlement of accounts follow applicable partnership law "
         "and any special conditions."},
        {"id": "dispute_resolution", "title": "Dispute resolution", "required": True, "provision_class": "required", "body":
         "Disputes shall first be discussed in good faith. If arbitration is selected, unresolved disputes shall be referred "
         "to arbitration in India with the seat at {governing_law_seat}. If courts are selected, or no method is stated, "
         "the courts at {governing_law_seat} have non-exclusive jurisdiction."},
        {"id": "governing_law", "title": "Governing law", "required": True, "provision_class": "required",
         "needs_legal_context": True, "body":
         "This Agreement is governed by the laws of India as applicable in {jurisdiction_region}. "
         "Registration of the firm, stamp duty, and tax registrations are not completed by this draft "
         "unless a verified legal source is attached."},
        {"id": "schedules", "title": "Schedules", "required": False, "provision_class": "user_specific",
         "condition": {"has_value": "special_conditions"}, "body":
         "Schedule / special conditions agreed by the Partners: {special_conditions}"},
        {"id": "signatures", "title": "Signatures", "required": True, "provision_class": "required",
         "include_signature": True, "body":
         "IN WITNESS WHEREOF the Partners have executed this Agreement on the date first written above."},
    ],
}

SALE_AGREEMENT_TEMPLATE: TemplateSpec = {
    "id": "sale_agreement",
    "category": "agreement",
    "title": "Sale Agreement (Agreement to Sell)",
    "description": "A sale of goods or property agreement based on Indian model formats with consideration, delivery schedule, and warranties.",
    "document_type": "Sale Agreement",
    "jurisdiction_country": "IN",
    "language": ["English", "Tamil"],
    "version": "2026.1",
    "applicability": "Agreements to sell under Sale of Goods Act, 1930 and Transfer of Property Act, 1882.",
    "source": {
        "authority": "Sale of Goods Act, 1930 & Startup India Model Contracts",
        "url": "https://www.startupindia.gov.in/content/sih/en/model-contracts.html",
        "document_name": "Model Agreement to Sell",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on appropriate non-judicial stamp paper under State Stamp Act",
    ],
    "legal_query": "sale of goods agreement seller buyer consideration India contract",
    "parties": [
        {"id": "seller", "role": "Seller", "name_field": "seller_name",
         "type_field": "seller_type", "address_field": "seller_address"},
        {"id": "buyer", "role": "Buyer", "name_field": "buyer_name",
         "type_field": "buyer_type", "address_field": "buyer_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the agreement you need.",
         "field_ids": ["document_title", "asset_type"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Where the sale is intended to operate.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Identify the seller and the buyer.",
         "field_ids": ["seller_name", "seller_type", "seller_address", "buyer_name", "buyer_type", "buyer_address"]},
        {"id": "goods", "title": "Subject of sale", "description": "Describe what is being sold.",
         "field_ids": ["goods_description", "delivery_place", "effective_date"]},
        {"id": "financial", "title": "Price and payment", "description": "Record price only if agreed.",
         "field_ids": ["price_amount", "price_currency", "payment_schedule", "delivery_date"]},
        {"id": "conditions", "title": "Risk, warranties, ending", "description": "Optional protections and disputes.",
         "field_ids": ["include_warranties", "termination_notice_days", "dispute_resolution", "special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        _field("asset_type", "What is being sold", "ASSET TYPE", "select", "required", "type",
               options=[{"value": "goods", "label": "Goods / movable property"},
                        {"value": "other_assets", "label": "Other assets (describe in goods description)"}]),
        *_jurisdiction_fields(),
        _field("seller_name", "Seller name", "SELLER NAME", "text", "required", "parties"),
        _field("seller_type", "Seller type", "SELLER TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("seller_address", "Seller address", "SELLER ADDRESS", "textarea", "required", "parties"),
        _field("buyer_name", "Buyer name", "BUYER NAME", "text", "required", "parties"),
        _field("buyer_type", "Buyer type", "BUYER TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("buyer_address", "Buyer address", "BUYER ADDRESS", "textarea", "required", "parties"),
        _field("goods_description", "Description of goods / assets", "GOODS DESCRIPTION", "textarea", "required",
               "goods"),
        _field("delivery_place", "Place of delivery", "DELIVERY PLACE", "text", "recommended", "goods"),
        _field("effective_date", "Agreement date", "AGREEMENT DATE", "date", "required", "goods"),
        _field("price_amount", "Sale price", "SALE PRICE", "currency", "recommended", "financial",
               "Leave blank if price is still to be agreed.", min=0),
        _field("price_currency", "Currency", "CURRENCY", "select", "optional", "financial",
               options=[{"value": "INR", "label": "INR"}, {"value": "USD", "label": "USD"}]),
        _field("payment_schedule", "Payment schedule", "PAYMENT SCHEDULE", "textarea", "optional", "financial"),
        _field("delivery_date", "Delivery date", "DELIVERY DATE", "date", "recommended", "financial"),
        _field("include_warranties", "Include limited title / quality warranties", "WARRANTIES", "checkbox",
               "recommended", "conditions"),
        _field("termination_notice_days", "Cancellation notice (days)", "CANCELLATION NOTICE", "number", "optional",
               "conditions", min=1, max=365),
        _field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions",
               options=list(DISPUTE_OPTIONS)),
        _field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional",
               "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "provision_class": "required", "body":
         "{document_title}\n\nThis Sale Agreement is made on {effective_date}."},
        {"id": "parties", "title": "Parties", "required": True, "provision_class": "required", "body":
         "BETWEEN:\n\n(1) {seller_name}, a {seller_type}, of {seller_address} (the \"Seller\"); and\n\n"
         "(2) {buyer_name}, a {buyer_type}, of {buyer_address} (the \"Buyer\")."},
        {"id": "recitals", "title": "Background", "required": True, "provision_class": "recommended", "body":
         "The Seller agrees to sell and the Buyer agrees to buy the {asset_type} described below on the terms of this Agreement."},
        {"id": "definitions", "title": "Definitions", "required": True, "provision_class": "recommended", "body":
         "\"Goods\" means: {goods_description}. \"Delivery Place\" means {delivery_place}."},
        {"id": "sale", "title": "Sale and transfer", "required": True, "provision_class": "required", "body":
         "The Seller sells and the Buyer buys the Goods. Title and risk pass on delivery at the Delivery Place "
         "unless the Parties have agreed otherwise in writing in special conditions."},
        {"id": "price", "title": "Price and payment", "required": False, "provision_class": "user_specific",
         "condition": {"has_value": "price_amount"}, "body":
         "The price is {price_currency} {price_amount}. Payment schedule: {payment_schedule}. "
         "The draft does not invent taxes, interest, or extra charges that were not supplied."},
        {"id": "delivery", "title": "Delivery", "required": True, "provision_class": "required", "body":
         "Delivery shall be made at {delivery_place} on or about {delivery_date}. "
         "The Buyer shall inspect the Goods on delivery and notify obvious defects within a reasonable time."},
        {"id": "seller_obligations", "title": "Seller obligations", "required": True, "provision_class": "required", "body":
         "The Seller shall deliver the Goods as described, free from undisclosed encumbrances created by the Seller, "
         "except as disclosed in writing."},
        {"id": "buyer_obligations", "title": "Buyer obligations", "required": True, "provision_class": "required", "body":
         "The Buyer shall pay the agreed price in accordance with this Agreement and take delivery when the Goods are duly tendered."},
        {"id": "warranties", "title": "Warranties", "required": False, "provision_class": "recommended",
         "condition": {"truthy": "include_warranties"}, "body":
         "The Seller warrants that it has the right to sell the Goods and that, at delivery, the Goods materially match the description. "
         "No other warranty is stated unless supplied in special conditions. Mandatory consumer or sale-of-goods protections are not excluded."},
        {"id": "termination", "title": "Cancellation", "required": False, "provision_class": "recommended",
         "condition": {"has_value": "termination_notice_days"}, "body":
         "Either Party may cancel for material breach uncured after {termination_notice_days} days' written notice, "
         "without limiting remedies available under applicable law."},
        {"id": "dispute_resolution", "title": "Dispute resolution", "required": True, "provision_class": "required", "body":
         "Disputes shall first be discussed in good faith. If arbitration is selected, unresolved disputes shall be referred "
         "to arbitration in India with the seat at {governing_law_seat}. If courts are selected, or no method is stated, "
         "the courts at {governing_law_seat} have non-exclusive jurisdiction."},
        {"id": "governing_law", "title": "Governing law", "required": True, "provision_class": "required",
         "needs_legal_context": True, "body":
         "This Agreement is governed by the laws of India as applicable in {jurisdiction_region}. "
         "GST, stamp duty, registration, and sector licences are not determined by this draft unless a verified legal source is attached."},
        {"id": "schedules", "title": "Annexures", "required": False, "provision_class": "user_specific",
         "condition": {"has_value": "special_conditions"}, "body":
         "Annexure / special conditions: {special_conditions}"},
        {"id": "signatures", "title": "Signatures", "required": True, "provision_class": "required",
         "include_signature": True, "body":
         "IN WITNESS WHEREOF the Parties have executed this Agreement on the date first written above."},
    ],
}

MOU_TEMPLATE: TemplateSpec = {
    "id": "mou",
    "category": "agreement",
    "title": "Memorandum of Understanding (MoU)",
    "description": "A memorandum of understanding recording mutual intent, collaborative scope, and binding/non-binding provisions.",
    "document_type": "Memorandum of Understanding",
    "jurisdiction_country": "IN",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "Bilateral institutional and commercial understandings in India.",
    "source": {
        "authority": "Department of Legal Affairs & Startup India Model Contracts",
        "url": "https://www.startupindia.gov.in/content/sih/en/model-contracts.html",
        "document_name": "Model Memorandum of Understanding",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on appropriate non-judicial stamp paper if binding financial or IP obligations are created",
    ],
    "legal_query": "memorandum of understanding MoU non-binding cooperation agreement India",
    "parties": [
        {"id": "party_a", "role": "Party A", "name_field": "party_a_name",
         "type_field": "party_a_type", "address_field": "party_a_address"},
        {"id": "party_b", "role": "Party B", "name_field": "party_b_name",
         "type_field": "party_b_type", "address_field": "party_b_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the MoU you need.",
         "field_ids": ["document_title", "binding_intent"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Where cooperation is intended.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Identify the parties.",
         "field_ids": ["party_a_name", "party_a_type", "party_a_address", "party_b_name", "party_b_type", "party_b_address"]},
        {"id": "purpose", "title": "Purpose and scope", "description": "What the parties intend to do together.",
         "field_ids": ["purpose", "scope", "effective_date", "end_date"]},
        {"id": "conditions", "title": "Confidentiality and process", "description": "Optional protections and disputes.",
         "field_ids": ["include_confidentiality", "termination_notice_days", "dispute_resolution", "special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        _field("binding_intent", "Intended legal effect", "BINDING INTENT", "select", "required", "type",
               options=[{"value": "non_binding", "label": "Generally non-binding (record of intent)"},
                        {"value": "partly_binding", "label": "Partly binding (e.g. confidentiality / costs)"}]),
        *_jurisdiction_fields(),
        _field("party_a_name", "Party A name", "PARTY A NAME", "text", "required", "parties"),
        _field("party_a_type", "Party A type", "PARTY A TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("party_a_address", "Party A address", "PARTY A ADDRESS", "textarea", "required", "parties"),
        _field("party_b_name", "Party B name", "PARTY B NAME", "text", "required", "parties"),
        _field("party_b_type", "Party B type", "PARTY B TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("party_b_address", "Party B address", "PARTY B ADDRESS", "textarea", "required", "parties"),
        _field("purpose", "Purpose of MoU", "PURPOSE", "textarea", "required", "purpose"),
        _field("scope", "Scope of cooperation", "SCOPE", "textarea", "required", "purpose"),
        _field("effective_date", "Start date", "START DATE", "date", "required", "purpose"),
        _field("end_date", "End date", "END DATE", "date", "recommended", "purpose"),
        _field("include_confidentiality", "Include confidentiality", "CONFIDENTIALITY", "checkbox", "recommended",
               "conditions"),
        _field("termination_notice_days", "Notice to end (days)", "NOTICE DAYS", "number", "optional", "conditions",
               min=1, max=365),
        _field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions",
               options=list(DISPUTE_OPTIONS)),
        _field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional",
               "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "provision_class": "required", "body":
         "{document_title}\n\nThis Memorandum of Understanding is made on {effective_date}."},
        {"id": "parties", "title": "Parties", "required": True, "provision_class": "required", "body":
         "BETWEEN:\n\n(1) {party_a_name}, a {party_a_type}, of {party_a_address} (\"Party A\"); and\n\n"
         "(2) {party_b_name}, a {party_b_type}, of {party_b_address} (\"Party B\")."},
        {"id": "recitals", "title": "Background", "required": True, "provision_class": "recommended", "body":
         "The Parties wish to record their understanding regarding: {purpose}."},
        {"id": "purpose", "title": "Purpose and scope", "required": True, "provision_class": "required", "body":
         "Purpose: {purpose}. Scope of cooperation: {scope}."},
        {"id": "status", "title": "Legal status", "required": True, "provision_class": "required", "body":
         "Intended legal effect: {binding_intent}. Except for clauses the Parties expressly mark as binding "
         "(such as confidentiality, if included), this MoU is a statement of intent and does not create a partnership, "
         "agency, or employment relationship."},
        {"id": "obligations", "title": "Cooperation", "required": True, "provision_class": "recommended", "body":
         "Each Party shall cooperate in good faith to explore the Purpose within the Scope, without obligation to enter "
         "a definitive agreement unless and until such an agreement is signed."},
        {"id": "confidentiality", "title": "Confidentiality", "required": False, "provision_class": "recommended",
         "condition": {"truthy": "include_confidentiality"}, "body":
         "Each Party shall keep confidential the other Party's non-public information received under this MoU and use it "
         "only for the Purpose, except for information that is public, independently developed, or required to be disclosed by law. "
         "This clause is intended to be binding if the Parties selected partly binding effect or otherwise agree in writing."},
        {"id": "term", "title": "Term", "required": True, "provision_class": "required", "body":
         "This MoU starts on {effective_date} and continues until {end_date}, unless ended earlier by written notice "
         "or by a later definitive agreement that supersedes it."},
        {"id": "termination", "title": "Ending", "required": False, "provision_class": "recommended",
         "condition": {"has_value": "termination_notice_days"}, "body":
         "Either Party may end this MoU by giving {termination_notice_days} days' written notice. "
         "Surviving confidentiality obligations continue as stated."},
        {"id": "dispute_resolution", "title": "Dispute resolution", "required": True, "provision_class": "required", "body":
         "Disputes about binding clauses shall first be discussed in good faith. If arbitration is selected, unresolved disputes "
         "shall be referred to arbitration in India with the seat at {governing_law_seat}. If courts are selected, or no method "
         "is stated, the courts at {governing_law_seat} have non-exclusive jurisdiction."},
        {"id": "governing_law", "title": "Governing law", "required": True, "provision_class": "required",
         "needs_legal_context": True, "body":
         "This MoU is governed by the laws of India as applicable in {jurisdiction_region} for any binding provisions. "
         "Whether a particular clause is enforceable depends on the Parties' intent and applicable law and is not guaranteed by this draft."},
        {"id": "miscellaneous", "title": "General", "required": True, "provision_class": "user_specific", "body":
         "Amendments must be in writing and signed. Special conditions: {special_conditions}"},
        {"id": "signatures", "title": "Signatures", "required": True, "provision_class": "required",
         "include_signature": True, "body":
         "IN WITNESS WHEREOF the Parties have signed this Memorandum of Understanding on the date first written above."},
    ],
}

EXTRA_TEMPLATES: dict[str, TemplateSpec] = {
    EMPLOYMENT_AGREEMENT_TEMPLATE["id"]: EMPLOYMENT_AGREEMENT_TEMPLATE,
    PARTNERSHIP_AGREEMENT_TEMPLATE["id"]: PARTNERSHIP_AGREEMENT_TEMPLATE,
    SALE_AGREEMENT_TEMPLATE["id"]: SALE_AGREEMENT_TEMPLATE,
    MOU_TEMPLATE["id"]: MOU_TEMPLATE,
}
