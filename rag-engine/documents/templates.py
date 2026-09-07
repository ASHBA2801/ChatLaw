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
    "title": "Non-Disclosure Agreement (NDA)",
    "description": "A mutual or one-way confidentiality agreement based on Startup India model format with exclusions, non-solicitation, and dispute clauses.",
    "document_type": "Non-Disclosure Agreement",
    "jurisdiction_country": "IN",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "Mutual and unilateral confidential disclosures in India.",
    "source": {
        "authority": "Startup India Model Contracts & Indian Contract Act, 1872",
        "url": "https://www.startupindia.gov.in/content/sih/en/model-contracts.html",
        "document_name": "Model Non-Disclosure Agreement",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on appropriate non-judicial stamp paper as prescribed under State Stamp Act",
    ],
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
    "description": "A commercial services contract between a client and a service provider based on Startup India model format.",
    "document_type": "Service Agreement",
    "jurisdiction_country": "IN",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "Commercial and independent contractor services in India.",
    "source": {
        "authority": "Startup India Model Contracts & Indian Contract Act, 1872",
        "url": "https://www.startupindia.gov.in/content/sih/en/model-contracts.html",
        "document_name": "Model Service Agreement",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on non-judicial stamp paper as per State Stamp Act",
    ],
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
    "description": "A residential or commercial tenancy agreement based on Indian model formats, with recitals, numbered covenants, and property schedule.",
    "document_type": "Rent / Lease Agreement",
    "jurisdiction_country": "IN",
    "language": ["English", "Hindi"],
    "version": "2026.1",
    "applicability": "Residential and commercial tenancies across Indian States under applicable State Rent Control / Tenancy Acts.",
    "source": {
        "authority": "Startup India Model Contracts & Ministry of Housing and Urban Affairs Model Tenancy Act",
        "url": "https://www.startupindia.gov.in/content/sih/en/model-contracts.html",
        "document_name": "Model Tenancy Agreement",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on non-judicial stamp paper of value prescribed by State Stamp Act",
        "Mandatory registration before Sub-Registrar if tenancy term exceeds 11 months under Section 107 of Transfer of Property Act, 1882",
        "Attestation by two independent witnesses",
    ],
    "legal_query": "lease rent landlord tenant property agreement India",
    "parties": [
        {"id": "landlord", "role": "Landlord / Lessor", "name_field": "landlord_name",
         "type_field": "landlord_type", "address_field": "landlord_address"},
        {"id": "tenant", "role": "Tenant / Lessee", "name_field": "tenant_name",
         "type_field": "tenant_type", "address_field": "tenant_address"},
    ],
    "witnesses": [
        {"id": "witness_1", "role": "Witness 1", "name_field": "witness_1_name", "address_field": "witness_1_address"},
        {"id": "witness_2", "role": "Witness 2", "name_field": "witness_2_name", "address_field": "witness_2_address"},
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
        _field("witness_1_name", "Witness 1 name", "WITNESS 1 NAME", "text", "optional", "conditions"),
        _field("witness_1_address", "Witness 1 address", "WITNESS 1 ADDRESS", "text", "optional", "conditions"),
        _field("witness_2_name", "Witness 2 name", "WITNESS 2 NAME", "text", "optional", "conditions"),
        _field("witness_2_address", "Witness 2 address", "WITNESS 2 ADDRESS", "text", "optional", "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Title and Preamble", "required": True, "body":
         "{document_title}\n\nRENTAL AGREEMENT\n\nThis Rent / Lease Agreement is made and executed on this {effective_date} at {governing_law_seat}, {jurisdiction_region} for {property_use} premises."},
        {"id": "parties", "title": "Parties", "required": True, "body":
         "BY AND BETWEEN:\n\n"
         "(1) {landlord_name}, a {landlord_type}, residing at {landlord_address} (hereinafter referred to as the \"LANDLORD / LESSOR\", which expression shall include their heirs, executors, and assigns) of the FIRST PART;\n\n"
         "AND\n\n"
         "(2) {tenant_name}, a {tenant_type}, residing at {tenant_address} (hereinafter referred to as the \"TENANT / LESSEE\", which expression shall include their heirs and permitted assigns) of the SECOND PART."},
        {"id": "recitals", "title": "Recitals", "required": True, "body":
         "WHEREAS:\n"
         "A. The Landlord is the absolute lawful owner of the premises situated at {property_address}, fully described in the Schedule hereunder.\n"
         "B. The Tenant has approached the Landlord to take on rent the Scheduled Premises for {property_use} use, and the Landlord has agreed on the terms and covenants herein.\n\n"
         "NOW THIS AGREEMENT WITNESSETH AND IT IS MUTUALLY AGREED AS FOLLOWS:"},
        {"id": "property", "title": "1. Demised Premises", "required": True, "body":
         "1.1. The Landlord hereby lets out and the Tenant takes on rent the premises situated at {property_address}.\n"
         "1.2. Description of premises: {property_description}. The Tenant shall use the premises exclusively for {property_use} purposes and shall not change such use without prior written consent."},
        {"id": "term", "title": "2. Term and Duration", "required": True, "body":
         "2.1. The tenancy shall commence on {effective_date} and expire on {end_date}, unless terminated earlier in accordance with this Agreement or applicable law."},
        {"id": "rent", "title": "3. Rent and Payment", "required": False, "condition": {"has_value": "rent_amount"}, "body":
         "3.1. The Tenant shall pay a monthly rent of {rent_currency} {rent_amount} ({rent_frequency}) on or before the 10th day of each calendar month in advance."},
        {"id": "deposit", "title": "4. Security Deposit", "required": False, "condition": {"has_value": "deposit_amount"}, "body":
         "4.1. The Tenant has deposited with the Landlord an interest-free refundable security deposit of {rent_currency} {deposit_amount}.\n"
         "4.2. The Landlord shall refund this deposit upon vacant, peaceful handover of the premises, subject to deduction of unpaid rent or damage exceeding normal wear and tear."},
        {"id": "tenant_obligations", "title": "5. Tenant Covenants", "required": True, "body":
         "5.1. The Tenant shall pay agreed sums on time, maintain the premises in tenantable repair, and shall NOT sublet, assign, or part with possession of the premises to any third party."},
        {"id": "landlord_obligations", "title": "6. Landlord Covenants", "required": True, "body":
         "6.1. The Landlord covenants that the Tenant paying rent shall peaceably hold and enjoy the premises without interruption during the tenancy.\n"
         "6.2. The Landlord shall bear municipal property taxes and carry out necessary major structural repairs."},
        {"id": "maintenance", "title": "7. Maintenance and Utilities", "required": True, "body":
         "7.1. Routine maintenance responsibility: {maintenance_responsibility}. Electricity, water, and utility charges as per meter readings shall be paid by the Tenant."},
        {"id": "termination", "title": "8. Termination and Notice", "required": False, "condition": {"has_value": "termination_notice_days"}, "body":
         "8.1. Either party may terminate this tenancy by serving {termination_notice_days} days' prior written notice to the other party.\n"
         "8.2. On expiration or termination, the Tenant shall peacefully vacate and deliver vacant possession to the Landlord."},
        {"id": "dispute_resolution", "title": "9. Dispute Resolution", "required": True, "body":
         "9.1. Disputes arising out of this Agreement shall first be discussed amicably. If unresolved, disputes shall be referred to {dispute_resolution} at {governing_law_seat}."},
        {"id": "governing_law", "title": "10. Governing Law", "required": True, "needs_legal_context": True, "body":
         "10.1. This Agreement is governed by the laws of India as applicable in {jurisdiction_region}.\n"
         "10.2. Stamp duty and registration requirements under the State Stamp Act and Registration Act, 1908 should be verified prior to formal execution."},
        {"id": "schedule", "title": "Schedule of Property", "required": True, "body":
         "SCHEDULE OF PROPERTY:\n\n"
         "All that residential / commercial premises situated at: {property_address}.\n"
         "Description: {property_description}.\n"
         "Situate within {governing_law_seat}, {jurisdiction_region}."},
        {"id": "signatures", "title": "Signatures and Witnesses", "required": True, "include_signature": True, "body":
         "IN WITNESS WHEREOF, the Landlord and Tenant have signed this Agreement on the day, month, and year first written above in presence of witnesses."},
    ],
}

AFFIDAVIT_TEMPLATE: TemplateSpec = {
    "id": "affidavit",
    "category": "affidavit",
    "title": "General Affidavit",
    "description": "A formal sworn affidavit before a Notary Public / Oath Commissioner with deponent particulars, solemn affirmation, and statutory verification.",
    "document_type": "Affidavit",
    "jurisdiction_country": "IN",
    "language": ["English", "Hindi"],
    "version": "2026.1",
    "applicability": "General sworn statements of fact for submission before courts, authorities, and institutions across India.",
    "source": {
        "authority": "Notaries Act, 1952 & High Court Civil Rules of Practice",
        "url": "https://indiacode.nic.in/handle/123456789/1572",
        "document_name": "Standard Format of General Affidavit before Notary Public",
        "reference_date": "1952 (as amended)",
    },
    "execution_requirements": [
        "Execution on non-judicial stamp paper of prescribed denomination under State Stamp Act",
        "Mandatory oath and verification administered before an authorized Notary Public or Oath Commissioner",
    ],
    "legal_query": "affidavit sworn statement verification of facts India oath notary",
    "parties": [
        {"id": "deponent", "role": "Deponent", "name_field": "deponent_name",
         "type_field": "deponent_type", "address_field": "deponent_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Confirm the affidavit you need.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Where this affidavit is intended to be used.",
         "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Deponent", "description": "Identify the person who will swear the facts.",
         "field_ids": ["deponent_name", "deponent_type", "deponent_parent_spouse", "deponent_address", "deponent_age", "deponent_occupation"]},
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
        _field("deponent_parent_spouse", "Father / Spouse name", "PARENT OR SPOUSE NAME", "text", "optional", "parties"),
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
        {"id": "title", "title": "Heading and Solemn Affirmation", "required": True, "body":
         "BEFORE THE NOTARY PUBLIC / OATH COMMISSIONER AT {place_of_swearing}, {jurisdiction_region}\n\n"
         "AFFIDAVIT\n\n"
         "I, {deponent_name}, son/daughter/wife of {deponent_parent_spouse}, a {deponent_type}, aged about {deponent_age} years, "
         "occupation {deponent_occupation}, residing at {deponent_address} (the \"Deponent\"), do hereby solemnly affirm and state on oath as under:"},
        {"id": "purpose", "title": "1. Competence and Purpose", "required": True, "body":
         "1. That I am the deponent herein, fully conversant with the facts deposed herein, and competent to swear this Affidavit.\n"
         "2. That this Affidavit is sworn in connection with: {purpose}."},
        {"id": "facts", "title": "2. Sworn Statements of Fact", "required": True, "body":
         "3. That the Deponent states and affirms the following facts from personal knowledge:\n\n{facts}\n\n"
         "Additional particulars: {special_conditions}"},
        {"id": "verification", "title": "3. Statutory Verification", "required": True, "body":
         "VERIFICATION\n\n"
         "I, the Deponent above named, do hereby solemnly verify and declare that the contents of paragraphs 1 to 3 above are true and correct "
         "to my personal knowledge and belief, no part of it is false, and nothing material has been concealed therefrom.\n\n"
         "Verified at {place_of_swearing} on this {effective_date}."},
        {"id": "signatures", "title": "Signatures and Notary Jurat", "required": True, "include_signature": True, "body":
         "DEPONENT\n\n"
         "Identified by me:\nAdvocate\n\n"
         "Solemnly affirmed and signed before me on this {effective_date} at {place_of_swearing}.\n\n"
         "NOTARY PUBLIC / OATH COMMISSIONER\n(Seal and Signature)"},
    ],
}

LEGAL_NOTICE_TEMPLATE: TemplateSpec = {
    "id": "legal_notice",
    "category": "notice",
    "title": "Legal Notice",
    "description": "Advocate legal notice for civil and commercial demands, issued under Registered Post with A.D. with factual chronology and statutory consequence notice.",
    "document_type": "Legal Notice",
    "jurisdiction_country": "IN",
    "language": ["English", "Hindi"],
    "version": "2026.1",
    "applicability": "Pre-litigation demand notice under Indian civil and commercial law.",
    "source": {
        "authority": "Bar Council of India Standards & Code of Civil Procedure, 1908",
        "url": "https://barcouncilofindia.org",
        "document_name": "Standard Format of Advocate Legal Notice",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Dispatch via Registered Post with Acknowledgement Due (RPAD) or Speed Post",
        "Preserve postal booking receipt and delivery tracking report for court record",
    ],
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
         "field_ids": ["sender_name", "sender_type", "sender_address", "recipient_name", "recipient_type", "recipient_address", "advocate_name"]},
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
        _field("sender_name", "Sender (Client) full name", "SENDER NAME", "text", "required", "parties"),
        _field("sender_type", "Sender type", "SENDER TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("sender_address", "Sender address", "SENDER ADDRESS", "textarea", "required", "parties"),
        _field("recipient_name", "Recipient full name", "RECIPIENT NAME", "text", "required", "parties"),
        _field("recipient_type", "Recipient type", "RECIPIENT TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("recipient_address", "Recipient address", "RECIPIENT ADDRESS", "textarea", "required", "parties"),
        _field("advocate_name", "Advocate / Counsel name", "ADVOCATE NAME", "text", "optional", "parties"),
        _field("purpose", "Subject of notice", "SUBJECT", "textarea", "required", "purpose"),
        _field("facts", "Background facts and chronology", "FACTS", "textarea", "required", "purpose"),
        _field("effective_date", "Date of notice", "DATE OF NOTICE", "date", "required", "purpose"),
        _field("relief_sought", "Demand / relief sought", "RELIEF SOUGHT", "textarea", "required", "demand"),
        _field("compliance_days", "Days to comply", "COMPLIANCE DAYS", "number", "recommended", "demand",
               "Standard 15 or 30 days.", min=1, max=365),
        _field("special_conditions", "Additional particulars", "ADDITIONAL PARTICULARS", "textarea", "optional", "conditions"),
    ],
    "clauses": [
        {"id": "title", "title": "Dispatch Mode and Header", "required": True, "body":
         "BY REGISTERED POST WITH ACKNOWLEDGEMENT DUE / SPEED POST\n\n"
         "LEGAL NOTICE\n\n"
         "Date: {effective_date}\n\n"
         "TO:\n"
         "{recipient_name},\n"
         "a {recipient_type},\n"
         "residing/having office at:\n"
         "{recipient_address}.\n\n"
         "SUBJECT: {purpose}\n\n"
         "Sir / Madam,"},
        {"id": "parties", "title": "Instructions and Client Identification", "required": True, "body":
         "Under instructions from and on behalf of my client, {sender_name}, a {sender_type}, residing at {sender_address} "
         "(hereinafter referred to as \"my Client\"), I hereby serve upon you this Legal Notice as under:"},
        {"id": "facts", "title": "1. Factual Chronology and Contractual Relations", "required": True, "body":
         "1.1. That my Client states the following factual background:\n\n{facts}\n\n"
         "1.2. Additional particulars: {special_conditions}"},
        {"id": "demand", "title": "2. Breach, Default, and Legal Demand", "required": True, "body":
         "2.1. That you have committed default and breach of your binding legal obligations towards my Client.\n"
         "2.2. You are hereby called upon to: {relief_sought}."},
        {"id": "consequences", "title": "3. Notice Period and Legal Consequences", "required": True, "needs_legal_context": True, "body":
         "3.1. TAKE NOTICE that you are hereby required to comply with the above demands within a period of {compliance_days} days from the date of receipt of this notice.\n"
         "3.2. Failing compliance within the stipulated period of {compliance_days} days, my Client has given me peremptory instructions to institute appropriate civil and/or criminal legal proceedings "
         "against you in the competent Court of Law having jurisdiction at {governing_law_seat}, {jurisdiction_region}, entirely at your risk, cost, and consequence."},
        {"id": "signatures", "title": "Advocate / Counsel Signature", "required": True, "include_signature": True, "body":
         "Yours faithfully,\n\n"
         "ADVOCATE FOR THE SENDER\n"
         "({advocate_name})\n"
         "Place: {governing_law_seat}"},
    ],
}

AUTHORIZATION_LETTER_TEMPLATE: TemplateSpec = {
    "id": "authorization_letter",
    "category": "affidavit",
    "title": "Authorization Letter",
    "description": "A formal letter of authority authorizing a representative to act on the principal's behalf before authorities or private bodies.",
    "document_type": "Authorization Letter",
    "jurisdiction_country": "IN",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "Letter of authority for representation before administrative bodies in India.",
    "source": {
        "authority": "Department of Legal Affairs, Government of India",
        "url": "https://legalaffairs.gov.in",
        "document_name": "Standard Format of Letter of Authority",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Signature on company letterhead or with identity verification",
    ],
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
    "category": "complaint",
    "title": "Consumer Complaint",
    "description": "Formal consumer dispute complaint under Section 35 of the Consumer Protection Act, 2019 before the District Commission with cause title, grounds, prayer, and verification.",
    "document_type": "Consumer Complaint",
    "jurisdiction_country": "IN",
    "language": ["English", "Hindi"],
    "version": "2026.1",
    "applicability": "Filing consumer complaints under Consumer Protection Act, 2019 before District Consumer Disputes Redressal Commissions in India.",
    "source": {
        "authority": "Department of Consumer Affairs, Government of India & e-Daakhil Portal",
        "url": "https://edaakhil.nic.in",
        "document_name": "Model Consumer Complaint Format under Section 35 CPA 2019",
        "reference_date": "2019 (as amended)",
    },
    "execution_requirements": [
        "Filing before the jurisdictional District Consumer Disputes Redressal Commission based on complainant's residence or opposite party's workplace",
        "Payment of prescribed court/forum fee (exempt up to Rs. 5 Lakhs claim value)",
        "Accompanied by an affidavit of verification and supporting invoices/documents",
    ],
    "legal_query": "consumer complaint deficiency goods services Consumer Protection Act India Section 35",
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
        {"id": "title", "title": "Cause Title and Forum", "required": True, "body":
         "BEFORE THE HON'BLE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION AT {governing_law_seat}, {jurisdiction_region}\n\n"
         "CONSUMER COMPLAINT NO. _____ OF 2026\n\n"
         "IN THE MATTER OF:\n\n"
         "{complainant_name}, a {complainant_type}, residing at {complainant_address}\n"
         "... COMPLAINANT\n\n"
         "VERSUS\n\n"
         "{opposite_party_name}, a {opposite_party_type}, having office/residence at {opposite_party_address}\n"
         "... OPPOSITE PARTY\n\n"
         "COMPLAINT UNDER SECTION 35 OF THE CONSUMER PROTECTION ACT, 2019\n\n"
         "MOST RESPECTFULLY SHOWETH:"},
        {"id": "parties", "title": "1. Description of the Parties", "required": True, "body":
         "1.1. That the Complainant is a consumer within the meaning of Section 2(7) of the Consumer Protection Act, 2019, having purchased/availed {product_or_service} for consideration.\n"
         "1.2. That the Opposite Party is a trader/service provider having office/business at {opposite_party_address}."},
        {"id": "transaction", "title": "2. Facts of the Case and Transaction", "required": True, "body":
         "2.1. That on or about {transaction_date}, the Complainant availed/purchased {product_or_service} from the Opposite Party.\n"
         "2.2. Statement of Facts: {facts}\n"
         "2.3. Additional particulars: {special_conditions}"},
        {"id": "cause", "title": "3. Deficiency in Service / Unfair Trade Practice", "required": True, "body":
         "3.1. That the Opposite Party committed deficiency in service and/or unfair trade practice under Section 2(11) and Section 2(47) of the Act as follows: {purpose}.\n"
         "3.2. That despite representations and requests, the Opposite Party failed to redress the grievance of the Complainant."},
        {"id": "governing_law", "title": "4. Jurisdiction and Limitation", "required": True, "needs_legal_context": True, "body":
         "4.1. That the cause of action arose within the territorial jurisdiction of this Hon'ble Commission at {governing_law_seat}, {jurisdiction_region}.\n"
         "4.2. That this Complaint is filed within the two-year limitation period prescribed under Section 69 of the Consumer Protection Act, 2019."},
        {"id": "relief", "title": "5. Prayer (Relief Claimed)", "required": True, "body":
         "PRAYER:\n\n"
         "Wherefore, the Complainant most respectfully prays that this Hon'ble Commission may be pleased to:\n"
         "(a) Direct the Opposite Party to: {relief_sought};\n"
         "(b) Award the claim amount of {claim_currency} {claim_amount} along with interest;\n"
         "(c) Award compensation towards mental agony, harassment, and litigation expenses;\n"
         "(d) Pass such further order(s) as this Hon'ble Commission deems fit in the interest of justice."},
        {"id": "verification", "title": "Statutory Verification", "required": True, "body":
         "VERIFICATION\n\n"
         "I, {complainant_name}, the Complainant above named, do hereby verify and declare that the contents of paragraphs 1 to 5 "
         "of the above complaint are true and correct to the best of my knowledge, information, and belief, and nothing material has been concealed therefrom.\n\n"
         "Verified at {governing_law_seat} on this {effective_date}."},
        {"id": "signatures", "title": "Signatures", "required": True, "include_signature": True, "body":
         "COMPLAINANT\n\nPlace: {governing_law_seat}\nDate: {effective_date}"},
    ],
}

COMPLAINT_TEMPLATE: TemplateSpec = {
    "id": "complaint",
    "category": "complaint",
    "title": "General Complaint / Police Complaint",
    "description": "A formal police complaint / First Information statement narrative for reporting cognizable offences before the Station House Officer.",
    "document_type": "Complaint",
    "jurisdiction_country": "IN",
    "language": ["English", "Hindi"],
    "version": "2026.1",
    "applicability": "Filing complaints before police authorities or statutory enforcement agencies in India.",
    "source": {
        "authority": "Ministry of Home Affairs & Bharatiya Nagarik Suraksha Sanhita, 2023 / Cr.P.C.",
        "url": "https://mha.gov.in",
        "document_name": "Standard Format of Police Information / Complaint",
        "reference_date": "2023",
    },
    "execution_requirements": [
        "Submission in person or by registered post to the jurisdictional Station House Officer (SHO)",
        "Complainant is entitled to receive a free certified copy of the FIR upon registration under Section 173(2) BNSS / 154(2) Cr.P.C.",
    ],
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
        {"id": "title", "title": "Authority Heading and Subject", "required": True, "body":
         "BEFORE THE STATION HOUSE OFFICER / OFFICER-IN-CHARGE\n"
         "POLICE STATION: {police_station}, {incident_place}, {jurisdiction_region}\n\n"
         "COMPLAINT / FIRST INFORMATION STATEMENT\n"
         "[Under Section 173 of Bharatiya Nagarik Suraksha Sanhita, 2023 / Section 154 Cr.P.C.]\n\n"
         "Date: {effective_date}"},
        {"id": "parties", "title": "1. Particulars of Complainant and Accused", "required": True, "body":
         "1. Informant / Complainant: {complainant_name}, a {complainant_type}, residing at {complainant_address}.\n"
         "2. Accused / Suspect: {accused_name}, a {accused_type}, residing/having office at {accused_address}."},
        {"id": "subject", "title": "2. Time, Place, and Incident Overview", "required": True, "body":
         "Subject: {purpose}\n"
         "Date and Time of Occurrence: {incident_date}\n"
         "Place of Occurrence: {incident_place}\n"
         "Jurisdictional Police Station: {police_station}"},
        {"id": "facts", "title": "3. Statement of Facts and Cognizable Offences", "required": True, "body":
         "The Complainant states the following facts regarding the commission of offences:\n\n{facts}\n\n"
         "Additional particulars: {special_conditions}"},
        {"id": "request", "title": "4. Prayer / Action Requested", "required": True, "body":
         "PRAYER:\n\n"
         "It is therefore most respectfully prayed that this Police Authority may be pleased to register a First Information Report (FIR) "
         "against the accused person(s), investigate the matter strictly in accordance with law, and take action as requested: {relief_sought}."},
        {"id": "signatures", "title": "Signatures", "required": True, "include_signature": True, "body":
         "Yours faithfully,\n\n"
         "INFORMANT / COMPLAINANT\n"
         "({complainant_name})\n"
         "Place: {incident_place}\n"
         "Date: {effective_date}"},
    ],
}

from .extra_templates import EXTRA_TEMPLATES
from .model_templates import MODEL_TEMPLATES

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
    **MODEL_TEMPLATES,
}


def list_templates() -> list[TemplateSpec]:
    return [TEMPLATES[key] for key in TEMPLATES]


def get_template(template_id: str) -> TemplateSpec:
    template = TEMPLATES.get(template_id)
    if template is None:
        raise KeyError(template_id)
    return template
