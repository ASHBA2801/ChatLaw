"""Extensible document-template registry.

Only templates listed here are exposed. Adding a document type means adding a
TemplateSpec; the builder, validator, assembler, and generator consume this
registry without per-type UI branches.
"""

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


NDA_TEMPLATE: TemplateSpec = {
    "id": "nda",
    "category": "agreement",
    "title": "Non-Disclosure Agreement",
    "description": "A mutual or one-way confidentiality agreement for sharing information in India.",
    "document_type": "Non-Disclosure Agreement",
    "jurisdiction_country": "IN",
    "legal_query": "confidentiality non-disclosure agreement obligations India contract",
    "parties": [
        {"id": "disclosing", "role": "Disclosing Party", "name_field": "disclosing_party_name",
         "type_field": "disclosing_party_type", "address_field": "disclosing_party_address"},
        {"id": "receiving", "role": "Receiving Party", "name_field": "receiving_party_name",
         "type_field": "receiving_party_type", "address_field": "receiving_party_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the agreement you need.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Choose where this agreement is intended to operate.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Identify who is disclosing and receiving information.",
         "field_ids": ["disclosing_party_name", "disclosing_party_type", "disclosing_party_address",
                       "receiving_party_name", "receiving_party_type", "receiving_party_address", "mutual"]},
        {"id": "purpose", "title": "Purpose", "description": "State why confidential information will be shared.",
         "field_ids": ["purpose", "effective_date"]},
        {"id": "duration", "title": "Duration", "description": "How long confidentiality lasts.",
         "field_ids": ["duration_months"]},
        {"id": "conditions", "title": "Special conditions", "description": "Optional protections the parties want in writing.",
         "field_ids": ["exclude_public_info", "include_non_solicit", "dispute_resolution", "special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type",
               "Leave blank to use the standard title."),
        *_jurisdiction_fields(),
        _field("disclosing_party_name", "Disclosing party name", "DISCLOSING PARTY NAME", "text", "required", "parties"),
        _field("disclosing_party_type", "Disclosing party type", "DISCLOSING PARTY TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("disclosing_party_address", "Disclosing party address", "DISCLOSING PARTY ADDRESS", "textarea", "required", "parties"),
        _field("receiving_party_name", "Receiving party name", "RECEIVING PARTY NAME", "text", "required", "parties"),
        _field("receiving_party_type", "Receiving party type", "RECEIVING PARTY TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("receiving_party_address", "Receiving party address", "RECEIVING PARTY ADDRESS", "textarea", "required", "parties"),
        _field("mutual", "Mutual confidentiality", "MUTUAL CONFIDENTIALITY", "checkbox", "optional", "parties",
               "If selected, both parties protect information they receive from each other."),
        _field("purpose", "Purpose of disclosure", "PURPOSE", "textarea", "required", "purpose",
               "Describe the project or discussion. Do not invent a purpose if it is not yet agreed."),
        _field("effective_date", "Effective date", "EFFECTIVE DATE", "date", "required", "purpose"),
        _field("duration_months", "Confidentiality period (months)", "CONFIDENTIALITY PERIOD", "number", "required", "duration",
               "Number of months after disclosure or after the effective date, as the draft will state.",
               min=1, max=120),
        _field("exclude_public_info", "Exclude public and independently developed information",
               "PUBLIC INFORMATION EXCLUSION", "checkbox", "recommended", "conditions"),
        _field("include_non_solicit", "Include a non-solicitation restriction",
               "NON-SOLICITATION", "checkbox", "optional", "conditions"),
        _field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions",
               options=list(DISPUTE_OPTIONS)),
        _field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions",
               "Only include terms the parties have actually discussed."),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "body":
         "{document_title}\n\nThis Non-Disclosure Agreement is made on {effective_date}."},
        {"id": "parties", "title": "Parties", "required": True, "body":
         "BETWEEN:\n\n(1) {disclosing_party_name}, a {disclosing_party_type}, of {disclosing_party_address} (the \"Disclosing Party\"); and\n\n"
         "(2) {receiving_party_name}, a {receiving_party_type}, of {receiving_party_address} (the \"Receiving Party\").\n\n"
         "Each is a \"Party\" and together the \"Parties\"."},
        {"id": "purpose", "title": "Purpose", "required": True, "body":
         "The Parties intend to disclose information for the following purpose: {purpose} (the \"Purpose\"). "
         "Confidential Information may be used only for the Purpose."},
        {"id": "definitions", "title": "Confidential Information", "required": True, "body":
         "\"Confidential Information\" means information disclosed by the Disclosing Party to the Receiving Party, "
         "in any form, that is identified as confidential or that a reasonable person would understand to be confidential, "
         "including business, technical, financial, and personal information relating to the Purpose."},
        {"id": "obligations", "title": "Confidentiality obligations", "required": True, "body":
         "The Receiving Party shall keep Confidential Information in confidence, use it only for the Purpose, "
         "protect it with at least the same degree of care it uses for its own confidential information, "
         "and disclose it only to personnel who need it for the Purpose and are bound to protect it. "
         "The Receiving Party shall not reverse engineer or copy Confidential Information except as needed for the Purpose."},
        {"id": "exclusions", "title": "Exclusions", "required": False, "condition": {"truthy": "exclude_public_info"}, "body":
         "Confidential Information does not include information that the Receiving Party can show: "
         "(a) is or becomes public other than by breach of this Agreement; "
         "(b) was already lawfully in its possession; "
         "(c) is independently developed without use of Confidential Information; or "
         "(d) is received from a third party without breach of a confidentiality duty. "
         "The Receiving Party may disclose Confidential Information if required by law, provided it gives "
         "notice reasonably practicable in the circumstances and discloses only what is required."},
        {"id": "term", "title": "Term", "required": True, "body":
         "This Agreement takes effect on {effective_date}. The obligations of confidentiality continue for "
         "{duration_months} months after the last disclosure of Confidential Information, unless a longer period "
         "is required by law for a particular class of information."},
        {"id": "return", "title": "Return and destruction", "required": True, "body":
         "On written request, or when the Purpose ends, the Receiving Party shall return or securely destroy "
         "Confidential Information in its possession, except copies it must retain under law or ordinary backup systems, "
         "which remain subject to this Agreement."},
        {"id": "non_solicit", "title": "Non-solicitation", "required": False, "condition": {"truthy": "include_non_solicit"}, "body":
         "During the term of this Agreement and for {duration_months} months afterwards, neither Party shall knowingly "
         "solicit for employment the other Party's employees who were introduced in connection with the Purpose, "
         "except through general public advertisements not targeted at those employees."},
        {"id": "no_license", "title": "No licence", "required": True, "body":
         "No licence or other right in intellectual property is granted by this Agreement except the limited right "
         "to use Confidential Information for the Purpose."},
        {"id": "remedies", "title": "Remedies", "required": True, "body":
         "The Parties acknowledge that a breach of confidentiality may cause harm that damages alone may not adequately "
         "remedy, and that a Party may seek injunctive or other relief from a court of competent jurisdiction, "
         "without limiting other rights."},
        {"id": "dispute_resolution", "title": "Dispute resolution", "required": True, "body":
         "If a dispute arises under this Agreement, the Parties shall first attempt to resolve it in good faith discussion. "
         "If they selected arbitration, unresolved disputes shall be referred to arbitration in India, with the seat at "
         "{governing_law_seat}, in the English language, before a sole arbitrator appointed by agreement or, failing agreement, "
         "in accordance with applicable Indian arbitration law. If they selected courts, or no method is stated, "
         "the courts at {governing_law_seat} have non-exclusive jurisdiction, without prejudice to mandatory law."},
        {"id": "governing_law", "title": "Governing law and jurisdiction", "required": True, "needs_legal_context": True, "body":
         "This Agreement is governed by the laws of India as applicable in {jurisdiction_region}. "
         "Jurisdiction-specific requirements, including stamp duty where applicable, must be checked before the document is used. "
         "This draft does not determine that any particular statute applies unless a verified legal source is attached below."},
        {"id": "notices", "title": "Notices", "required": True, "body":
         "Notices under this Agreement must be in writing and delivered to the addresses stated for the Parties, "
         "or to another address notified in writing."},
        {"id": "amendments", "title": "Amendments", "required": True, "body":
         "No amendment is effective unless it is in writing and signed by both Parties."},
        {"id": "severability", "title": "Severability", "required": True, "body":
         "If a provision is held unenforceable, the remaining provisions continue in effect."},
        {"id": "entire_agreement", "title": "Entire agreement", "required": True, "body":
         "This Agreement is the entire agreement on its subject and supersedes prior statements on that subject. "
         "Special conditions agreed by the Parties: {special_conditions}"},
        {"id": "signatures", "title": "Signatures", "required": True, "include_signature": True, "body":
         "IN WITNESS WHEREOF the Parties have executed this Agreement on the date first written above."},
    ],
}

SERVICE_AGREEMENT_TEMPLATE: TemplateSpec = {
    "id": "service_agreement",
    "category": "agreement",
    "title": "Service Agreement",
    "description": "A services contract between a client and a service provider in India.",
    "document_type": "Service Agreement",
    "jurisdiction_country": "IN",
    "legal_query": "service agreement consideration payment obligations India contract",
    "parties": [
        {"id": "client", "role": "Client", "name_field": "client_name",
         "type_field": "client_type", "address_field": "client_address"},
        {"id": "provider", "role": "Service Provider", "name_field": "provider_name",
         "type_field": "provider_type", "address_field": "provider_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the agreement you need.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Choose where this agreement is intended to operate.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Identify the client and the service provider.",
         "field_ids": ["client_name", "client_type", "client_address", "provider_name", "provider_type", "provider_address"]},
        {"id": "purpose", "title": "Services", "description": "Describe the work to be performed.",
         "field_ids": ["purpose", "deliverables", "effective_date"]},
        {"id": "financial", "title": "Financial terms", "description": "Record fees only if they have been agreed.",
         "field_ids": ["fee_amount", "fee_currency", "payment_schedule"]},
        {"id": "duration", "title": "Duration and ending", "description": "How long the services last and how they may end.",
         "field_ids": ["end_date", "termination_notice_days"]},
        {"id": "conditions", "title": "Rights and conditions", "description": "Confidentiality, disputes, and extra terms.",
         "field_ids": ["include_confidentiality", "dispute_resolution", "special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("client_name", "Client name", "CLIENT NAME", "text", "required", "parties"),
        _field("client_type", "Client type", "CLIENT TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("client_address", "Client address", "CLIENT ADDRESS", "textarea", "required", "parties"),
        _field("provider_name", "Service provider name", "SERVICE PROVIDER NAME", "text", "required", "parties"),
        _field("provider_type", "Service provider type", "SERVICE PROVIDER TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("provider_address", "Service provider address", "SERVICE PROVIDER ADDRESS", "textarea", "required", "parties"),
        _field("purpose", "Description of services", "SERVICES DESCRIPTION", "textarea", "required", "purpose"),
        _field("deliverables", "Deliverables", "DELIVERABLES", "textarea", "recommended", "purpose"),
        _field("effective_date", "Start date", "START DATE", "date", "required", "purpose"),
        _field("fee_amount", "Fee amount", "FEE AMOUNT", "currency", "recommended", "financial",
               "Leave blank if fees are still to be agreed. The draft will not invent a price.", min=0),
        _field("fee_currency", "Currency", "CURRENCY", "select", "optional", "financial",
               options=[{"value": "INR", "label": "INR"}, {"value": "USD", "label": "USD"}, {"value": "EUR", "label": "EUR"}]),
        _field("payment_schedule", "Payment schedule", "PAYMENT SCHEDULE", "textarea", "optional", "financial"),
        _field("end_date", "End date", "END DATE", "date", "recommended", "duration"),
        _field("termination_notice_days", "Termination notice (days)", "TERMINATION NOTICE DAYS", "number", "optional",
               "duration", min=1, max=365),
        _field("include_confidentiality", "Include confidentiality obligations", "CONFIDENTIALITY", "checkbox",
               "recommended", "conditions"),
        _field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions",
               options=list(DISPUTE_OPTIONS)),
        _field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "body":
         "{document_title}\n\nThis Service Agreement is made on {effective_date}."},
        {"id": "parties", "title": "Parties", "required": True, "body":
         "BETWEEN:\n\n(1) {client_name}, a {client_type}, of {client_address} (the \"Client\"); and\n\n"
         "(2) {provider_name}, a {provider_type}, of {provider_address} (the \"Service Provider\")."},
        {"id": "services", "title": "Services", "required": True, "body":
         "The Service Provider shall perform the following services: {purpose}. "
         "Agreed deliverables, if any: {deliverables}."},
        {"id": "client_obligations", "title": "Client obligations", "required": True, "body":
         "The Client shall provide information, access, and decisions reasonably required for the services, "
         "and shall pay any agreed fees in accordance with this Agreement."},
        {"id": "provider_obligations", "title": "Service Provider obligations", "required": True, "body":
         "The Service Provider shall perform the services with reasonable skill and care, in accordance with this Agreement, "
         "and shall not represent that the services constitute legal advice unless the Service Provider is engaged and authorised to do so."},
        {"id": "fees", "title": "Fees and payment", "required": False, "condition": {"has_value": "fee_amount"}, "body":
         "The Client shall pay {fee_currency} {fee_amount} for the services. Payment schedule: {payment_schedule}. "
         "Unless the Parties have agreed otherwise in writing, invoices are payable as stated in the payment schedule, "
         "and the draft does not add taxes, interest, or extra charges that were not supplied."},
        {"id": "term", "title": "Term", "required": True, "body":
         "This Agreement starts on {effective_date} and continues until {end_date}, unless ended earlier in accordance with this Agreement."},
        {"id": "termination", "title": "Termination", "required": False, "condition": {"has_value": "termination_notice_days"}, "body":
         "Either Party may end this Agreement by giving {termination_notice_days} days' written notice. "
         "A Party may end this Agreement immediately by written notice if the other Party materially breaches it and does not remedy the breach within a reasonable time after notice, "
         "or if the other Party becomes insolvent. Accrued payment obligations survive termination."},
        {"id": "confidentiality", "title": "Confidentiality", "required": False, "condition": {"truthy": "include_confidentiality"}, "body":
         "Each Party shall keep confidential the other Party's non-public information received in connection with the services "
         "and use it only to perform this Agreement, except for information that is public, independently developed, "
         "or required to be disclosed by law."},
        {"id": "intellectual_property", "title": "Intellectual property", "required": True, "body":
         "Materials created by the Service Provider specifically for the Client under this Agreement and paid for by the Client "
         "are assigned to the Client on payment, excluding the Service Provider's pre-existing tools and know-how, "
         "which remain the Service Provider's property. The Client receives a licence to use those pre-existing materials as needed to use the deliverables."},
        {"id": "indemnification", "title": "Indemnity and liability", "required": True, "body":
         "Each Party shall indemnify the other against third-party claims arising from its own fraud, wilful misconduct, or infringement that it causes. "
         "This clause does not exclude liability that cannot be excluded under applicable law. "
         "No cap or exclusion is stated here unless the Parties supplied one in special conditions."},
        {"id": "force_majeure", "title": "Force majeure", "required": True, "body":
         "A Party is not liable for delay or failure caused by events beyond its reasonable control, provided it notifies the other Party "
         "and resumes performance when reasonably possible. If such an event continues for 30 days, either Party may end this Agreement by written notice."},
        {"id": "dispute_resolution", "title": "Dispute resolution", "required": True, "body":
         "Disputes shall first be discussed in good faith. If arbitration is selected, unresolved disputes shall be referred to arbitration in India "
         "with the seat at {governing_law_seat}. If courts are selected, or no method is stated, the courts at {governing_law_seat} have non-exclusive jurisdiction."},
        {"id": "governing_law", "title": "Governing law", "required": True, "needs_legal_context": True, "body":
         "This Agreement is governed by the laws of India as applicable in {jurisdiction_region}. "
         "Stamp duty, registration, and sector-specific licensing are not determined by this draft unless a verified legal source is attached."},
        {"id": "notices", "title": "Notices", "required": True, "body":
         "Notices must be in writing and sent to the addresses of the Parties set out above, or to an address notified in writing."},
        {"id": "miscellaneous", "title": "General", "required": True, "body":
         "Amendments must be in writing and signed. If a provision is unenforceable, the rest remains in effect. "
         "This is the entire agreement on its subject. Special conditions: {special_conditions}"},
        {"id": "signatures", "title": "Signatures", "required": True, "include_signature": True, "body":
         "IN WITNESS WHEREOF the Parties have executed this Agreement on the date first written above."},
    ],
}

RENT_LEASE_TEMPLATE: TemplateSpec = {
    "id": "rent_lease",
    "category": "agreement",
    "title": "Rent / Lease Agreement",
    "description": "A residential or commercial lease draft for property in India.",
    "document_type": "Rent / Lease Agreement",
    "jurisdiction_country": "IN",
    "legal_query": "lease rent landlord tenant property agreement India",
    "parties": [
        {"id": "landlord", "role": "Landlord / Lessor", "name_field": "landlord_name",
         "type_field": "landlord_type", "address_field": "landlord_address"},
        {"id": "tenant", "role": "Tenant / Lessee", "name_field": "tenant_name",
         "type_field": "tenant_type", "address_field": "tenant_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the agreement you need.", "field_ids": ["document_title", "property_use"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "The property's location governs many lease rules.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Identify the landlord and the tenant.",
         "field_ids": ["landlord_name", "landlord_type", "landlord_address", "tenant_name", "tenant_type", "tenant_address"]},
        {"id": "purpose", "title": "Property", "description": "Describe the premises being let.",
         "field_ids": ["property_address", "property_description", "effective_date"]},
        {"id": "financial", "title": "Rent and deposit", "description": "Record amounts only if they have been agreed.",
         "field_ids": ["rent_amount", "rent_currency", "rent_frequency", "deposit_amount"]},
        {"id": "duration", "title": "Term", "description": "When the tenancy starts and ends.",
         "field_ids": ["end_date", "termination_notice_days"]},
        {"id": "conditions", "title": "Obligations and conditions", "description": "Use, maintenance, and extra terms.",
         "field_ids": ["maintenance_responsibility", "dispute_resolution", "special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        _field("property_use", "Intended use", "PROPERTY USE", "select", "required", "type",
               options=[{"value": "residential", "label": "Residential"}, {"value": "commercial", "label": "Commercial"}]),
        *_jurisdiction_fields(),
        _field("landlord_name", "Landlord name", "LANDLORD NAME", "text", "required", "parties"),
        _field("landlord_type", "Landlord type", "LANDLORD TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("landlord_address", "Landlord address", "LANDLORD ADDRESS", "textarea", "required", "parties"),
        _field("tenant_name", "Tenant name", "TENANT NAME", "text", "required", "parties"),
        _field("tenant_type", "Tenant type", "TENANT TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("tenant_address", "Tenant address for notices", "TENANT ADDRESS", "textarea", "required", "parties"),
        _field("property_address", "Property address", "PROPERTY ADDRESS", "textarea", "required", "purpose"),
        _field("property_description", "Description of premises", "PROPERTY DESCRIPTION", "textarea", "recommended", "purpose"),
        _field("effective_date", "Lease start date", "LEASE START DATE", "date", "required", "purpose"),
        _field("rent_amount", "Rent amount", "RENT AMOUNT", "currency", "recommended", "financial",
               "Leave blank if rent is still to be agreed. The draft will not invent rent.", min=0),
        _field("rent_currency", "Currency", "CURRENCY", "select", "optional", "financial",
               options=[{"value": "INR", "label": "INR"}]),
        _field("rent_frequency", "Rent frequency", "RENT FREQUENCY", "select", "optional", "financial",
               options=[{"value": "monthly", "label": "Monthly"}, {"value": "quarterly", "label": "Quarterly"},
                        {"value": "yearly", "label": "Yearly"}]),
        _field("deposit_amount", "Security deposit", "SECURITY DEPOSIT", "currency", "optional", "financial", min=0),
        _field("end_date", "Lease end date", "LEASE END DATE", "date", "required", "duration"),
        _field("termination_notice_days", "Notice to end (days)", "TERMINATION NOTICE DAYS", "number", "recommended",
               "duration", min=1, max=365),
        _field("maintenance_responsibility", "Routine maintenance", "MAINTENANCE RESPONSIBILITY", "select", "recommended",
               "conditions",
               options=[{"value": "tenant", "label": "Tenant for routine upkeep"},
                        {"value": "landlord", "label": "Landlord for routine upkeep"},
                        {"value": "shared", "label": "Shared as described in special conditions"}]),
        _field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions",
               options=list(DISPUTE_OPTIONS)),
        _field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "body":
         "{document_title}\n\nThis Rent / Lease Agreement is made on {effective_date} for {property_use} use."},
        {"id": "parties", "title": "Parties", "required": True, "body":
         "BETWEEN:\n\n(1) {landlord_name}, a {landlord_type}, of {landlord_address} (the \"Landlord\"); and\n\n"
         "(2) {tenant_name}, a {tenant_type}, of {tenant_address} (the \"Tenant\")."},
        {"id": "property", "title": "Premises", "required": True, "body":
         "The Landlord lets and the Tenant takes the premises at {property_address}. Description: {property_description}. "
         "The Tenant shall use the premises only for {property_use} use, and shall not change that use without the Landlord's prior written consent."},
        {"id": "term", "title": "Term", "required": True, "body":
         "The tenancy starts on {effective_date} and ends on {end_date}, unless ended earlier in accordance with this Agreement or applicable law."},
        {"id": "rent", "title": "Rent", "required": False, "condition": {"has_value": "rent_amount"}, "body":
         "The Tenant shall pay rent of {rent_currency} {rent_amount} ({rent_frequency}) for the premises. "
         "The draft does not add interest, GST, or other charges that were not supplied."},
        {"id": "deposit", "title": "Security deposit", "required": False, "condition": {"has_value": "deposit_amount"}, "body":
         "The Tenant shall pay a security deposit of {rent_currency} {deposit_amount}. The Landlord shall hold it as security "
         "for unpaid rent and damage beyond fair wear and tear, and shall return the balance after the premises are vacated, "
         "subject to applicable law and a written statement of deductions."},
        {"id": "tenant_obligations", "title": "Tenant obligations", "required": True, "body":
         "The Tenant shall pay agreed sums on time, keep the premises in a reasonably clean condition, "
         "not assign or sublet without prior written consent, and comply with applicable building and society rules notified to the Tenant."},
        {"id": "landlord_obligations", "title": "Landlord obligations", "required": True, "body":
         "The Landlord shall give quiet enjoyment of the premises while the Tenant complies with this Agreement, "
         "and shall carry out structural and major repairs that are the Landlord's responsibility, except where damage is caused by the Tenant."},
        {"id": "maintenance", "title": "Maintenance", "required": True, "body":
         "Routine maintenance responsibility: {maintenance_responsibility}. The Parties should record any specific repair allocation in special conditions."},
        {"id": "termination", "title": "Ending the tenancy", "required": False, "condition": {"has_value": "termination_notice_days"}, "body":
         "Either Party may end this Agreement by giving {termination_notice_days} days' written notice, subject to any mandatory notice period that applies in {jurisdiction_region}. "
         "The Landlord may also end the tenancy for unpaid rent or material breach after written notice and any cure period required by applicable law."},
        {"id": "dispute_resolution", "title": "Dispute resolution", "required": True, "body":
         "Disputes shall first be discussed in good faith. If arbitration is selected, unresolved disputes shall be referred to arbitration in India "
         "with the seat at {governing_law_seat}, except where a tenancy statute requires a particular forum. "
         "If courts are selected, or no method is stated, the courts at {governing_law_seat} have non-exclusive jurisdiction, subject to that limitation."},
        {"id": "governing_law", "title": "Governing law", "required": True, "needs_legal_context": True, "body":
         "This Agreement is governed by the laws of India as applicable in {jurisdiction_region}. "
         "Registration, stamp duty, and local tenancy controls are not determined by this draft unless a verified legal source is attached. "
         "[JURISDICTION REVIEW REQUIRED]"},
        {"id": "notices", "title": "Notices", "required": True, "body":
         "Notices must be in writing and sent to the addresses of the Parties set out above, or to an address notified in writing."},
        {"id": "miscellaneous", "title": "General", "required": True, "body":
         "Amendments must be in writing and signed. If a provision is unenforceable, the rest remains in effect. "
         "Special conditions: {special_conditions}"},
        {"id": "signatures", "title": "Signatures", "required": True, "include_signature": True, "body":
         "IN WITNESS WHEREOF the Parties have executed this Agreement on the date first written above."},
    ],
}

AFFIDAVIT_TEMPLATE: TemplateSpec = {
    "id": "affidavit",
    "category": "legal_document",
    "title": "Affidavit",
    "description": "A sworn statement of facts for use in India. Notary or oath formalities are not completed by this draft.",
    "document_type": "Affidavit",
    "jurisdiction_country": "IN",
    "legal_query": "affidavit sworn statement verification of facts India oath",
    "parties": [
        {"id": "deponent", "role": "Deponent", "name_field": "deponent_name",
         "type_field": "deponent_type", "address_field": "deponent_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the affidavit you need.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Where this affidavit is intended to be used.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Deponent", "description": "Identify the person who will swear the facts.",
         "field_ids": ["deponent_name", "deponent_type", "deponent_address", "deponent_age", "deponent_occupation"]},
        {"id": "purpose", "title": "Subject and facts", "description": "State why the affidavit is needed and the facts to be sworn.",
         "field_ids": ["purpose", "facts", "effective_date", "place_of_swearing"]},
        {"id": "conditions", "title": "Extra details", "description": "Optional supporting information.",
         "field_ids": ["special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type",
               "Leave blank to use the standard title."),
        *_jurisdiction_fields(),
        _field("deponent_name", "Deponent name", "DEPONENT NAME", "text", "required", "parties"),
        _field("deponent_type", "Deponent type", "DEPONENT TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("deponent_address", "Deponent address", "DEPONENT ADDRESS", "textarea", "required", "parties"),
        _field("deponent_age", "Deponent age (years)", "DEPONENT AGE", "number", "recommended", "parties",
               min=18, max=120),
        _field("deponent_occupation", "Occupation", "DEPONENT OCCUPATION", "text", "optional", "parties"),
        _field("purpose", "Purpose of affidavit", "PURPOSE", "textarea", "required", "purpose",
               "State the proceeding or purpose. Do not invent a purpose."),
        _field("facts", "Facts to be sworn", "FACTS", "textarea", "required", "purpose",
               "List only facts the deponent can personally affirm."),
        _field("effective_date", "Date of affidavit", "DATE OF AFFIDAVIT", "date", "required", "purpose"),
        _field("place_of_swearing", "Place of swearing", "PLACE OF SWEARING", "text", "required", "purpose"),
        _field("special_conditions", "Additional particulars", "ADDITIONAL PARTICULARS", "textarea", "optional", "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "body":
         "{document_title}\n\nAFFIDAVIT\n\nDated {effective_date}"},
        {"id": "parties", "title": "Deponent", "required": True, "body":
         "I, {deponent_name}, a {deponent_type}, aged about {deponent_age} years, occupation {deponent_occupation}, "
         "residing at {deponent_address} (the \"Deponent\"), do hereby solemnly affirm and state as follows."},
        {"id": "purpose", "title": "Purpose", "required": True, "body":
         "This affidavit is made for the following purpose: {purpose}."},
        {"id": "facts", "title": "Facts", "required": True, "body":
         "The Deponent states the following facts from personal knowledge, unless otherwise indicated:\n\n{facts}\n\n"
         "Additional particulars: {special_conditions}"},
        {"id": "verification", "title": "Verification", "required": True, "body":
         "I, the Deponent, verify that the contents of this affidavit are true to my personal knowledge, "
         "that no part of it is false, and that nothing material has been concealed. "
         "Verified at {place_of_swearing} on {effective_date}."},
        {"id": "governing_law", "title": "Jurisdiction note", "required": True, "needs_legal_context": True, "body":
         "This draft is intended for use in India as applicable in {jurisdiction_region}. "
         "Oath, attestation, stamp, and filing requirements are not completed by this draft and must be checked before use. "
         "This draft does not determine that any particular statute or form applies unless a verified legal source is attached."},
        {"id": "signatures", "title": "Signatures", "required": True, "include_signature": True, "body":
         "DEPONENT\n\nPlace: {place_of_swearing}\nDate: {effective_date}"},
    ],
}

LEGAL_NOTICE_TEMPLATE: TemplateSpec = {
    "id": "legal_notice",
    "category": "legal_document",
    "title": "Legal Notice",
    "description": "A formal notice of demand or grievance under Indian practice. Sending and service formalities are not completed by this draft.",
    "document_type": "Legal Notice",
    "jurisdiction_country": "IN",
    "legal_query": "legal notice demand grievance reply India civil dispute",
    "parties": [
        {"id": "sender", "role": "Sender", "name_field": "sender_name",
         "type_field": "sender_type", "address_field": "sender_address"},
        {"id": "recipient", "role": "Recipient", "name_field": "recipient_name",
         "type_field": "recipient_type", "address_field": "recipient_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the notice you need.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Where the dispute or demand arises.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Identify who is sending and receiving the notice.",
         "field_ids": ["sender_name", "sender_type", "sender_address", "recipient_name", "recipient_type", "recipient_address"]},
        {"id": "purpose", "title": "Subject and facts", "description": "Describe the grievance and background.",
         "field_ids": ["purpose", "facts", "effective_date"]},
        {"id": "demand", "title": "Demand", "description": "State what is demanded and by when.",
         "field_ids": ["relief_sought", "compliance_days"]},
        {"id": "conditions", "title": "Extra terms", "description": "Optional additional particulars.",
         "field_ids": ["special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("sender_name", "Sender name", "SENDER NAME", "text", "required", "parties"),
        _field("sender_type", "Sender type", "SENDER TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("sender_address", "Sender address", "SENDER ADDRESS", "textarea", "required", "parties"),
        _field("recipient_name", "Recipient name", "RECIPIENT NAME", "text", "required", "parties"),
        _field("recipient_type", "Recipient type", "RECIPIENT TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("recipient_address", "Recipient address", "RECIPIENT ADDRESS", "textarea", "required", "parties"),
        _field("purpose", "Subject of notice", "SUBJECT", "textarea", "required", "purpose"),
        _field("facts", "Background facts", "FACTS", "textarea", "required", "purpose"),
        _field("effective_date", "Date of notice", "DATE OF NOTICE", "date", "required", "purpose"),
        _field("relief_sought", "Demand / relief sought", "RELIEF SOUGHT", "textarea", "required", "demand"),
        _field("compliance_days", "Days to comply", "COMPLIANCE DAYS", "number", "recommended", "demand",
               "Leave blank if no fixed period is agreed.", min=1, max=365),
        _field("special_conditions", "Additional particulars", "ADDITIONAL PARTICULARS", "textarea", "optional", "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "body":
         "{document_title}\n\nLEGAL NOTICE\n\nDate: {effective_date}"},
        {"id": "parties", "title": "Parties", "required": True, "body":
         "FROM:\n{sender_name}, a {sender_type}, of {sender_address}\n\n"
         "TO:\n{recipient_name}, a {recipient_type}, of {recipient_address}"},
        {"id": "subject", "title": "Subject", "required": True, "body":
         "Subject: {purpose}"},
        {"id": "facts", "title": "Facts", "required": True, "body":
         "Under instructions from and on behalf of the Sender, you are informed of the following facts:\n\n{facts}\n\n"
         "Additional particulars: {special_conditions}"},
        {"id": "demand", "title": "Demand", "required": True, "body":
         "You are hereby called upon to: {relief_sought}."},
        {"id": "consequences", "title": "Consequences of non-compliance", "required": False,
         "condition": {"has_value": "compliance_days"}, "body":
         "You are called upon to comply within {compliance_days} days of receipt of this notice. "
         "Failing compliance, the Sender may pursue such remedies as are available under applicable law, "
         "without further notice, at your risk as to costs and consequences. This draft does not itself commence any proceeding."},
        {"id": "governing_law", "title": "Jurisdiction note", "required": True, "needs_legal_context": True, "body":
         "This notice is drafted with reference to India as applicable in {jurisdiction_region}, "
         "with disputes contemplated at {governing_law_seat} only if the parties have agreed that seat. "
         "Service, limitation, and mandatory pre-suit requirements are not determined by this draft unless a verified legal source is attached."},
        {"id": "signatures", "title": "Signatures", "required": True, "include_signature": True, "body":
         "Yours faithfully,\n\nFor the Sender"},
    ],
}

AUTHORIZATION_LETTER_TEMPLATE: TemplateSpec = {
    "id": "authorization_letter",
    "category": "legal_document",
    "title": "Authorization Letter",
    "description": "A letter authorizing another person to act on the principal's behalf in India for a stated purpose.",
    "document_type": "Authorization Letter",
    "jurisdiction_country": "IN",
    "legal_query": "authorization letter letter of authority agent principal India",
    "parties": [
        {"id": "principal", "role": "Principal", "name_field": "principal_name",
         "type_field": "principal_type", "address_field": "principal_address"},
        {"id": "authorized", "role": "Authorized Person", "name_field": "authorized_name",
         "type_field": "authorized_type", "address_field": "authorized_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the authorization letter you need.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Where the authorization is intended to operate.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Identify the principal and the authorized person.",
         "field_ids": ["principal_name", "principal_type", "principal_address", "authorized_name", "authorized_type", "authorized_address"]},
        {"id": "purpose", "title": "Authority", "description": "Describe what the authorized person may do.",
         "field_ids": ["purpose", "scope_of_authority", "effective_date", "end_date"]},
        {"id": "conditions", "title": "Limits and conditions", "description": "Optional limits and extra terms.",
         "field_ids": ["special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("principal_name", "Principal name", "PRINCIPAL NAME", "text", "required", "parties"),
        _field("principal_type", "Principal type", "PRINCIPAL TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("principal_address", "Principal address", "PRINCIPAL ADDRESS", "textarea", "required", "parties"),
        _field("authorized_name", "Authorized person name", "AUTHORIZED PERSON NAME", "text", "required", "parties"),
        _field("authorized_type", "Authorized person type", "AUTHORIZED PERSON TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("authorized_address", "Authorized person address", "AUTHORIZED PERSON ADDRESS", "textarea", "required", "parties"),
        _field("purpose", "Purpose of authorization", "PURPOSE", "textarea", "required", "purpose"),
        _field("scope_of_authority", "Scope of authority", "SCOPE OF AUTHORITY", "textarea", "required", "purpose",
               "List only acts the principal intends to authorize."),
        _field("effective_date", "Effective date", "EFFECTIVE DATE", "date", "required", "purpose"),
        _field("end_date", "End date", "END DATE", "date", "recommended", "purpose"),
        _field("special_conditions", "Limits or other conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "body":
         "{document_title}\n\nAUTHORIZATION LETTER\n\nDate: {effective_date}"},
        {"id": "parties", "title": "Parties", "required": True, "body":
         "I, {principal_name}, a {principal_type}, of {principal_address} (the \"Principal\"), "
         "hereby authorize {authorized_name}, a {authorized_type}, of {authorized_address} "
         "(the \"Authorized Person\"), to act on my behalf as stated below."},
        {"id": "purpose", "title": "Purpose", "required": True, "body":
         "Purpose of this authorization: {purpose}."},
        {"id": "authority", "title": "Authority granted", "required": True, "body":
         "The Authorized Person is authorized to do the following: {scope_of_authority}. "
         "This letter does not grant authority beyond what is expressly stated."},
        {"id": "term", "title": "Term", "required": True, "body":
         "This authorization takes effect on {effective_date} and continues until {end_date}, "
         "unless revoked earlier in writing by the Principal, or for so long as needed for the stated purpose if no end date is supplied."},
        {"id": "limits", "title": "Limits", "required": False, "condition": {"has_value": "special_conditions"}, "body":
         "This authorization is subject to the following limits and conditions: {special_conditions}."},
        {"id": "governing_law", "title": "Jurisdiction note", "required": True, "needs_legal_context": True, "body":
         "This letter is intended for use in India as applicable in {jurisdiction_region}. "
         "Whether a power of attorney, board resolution, or other formal instrument is required instead of or in addition to this letter "
         "must be checked before reliance. This draft is not itself a registered power of attorney."},
        {"id": "signatures", "title": "Signatures", "required": True, "include_signature": True, "body":
         "IN WITNESS WHEREOF the Principal has signed this Authorization Letter on the date first written above."},
    ],
}

CONSUMER_COMPLAINT_TEMPLATE: TemplateSpec = {
    "id": "consumer_complaint",
    "category": "legal_document",
    "title": "Consumer Complaint",
    "description": "A consumer dispute complaint draft for India. Forum filing and fee formalities are not completed by this draft.",
    "document_type": "Consumer Complaint",
    "jurisdiction_country": "IN",
    "legal_query": "consumer complaint deficiency goods services Consumer Protection Act India",
    "parties": [
        {"id": "complainant", "role": "Complainant", "name_field": "complainant_name",
         "type_field": "complainant_type", "address_field": "complainant_address"},
        {"id": "opposite", "role": "Opposite Party", "name_field": "opposite_party_name",
         "type_field": "opposite_party_type", "address_field": "opposite_party_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the consumer complaint you need.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Where the transaction or dispute arose.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Identify the complainant and the opposite party.",
         "field_ids": ["complainant_name", "complainant_type", "complainant_address",
                       "opposite_party_name", "opposite_party_type", "opposite_party_address"]},
        {"id": "purpose", "title": "Transaction and grievance", "description": "Describe the goods or services and what went wrong.",
         "field_ids": ["product_or_service", "transaction_date", "purpose", "facts", "effective_date"]},
        {"id": "demand", "title": "Relief", "description": "State the relief sought and any amount claimed.",
         "field_ids": ["relief_sought", "claim_amount", "claim_currency"]},
        {"id": "conditions", "title": "Extra details", "description": "Optional supporting information.",
         "field_ids": ["special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("complainant_name", "Complainant name", "COMPLAINANT NAME", "text", "required", "parties"),
        _field("complainant_type", "Complainant type", "COMPLAINANT TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("complainant_address", "Complainant address", "COMPLAINANT ADDRESS", "textarea", "required", "parties"),
        _field("opposite_party_name", "Opposite party name", "OPPOSITE PARTY NAME", "text", "required", "parties"),
        _field("opposite_party_type", "Opposite party type", "OPPOSITE PARTY TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("opposite_party_address", "Opposite party address", "OPPOSITE PARTY ADDRESS", "textarea", "required", "parties"),
        _field("product_or_service", "Goods or services", "PRODUCT OR SERVICE", "textarea", "required", "purpose"),
        _field("transaction_date", "Transaction / purchase date", "TRANSACTION DATE", "date", "recommended", "purpose"),
        _field("purpose", "Nature of complaint", "NATURE OF COMPLAINT", "textarea", "required", "purpose"),
        _field("facts", "Detailed facts", "FACTS", "textarea", "required", "purpose"),
        _field("effective_date", "Date of complaint", "DATE OF COMPLAINT", "date", "required", "purpose"),
        _field("relief_sought", "Relief sought", "RELIEF SOUGHT", "textarea", "required", "demand"),
        _field("claim_amount", "Amount claimed", "AMOUNT CLAIMED", "currency", "optional", "demand",
               "Leave blank if no specific amount is claimed.", min=0),
        _field("claim_currency", "Currency", "CURRENCY", "select", "optional", "demand",
               options=[{"value": "INR", "label": "INR"}]),
        _field("special_conditions", "Additional particulars", "ADDITIONAL PARTICULARS", "textarea", "optional", "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "body":
         "{document_title}\n\nCONSUMER COMPLAINT\n\nDate: {effective_date}"},
        {"id": "parties", "title": "Parties", "required": True, "body":
         "BETWEEN:\n\n(1) {complainant_name}, a {complainant_type}, of {complainant_address} (the \"Complainant\"); and\n\n"
         "(2) {opposite_party_name}, a {opposite_party_type}, of {opposite_party_address} (the \"Opposite Party\")."},
        {"id": "transaction", "title": "Transaction", "required": True, "body":
         "The complaint concerns the following goods or services: {product_or_service}. "
         "Transaction / purchase date: {transaction_date}."},
        {"id": "facts", "title": "Facts", "required": True, "body":
         "The Complainant states the following facts:\n\n{facts}\n\nAdditional particulars: {special_conditions}"},
        {"id": "cause", "title": "Cause of action", "required": True, "body":
         "Nature of the complaint: {purpose}. "
         "The draft does not assert that any particular consumer forum has jurisdiction unless a verified legal source is attached."},
        {"id": "relief", "title": "Relief sought", "required": True, "body":
         "The Complainant seeks the following relief: {relief_sought}."},
        {"id": "claim_amount", "title": "Amount claimed", "required": False, "condition": {"has_value": "claim_amount"}, "body":
         "Amount claimed: {claim_currency} {claim_amount}. The draft does not invent interest, costs, or other sums that were not supplied."},
        {"id": "governing_law", "title": "Jurisdiction note", "required": True, "needs_legal_context": True, "body":
         "This draft is intended with reference to India as applicable in {jurisdiction_region}. "
         "Forum, limitation, fees, and filing formalities under consumer protection law are not completed by this draft "
         "and must be checked before filing."},
        {"id": "signatures", "title": "Signatures", "required": True, "include_signature": True, "body":
         "Place: {governing_law_seat}\nDate: {effective_date}\n\nCOMPLAINANT"},
    ],
}

COMPLAINT_TEMPLATE: TemplateSpec = {
    "id": "complaint",
    "category": "legal_document",
    "title": "General Complaint / Police Complaint",
    "description": "A draft complaint or police complaint narrative for India. Filing with police or any authority is not completed by this draft.",
    "document_type": "Complaint",
    "jurisdiction_country": "IN",
    "legal_query": "police complaint FIR complaint to authority India criminal civil grievance",
    "parties": [
        {"id": "complainant", "role": "Complainant", "name_field": "complainant_name",
         "type_field": "complainant_type", "address_field": "complainant_address"},
        {"id": "accused", "role": "Accused / Opposite Party", "name_field": "accused_name",
         "type_field": "accused_type", "address_field": "accused_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the complaint draft you need.",
         "field_ids": ["document_title", "complaint_kind"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Where the incident occurred or will be reported.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Identify the complainant and the accused or opposite party.",
         "field_ids": ["complainant_name", "complainant_type", "complainant_address",
                       "accused_name", "accused_type", "accused_address"]},
        {"id": "purpose", "title": "Incident", "description": "Describe what happened and where it should be reported.",
         "field_ids": ["purpose", "facts", "incident_date", "incident_place", "police_station", "effective_date"]},
        {"id": "demand", "title": "Request", "description": "State the action requested.",
         "field_ids": ["relief_sought"]},
        {"id": "conditions", "title": "Extra details", "description": "Optional supporting information.",
         "field_ids": ["special_conditions"]},
        {"id": "review", "title": "Review", "description": "Check the details before generating a draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        _field("complaint_kind", "Complaint kind", "COMPLAINT KIND", "select", "required", "type",
               options=[{"value": "police", "label": "Police complaint / FIR narrative"},
                        {"value": "general", "label": "General complaint to an authority"}]),
        *_jurisdiction_fields(),
        _field("complainant_name", "Complainant name", "COMPLAINANT NAME", "text", "required", "parties"),
        _field("complainant_type", "Complainant type", "COMPLAINANT TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("complainant_address", "Complainant address", "COMPLAINANT ADDRESS", "textarea", "required", "parties"),
        _field("accused_name", "Accused / opposite party name", "ACCUSED NAME", "text", "required", "parties"),
        _field("accused_type", "Accused / opposite party type", "ACCUSED TYPE", "select", "required", "parties",
               options=list(PARTY_TYPE_OPTIONS)),
        _field("accused_address", "Accused / opposite party address", "ACCUSED ADDRESS", "textarea", "recommended", "parties"),
        _field("purpose", "Subject of complaint", "SUBJECT", "textarea", "required", "purpose"),
        _field("facts", "Detailed facts of the incident", "FACTS", "textarea", "required", "purpose"),
        _field("incident_date", "Date of incident", "INCIDENT DATE", "date", "required", "purpose"),
        _field("incident_place", "Place of incident", "INCIDENT PLACE", "text", "required", "purpose"),
        _field("police_station", "Police station / authority", "POLICE STATION OR AUTHORITY", "text", "recommended", "purpose"),
        _field("effective_date", "Date of complaint", "DATE OF COMPLAINT", "date", "required", "purpose"),
        _field("relief_sought", "Action requested", "ACTION REQUESTED", "textarea", "required", "demand"),
        _field("special_conditions", "Additional particulars", "ADDITIONAL PARTICULARS", "textarea", "optional", "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title", "required": True, "body":
         "{document_title}\n\nCOMPLAINT ({complaint_kind})\n\nDate: {effective_date}"},
        {"id": "parties", "title": "Parties", "required": True, "body":
         "Complainant: {complainant_name}, a {complainant_type}, of {complainant_address}.\n\n"
         "Accused / Opposite Party: {accused_name}, a {accused_type}, of {accused_address}."},
        {"id": "subject", "title": "Subject", "required": True, "body":
         "Subject: {purpose}\n\n"
         "Incident date: {incident_date}. Place of incident: {incident_place}. "
         "Police station / authority: {police_station}."},
        {"id": "facts", "title": "Facts", "required": True, "body":
         "The Complainant states the following facts:\n\n{facts}\n\nAdditional particulars: {special_conditions}"},
        {"id": "request", "title": "Request", "required": True, "body":
         "The Complainant requests that appropriate action be taken as follows: {relief_sought}. "
         "This draft does not register an FIR or commence any proceeding."},
        {"id": "governing_law", "title": "Jurisdiction note", "required": True, "needs_legal_context": True, "body":
         "This draft is intended with reference to India as applicable in {jurisdiction_region}. "
         "Police station jurisdiction, cognizable offences, and filing formalities are not determined by this draft "
         "unless a verified legal source is attached. Obtain professional review before filing."},
        {"id": "signatures", "title": "Signatures", "required": True, "include_signature": True, "body":
         "Place: {incident_place}\nDate: {effective_date}\n\nCOMPLAINANT"},
    ],
}

from .extra_templates import EXTRA_TEMPLATES

TEMPLATES: dict[str, TemplateSpec] = {
    NDA_TEMPLATE["id"]: NDA_TEMPLATE,
    SERVICE_AGREEMENT_TEMPLATE["id"]: SERVICE_AGREEMENT_TEMPLATE,
    RENT_LEASE_TEMPLATE["id"]: RENT_LEASE_TEMPLATE,
    AFFIDAVIT_TEMPLATE["id"]: AFFIDAVIT_TEMPLATE,
    LEGAL_NOTICE_TEMPLATE["id"]: LEGAL_NOTICE_TEMPLATE,
    AUTHORIZATION_LETTER_TEMPLATE["id"]: AUTHORIZATION_LETTER_TEMPLATE,
    CONSUMER_COMPLAINT_TEMPLATE["id"]: CONSUMER_COMPLAINT_TEMPLATE,
    COMPLAINT_TEMPLATE["id"]: COMPLAINT_TEMPLATE,
    **EXTRA_TEMPLATES,
}


def list_templates() -> list[TemplateSpec]:
    return [TEMPLATES[key] for key in TEMPLATES]


def get_template(template_id: str) -> TemplateSpec:
    template = TEMPLATES.get(template_id)
    if template is None:
        raise KeyError(template_id)
    return template
