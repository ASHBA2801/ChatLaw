"""Official model legal document templates based on Indian statutory authorities,
State registration departments, Startup India model contracts, NALSA, and judicial portals.
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
            "Required because contract, stamp duty, and property rules vary within India.",
            options=REGION_OPTIONS,
        ),
        _field(
            "governing_law_seat",
            "Seat / place for disputes",
            "DISPUTE SEAT",
            "text",
            "recommended",
            step,
            "City or district where disputes are to be heard (e.g. Chennai, Coimbatore, Bengaluru).",
        ),
    ]


# =============================================================================
# 1. TAMIL NADU RENTAL AGREEMENT (வாடகை ஒப்பந்த பத்திரம்)
# Official reference: Tamil Nadu Regulation of Rights and Responsibilities of
# Landlords and Tenants Act, 2017 (TNRRRLT Act) & TN Tenancy Portal.
# =============================================================================
RENTAL_AGREEMENT_TAMIL_NADU_TEMPLATE: TemplateSpec = {
    "id": "rental_agreement_tamil_nadu",
    "category": "agreement",
    "title": "Tamil Nadu Rental Agreement (வாடகை ஒப்பந்த பத்திரம்)",
    "description": "Standard 11-month residential tenancy agreement compliant with the Tamil Nadu Regulation of Rights and Responsibilities of Landlords and Tenants Act, 2017.",
    "document_type": "Rental Agreement",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "Tamil Nadu",
    "language": ["English", "Tamil"],
    "version": "2026.1",
    "applicability": "Residential and light commercial rental premises in Tamil Nadu.",
    "source": {
        "authority": "Government of Tamil Nadu, Housing and Urban Development Department & TN Tenancy Portal",
        "url": "https://tenancy.tn.gov.in",
        "document_name": "Model Tenancy Agreement under TNRRRLT Act, 2017",
        "reference_date": "2017 (as amended)",
    },
    "execution_requirements": [
        "Pay non-judicial stamp duty applicable in Tamil Nadu (1% of total rent + deposit or standard Rs. 100-500 stamp paper)",
        "Mandatory registration on the Tamil Nadu Tenancy Portal (tenancy.tn.gov.in) within 90 days of execution",
        "Attestation by two independent witnesses with complete addresses",
    ],
    "legal_query": "Tamil Nadu rental tenancy agreement TNRRRLT Act 2017 landlord tenant rights Coimbatore Chennai",
    "parties": [
        {"id": "landlord", "role": "Landlord (வீட்டின் உரிமையாளர்)", "name_field": "landlord_name",
         "type_field": "landlord_type", "address_field": "landlord_address"},
        {"id": "tenant", "role": "Tenant (வாடகைக்கு குடியிருப்பவர்)", "name_field": "tenant_name",
         "type_field": "tenant_type", "address_field": "tenant_address"},
    ],
    "witnesses": [
        {"id": "witness_1", "role": "Witness 1 (சாட்சி 1)", "name_field": "witness_1_name", "address_field": "witness_1_address"},
        {"id": "witness_2", "role": "Witness 2 (சாட்சி 2)", "name_field": "witness_2_name", "address_field": "witness_2_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Tamil Nadu Tenancy Agreement.", "field_ids": ["document_title", "property_use"]},
        {"id": "jurisdiction", "title": "Location", "description": "Property location in Tamil Nadu.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Landlord and tenant details.",
         "field_ids": ["landlord_name", "landlord_type", "landlord_address", "tenant_name", "tenant_type", "tenant_address"]},
        {"id": "property", "title": "Premises", "description": "Complete address and schedule boundaries.",
         "field_ids": ["property_address", "property_description", "boundary_north", "boundary_south", "boundary_east", "boundary_west", "effective_date"]},
        {"id": "financial", "title": "Rent & Deposit", "description": "Monthly rent and interest-free deposit.",
         "field_ids": ["rent_amount", "rent_frequency", "deposit_amount", "rent_due_day"]},
        {"id": "duration", "title": "Term & Notice", "description": "Duration (standard 11 months) and notice period.",
         "field_ids": ["duration_months", "end_date", "termination_notice_days"]},
        {"id": "conditions", "title": "Covenants & Utilities", "description": "Electricity, maintenance, and restrictions.",
         "field_ids": ["maintenance_amount", "electricity_meter_no", "pet_restriction", "dispute_resolution", "special_conditions"]},
        {"id": "review", "title": "Review", "description": "Review details before draft generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        _field("property_use", "Premises use", "PROPERTY USE", "select", "required", "type",
               options=[{"value": "residential", "label": "Residential (குடியிருப்பு)"},
                        {"value": "commercial", "label": "Commercial (வணிகம்)"}]),
        *_jurisdiction_fields(),
        _field("landlord_name", "Landlord full name", "LANDLORD FULL NAME", "text", "required", "parties"),
        _field("landlord_type", "Landlord legal status", "LANDLORD TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("landlord_address", "Landlord permanent address", "LANDLORD ADDRESS", "textarea", "required", "parties"),
        _field("tenant_name", "Tenant full name", "TENANT FULL NAME", "text", "required", "parties"),
        _field("tenant_type", "Tenant legal status", "TENANT TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("tenant_address", "Tenant permanent address", "TENANT PERMANENT ADDRESS", "textarea", "required", "parties"),
        _field("property_address", "Rental property complete address", "PROPERTY COMPLETE ADDRESS", "textarea", "required", "property"),
        _field("property_description", "Description of premises (door no, floor, fixtures)", "PROPERTY DESCRIPTION", "textarea", "recommended", "property"),
        _field("boundary_north", "North boundary", "NORTH BOUNDARY", "text", "optional", "property"),
        _field("boundary_south", "South boundary", "SOUTH BOUNDARY", "text", "optional", "property"),
        _field("boundary_east", "East boundary", "EAST BOUNDARY", "text", "optional", "property"),
        _field("boundary_west", "West boundary", "WEST BOUNDARY", "text", "optional", "property"),
        _field("effective_date", "Tenancy commencement date", "COMMENCEMENT DATE", "date", "required", "property"),
        _field("rent_amount", "Monthly rent (in INR)", "MONTHLY RENT", "currency", "required", "financial", min=0),
        _field("rent_frequency", "Rent frequency", "RENT FREQUENCY", "select", "optional", "financial",
               options=[{"value": "monthly", "label": "Monthly"}]),
        _field("rent_due_day", "Rent payment due day", "RENT DUE DAY", "number", "recommended", "financial", min=1, max=31),
        _field("deposit_amount", "Interest-free refundable security deposit", "SECURITY DEPOSIT", "currency", "required", "financial", min=0),
        _field("duration_months", "Tenancy term (months)", "TERM IN MONTHS", "number", "required", "duration", min=1, max=36),
        _field("end_date", "Tenancy expiry date", "EXPIRY DATE", "date", "required", "duration"),
        _field("termination_notice_days", "Notice period for vacation (days)", "NOTICE PERIOD DAYS", "number", "recommended", "duration", min=15, max=180),
        _field("maintenance_amount", "Monthly maintenance charge (INR)", "MAINTENANCE CHARGE", "currency", "optional", "conditions", min=0),
        _field("electricity_meter_no", "Electricity service connection number", "EB CONNECTION NUMBER", "text", "optional", "conditions"),
        _field("pet_restriction", "Pets permitted on premises", "PET PERMISSION", "checkbox", "optional", "conditions"),
        _field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions", options=list(DISPUTE_OPTIONS)),
        _field("special_conditions", "Additional covenants", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
        _field("witness_1_name", "Witness 1 name", "WITNESS 1 NAME", "text", "optional", "conditions"),
        _field("witness_1_address", "Witness 1 address", "WITNESS 1 ADDRESS", "text", "optional", "conditions"),
        _field("witness_2_name", "Witness 2 name", "WITNESS 2 NAME", "text", "optional", "conditions"),
        _field("witness_2_address", "Witness 2 address", "WITNESS 2 ADDRESS", "text", "optional", "conditions"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Heading and Title",
            "required": True,
            "provision_class": "required",
            "body": (
                "வாடகை ஒப்பந்த பத்திரம்\n"
                "RENTAL AGREEMENT\n\n"
                "THIS RESIDENTIAL RENTAL AGREEMENT is executed on this {effective_date} at {governing_law_seat}, Tamil Nadu."
            ),
        },
        {
            "id": "parties",
            "title": "Parties to the Agreement",
            "required": True,
            "provision_class": "required",
            "body": (
                "BY AND BETWEEN:\n\n"
                "1. {landlord_name}, a {landlord_type}, residing at {landlord_address} "
                "(hereinafter referred to as the \"LANDLORD / OWNER\" / முதலாம் தரப்பினர் - வீட்டின் உரிமையாளர், "
                "which expression shall, unless repugnant to the context, include their heirs, legal representatives, and assigns) of the ONE PART;\n\n"
                "AND\n\n"
                "2. {tenant_name}, a {tenant_type}, residing at {tenant_address} "
                "(hereinafter referred to as the \"TENANT / OCCUPANT\" / இரண்டாம் தரப்பினர் - வாடகைக்கு குடியிருப்பவர், "
                "which expression shall, unless repugnant to the context, include their heirs and permitted assigns) of the OTHER PART."
            ),
        },
        {
            "id": "recitals",
            "title": "Recitals (முன்னுரை)",
            "required": True,
            "provision_class": "recommended",
            "body": (
                "WHEREAS:\n"
                "A. The Landlord is the sole and absolute owner of the premises situated at {property_address}, "
                "more particularly described in the SCHEDULE hereunder (hereinafter referred to as the \"Scheduled Premises\").\n"
                "B. The Tenant has approached the Landlord with a request to grant on rent the Scheduled Premises for {property_use} occupation "
                "for a term of {duration_months} months.\n"
                "C. The Landlord has agreed to let out the Scheduled Premises to the Tenant on the covenants, stipulations, and conditions mutually agreed upon herein, "
                "subject to the provisions of the Tamil Nadu Regulation of Rights and Responsibilities of Landlords and Tenants Act, 2017 (TNRRRLT Act).\n\n"
                "NOW THIS AGREEMENT WITNESSETH AND IT IS HEREBY MUTUALLY AGREED BY AND BETWEEN THE PARTIES AS FOLLOWS:"
            ),
        },
        {
            "id": "term",
            "title": "1. Term and Duration (ஒப்பந்த காலம்)",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. The tenancy shall be for a fixed period of {duration_months} months, commencing on {effective_date} "
                "and terminating on {end_date}, unless terminated earlier in accordance with the provisions of this Agreement.\n"
                "1.2. Any renewal of this tenancy shall be strictly upon mutually agreed fresh terms reduced into writing prior to the expiration of this term."
            ),
        },
        {
            "id": "rent",
            "title": "2. Monthly Rent (மாதாந்திர வாடகை)",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. The Tenant shall pay to the Landlord a monthly rent of Rs. {rent_amount}/- (Rupees [AMOUNT IN WORDS]) "
                "payable in advance on or before the {rent_due_day}th day of each succeeding English calendar month.\n"
                "2.2. The rent shall be remitted through electronic bank transfer, cheque, or other agreed official payment mode against acknowledgement receipt."
            ),
        },
        {
            "id": "deposit",
            "title": "3. Interest-Free Security Deposit (முன்பணம் / பிணைத்தொகை)",
            "required": True,
            "provision_class": "required",
            "body": (
                "3.1. The Tenant has deposited with the Landlord an interest-free refundable security deposit of Rs. {deposit_amount}/- (Rupees [AMOUNT IN WORDS]), "
                "the receipt of which the Landlord hereby acknowledges.\n"
                "3.2. The security deposit shall be refunded to the Tenant simultaneously with the peaceful, vacant handover of the Scheduled Premises, "
                "subject to valid deductions for arrears of rent, electricity charges, or actual repair costs for damages exceeding normal wear and tear."
            ),
        },
        {
            "id": "utilities",
            "title": "4. Outgoings, Utilities and Maintenance",
            "required": True,
            "provision_class": "recommended",
            "body": (
                "4.1. The Tenant shall pay the electricity consumption charges directly to the Tamil Nadu Generation and Distribution Corporation (TANGEDCO) "
                "for Electricity Service Connection No. {electricity_meter_no} as per actual meter readings.\n"
                "4.2. Routine minor repairs shall be borne by the Tenant, while major structural repairs and property taxes shall remain the responsibility of the Landlord.\n"
                "4.3. Monthly building maintenance charges of Rs. {maintenance_amount}/- shall be paid regularly as agreed."
            ),
        },
        {
            "id": "tenant_covenants",
            "title": "5. Covenants of the Tenant (குடியிருப்பவர் கடமைகள்)",
            "required": True,
            "provision_class": "required",
            "body": (
                "5.1. The Tenant shall use the Scheduled Premises solely for lawful {property_use} purposes and shall not conduct any illegal, immoral, or hazardous activities.\n"
                "5.2. The Tenant shall NOT sublet, assign, mortgage, or part with the possession of the premises or any part thereof to any third party.\n"
                "5.3. The Tenant shall maintain the premises, fittings, and fixtures in good tenantable condition without making structural alterations without the Landlord's prior written consent."
            ),
        },
        {
            "id": "termination",
            "title": "6. Termination and Vacating Notice (ஒப்பந்த ரத்து)",
            "required": True,
            "provision_class": "required",
            "body": (
                "6.1. Either party may terminate this Agreement prior to expiry by serving a minimum of {termination_notice_days} days' prior written notice to the other party.\n"
                "6.2. On expiration or termination, the Tenant shall peacefully vacate and hand over vacant possession of the Scheduled Premises with all fixtures in working condition."
            ),
        },
        {
            "id": "governing_law",
            "title": "7. Governing Law and TN Portal Registration",
            "required": True,
            "provision_class": "required",
            "needs_legal_context": True,
            "body": (
                "7.1. This Agreement is governed by the laws of India and specifically the Tamil Nadu Regulation of Rights and Responsibilities of Landlords and Tenants Act, 2017.\n"
                "7.2. The parties undertake to register this tenancy on the official Tamil Nadu Tenancy Portal (tenancy.tn.gov.in) as required by statutory rules.\n"
                "7.3. Courts and the Rent Court / Rent Tribunal having territorial jurisdiction at {governing_law_seat}, Tamil Nadu shall have jurisdiction."
            ),
        },
        {
            "id": "schedule",
            "title": "Schedule of Property (சொத்து விவரம்)",
            "required": True,
            "provision_class": "required",
            "body": (
                "SCHEDULE OF THE PREMISES (சொத்து விவரம்):\n\n"
                "All that residential/commercial premises bearing address: {property_address}.\n"
                "Description & fixtures: {property_description}.\n"
                "Boundaries (நான்கு எல்லைகள்):\n"
                "North by: {boundary_north}\n"
                "South by: {boundary_south}\n"
                "East by:  {boundary_east}\n"
                "West by:  {boundary_west}\n"
                "Situate within the Registration Sub-District and District of {governing_law_seat}, Tamil Nadu."
            ),
        },
        {
            "id": "signatures",
            "title": "Execution and Attestation (கையொப்பம் மற்றும் சாட்சிகள்)",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, the Landlord and the Tenant have set their respective hands and signatures to this Agreement "
                "on the day, month, and year first above written at {governing_law_seat}, Tamil Nadu in the presence of the following witnesses."
            ),
        },
    ],
}


# =============================================================================
# 2. SALE DEED (விற்பனை கிரைய பத்திரம்)
# Official reference: Registration Act, 1908, Transfer of Property Act, 1882,
# Tnreginet model deeds & Startup India model contract.
# =============================================================================
SALE_DEED_TEMPLATE: TemplateSpec = {
    "id": "sale_deed",
    "category": "deed",
    "title": "Deed of Absolute Sale (விற்பனை கிரைய பத்திரம்)",
    "description": "Conveyance deed for the absolute sale of immovable property (land, house, flat) with clear title recitals, indemnity, and boundary schedules.",
    "document_type": "Sale Deed",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "Tamil Nadu / All India",
    "language": ["English", "Tamil"],
    "version": "2026.1",
    "applicability": "Conveyance of freehold immovable property under the Transfer of Property Act, 1882 and Registration Act, 1908.",
    "source": {
        "authority": "Registration Department, Government of Tamil Nadu (Tnreginet) & Startup India Model Contracts",
        "url": "https://tnreginet.gov.in",
        "document_name": "Model Absolute Sale Deed for Immovable Property",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Pay ad-valorem stamp duty as mandated by the State Stamp Act on the sale consideration or guideline value (whichever is higher)",
        "Mandatory registration before the jurisdictional Sub-Registrar under Section 17 of the Registration Act, 1908 within 4 months of execution",
        "Presence of Vendor and Purchaser along with two independent witnesses possessing valid government photo ID (Aadhaar / Voter ID / Passport)",
    ],
    "legal_query": "sale deed conveyance immovable property registration act transfer of property title schedule boundaries India",
    "parties": [
        {"id": "vendor", "role": "Vendor / Seller (கிரைய தாரர் / விற்பனையாளர்)", "name_field": "vendor_name",
         "type_field": "vendor_type", "address_field": "vendor_address"},
        {"id": "purchaser", "role": "Purchaser / Buyer (கிரைய வாங்குபவர்)", "name_field": "purchaser_name",
         "type_field": "purchaser_type", "address_field": "purchaser_address"},
    ],
    "witnesses": [
        {"id": "witness_1", "role": "Witness 1 (சாட்சி 1)", "name_field": "witness_1_name", "address_field": "witness_1_address"},
        {"id": "witness_2", "role": "Witness 2 (சாட்சி 2)", "name_field": "witness_2_name", "address_field": "witness_2_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Conveyance Deed.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Registration Jurisdiction", "description": "Sub-Registrar office jurisdiction.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Vendor and Purchaser details.",
         "field_ids": ["vendor_name", "vendor_type", "vendor_parent_spouse", "vendor_address", "purchaser_name", "purchaser_type", "purchaser_parent_spouse", "purchaser_address"]},
        {"id": "title_history", "title": "Title Derivation", "description": "How vendor acquired title.", "field_ids": ["title_deed_details", "effective_date"]},
        {"id": "financial", "title": "Sale Consideration", "description": "Total agreed price and payment mode.", "field_ids": ["sale_consideration", "payment_mode"]},
        {"id": "property", "title": "Property Schedule", "description": "Survey no, extent, and boundaries.",
         "field_ids": ["property_address", "survey_number", "extent_sqft", "boundary_north", "boundary_south", "boundary_east", "boundary_west"]},
        {"id": "review", "title": "Review", "description": "Review before generating deed.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("vendor_name", "Vendor / Seller full name", "VENDOR NAME", "text", "required", "parties"),
        _field("vendor_type", "Vendor legal status", "VENDOR TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("vendor_parent_spouse", "Vendor Father / Spouse name", "VENDOR PARENT OR SPOUSE", "text", "required", "parties"),
        _field("vendor_address", "Vendor permanent address", "VENDOR ADDRESS", "textarea", "required", "parties"),
        _field("purchaser_name", "Purchaser / Buyer full name", "PURCHASER NAME", "text", "required", "parties"),
        _field("purchaser_type", "Purchaser legal status", "PURCHASER TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("purchaser_parent_spouse", "Purchaser Father / Spouse name", "PURCHASER PARENT OR SPOUSE", "text", "required", "parties"),
        _field("purchaser_address", "Purchaser permanent address", "PURCHASER ADDRESS", "textarea", "required", "parties"),
        _field("title_deed_details", "Prior title deed details (Document no, Year, SRO)", "PRIOR TITLE DEED DETAILS", "textarea", "required", "title_history"),
        _field("effective_date", "Date of execution", "EXECUTION DATE", "date", "required", "title_history"),
        _field("sale_consideration", "Total sale price in INR", "SALE CONSIDERATION", "currency", "required", "financial", min=0),
        _field("payment_mode", "Payment details (Cheque/DD/NEFT/RTGS details)", "PAYMENT MODE DETAILS", "textarea", "required", "financial"),
        _field("property_address", "Property complete location", "PROPERTY LOCATION", "textarea", "required", "property"),
        _field("survey_number", "Survey / Plot / Sub-division number", "SURVEY NUMBER", "text", "required", "property"),
        _field("extent_sqft", "Total area / extent (sq ft or cents)", "PROPERTY EXTENT", "text", "required", "property"),
        _field("boundary_north", "North boundary", "NORTH BOUNDARY", "text", "required", "property"),
        _field("boundary_south", "South boundary", "SOUTH BOUNDARY", "text", "required", "property"),
        _field("boundary_east", "East boundary", "EAST BOUNDARY", "text", "required", "property"),
        _field("boundary_west", "West boundary", "WEST BOUNDARY", "text", "required", "property"),
        _field("witness_1_name", "Witness 1 name", "WITNESS 1 NAME", "text", "optional", "property"),
        _field("witness_1_address", "Witness 1 address", "WITNESS 1 ADDRESS", "text", "optional", "property"),
        _field("witness_2_name", "Witness 2 name", "WITNESS 2 NAME", "text", "optional", "property"),
        _field("witness_2_address", "Witness 2 address", "WITNESS 2 ADDRESS", "text", "optional", "property"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Title and Preamble",
            "required": True,
            "provision_class": "required",
            "body": (
                "விற்பனை கிரைய பத்திரம்\n"
                "DEED OF ABSOLUTE SALE\n\n"
                "THIS DEED OF ABSOLUTE SALE is made and executed on this {effective_date} at {governing_law_seat}, {jurisdiction_region}."
            ),
        },
        {
            "id": "parties",
            "title": "Parties",
            "required": True,
            "provision_class": "required",
            "body": (
                "BY AND BETWEEN:\n\n"
                "1. {vendor_name}, son/daughter/wife of {vendor_parent_spouse}, a {vendor_type}, residing at {vendor_address} "
                "(hereinafter called the \"VENDOR\" / விற்பனையாளர், which expression shall include their heirs, executors, administrators, and assigns) of the ONE PART;\n\n"
                "AND\n\n"
                "2. {purchaser_name}, son/daughter/wife of {purchaser_parent_spouse}, a {purchaser_type}, residing at {purchaser_address} "
                "(hereinafter called the \"PURCHASER\" / கிரைய வாங்குபவர், which expression shall include their heirs, executors, administrators, and assigns) of the OTHER PART."
            ),
        },
        {
            "id": "recitals",
            "title": "Recitals of Title and Derivation (முன்னுரை மற்றும் உரிமை விவரம்)",
            "required": True,
            "provision_class": "recommended",
            "body": (
                "WHEREAS:\n"
                "A. The Vendor is the absolute owner and in peaceful possession and enjoyment of the immovable property bearing Survey No. {survey_number}, "
                "measuring {extent_sqft}, situated at {property_address}, fully described in the SCHEDULE hereunder (the \"Schedule Property\").\n"
                "B. The Vendor acquired absolute marketable title over the Schedule Property by virtue of: {title_deed_details}.\n"
                "C. The Vendor, being in need of funds, has agreed to sell, transfer, and convey the absolute freehold ownership of the Schedule Property to the Purchaser, "
                "and the Purchaser has agreed to purchase the same for a total consideration of Rs. {sale_consideration}/- (Rupees [CONSIDERATION IN WORDS]).\n\n"
                "NOW THIS DEED OF ABSOLUTE SALE WITNESSETH AS FOLLOWS:"
            ),
        },
        {
            "id": "consideration",
            "title": "1. Consideration and Receipt (கிரையத் தொகை)",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. In pursuance of the said agreement and in consideration of the sum of Rs. {sale_consideration}/- (Rupees [CONSIDERATION IN WORDS]) "
                "paid by the Purchaser to the Vendor by mode of {payment_mode}, the receipt whereof the Vendor hereby admits and acknowledges.\n"
                "1.2. The Vendor does hereby release, acquit, and forever discharge the Purchaser from any further payment or claim towards the sale consideration."
            ),
        },
        {
            "id": "conveyance",
            "title": "2. Operative Conveyance and Transfer of Rights",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. The Vendor does hereby grant, convey, transfer, and assign unto the Purchaser, by way of absolute sale, all that piece and parcel of "
                "immovable property described in the Schedule hereunder, together with all rights, easements, pathways, privileges, trees, and appurtenances belonging thereto.\n"
                "2.2. TO HAVE AND TO HOLD the Schedule Property absolutely and forever unto the Purchaser without any interruption, claim, or demand from the Vendor or any person claiming under them."
            ),
        },
        {
            "id": "encumbrance",
            "title": "3. Covenant of Free Encumbrance and Indemnity (வில்லங்கமின்மை உறுதிமொழி)",
            "required": True,
            "provision_class": "required",
            "body": (
                "3.1. The Vendor expressly covenants that the Schedule Property is free from all encumbrances, mortgages, charges, liens, attachments, lis pendens, tax demands, or court decrees.\n"
                "3.2. If any defect in title or prior encumbrance is found or any claim is made against the Schedule Property, the Vendor shall indemnify and hold harmless the Purchaser against all losses, damages, and costs arising therefrom."
            ),
        },
        {
            "id": "possession",
            "title": "4. Delivery of Peaceful Vacant Possession (சுவாதீனம் ஒப்படைப்பு)",
            "required": True,
            "provision_class": "required",
            "body": (
                "4.1. The Vendor has on this day delivered peaceful, physical, and vacant possession of the Schedule Property to the Purchaser.\n"
                "4.2. The Vendor has simultaneously handed over to the Purchaser all original title deeds, tax receipts, and patta documents relating to the Schedule Property."
            ),
        },
        {
            "id": "schedule",
            "title": "Schedule of Property (சொத்து விவரம் மற்றும் நான்கு எல்லைகள்)",
            "required": True,
            "provision_class": "required",
            "body": (
                "SCHEDULE OF THE PROPERTY (சொத்து விவரம்):\n\n"
                "All that piece and parcel of land / house situated at: {property_address}.\n"
                "Survey / Sub-Division No: {survey_number}.\n"
                "Extent / Measurement: {extent_sqft}.\n"
                "Boundaries (நான்கு எல்லைகள்):\n"
                "North by: {boundary_north}\n"
                "South by: {boundary_south}\n"
                "East by:  {boundary_east}\n"
                "West by:  {boundary_west}\n"
                "Situate within the Registration District and Sub-Registration District of {governing_law_seat}."
            ),
        },
        {
            "id": "signatures",
            "title": "Signatures and Witnesses (கையொப்பங்கள் மற்றும் சாட்சிகள்)",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, the Vendor and the Purchaser have signed, sealed, and executed this Deed of Absolute Sale "
                "on the day, month, and year first above written at {governing_law_seat} in the presence of the following witnesses."
            ),
        },
    ],
}


# =============================================================================
# 3. GENERAL POWER OF ATTORNEY (பொது அதிகார ஆவணம்)
# Official reference: Powers of Attorney Act, 1882, Indian Contract Act, 1872,
# Registration Act, 1908 & Startup India model format.
# =============================================================================
GENERAL_POWER_OF_ATTORNEY_TEMPLATE: TemplateSpec = {
    "id": "general_power_of_attorney",
    "category": "deed",
    "title": "General Power of Attorney (பொது அதிகார ஆவணம்)",
    "description": "General Power of Attorney authorizing an attorney-in-fact to manage, lease, supervise property, represent before government bodies, courts, and conduct lawful affairs.",
    "document_type": "General Power of Attorney",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English", "Tamil", "Hindi"],
    "version": "2026.1",
    "applicability": "Grant of general agency powers under Powers of Attorney Act, 1882.",
    "source": {
        "authority": "Department of Legal Affairs, Government of India & Startup India Model Contracts",
        "url": "https://www.startupindia.gov.in/content/sih/en/model-contracts.html",
        "document_name": "Model General Power of Attorney",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on appropriate non-judicial stamp paper as prescribed by the State Stamp Act",
        "Mandatory attestation and notarization before a Notary Public or Magistrate under Section 85 of the Indian Evidence Act",
        "Compulsory registration before the Sub-Registrar if authorizing conveyance of immovable property",
    ],
    "legal_query": "General power of attorney attorney agent principal powers of attorney act 1882 India property management",
    "parties": [
        {"id": "principal", "role": "Principal (முதல்வர் / அதிகாரம் அளிப்பவர்)", "name_field": "principal_name",
         "type_field": "principal_type", "address_field": "principal_address"},
        {"id": "attorney", "role": "Attorney-in-Fact (முகவர் / அதிகாரம் பெறுபவர்)", "name_field": "attorney_name",
         "type_field": "attorney_type", "address_field": "attorney_address"},
    ],
    "witnesses": [
        {"id": "witness_1", "role": "Witness 1 (சாட்சி 1)", "name_field": "witness_1_name", "address_field": "witness_1_address"},
        {"id": "witness_2", "role": "Witness 2 (சாட்சி 2)", "name_field": "witness_2_name", "address_field": "witness_2_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "General Power of Attorney.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Place of execution.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Principal and Attorney details.",
         "field_ids": ["principal_name", "principal_type", "principal_parent_spouse", "principal_address", "attorney_name", "attorney_type", "attorney_parent_spouse", "attorney_address"]},
        {"id": "purpose", "title": "Scope & Property", "description": "Property details and reasons for delegation.",
         "field_ids": ["property_details", "reason_for_poa", "effective_date"]},
        {"id": "powers", "title": "Powers Granted", "description": "Specific authority granted.",
         "field_ids": ["include_litigation_powers", "include_banking_powers", "special_conditions"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("principal_name", "Principal full name", "PRINCIPAL NAME", "text", "required", "parties"),
        _field("principal_type", "Principal type", "PRINCIPAL TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("principal_parent_spouse", "Principal Father / Spouse name", "PRINCIPAL PARENT OR SPOUSE", "text", "required", "parties"),
        _field("principal_address", "Principal permanent address", "PRINCIPAL ADDRESS", "textarea", "required", "parties"),
        _field("attorney_name", "Attorney Agent full name", "ATTORNEY NAME", "text", "required", "parties"),
        _field("attorney_type", "Attorney legal status", "ATTORNEY TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("attorney_parent_spouse", "Attorney Father / Spouse name", "ATTORNEY PARENT OR SPOUSE", "text", "required", "parties"),
        _field("attorney_address", "Attorney permanent address", "ATTORNEY ADDRESS", "textarea", "required", "parties"),
        _field("property_details", "Description of property / assets managed", "PROPERTY DETAILS", "textarea", "required", "purpose"),
        _field("reason_for_poa", "Reason for appointment (e.g. non-residence, business, age)", "REASON FOR APPOINTMENT", "textarea", "recommended", "purpose"),
        _field("effective_date", "Date of execution", "EXECUTION DATE", "date", "required", "purpose"),
        _field("include_litigation_powers", "Authorize representation in courts and tribunals", "COURT POWERS", "checkbox", "recommended", "powers"),
        _field("include_banking_powers", "Authorize opening / operating bank accounts", "BANKING POWERS", "checkbox", "optional", "powers"),
        _field("special_conditions", "Specific restrictions or instructions", "SPECIAL INSTRUCTIONS", "textarea", "optional", "powers"),
        _field("witness_1_name", "Witness 1 name", "WITNESS 1 NAME", "text", "optional", "powers"),
        _field("witness_1_address", "Witness 1 address", "WITNESS 1 ADDRESS", "text", "optional", "powers"),
        _field("witness_2_name", "Witness 2 name", "WITNESS 2 NAME", "text", "optional", "powers"),
        _field("witness_2_address", "Witness 2 address", "WITNESS 2 ADDRESS", "text", "optional", "powers"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Title and Preamble",
            "required": True,
            "provision_class": "required",
            "body": (
                "பொது அதிகார ஆவணம்\n"
                "GENERAL POWER OF ATTORNEY\n\n"
                "TO ALL TO WHOM THESE PRESENTS SHALL COME, I, {principal_name}, son/daughter/wife of {principal_parent_spouse}, "
                "aged about [AGE] years, residing at {principal_address}, SEND GREETINGS."
            ),
        },
        {
            "id": "recitals",
            "title": "Recitals and Appointment",
            "required": True,
            "provision_class": "required",
            "body": (
                "WHEREAS:\n"
                "1. I am the absolute owner of the property/affairs described as: {property_details}.\n"
                "2. Owing to {reason_for_poa}, I am unable to personally look after, manage, and supervise my said affairs and properties.\n"
                "3. I have absolute faith and confidence in {attorney_name}, son/daughter/wife of {attorney_parent_spouse}, "
                "residing at {attorney_address}, and desire to appoint them as my true and lawful Attorney-in-Fact.\n\n"
                "NOW KNOW YE ALL AND THESE PRESENTS WITNESS that I do hereby nominate, constitute, and appoint the said {attorney_name} "
                "as my true and lawful Attorney, in my name and on my behalf to do and execute all or any of the following acts, deeds, and things:"
            ),
        },
        {
            "id": "powers_management",
            "title": "1. Powers of Management and Supervision",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. To manage, control, inspect, and supervise the said properties, to collect rents, profits, and receivables, "
                "and to grant valid receipts and discharges for the same.\n"
                "1.2. To pay all government revenues, municipal taxes, electricity dues, water rates, and other public outgoings relating to the property."
            ),
        },
        {
            "id": "powers_authorities",
            "title": "2. Representation Before Government Authorities",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. To appear, represent, and act on my behalf before any Municipal Corporation, Revenue Office, Sub-Registrar of Assurances, "
                "Electricity Board, Water Supply Board, Town Planning Authorities, and Police Authorities.\n"
                "2.2. To sign, verify, and submit all necessary applications, petitions, affidavits, declarations, statements, and forms."
            ),
        },
        {
            "id": "powers_litigation",
            "title": "3. Legal and Court Proceedings",
            "required": False,
            "condition": {"truthy": "include_litigation_powers"},
            "provision_class": "recommended",
            "body": (
                "3.1. To institute, prosecute, defend, compromise, or settle any suit, appeal, revision, execution petition, or legal proceeding "
                "before any Court of Law, Tribunal, Arbitrator, or quasi-judicial authority.\n"
                "3.2. To appoint advocates, sign Vakalatnamas, plaints, written statements, affidavits, and compromise petitions on my behalf."
            ),
        },
        {
            "id": "ratification",
            "title": "4. Ratification and Revocation Covenant",
            "required": True,
            "provision_class": "required",
            "body": (
                "4.1. AND I hereby agree that all acts, deeds, and things lawfully done or executed by my said Attorney shall be construed as acts done by me personally, "
                "and I hereby ratify and confirm all such lawful acts.\n"
                "4.2. This Power of Attorney is executed without consideration and may be revoked by me at any time by giving written notice to the Attorney, "
                "subject to the provisions of the Indian Contract Act, 1872."
            ),
        },
        {
            "id": "signatures",
            "title": "Execution, Attestation, and Notary Jurat",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, I, the Principal above named, have signed and executed this General Power of Attorney on this {effective_date} "
                "at {governing_law_seat}, {jurisdiction_region} in the presence of the witnesses subscribed below.\n\n"
                "PRINCIPAL (முதல்வர் / அதிகாரம் அளிப்பவர்)\n\n"
                "I accept the above power and authority:\n"
                "ATTORNEY (முகவர் / அதிகாரம் பெறுபவர்)"
            ),
        },
    ],
}


# =============================================================================
# 4. RTI APPLICATION (FORM 'A')
# Official reference: Section 6(1) Right to Information Act, 2005 & DoPT Model.
# =============================================================================
RTI_APPLICATION_TEMPLATE: TemplateSpec = {
    "id": "rti_application",
    "category": "application",
    "title": "RTI Application (Form 'A' under RTI Act, 2005)",
    "description": "Statutory application to Public Information Officer under Section 6(1) of the Right to Information Act, 2005 seeking certified information.",
    "document_type": "RTI Application",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English", "Hindi", "Tamil"],
    "version": "2026.1",
    "applicability": "Filing with Central or State Public Information Officers across India.",
    "source": {
        "authority": "Department of Personnel and Training (DoPT), Government of India & Central Information Commission",
        "url": "https://cic.gov.in",
        "document_name": "Standard RTI Application Format under RTI Act, 2005",
        "reference_date": "2005 (as amended)",
    },
    "execution_requirements": [
        "Enclose mandatory application fee of Rs. 10/- by Postal Order (IPO), Demand Draft, Court Fee Stamp, or online payment receipt",
        "Applicants belonging to Below Poverty Line (BPL) category are exempt from fees upon enclosing a certified BPL card copy",
        "Filing before the designated Central/State Public Information Officer (CPIO / SPIO) of the concerned public authority",
    ],
    "legal_query": "RTI application form A section 6 1 right to information act 2005 public information officer fee information requested India",
    "parties": [
        {"id": "applicant", "role": "Applicant (விண்ணப்பதாரர்)", "name_field": "applicant_name",
         "type_field": "applicant_type", "address_field": "applicant_address"},
        {"id": "authority", "role": "Public Authority (அரசுத்துறை / அதிகாரி)", "name_field": "authority_name",
         "type_field": "authority_type", "address_field": "authority_address"},
    ],
    "steps": [
        {"id": "type", "title": "Application", "description": "RTI Form 'A'.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Authority Location", "description": "State and seat.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Applicant Details", "description": "Applicant and authority details.",
         "field_ids": ["applicant_name", "applicant_address", "applicant_phone", "applicant_email", "authority_name", "authority_address"]},
        {"id": "information", "title": "Information Sought", "description": "Subject and specific point-wise queries.",
         "field_ids": ["subject_matter", "period_of_information", "specific_queries", "effective_date"]},
        {"id": "fee", "title": "Fee Details", "description": "Fee payment mode.", "field_ids": ["fee_mode", "bpl_status"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("applicant_name", "Applicant full name", "APPLICANT NAME", "text", "required", "parties"),
        _field("applicant_address", "Applicant postal address for reply", "APPLICANT POSTAL ADDRESS", "textarea", "required", "parties"),
        _field("applicant_phone", "Applicant phone / mobile number", "APPLICANT PHONE", "tel", "recommended", "parties"),
        _field("applicant_email", "Applicant email address", "APPLICANT EMAIL", "email", "optional", "parties"),
        _field("authority_name", "Name of Public Authority / Department", "PUBLIC AUTHORITY NAME", "text", "required", "parties"),
        _field("authority_address", "Office address of Public Information Officer", "PIO OFFICE ADDRESS", "textarea", "required", "parties"),
        _field("subject_matter", "Subject matter of information sought", "SUBJECT OF INFORMATION", "textarea", "required", "information"),
        _field("period_of_information", "Period to which information relates (e.g. 2024-2026)", "PERIOD OF INFORMATION", "text", "recommended", "information"),
        _field("specific_queries", "Specific questions / certified documents requested (numbered)", "SPECIFIC QUERIES", "textarea", "required", "information"),
        _field("effective_date", "Date of application", "DATE OF APPLICATION", "date", "required", "information"),
        _field("fee_mode", "Application fee mode (IPO / DD / Court Fee Stamp / Online)", "FEE PAYMENT MODE", "text", "required", "fee"),
        _field("bpl_status", "Applicant is Below Poverty Line (BPL)", "BPL STATUS", "checkbox", "optional", "fee"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Statutory Heading",
            "required": True,
            "provision_class": "required",
            "body": (
                "FORM 'A'\n"
                "[See Rule 3(1)]\n\n"
                "APPLICATION FOR OBTAINING INFORMATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005\n\n"
                "Date: {effective_date}\n\n"
                "TO:\n"
                "The Central / State Public Information Officer (PIO),\n"
                "{authority_name},\n"
                "{authority_address}."
            ),
        },
        {
            "id": "applicant_particulars",
            "title": "1. Particulars of the Applicant",
            "required": True,
            "provision_class": "required",
            "body": (
                "1. Full Name of the Applicant: {applicant_name}\n"
                "2. Address for Correspondence: {applicant_address}\n"
                "3. Contact Details: Phone: {applicant_phone} | Email: {applicant_email}\n"
                "4. Citizenship: Citizen of India (as required under Section 3 of the RTI Act, 2005)."
            ),
        },
        {
            "id": "information_details",
            "title": "2. Particulars of Information Sought",
            "required": True,
            "provision_class": "required",
            "body": (
                "(a) Subject Matter of Information:\n{subject_matter}\n\n"
                "(b) Period to which the information relates:\n{period_of_information}\n\n"
                "(c) Description of the information / documents required (Point-wise):\n\n"
                "{specific_queries}\n\n"
                "(d) Preferred mode of supply: Certified physical copies by Registered Post / Speed Post."
            ),
        },
        {
            "id": "fee_particulars",
            "title": "3. Application Fee Details",
            "required": True,
            "provision_class": "required",
            "body": (
                "The prescribed application fee of Rs. 10/- has been paid through: {fee_mode}.\n"
                "(BPL category exemption claimed: {bpl_status} - proof enclosed if applicable).\n"
                "The Applicant undertakes to pay any additional fees for photocopying or inspection as notified under the RTI Rules."
            ),
        },
        {
            "id": "declaration",
            "title": "4. Declaration and Signature",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "I hereby declare that the information sought does not fall under any of the exemptions stipulated under Section 8 or 9 of the RTI Act, 2005, "
                "and to the best of my knowledge it pertains to your esteemed public authority.\n\n"
                "Place: {governing_law_seat}\n"
                "Date: {effective_date}\n\n"
                "SIGNATURE OF THE APPLICANT\n"
                "({applicant_name})"
            ),
        },
    ],
}


# =============================================================================
# 5. SECTION 138 NEGOTIABLE INSTRUMENTS ACT DEMAND NOTICE
# Official reference: Section 138(b) of Negotiable Instruments Act, 1881.
# =============================================================================
PAYMENT_DEMAND_NOTICE_TEMPLATE: TemplateSpec = {
    "id": "payment_demand_notice",
    "category": "notice",
    "title": "Statutory Demand Notice (Section 138 NI Act - Cheque Bounce)",
    "description": "Statutory legal notice under Section 138(b) of the Negotiable Instruments Act, 1881 demanding payment of dishonoured cheque within 15 days.",
    "document_type": "Payment Demand Notice",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English", "Tamil", "Hindi"],
    "version": "2026.1",
    "applicability": "Dishonour of cheques for discharge of legally enforceable debt in India.",
    "source": {
        "authority": "Supreme Court of India Guidelines & Negotiable Instruments Act, 1881",
        "url": "https://indiacode.nic.in/handle/123456789/2189",
        "document_name": "Statutory Notice under Section 138 Negotiable Instruments Act",
        "reference_date": "1881 (as amended 2018)",
    },
    "execution_requirements": [
        "Must be issued within 30 days of receiving the cheque return memo from the bank",
        "Must provide a clear 15-day notice window from receipt of notice for the drawer to pay the amount",
        "Mandatory dispatch via Registered Post with A.D. or Speed Post and tracking receipt preserved",
    ],
    "legal_query": "section 138 negotiable instruments act cheque bounce legal notice demand memo drawer payee India",
    "parties": [
        {"id": "payee", "role": "Payee / Holder in Due Course", "name_field": "payee_name",
         "type_field": "payee_type", "address_field": "payee_address"},
        {"id": "drawer", "role": "Drawer of Cheque", "name_field": "drawer_name",
         "type_field": "drawer_type", "address_field": "drawer_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "138 NI Act Demand Notice.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Place and court jurisdiction.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Payee and Drawer details.",
         "field_ids": ["payee_name", "payee_address", "drawer_name", "drawer_address", "advocate_name"]},
        {"id": "cheque", "title": "Cheque Details", "description": "Cheque number, amount, bank, return memo date.",
         "field_ids": ["cheque_number", "cheque_date", "cheque_amount", "bank_name", "memo_date", "return_reason", "effective_date"]},
        {"id": "debt", "title": "Transaction Background", "description": "Underlying debt or liability.", "field_ids": ["liability_facts"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("payee_name", "Payee (Creditor) full name", "PAYEE NAME", "text", "required", "parties"),
        _field("payee_address", "Payee address", "PAYEE ADDRESS", "textarea", "required", "parties"),
        _field("drawer_name", "Drawer (Debtor) full name", "DRAWER NAME", "text", "required", "parties"),
        _field("drawer_address", "Drawer postal address", "DRAWER ADDRESS", "textarea", "required", "parties"),
        _field("advocate_name", "Advocate issuing notice (or Payee)", "ADVOCATE NAME", "text", "required", "parties"),
        _field("cheque_number", "Cheque number", "CHEQUE NUMBER", "text", "required", "cheque"),
        _field("cheque_date", "Date of cheque", "CHEQUE DATE", "date", "required", "cheque"),
        _field("cheque_amount", "Cheque amount in INR", "CHEQUE AMOUNT", "currency", "required", "cheque", min=1),
        _field("bank_name", "Drawee bank and branch", "BANK NAME", "text", "required", "cheque"),
        _field("memo_date", "Date of bank return memo", "RETURN MEMO DATE", "date", "required", "cheque"),
        _field("return_reason", "Reason for dishonour (e.g. Funds Insufficient)", "RETURN REASON", "text", "required", "cheque"),
        _field("effective_date", "Date of notice", "DATE OF NOTICE", "date", "required", "cheque"),
        _field("liability_facts", "Facts of legally enforceable liability / consideration", "LIABILITY FACTS", "textarea", "required", "debt"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Dispatch Mode and Header",
            "required": True,
            "provision_class": "required",
            "body": (
                "BY REGISTERED POST WITH ACKNOWLEDGEMENT DUE / SPEED POST\n\n"
                "STATUTORY DEMAND NOTICE UNDER SECTION 138(b) OF THE NEGOTIABLE INSTRUMENTS ACT, 1881\n\n"
                "Date: {effective_date}\n\n"
                "TO:\n"
                "{drawer_name},\n"
                "{drawer_address}.\n\n"
                "Sir / Madam,"
            ),
        },
        {
            "id": "instructions",
            "title": "Advocate Instructions",
            "required": True,
            "provision_class": "required",
            "body": (
                "Under instructions from and on behalf of my client, {payee_name}, residing at {payee_address} "
                "(hereinafter referred to as \"my Client\"), I hereby serve upon you this Statutory Legal Notice as under:"
            ),
        },
        {
            "id": "facts",
            "title": "1. Factual Background and Legally Enforceable Debt",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. That you, the addressee, approached my Client towards {liability_facts}, in discharge of which legally enforceable debt and liability, "
                "you issued in favour of my Client Cheque bearing No. {cheque_number} dated {cheque_date} for a sum of Rs. {cheque_amount}/- "
                "(Rupees [AMOUNT IN WORDS]) drawn on {bank_name}.\n"
                "1.2. That while issuing the said cheque, you expressly assured and represented to my Client that the cheque would be duly honoured on presentation."
            ),
        },
        {
            "id": "dishonour",
            "title": "2. Presentation and Dishonour",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. Believing your representations, my Client presented the said cheque for clearance through their bank, but to my Client's shock, "
                "the said cheque was returned unpaid and dishonoured by the bank vide Cheque Return Memo dated {memo_date} with the endorsement: \"{return_reason}\".\n"
                "2.2. The dishonour of the said cheque demonstrates your deliberate dishonest intention to cheat and cause wrongful loss to my Client."
            ),
        },
        {
            "id": "demand",
            "title": "3. Statutory 15-Day Demand and Legal Consequences",
            "required": True,
            "provision_class": "required",
            "needs_legal_context": True,
            "body": (
                "3.1. NOW THEREFORE, I, on behalf of my Client, hereby call upon you to pay the said cheque amount of Rs. {cheque_amount}/- (Rupees [AMOUNT IN WORDS]) "
                "to my Client within a period of 15 (FIFTEEN) DAYS from the date of receipt of this notice.\n"
                "3.2. TAKE NOTICE that if you fail to pay the said amount within the stipulated period of 15 days, my Client shall be constrained to institute "
                "criminal proceedings against you under Section 138 and Section 142 of the Negotiable Instruments Act, 1881, as well as provisions of the Bharatiya Nyaya Sanhita, 2023 / IPC, "
                "wherein you may be punished with imprisonment for a term extending up to TWO YEARS, or with fine up to TWICE the cheque amount, or both, "
                "at your sole risk, cost, and legal consequences."
            ),
        },
        {
            "id": "signatures",
            "title": "Advocate Signature Block",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "Yours faithfully,\n\n"
                "ADVOCATE FOR THE PAYEE\n"
                "({advocate_name})\n"
                "Place: {governing_law_seat}"
            ),
        },
    ],
}


# =============================================================================
# 6. CO-FOUNDERS' / FOUNDER AGREEMENT
# Official reference: Startup India Model Contracts (DPIIT)
# =============================================================================
FOUNDER_AGREEMENT_TEMPLATE: TemplateSpec = {
    "id": "founder_agreement",
    "category": "agreement",
    "title": "Co-Founders' Agreement",
    "description": "Comprehensive startup co-founders' agreement covering equity split, 4-year vesting schedule with 1-year cliff, IP assignment, roles, and transfer restrictions.",
    "document_type": "Co-Founders' Agreement",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "Early-stage startup co-founders in India prior to or post incorporation.",
    "source": {
        "authority": "Startup India, Department for Promotion of Industry and Internal Trade (DPIIT), Ministry of Commerce & Industry",
        "url": "https://www.startupindia.gov.in/content/sih/en/model-contracts.html",
        "document_name": "Model Co-Founders Agreement",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on appropriate non-judicial stamp paper as prescribed by the State Stamp Act",
        "Attestation by all co-founders with signature on all pages",
        "IP assignment covenants require distinct written confirmation under Indian Copyright Act, 1957",
    ],
    "legal_query": "founder agreement startup co-founder equity vesting intellectual property assignment reverse vesting India",
    "parties": [
        {"id": "founder_1", "role": "Founder 1", "name_field": "founder_1_name",
         "type_field": "founder_1_type", "address_field": "founder_1_address"},
        {"id": "founder_2", "role": "Founder 2", "name_field": "founder_2_name",
         "type_field": "founder_2_type", "address_field": "founder_2_address"},
    ],
    "steps": [
        {"id": "type", "title": "Agreement", "description": "Founder Agreement.", "field_ids": ["document_title", "startup_name"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Governing seat.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Founders", "description": "Co-founders particulars.",
         "field_ids": ["founder_1_name", "founder_1_address", "founder_1_role", "founder_2_name", "founder_2_address", "founder_2_role"]},
        {"id": "equity", "title": "Equity & Vesting", "description": "Ownership ratio and vesting terms.",
         "field_ids": ["founder_1_equity", "founder_2_equity", "vesting_years", "cliff_months", "effective_date"]},
        {"id": "conditions", "title": "Governance & Disputes", "description": "Non-compete, IP assignment, and dispute forum.",
         "field_ids": ["dispute_resolution", "special_conditions"]},
        {"id": "review", "title": "Review", "description": "Review before draft.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        _field("startup_name", "Startup / Company name (or proposed name)", "STARTUP NAME", "text", "required", "type"),
        *_jurisdiction_fields(),
        _field("founder_1_name", "Founder 1 full name", "FOUNDER 1 NAME", "text", "required", "parties"),
        _field("founder_1_address", "Founder 1 address", "FOUNDER 1 ADDRESS", "textarea", "required", "parties"),
        _field("founder_1_role", "Founder 1 designation (e.g. CEO)", "FOUNDER 1 ROLE", "text", "required", "parties"),
        _field("founder_2_name", "Founder 2 full name", "FOUNDER 2 NAME", "text", "required", "parties"),
        _field("founder_2_address", "Founder 2 address", "FOUNDER 2 ADDRESS", "textarea", "required", "parties"),
        _field("founder_2_role", "Founder 2 designation (e.g. CTO)", "FOUNDER 2 ROLE", "text", "required", "parties"),
        _field("founder_1_equity", "Founder 1 equity percentage", "FOUNDER 1 EQUITY", "number", "required", "equity", min=1, max=99),
        _field("founder_2_equity", "Founder 2 equity percentage", "FOUNDER 2 EQUITY", "number", "required", "equity", min=1, max=99),
        _field("vesting_years", "Total vesting period in years (standard 4)", "VESTING YEARS", "number", "recommended", "equity", min=1, max=10),
        _field("cliff_months", "Cliff period in months (standard 12)", "CLIFF MONTHS", "number", "recommended", "equity", min=0, max=24),
        _field("effective_date", "Effective date", "EFFECTIVE DATE", "date", "required", "equity"),
        _field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions", options=list(DISPUTE_OPTIONS)),
        _field("special_conditions", "Special terms or milestones", "SPECIAL TERMS", "textarea", "optional", "conditions"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Title and Preamble",
            "required": True,
            "provision_class": "required",
            "body": (
                "CO-FOUNDERS' AGREEMENT\n\n"
                "THIS CO-FOUNDERS' AGREEMENT is entered into on this {effective_date} at {governing_law_seat}, {jurisdiction_region}, "
                "by and between the undersigned Co-Founders of {startup_name}."
            ),
        },
        {
            "id": "parties",
            "title": "Parties",
            "required": True,
            "provision_class": "required",
            "body": (
                "BETWEEN:\n\n"
                "1. {founder_1_name}, residing at {founder_1_address} (hereinafter referred to as \"Founder 1 / {founder_1_role}\");\n\n"
                "AND\n\n"
                "2. {founder_2_name}, residing at {founder_2_address} (hereinafter referred to as \"Founder 2 / {founder_2_role}\").\n\n"
                "Each individually referred to as a \"Founder\" and collectively as the \"Founders\"."
            ),
        },
        {
            "id": "equity",
            "title": "1. Equity Ownership and Capitalization",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. The Founders agree that the initial equity ownership of {startup_name} shall be allocated as follows:\n"
                "- {founder_1_name}: {founder_1_equity}%\n"
                "- {founder_2_name}: {founder_2_equity}%\n"
                "1.2. The Founders agree to contribute their agreed initial capital and bear preliminary expenses in proportion to their respective equity share."
            ),
        },
        {
            "id": "vesting",
            "title": "2. Reverse Vesting and Cliff Period",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. All equity held by the Founders shall be subject to reverse vesting over a period of {vesting_years} years, "
                "with a {cliff_months}-month cliff from {effective_date}.\n"
                "2.2. If a Founder departs or terminates their active association prior to the expiry of the cliff period, "
                "all their unvested shares shall be forfeited or transferred to the Company/remaining Founder at nominal face value.\n"
                "2.3. Following the cliff, the remaining shares shall vest monthly in equal tranches over the remaining term."
            ),
        },
        {
            "id": "ip_assignment",
            "title": "3. Intellectual Property Assignment",
            "required": True,
            "provision_class": "required",
            "body": (
                "3.1. Each Founder irrevocably assigns and transfers to the Company all right, title, and interest in any intellectual property, "
                "inventions, software code, domain names, trademarks, designs, and business know-how developed for or relating to {startup_name}.\n"
                "3.2. All future work product created by the Founders for the Company shall constitute \"work made for hire\" owned exclusively by the Company."
            ),
        },
        {
            "id": "roles",
            "title": "4. Roles and Responsibilities",
            "required": True,
            "provision_class": "required",
            "body": (
                "4.1. {founder_1_name} shall primarily serve as {founder_1_role} overseeing business strategy and operations.\n"
                "4.2. {founder_2_name} shall primarily serve as {founder_2_role} overseeing technical architecture and product development.\n"
                "4.3. Key decisions, including fundraising, indebtedness, and winding up, shall require the unanimous consent of both Founders."
            ),
        },
        {
            "id": "signatures",
            "title": "Signatures",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, the Founders have executed this Co-Founders' Agreement as of the date first written above."
            ),
        },
    ],
}


# =============================================================================
# 7. SPECIAL POWER OF ATTORNEY (குறிப்பிட்ட அதிகார ஆவணம்)
# =============================================================================
SPECIAL_POWER_OF_ATTORNEY_TEMPLATE: TemplateSpec = {
    "id": "special_power_of_attorney",
    "category": "deed",
    "title": "Special Power of Attorney (குறிப்பிட்ட அதிகார ஆவணம்)",
    "description": "Specific power of attorney authorizing an agent to perform a single designated legal transaction (e.g., property sale registration or court appearance).",
    "document_type": "Special Power of Attorney",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English", "Tamil", "Hindi"],
    "version": "2026.1",
    "applicability": "Single-transaction agency under Powers of Attorney Act, 1882.",
    "source": {
        "authority": "Department of Legal Affairs, Government of India",
        "url": "https://legalaffairs.gov.in",
        "document_name": "Model Special Power of Attorney Format",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on appropriate non-judicial stamp paper as prescribed by the State Stamp Act",
        "Attestation before a Notary Public with seal",
        "Registration before the Sub-Registrar if authorizing execution of an immovable property conveyance",
    ],
    "legal_query": "special power of attorney specific transaction powers of attorney act 1882 India",
    "parties": [
        {"id": "principal", "role": "Principal (முதல்வர்)", "name_field": "principal_name",
         "type_field": "principal_type", "address_field": "principal_address"},
        {"id": "attorney", "role": "Special Attorney (முகவர்)", "name_field": "attorney_name",
         "type_field": "attorney_type", "address_field": "attorney_address"},
    ],
    "witnesses": [
        {"id": "witness_1", "role": "Witness 1", "name_field": "witness_1_name", "address_field": "witness_1_address"},
        {"id": "witness_2", "role": "Witness 2", "name_field": "witness_2_name", "address_field": "witness_2_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Special Power of Attorney.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Place of execution.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Principal and Attorney details.",
         "field_ids": ["principal_name", "principal_parent_spouse", "principal_address", "attorney_name", "attorney_parent_spouse", "attorney_address"]},
        {"id": "powers", "title": "Specific Power", "description": "Exact act authorized.",
         "field_ids": ["specific_matter_description", "authority_or_property", "effective_date"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("principal_name", "Principal full name", "PRINCIPAL NAME", "text", "required", "parties"),
        _field("principal_parent_spouse", "Principal Father / Spouse name", "PRINCIPAL PARENT OR SPOUSE", "text", "required", "parties"),
        _field("principal_address", "Principal permanent address", "PRINCIPAL ADDRESS", "textarea", "required", "parties"),
        _field("attorney_name", "Attorney Agent full name", "ATTORNEY NAME", "text", "required", "parties"),
        _field("attorney_parent_spouse", "Attorney Father / Spouse name", "ATTORNEY PARENT OR SPOUSE", "text", "required", "parties"),
        _field("attorney_address", "Attorney permanent address", "ATTORNEY ADDRESS", "textarea", "required", "parties"),
        _field("specific_matter_description", "Exact act / matter authorized", "SPECIFIC MATTER DESCRIPTION", "textarea", "required", "powers"),
        _field("authority_or_property", "Concerned property / court / authority details", "CONCERNED MATTER DETAILS", "textarea", "required", "powers"),
        _field("effective_date", "Date of execution", "EXECUTION DATE", "date", "required", "powers"),
        _field("witness_1_name", "Witness 1 name", "WITNESS 1 NAME", "text", "optional", "powers"),
        _field("witness_1_address", "Witness 1 address", "WITNESS 1 ADDRESS", "text", "optional", "powers"),
        _field("witness_2_name", "Witness 2 name", "WITNESS 2 NAME", "text", "optional", "powers"),
        _field("witness_2_address", "Witness 2 address", "WITNESS 2 ADDRESS", "text", "optional", "powers"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Title and Preamble",
            "required": True,
            "provision_class": "required",
            "body": (
                "குறிப்பிட்ட அதிகார ஆவணம்\n"
                "SPECIAL POWER OF ATTORNEY\n\n"
                "KNOW ALL MEN BY THESE PRESENTS that I, {principal_name}, son/daughter/wife of {principal_parent_spouse}, "
                "residing at {principal_address}, do hereby nominate, constitute, and appoint {attorney_name}, "
                "son/daughter/wife of {attorney_parent_spouse}, residing at {attorney_address}, as my true and lawful Special Attorney."
            ),
        },
        {
            "id": "specific_authority",
            "title": "1. Specific Authority Granted",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. My said Attorney is hereby authorized strictly to perform the following specific act(s) on my behalf: {specific_matter_description}.\n"
                "1.2. The power hereby conferred relates solely to: {authority_or_property}.\n"
                "1.3. My Attorney shall have power to sign papers, present documents for registration, submit representations, and receive receipts exclusively in connection with the said specific act."
            ),
        },
        {
            "id": "ratification",
            "title": "2. Ratification and Limitation",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. I hereby ratify and confirm all lawful acts done by my said Attorney pursuant to this Special Power of Attorney.\n"
                "2.2. This Power of Attorney shall automatically cease and determine upon the completion of the said specific transaction."
            ),
        },
        {
            "id": "signatures",
            "title": "Execution and Attestation",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, I have executed this Special Power of Attorney on this {effective_date} at {governing_law_seat}, {jurisdiction_region}."
            ),
        },
    ],
}


# =============================================================================
# 8. GIFT DEED (தான செட்டில்மென்ட் பத்திரம்)
# =============================================================================
GIFT_DEED_TEMPLATE: TemplateSpec = {
    "id": "gift_deed",
    "category": "deed",
    "title": "Deed of Gift (தான செட்டில்மென்ட் பத்திரம்)",
    "description": "Conveyance deed for transferring immovable property out of natural love and affection without monetary consideration under Section 122 of Transfer of Property Act, 1882.",
    "document_type": "Gift Deed",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English", "Tamil"],
    "version": "2026.1",
    "applicability": "Voluntary transfer of property under Section 122 of Transfer of Property Act, 1882.",
    "source": {
        "authority": "Registration Department, Government of Tamil Nadu & Department of Legal Affairs",
        "url": "https://tnreginet.gov.in",
        "document_name": "Model Deed of Gift under Transfer of Property Act, 1882",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Mandatory registration before the Sub-Registrar under Section 123 of Transfer of Property Act, 1882 and Section 17 of Registration Act, 1908",
        "Attestation by at least two independent witnesses",
        "Stamp duty payable as per State Stamp Act (concessional rates often available for family members)",
    ],
    "legal_query": "gift deed transfer of property act section 122 natural love affection donee donor acceptance India",
    "parties": [
        {"id": "donor", "role": "Donor (தானம் அளிப்பவர்)", "name_field": "donor_name",
         "type_field": "donor_type", "address_field": "donor_address"},
        {"id": "donee", "role": "Donee (தானம் பெறுபவர்)", "name_field": "donee_name",
         "type_field": "donee_type", "address_field": "donee_address"},
    ],
    "witnesses": [
        {"id": "witness_1", "role": "Witness 1", "name_field": "witness_1_name", "address_field": "witness_1_address"},
        {"id": "witness_2", "role": "Witness 2", "name_field": "witness_2_name", "address_field": "witness_2_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Gift Deed.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Sub-Registrar office jurisdiction.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Donor and Donee details.",
         "field_ids": ["donor_name", "donor_parent_spouse", "donor_address", "donee_name", "donee_parent_spouse", "donee_address", "relationship"]},
        {"id": "property", "title": "Property Schedule", "description": "Description and boundaries.",
         "field_ids": ["property_address", "survey_number", "extent_sqft", "boundary_north", "boundary_south", "boundary_east", "boundary_west", "effective_date"]},
        {"id": "review", "title": "Review", "description": "Review details before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("donor_name", "Donor full name", "DONOR NAME", "text", "required", "parties"),
        _field("donor_parent_spouse", "Donor Father / Spouse name", "DONOR PARENT OR SPOUSE", "text", "required", "parties"),
        _field("donor_address", "Donor permanent address", "DONOR ADDRESS", "textarea", "required", "parties"),
        _field("donee_name", "Donee full name", "DONEE NAME", "text", "required", "parties"),
        _field("donee_parent_spouse", "Donee Father / Spouse name", "DONEE PARENT OR SPOUSE", "text", "required", "parties"),
        _field("donee_address", "Donee permanent address", "DONEE ADDRESS", "textarea", "required", "parties"),
        _field("relationship", "Relationship of Donee to Donor (e.g. son, daughter, spouse)", "RELATIONSHIP", "text", "required", "parties"),
        _field("property_address", "Property complete location", "PROPERTY LOCATION", "textarea", "required", "property"),
        _field("survey_number", "Survey / Plot number", "SURVEY NUMBER", "text", "required", "property"),
        _field("extent_sqft", "Extent / Measurement", "PROPERTY EXTENT", "text", "required", "property"),
        _field("boundary_north", "North boundary", "NORTH BOUNDARY", "text", "required", "property"),
        _field("boundary_south", "South boundary", "SOUTH BOUNDARY", "text", "required", "property"),
        _field("boundary_east", "East boundary", "EAST BOUNDARY", "text", "required", "property"),
        _field("boundary_west", "West boundary", "WEST BOUNDARY", "text", "required", "property"),
        _field("effective_date", "Date of execution", "EXECUTION DATE", "date", "required", "property"),
        _field("witness_1_name", "Witness 1 name", "WITNESS 1 NAME", "text", "optional", "property"),
        _field("witness_1_address", "Witness 1 address", "WITNESS 1 ADDRESS", "text", "optional", "property"),
        _field("witness_2_name", "Witness 2 name", "WITNESS 2 NAME", "text", "optional", "property"),
        _field("witness_2_address", "Witness 2 address", "WITNESS 2 ADDRESS", "text", "optional", "property"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Title and Preamble",
            "required": True,
            "provision_class": "required",
            "body": (
                "தான செட்டில்மென்ட் பத்திரம்\n"
                "DEED OF GIFT\n\n"
                "THIS DEED OF GIFT is made and executed on this {effective_date} at {governing_law_seat}, {jurisdiction_region}."
            ),
        },
        {
            "id": "parties",
            "title": "Parties",
            "required": True,
            "provision_class": "required",
            "body": (
                "BY AND BETWEEN:\n\n"
                "1. {donor_name}, son/daughter/wife of {donor_parent_spouse}, residing at {donor_address} "
                "(hereinafter called the \"DONOR\" / தானம் அளிப்பவர், which expression shall include their legal representatives) of the ONE PART;\n\n"
                "AND\n\n"
                "2. {donee_name}, son/daughter/wife of {donee_parent_spouse}, residing at {donee_address} "
                "(hereinafter called the \"DONEE\" / தானம் பெறுபவர், which expression shall include their heirs and assigns) of the OTHER PART."
            ),
        },
        {
            "id": "recitals",
            "title": "Recitals of Natural Love and Affection",
            "required": True,
            "provision_class": "required",
            "body": (
                "WHEREAS:\n"
                "1. The Donor is the absolute owner in possession of the immovable property situated at {property_address}, "
                "Survey No. {survey_number}, measuring {extent_sqft}, fully described in the Schedule hereunder (the \"Schedule Property\").\n"
                "2. The Donee is the {relationship} of the Donor, and out of natural love and affection towards the Donee, "
                "the Donor desires to transfer and convey the Schedule Property unto the Donee without any monetary consideration.\n\n"
                "NOW THIS DEED WITNESSETH AS FOLLOWS:"
            ),
        },
        {
            "id": "gift_grant",
            "title": "1. Grant of Gift",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. In consideration of natural love and affection, the Donor hereby voluntarily, absolutely, and irrevocably grants, "
                "transfers, and conveys unto the Donee the Schedule Property together with all rights, easements, and appurtenances.\n"
                "1.2. The Donor has on this day delivered peaceful vacant possession of the Schedule Property to the Donee."
            ),
        },
        {
            "id": "acceptance",
            "title": "2. Acceptance by Donee",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. The Donee hereby gratefully accepts the gift of the Schedule Property during the lifetime of the Donor, "
                "in accordance with Section 122 of the Transfer of Property Act, 1882."
            ),
        },
        {
            "id": "schedule",
            "title": "Schedule of Property",
            "required": True,
            "provision_class": "required",
            "body": (
                "SCHEDULE OF THE PROPERTY:\n\n"
                "Location: {property_address}\n"
                "Survey / Sub-Division No: {survey_number}\n"
                "Extent: {extent_sqft}\n"
                "Boundaries:\n"
                "North by: {boundary_north}\n"
                "South by: {boundary_south}\n"
                "East by:  {boundary_east}\n"
                "West by:  {boundary_west}\n"
                "Situate within the Registration Sub-District of {governing_law_seat}."
            ),
        },
        {
            "id": "signatures",
            "title": "Signatures and Witnesses",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, the Donor has signed and delivered this Deed of Gift and the Donee has signed in token of acceptance "
                "in the presence of the witnesses subscribed below."
            ),
        },
    ],
}


# =============================================================================
# 9. RELEASE DEED (விடுதலைப் பத்திரம்)
# =============================================================================
RELEASE_DEED_TEMPLATE: TemplateSpec = {
    "id": "release_deed",
    "category": "deed",
    "title": "Deed of Release / Relinquishment (விடுதலைப் பத்திரம்)",
    "description": "Deed whereby a co-owner or legal heir releases and relinquishes their undivided share and interest in family or joint property in favour of other co-owners.",
    "document_type": "Release Deed",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English", "Tamil"],
    "version": "2026.1",
    "applicability": "Relinquishment of undivided share among co-owners under the Registration Act, 1908.",
    "source": {
        "authority": "Registration Department, Government of Tamil Nadu (Tnreginet)",
        "url": "https://tnreginet.gov.in",
        "document_name": "Model Release Deed",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Registration before the Sub-Registrar under Section 17(1)(b) of Registration Act, 1908",
        "Stamp duty payable as prescribed under State Stamp Act",
        "Attestation by two witnesses",
    ],
    "legal_query": "release deed relinquishment deed undivided share co-owner legal heir family property India",
    "parties": [
        {"id": "releasor", "role": "Releasor (உரிமை விடுவிப்பவர்)", "name_field": "releasor_name",
         "type_field": "releasor_type", "address_field": "releasor_address"},
        {"id": "releasee", "role": "Releasee (உரிமை பெறுபவர்)", "name_field": "releasee_name",
         "type_field": "releasee_type", "address_field": "releasee_address"},
    ],
    "witnesses": [
        {"id": "witness_1", "role": "Witness 1", "name_field": "witness_1_name", "address_field": "witness_1_address"},
        {"id": "witness_2", "role": "Witness 2", "name_field": "witness_2_name", "address_field": "witness_2_address"},
    ],
    "steps": [
        {"id": "type", "title": "Document type", "description": "Release Deed.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Registration jurisdiction.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Releasor and Releasee details.",
         "field_ids": ["releasor_name", "releasor_parent_spouse", "releasor_address", "releasee_name", "releasee_parent_spouse", "releasee_address", "relationship"]},
        {"id": "property", "title": "Property Schedule", "description": "Property details and relinquished share.",
         "field_ids": ["property_address", "survey_number", "extent_sqft", "relinquished_share_fraction", "effective_date"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("releasor_name", "Releasor full name", "RELEASOR NAME", "text", "required", "parties"),
        _field("releasor_parent_spouse", "Releasor Father / Spouse name", "RELEASOR PARENT OR SPOUSE", "text", "required", "parties"),
        _field("releasor_address", "Releasor permanent address", "RELEASOR ADDRESS", "textarea", "required", "parties"),
        _field("releasee_name", "Releasee full name", "RELEASEE NAME", "text", "required", "parties"),
        _field("releasee_parent_spouse", "Releasee Father / Spouse name", "RELEASEE PARENT OR SPOUSE", "text", "required", "parties"),
        _field("releasee_address", "Releasee permanent address", "RELEASEE ADDRESS", "textarea", "required", "parties"),
        _field("relationship", "Family relationship between parties", "RELATIONSHIP", "text", "required", "parties"),
        _field("property_address", "Property complete location", "PROPERTY LOCATION", "textarea", "required", "property"),
        _field("survey_number", "Survey / Plot number", "SURVEY NUMBER", "text", "required", "property"),
        _field("extent_sqft", "Total property extent", "PROPERTY EXTENT", "text", "required", "property"),
        _field("relinquished_share_fraction", "Share being relinquished (e.g. 1/3rd share)", "RELINQUISHED SHARE", "text", "required", "property"),
        _field("effective_date", "Date of execution", "EXECUTION DATE", "date", "required", "property"),
        _field("witness_1_name", "Witness 1 name", "WITNESS 1 NAME", "text", "optional", "property"),
        _field("witness_1_address", "Witness 1 address", "WITNESS 1 ADDRESS", "text", "optional", "property"),
        _field("witness_2_name", "Witness 2 name", "WITNESS 2 NAME", "text", "optional", "property"),
        _field("witness_2_address", "Witness 2 address", "WITNESS 2 ADDRESS", "text", "optional", "property"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Title and Preamble",
            "required": True,
            "provision_class": "required",
            "body": (
                "விடுதலைப் பத்திரம்\n"
                "DEED OF RELEASE AND RELINQUISHMENT\n\n"
                "THIS DEED OF RELEASE is executed on this {effective_date} at {governing_law_seat}, {jurisdiction_region}."
            ),
        },
        {
            "id": "parties",
            "title": "Parties",
            "required": True,
            "provision_class": "required",
            "body": (
                "BETWEEN:\n\n"
                "1. {releasor_name}, son/daughter/wife of {releasor_parent_spouse}, residing at {releasor_address} "
                "(hereinafter called the \"RELEASOR\", which expression shall include their heirs and legal representatives) of the ONE PART;\n\n"
                "AND\n\n"
                "2. {releasee_name}, son/daughter/wife of {releasee_parent_spouse}, residing at {releasee_address} "
                "(hereinafter called the \"RELEASEE\", which expression shall include their heirs and assigns) of the OTHER PART."
            ),
        },
        {
            "id": "recitals",
            "title": "Recitals of Joint Title and Relinquishment",
            "required": True,
            "provision_class": "required",
            "body": (
                "WHEREAS:\n"
                "1. The parties hereto are {relationship} and co-owners of the immovable property fully described in the Schedule hereunder.\n"
                "2. The Releasor holds an undivided {relinquished_share_fraction} share in the Schedule Property.\n"
                "3. The Releasor has voluntarily agreed to release, extinguish, and relinquish all their undivided right, title, and interest "
                "in the Schedule Property in favour of the Releasee, so that the Releasee becomes the absolute owner thereof.\n\n"
                "NOW THIS DEED WITNESSETH AS FOLLOWS:"
            ),
        },
        {
            "id": "relinquishment",
            "title": "1. Operative Release and Renunciation",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. In consideration of the premises and natural family affection, the Releasor hereby forever releases, relinquishes, "
                "surrenders, and renounces unto the Releasee all their undivided {relinquished_share_fraction} share, right, title, and interest in the Schedule Property.\n"
                "1.2. The Releasor declares that from this day forward, they or anyone claiming through them shall have no claim, right, or demand over the Schedule Property."
            ),
        },
        {
            "id": "schedule",
            "title": "Schedule of Property",
            "required": True,
            "provision_class": "required",
            "body": (
                "SCHEDULE OF THE PROPERTY:\n\n"
                "All that immovable property situated at: {property_address}.\n"
                "Survey No: {survey_number}.\n"
                "Total Extent: {extent_sqft}.\n"
                "Relinquished Share: Undivided {relinquished_share_fraction} share."
            ),
        },
        {
            "id": "signatures",
            "title": "Signatures and Witnesses",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, the Releasor and the Releasee have signed this Deed of Release in the presence of the witnesses subscribed below."
            ),
        },
    ],
}


# =============================================================================
# 10. COMMERCIAL LEASE AGREEMENT
# =============================================================================
COMMERCIAL_LEASE_TEMPLATE: TemplateSpec = {
    "id": "commercial_lease",
    "category": "agreement",
    "title": "Commercial Lease Agreement",
    "description": "Commercial property lease agreement covering fit-out period, lock-in period, rent escalation (e.g. 5% annually), Common Area Maintenance (CAM), signage, and GST.",
    "document_type": "Commercial Lease Agreement",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "Office spaces, commercial buildings, retail outlets, and warehouses in India.",
    "source": {
        "authority": "Startup India Model Contracts & Transfer of Property Act, 1882",
        "url": "https://www.startupindia.gov.in/content/sih/en/model-contracts.html",
        "document_name": "Model Commercial Lease Agreement",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Pay non-judicial stamp duty applicable in the state for commercial leases",
        "Compulsory registration before the Sub-Registrar if the lease exceeds 11 months under Section 107 of Transfer of Property Act, 1882",
    ],
    "legal_query": "commercial lease agreement lock-in rent escalation common area maintenance CAM GST fit-out India",
    "parties": [
        {"id": "lessor", "role": "Lessor / Landlord", "name_field": "lessor_name",
         "type_field": "lessor_type", "address_field": "lessor_address"},
        {"id": "lessee", "role": "Lessee / Tenant", "name_field": "lessee_name",
         "type_field": "lessee_type", "address_field": "lessee_address"},
    ],
    "steps": [
        {"id": "type", "title": "Agreement", "description": "Commercial Lease.", "field_ids": ["document_title", "business_nature"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Property seat.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Lessor and Lessee details.",
         "field_ids": ["lessor_name", "lessor_type", "lessor_address", "lessee_name", "lessee_type", "lessee_address"]},
        {"id": "premises", "title": "Commercial Premises", "description": "Super built-up area and address.",
         "field_ids": ["property_address", "built_up_area_sqft", "effective_date"]},
        {"id": "financial", "title": "Commercial Terms", "description": "Rent, CAM, deposit, escalation.",
         "field_ids": ["monthly_rent", "cam_charges", "deposit_amount", "rent_escalation_percent", "lock_in_months"]},
        {"id": "duration", "title": "Lease Term", "description": "Total lease duration.", "field_ids": ["lease_years", "termination_notice_days"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        _field("business_nature", "Lessee business activity", "BUSINESS ACTIVITY", "text", "required", "type"),
        *_jurisdiction_fields(),
        _field("lessor_name", "Lessor full name / company name", "LESSOR NAME", "text", "required", "parties"),
        _field("lessor_type", "Lessor entity type", "LESSOR TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("lessor_address", "Lessor address", "LESSOR ADDRESS", "textarea", "required", "parties"),
        _field("lessee_name", "Lessee company / entity name", "LESSEE NAME", "text", "required", "parties"),
        _field("lessee_type", "Lessee entity type", "LESSEE TYPE", "select", "required", "parties", options=list(PARTY_TYPE_OPTIONS)),
        _field("lessee_address", "Lessee address", "LESSEE ADDRESS", "textarea", "required", "parties"),
        _field("property_address", "Commercial premises address", "PREMISES ADDRESS", "textarea", "required", "premises"),
        _field("built_up_area_sqft", "Super built-up area in sq. ft.", "SUPER BUILT-UP AREA", "text", "required", "premises"),
        _field("effective_date", "Lease commencement date", "COMMENCEMENT DATE", "date", "required", "premises"),
        _field("monthly_rent", "Monthly base rent in INR (exclusive of GST)", "MONTHLY BASE RENT", "currency", "required", "financial", min=0),
        _field("cam_charges", "Monthly Common Area Maintenance (CAM) charges in INR", "CAM CHARGES", "currency", "recommended", "financial", min=0),
        _field("deposit_amount", "Interest-free security deposit in INR", "SECURITY DEPOSIT", "currency", "required", "financial", min=0),
        _field("rent_escalation_percent", "Annual rent escalation percentage (e.g. 5%)", "RENT ESCALATION PERCENT", "number", "recommended", "financial", min=0, max=25),
        _field("lock_in_months", "Lock-in period in months (e.g. 12 or 24)", "LOCK-IN MONTHS", "number", "recommended", "financial", min=0, max=60),
        _field("lease_years", "Total lease term in years (e.g. 3, 5, or 9)", "LEASE TERM YEARS", "number", "required", "duration", min=1, max=30),
        _field("termination_notice_days", "Notice period after lock-in (days)", "NOTICE DAYS", "number", "recommended", "duration", min=30, max=180),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Title and Preamble",
            "required": True,
            "provision_class": "required",
            "body": (
                "COMMERCIAL LEASE AGREEMENT\n\n"
                "THIS COMMERCIAL LEASE AGREEMENT is executed on this {effective_date} at {governing_law_seat}, {jurisdiction_region}."
            ),
        },
        {
            "id": "parties",
            "title": "Parties",
            "required": True,
            "provision_class": "required",
            "body": (
                "BY AND BETWEEN:\n\n"
                "1. {lessor_name}, a {lessor_type}, having office/address at {lessor_address} (hereinafter referred to as the \"LESSOR\");\n\n"
                "AND\n\n"
                "2. {lessee_name}, a {lessee_type}, having office/address at {lessee_address} (hereinafter referred to as the \"LESSEE\")."
            ),
        },
        {
            "id": "premises",
            "title": "1. Demised Premises and Permitted Use",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. The Lessor hereby grants on lease to the Lessee commercial space comprising {built_up_area_sqft} sq. ft. "
                "situated at {property_address} (the \"Demised Premises\").\n"
                "1.2. The Lessee shall use the Demised Premises exclusively for commercial purposes relating to: {business_nature}."
            ),
        },
        {
            "id": "rent_and_cam",
            "title": "2. Rent, CAM, and Taxes",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. The Lessee shall pay to the Lessor a monthly base rent of Rs. {monthly_rent}/- (plus applicable Goods and Services Tax - GST) "
                "payable on or before the 7th day of each English calendar month in advance.\n"
                "2.2. The Lessee shall additionally pay Common Area Maintenance (CAM) charges of Rs. {cam_charges}/- per month.\n"
                "2.3. The monthly base rent shall escalate by {rent_escalation_percent}% at the expiry of every 12 months from the commencement date."
            ),
        },
        {
            "id": "deposit",
            "title": "3. Security Deposit",
            "required": True,
            "provision_class": "required",
            "body": (
                "3.1. The Lessee has paid an interest-free refundable security deposit of Rs. {deposit_amount}/-.\n"
                "3.2. The deposit shall be refunded upon expiration and peaceful handover of vacant possession, subject to clearance of dues."
            ),
        },
        {
            "id": "lock_in_term",
            "title": "4. Term, Lock-in, and Termination",
            "required": True,
            "provision_class": "required",
            "body": (
                "4.1. The lease shall be for a total term of {lease_years} years from {effective_date}.\n"
                "4.2. Both parties agree to a lock-in period of {lock_in_months} months. Neither party may terminate during the lock-in except for material breach.\n"
                "4.3. Post lock-in, either party may terminate by giving {termination_notice_days} days' prior written notice."
            ),
        },
        {
            "id": "signatures",
            "title": "Signatures",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, the Lessor and Lessee have caused this Commercial Lease Agreement to be duly executed."
            ),
        },
    ],
}


# =============================================================================
# 11. LEAVE AND LICENSE AGREEMENT
# =============================================================================
LEAVE_LICENSE_TEMPLATE: TemplateSpec = {
    "id": "leave_license",
    "category": "agreement",
    "title": "Leave and License Agreement",
    "description": "Leave and license agreement for residential or commercial property under Section 52 of the Indian Easements Act, 1882 (granting purely permissive occupancy with no tenancy rights).",
    "document_type": "Leave and License Agreement",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "Maharashtra / Karnataka / All India",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "Premises occupancy under Section 52 of Indian Easements Act, 1882.",
    "source": {
        "authority": "Department of Registration & Stamps, Government of Maharashtra & Easements Act, 1882",
        "url": "https://igrmaharashtra.gov.in",
        "document_name": "Model Leave and License Agreement",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "In Maharashtra, compulsory e-registration under Section 55 of Maharashtra Rent Control Act, 1999",
        "Execution on appropriate non-judicial stamp paper under State Stamp Act",
    ],
    "legal_query": "leave and license agreement licensee licensor easements act section 52 license fee security deposit India",
    "parties": [
        {"id": "licensor", "role": "Licensor (Owner)", "name_field": "licensor_name",
         "type_field": "licensor_type", "address_field": "licensor_address"},
        {"id": "licensee", "role": "Licensee (Occupant)", "name_field": "licensee_name",
         "type_field": "licensee_type", "address_field": "licensee_address"},
    ],
    "steps": [
        {"id": "type", "title": "Agreement", "description": "Leave and License.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Location.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Licensor and Licensee particulars.",
         "field_ids": ["licensor_name", "licensor_address", "licensee_name", "licensee_address"]},
        {"id": "premises", "title": "Licensed Premises", "description": "Property details and duration.",
         "field_ids": ["property_address", "effective_date", "duration_months"]},
        {"id": "financial", "title": "License Fee", "description": "Monthly license compensation and deposit.",
         "field_ids": ["license_fee", "deposit_amount", "termination_notice_days"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("licensor_name", "Licensor full name", "LICENSOR NAME", "text", "required", "parties"),
        _field("licensor_address", "Licensor permanent address", "LICENSOR ADDRESS", "textarea", "required", "parties"),
        _field("licensee_name", "Licensee full name", "LICENSEE NAME", "text", "required", "parties"),
        _field("licensee_address", "Licensee permanent address", "LICENSEE ADDRESS", "textarea", "required", "parties"),
        _field("property_address", "Licensed property address", "LICENSED PREMISES ADDRESS", "textarea", "required", "premises"),
        _field("effective_date", "License start date", "START DATE", "date", "required", "premises"),
        _field("duration_months", "Duration in months (e.g. 11 or 22 months)", "DURATION MONTHS", "number", "required", "premises", min=1, max=36),
        _field("license_fee", "Monthly license fee in INR", "MONTHLY LICENSE FEE", "currency", "required", "financial", min=0),
        _field("deposit_amount", "Interest-free refundable security deposit", "SECURITY DEPOSIT", "currency", "required", "financial", min=0),
        _field("termination_notice_days", "Notice period to vacate (days)", "NOTICE DAYS", "number", "recommended", "financial", min=15, max=90),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Title and Preamble",
            "required": True,
            "provision_class": "required",
            "body": (
                "LEAVE AND LICENSE AGREEMENT\n\n"
                "THIS LEAVE AND LICENSE AGREEMENT is made on this {effective_date} at {governing_law_seat}, {jurisdiction_region}."
            ),
        },
        {
            "id": "parties",
            "title": "Parties",
            "required": True,
            "provision_class": "required",
            "body": (
                "BETWEEN:\n\n"
                "1. {licensor_name}, residing at {licensor_address} (hereinafter called the \"LICENSOR\");\n\n"
                "AND\n\n"
                "2. {licensee_name}, residing at {licensee_address} (hereinafter called the \"LICENSEE\")."
            ),
        },
        {
            "id": "license_grant",
            "title": "1. Grant of License and Negative Tenancy Declaration",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. The Licensor hereby grants to the Licensee a purely temporary, revocable leave and license to occupy the premises at {property_address} "
                "for a period of {duration_months} months commencing on {effective_date}.\n"
                "1.2. IT IS EXPRESSLY AGREED that this Agreement is governed by Section 52 of the Indian Easements Act, 1882. "
                "Nothing herein shall be deemed to create any tenancy, sub-tenancy, lease, or proprietary interest in favour of the Licensee, "
                "the legal possession and ownership remaining exclusively with the Licensor at all times."
            ),
        },
        {
            "id": "license_fee",
            "title": "2. License Fee and Deposit",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. The Licensee shall pay a monthly license fee of Rs. {license_fee}/- in advance on or before the 5th of each month.\n"
                "2.2. The Licensee has deposited an interest-free refundable deposit of Rs. {deposit_amount}/-, refundable on peaceful vacation."
            ),
        },
        {
            "id": "termination",
            "title": "3. Vacation and Revocation",
            "required": True,
            "provision_class": "required",
            "body": (
                "3.1. Either party may revoke this license by giving {termination_notice_days} days' written notice.\n"
                "3.2. Upon expiration or revocation, the Licensee shall immediately remove their personal belongings and deliver vacant possession."
            ),
        },
        {
            "id": "signatures",
            "title": "Signatures",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, the Licensor and the Licensee have signed this Leave and License Agreement."
            ),
        },
    ],
}


# =============================================================================
# 12. LOAN AGREEMENT
# =============================================================================
LOAN_AGREEMENT_TEMPLATE: TemplateSpec = {
    "id": "loan_agreement",
    "category": "agreement",
    "title": "Loan Agreement",
    "description": "Standard bilateral loan agreement for personal or commercial lending specifying principal amount, interest rate, repayment tenure, and default covenants.",
    "document_type": "Loan Agreement",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "Bilateral personal and inter-corporate loans in India.",
    "source": {
        "authority": "Reserve Bank of India Guidelines & Indian Contract Act, 1872",
        "url": "https://rbi.org.in",
        "document_name": "Standard Bilateral Loan Agreement Format",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on non-judicial stamp paper as per State Stamp Act (Article on Agreement / Bond)",
        "Accompanied by a Demand Promissory Note for enhanced summary suit enforceability",
    ],
    "legal_query": "loan agreement lender borrower interest rate repayment principal promissory note default India",
    "parties": [
        {"id": "lender", "role": "Lender", "name_field": "lender_name",
         "type_field": "lender_type", "address_field": "lender_address"},
        {"id": "borrower", "role": "Borrower", "name_field": "borrower_name",
         "type_field": "borrower_type", "address_field": "borrower_address"},
    ],
    "steps": [
        {"id": "type", "title": "Agreement", "description": "Loan Agreement.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Seat.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Lender and Borrower particulars.",
         "field_ids": ["lender_name", "lender_address", "borrower_name", "borrower_address"]},
        {"id": "loan", "title": "Loan Terms", "description": "Principal amount, interest, and tenure.",
         "field_ids": ["principal_amount", "interest_rate_percent", "repayment_tenure_months", "effective_date"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("lender_name", "Lender full name", "LENDER NAME", "text", "required", "parties"),
        _field("lender_address", "Lender address", "LENDER ADDRESS", "textarea", "required", "parties"),
        _field("borrower_name", "Borrower full name", "BORROWER NAME", "text", "required", "parties"),
        _field("borrower_address", "Borrower address", "BORROWER ADDRESS", "textarea", "required", "parties"),
        _field("principal_amount", "Principal loan amount in INR", "PRINCIPAL LOAN AMOUNT", "currency", "required", "loan", min=1000),
        _field("interest_rate_percent", "Annual interest rate (e.g. 10% or 0% if interest-free)", "INTEREST RATE", "number", "required", "loan", min=0, max=48),
        _field("repayment_tenure_months", "Repayment period in months", "REPAYMENT PERIOD MONTHS", "number", "required", "loan", min=1, max=120),
        _field("effective_date", "Date of loan disbursement", "LOAN DATE", "date", "required", "loan"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Title and Preamble",
            "required": True,
            "provision_class": "required",
            "body": (
                "LOAN AGREEMENT\n\n"
                "THIS LOAN AGREEMENT is made on this {effective_date} at {governing_law_seat}, {jurisdiction_region}."
            ),
        },
        {
            "id": "parties",
            "title": "Parties",
            "required": True,
            "provision_class": "required",
            "body": (
                "BETWEEN:\n\n"
                "1. {lender_name}, residing at {lender_address} (hereinafter called the \"LENDER\");\n\n"
                "AND\n\n"
                "2. {borrower_name}, residing at {borrower_address} (hereinafter called the \"BORROWER\")."
            ),
        },
        {
            "id": "facility",
            "title": "1. Loan Facility and Disbursement",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. The Lender agrees to lend and the Borrower agrees to borrow a sum of Rs. {principal_amount}/- (Rupees [AMOUNT IN WORDS]).\n"
                "1.2. The said amount has been disbursed by the Lender to the Borrower through banking channels, receipt whereof the Borrower acknowledges."
            ),
        },
        {
            "id": "repayment",
            "title": "2. Interest and Repayment",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. The loan shall carry interest at the rate of {interest_rate_percent}% per annum.\n"
                "2.2. The Borrower shall repay the entire principal together with accrued interest within a period of {repayment_tenure_months} months from {effective_date}."
            ),
        },
        {
            "id": "default",
            "title": "3. Events of Default",
            "required": True,
            "provision_class": "required",
            "body": (
                "3.1. Non-payment of any installment on the due date shall constitute an Event of Default, entitling the Lender to recall the entire outstanding balance immediately.\n"
                "3.2. Default interest of 2% per month shall accrue on overdue amounts until full realization."
            ),
        },
        {
            "id": "signatures",
            "title": "Signatures",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, the parties have signed this Loan Agreement as of the date first written above."
            ),
        },
    ],
}


# =============================================================================
# 13. LEGAL AID APPLICATION (NALSA MODEL)
# =============================================================================
LEGAL_AID_APPLICATION_TEMPLATE: TemplateSpec = {
    "id": "legal_aid_application",
    "category": "application",
    "title": "Legal Aid Application (NALSA Model Format)",
    "description": "Statutory application for free legal aid and representation under Section 12 of the Legal Services Authorities Act, 1987 to DLSA / SLSA / HCLSC / SCLSC.",
    "document_type": "Legal Aid Application",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English", "Hindi", "Tamil"],
    "version": "2026.1",
    "applicability": "Applications for free legal services across India under Legal Services Authorities Act, 1987.",
    "source": {
        "authority": "National Legal Services Authority (NALSA) & Supreme Court Legal Services Committee",
        "url": "https://nalsa.gov.in",
        "document_name": "Model Application for Free Legal Services under Section 12 of LSA Act, 1987",
        "reference_date": "1987 (as amended)",
    },
    "execution_requirements": [
        "Applicant must satisfy eligibility under Section 12 (Women, Children, SC/ST, Industrial Workman, Disabled, Custody, or Annual Income criteria)",
        "No court fee or stamp duty is payable on this statutory application",
    ],
    "legal_query": "legal aid application NALSA section 12 legal services authorities act DLSA free legal services India",
    "parties": [
        {"id": "applicant", "role": "Applicant", "name_field": "applicant_name",
         "type_field": "applicant_type", "address_field": "applicant_address"},
        {"id": "authority", "role": "Legal Services Authority", "name_field": "authority_name",
         "type_field": "authority_type", "address_field": "authority_address"},
    ],
    "steps": [
        {"id": "type", "title": "Application", "description": "Legal Aid.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Authority", "description": "Location.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Applicant Details", "description": "Personal details.",
         "field_ids": ["applicant_name", "applicant_address", "applicant_phone", "eligibility_category", "annual_income"]},
        {"id": "case", "title": "Case Details", "description": "Nature of case and relief sought.",
         "field_ids": ["nature_of_case", "opposite_party_details", "relief_requested", "effective_date"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("applicant_name", "Applicant full name", "APPLICANT NAME", "text", "required", "parties"),
        _field("applicant_address", "Applicant address", "APPLICANT ADDRESS", "textarea", "required", "parties"),
        _field("applicant_phone", "Applicant phone number", "APPLICANT PHONE", "tel", "recommended", "parties"),
        _field("eligibility_category", "Eligibility category (e.g. Woman / Child / SC / ST / Income Below Limit)", "ELIGIBILITY CATEGORY", "text", "required", "parties"),
        _field("annual_income", "Annual family income in INR", "ANNUAL INCOME", "currency", "required", "parties", min=0),
        _field("nature_of_case", "Nature of dispute / legal matter (civil / criminal / family / labour)", "CASE NATURE", "textarea", "required", "case"),
        _field("opposite_party_details", "Opposite party name and address", "OPPOSITE PARTY DETAILS", "textarea", "required", "case"),
        _field("relief_requested", "Assistance requested (advocate assignment / advice / court fee)", "RELIEF REQUESTED", "textarea", "required", "case"),
        _field("effective_date", "Date of application", "APPLICATION DATE", "date", "required", "case"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Application Heading",
            "required": True,
            "provision_class": "required",
            "body": (
                "APPLICATION FOR FREE LEGAL SERVICES / LEGAL AID\n"
                "[Under Section 12 of the Legal Services Authorities Act, 1987]\n\n"
                "Date: {effective_date}\n\n"
                "TO:\n"
                "The Member Secretary / Secretary,\n"
                "District Legal Services Authority (DLSA) / State Legal Services Authority,\n"
                "{governing_law_seat}, {jurisdiction_region}."
            ),
        },
        {
            "id": "particulars",
            "title": "1. Applicant Particulars and Eligibility",
            "required": True,
            "provision_class": "required",
            "body": (
                "1. Full Name of Applicant: {applicant_name}\n"
                "2. Permanent Address: {applicant_address}\n"
                "3. Contact Number: {applicant_phone}\n"
                "4. Eligibility Category under Section 12: {eligibility_category}\n"
                "5. Total Annual Household Income: Rs. {annual_income}/-"
            ),
        },
        {
            "id": "dispute_details",
            "title": "2. Brief Statement of Case",
            "required": True,
            "provision_class": "required",
            "body": (
                "2.1. Nature of Legal Matter: {nature_of_case}\n"
                "2.2. Opposite Party: {opposite_party_details}\n"
                "2.3. Legal Assistance Requested: {relief_requested}."
            ),
        },
        {
            "id": "verification",
            "title": "3. Declaration and Undertaking",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "I solemnly declare that the statements made herein are true to the best of my knowledge and that I do not possess means to engage an advocate.\n\n"
                "Place: {governing_law_seat}\n"
                "Date: {effective_date}\n\n"
                "SIGNATURE OF APPLICANT\n"
                "({applicant_name})"
            ),
        },
    ],
}


# =============================================================================
# 14. NOTICE TO VACATE UNDER SECTION 106 TRANSFER OF PROPERTY ACT
# =============================================================================
EVICTION_NOTICE_TEMPLATE: TemplateSpec = {
    "id": "eviction_notice",
    "category": "notice",
    "title": "Notice to Vacate (Section 106 Transfer of Property Act, 1882)",
    "description": "Statutory eviction notice terminating month-to-month tenancy and demanding vacant possession within 15 days under Section 106 of the Transfer of Property Act, 1882.",
    "document_type": "Eviction Notice",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English", "Tamil"],
    "version": "2026.1",
    "applicability": "Termination of month-to-month leases under Section 106 of Transfer of Property Act, 1882.",
    "source": {
        "authority": "Transfer of Property Act, 1882 & High Court Practice Directions",
        "url": "https://indiacode.nic.in/handle/123456789/2338",
        "document_name": "Notice to Quit under Section 106 Transfer of Property Act",
        "reference_date": "1882 (as amended)",
    },
    "execution_requirements": [
        "Must provide at least 15 days clear notice for month-to-month tenancy (or 6 months for agricultural/manufacturing leases)",
        "Must be sent by Registered Post with Acknowledgement Due (RPAD) or Speed Post",
    ],
    "legal_query": "eviction notice section 106 transfer of property act quit vacate tenant landlord India",
    "parties": [
        {"id": "landlord", "role": "Landlord", "name_field": "landlord_name",
         "type_field": "landlord_type", "address_field": "landlord_address"},
        {"id": "tenant", "role": "Tenant", "name_field": "tenant_name",
         "type_field": "tenant_type", "address_field": "tenant_address"},
    ],
    "steps": [
        {"id": "type", "title": "Notice", "description": "Section 106 Notice.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Property seat.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Landlord and Tenant.",
         "field_ids": ["landlord_name", "landlord_address", "tenant_name", "tenant_address", "advocate_name"]},
        {"id": "premises", "title": "Tenancy Particulars", "description": "Premises and rent.",
         "field_ids": ["property_address", "monthly_rent", "grounds_for_eviction", "effective_date"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("landlord_name", "Landlord full name", "LANDLORD NAME", "text", "required", "parties"),
        _field("landlord_address", "Landlord address", "LANDLORD ADDRESS", "textarea", "required", "parties"),
        _field("tenant_name", "Tenant full name", "TENANT NAME", "text", "required", "parties"),
        _field("tenant_address", "Tenant premises address", "TENANT PREMISES ADDRESS", "textarea", "required", "parties"),
        _field("advocate_name", "Advocate issuing notice (or Landlord)", "ADVOCATE NAME", "text", "required", "parties"),
        _field("property_address", "Premises complete address", "PREMISES COMPLETE ADDRESS", "textarea", "required", "premises"),
        _field("monthly_rent", "Current monthly rent in INR", "MONTHLY RENT", "currency", "required", "premises", min=0),
        _field("grounds_for_eviction", "Grounds for termination (e.g. lease expired / personal occupation / rent arrears)", "GROUNDS FOR TERMINATION", "textarea", "required", "premises"),
        _field("effective_date", "Date of notice", "DATE OF NOTICE", "date", "required", "premises"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Dispatch Mode and Header",
            "required": True,
            "provision_class": "required",
            "body": (
                "BY REGISTERED POST WITH ACKNOWLEDGEMENT DUE / SPEED POST\n\n"
                "STATUTORY NOTICE TO VACATE UNDER SECTION 106 OF THE TRANSFER OF PROPERTY ACT, 1882\n\n"
                "Date: {effective_date}\n\n"
                "TO:\n"
                "{tenant_name},\n"
                "{tenant_address}.\n\n"
                "Sir / Madam,"
            ),
        },
        {
            "id": "instructions",
            "title": "Instructions",
            "required": True,
            "provision_class": "required",
            "body": (
                "Under instructions from and on behalf of my client, {landlord_name}, residing at {landlord_address} "
                "(hereinafter referred to as \"my Client\"), I hereby serve upon you this Statutory Notice to Quit and Vacate as under:"
            ),
        },
        {
            "id": "facts",
            "title": "1. Tenancy Particulars and Grounds",
            "required": True,
            "provision_class": "required",
            "body": (
                "1.1. That you are in occupation of premises situated at {property_address} on a monthly tenancy at a rent of Rs. {monthly_rent}/- per month.\n"
                "1.2. That my Client hereby determines and terminates your tenancy on the following grounds: {grounds_for_eviction}."
            ),
        },
        {
            "id": "demand",
            "title": "2. Statutory 15-Day Demand to Quit and Hand Over Possession",
            "required": True,
            "provision_class": "required",
            "needs_legal_context": True,
            "body": (
                "2.1. YOU ARE HEREBY CALLED UPON to vacate and hand over peaceful, physical, and vacant possession of the premises "
                "to my Client within a period of 15 (FIFTEEN) DAYS from the date of receipt of this notice.\n"
                "2.2. TAKE NOTICE that if you fail to quit and deliver vacant possession within the said 15 days, your continued occupation shall be that of an unauthorized occupant / trespasser, "
                "and my Client will immediately institute an Eviction Suit against you for recovery of possession, arrears, and mesne profits / damages at current market rates, at your entire cost and peril."
            ),
        },
        {
            "id": "signatures",
            "title": "Advocate Signature",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "Yours faithfully,\n\n"
                "ADVOCATE FOR THE LANDLORD\n"
                "({advocate_name})\n"
                "Place: {governing_law_seat}"
            ),
        },
    ],
}


# =============================================================================
# 15. NAME CHANGE AFFIDAVIT
# =============================================================================
NAME_CHANGE_AFFIDAVIT_TEMPLATE: TemplateSpec = {
    "id": "name_change_affidavit",
    "category": "affidavit",
    "title": "Affidavit for Change of Name",
    "description": "Sworn affidavit before a Notary Public declaring change of name for official records, gazette notification, passport, and identity updates.",
    "document_type": "Name Change Affidavit",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English", "Hindi", "Tamil"],
    "version": "2026.1",
    "applicability": "Official change of personal name in India.",
    "source": {
        "authority": "Department of Publication, Ministry of Housing and Urban Affairs & Notaries Act, 1952",
        "url": "https://deptpub.gov.in",
        "document_name": "Standard Format of Affidavit for Change of Name in The Gazette of India",
        "reference_date": "2024",
    },
    "execution_requirements": [
        "Execution on non-judicial stamp paper of prescribed value (Rs. 20-100 depending on state)",
        "Attestation before a Notary Public / First Class Magistrate with Notarial Seal and Stamp",
    ],
    "legal_query": "name change affidavit gazette notification notary public deponent India",
    "parties": [
        {"id": "deponent", "role": "Deponent", "name_field": "deponent_new_name",
         "type_field": "deponent_type", "address_field": "deponent_address"},
    ],
    "steps": [
        {"id": "type", "title": "Affidavit", "description": "Name Change Affidavit.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Notary seat.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "names", "title": "Name Particulars", "description": "Old and new name details.",
         "field_ids": ["deponent_old_name", "deponent_new_name", "deponent_parent_spouse", "deponent_age", "deponent_address", "effective_date"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("deponent_old_name", "Previous full name (as in records)", "OLD NAME", "text", "required", "names"),
        _field("deponent_new_name", "New adopted full name", "NEW ADOPTED NAME", "text", "required", "names"),
        _field("deponent_parent_spouse", "Father / Spouse full name", "PARENT OR SPOUSE NAME", "text", "required", "names"),
        _field("deponent_age", "Age in completed years", "AGE", "number", "required", "names", min=18, max=120),
        _field("deponent_address", "Permanent residential address", "RESIDENTIAL ADDRESS", "textarea", "required", "names"),
        _field("effective_date", "Date of sworn affirmation", "AFFIDAVIT DATE", "date", "required", "names"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Notary Heading and Solemn Affirmation",
            "required": True,
            "provision_class": "required",
            "body": (
                "BEFORE THE NOTARY PUBLIC / OATH COMMISSIONER AT {governing_law_seat}, {jurisdiction_region}\n\n"
                "AFFIDAVIT FOR CHANGE OF NAME\n\n"
                "I, {deponent_new_name}, formerly known as {deponent_old_name}, son/daughter/wife of {deponent_parent_spouse}, "
                "aged about {deponent_age} years, residing at {deponent_address}, do hereby solemnly affirm and declare on oath as under:"
            ),
        },
        {
            "id": "statements",
            "title": "1. Sworn Declarations",
            "required": True,
            "provision_class": "required",
            "body": (
                "1. That my birth name was recorded in all official documents as: {deponent_old_name}.\n"
                "2. That for all purposes and occasions, I have formally assumed and adopted the new name: {deponent_new_name}.\n"
                "3. That from this date forward, I shall at all times and in all records, deeds, proceedings, and transactions "
                "be known and addressed exclusively by my new adopted name: {deponent_new_name}.\n"
                "4. That this name change is voluntary and there is no fraudulent, unlawful, or dishonest intention behind the same."
            ),
        },
        {
            "id": "verification",
            "title": "2. Statutory Verification",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "VERIFICATION\n\n"
                "I, the deponent above named, do hereby verify and state that the contents of paragraphs 1 to 4 above are true and correct "
                "to my personal knowledge and belief, and nothing material has been concealed therefrom.\n\n"
                "Verified at {governing_law_seat} on this {effective_date}.\n\n"
                "DEPONENT\n"
                "({deponent_new_name})\n\n"
                "Identified by me: Advocate\n\n"
                "Solemnly affirmed before me: Notary Public (with Notarial Seal)"
            ),
        },
    ],
}


# =============================================================================
# 16. INDEMNITY BOND
# =============================================================================
INDEMNITY_BOND_TEMPLATE: TemplateSpec = {
    "id": "indemnity_bond",
    "category": "affidavit",
    "title": "Indemnity Bond",
    "description": "Standard indemnity bond under Section 124 of the Indian Contract Act, 1872 holding an obligee harmless against claims, damages, or financial loss.",
    "document_type": "Indemnity Bond",
    "jurisdiction_country": "IN",
    "jurisdiction_region": "All India",
    "language": ["English"],
    "version": "2026.1",
    "applicability": "Contract of indemnity under Section 124 of Indian Contract Act, 1872.",
    "source": {
        "authority": "Indian Contract Act, 1872 & Ministry of Finance Model Formats",
        "url": "https://indiacode.nic.in/handle/123456789/2187",
        "document_name": "Model Indemnity Bond",
        "reference_date": "1872 (as amended)",
    },
    "execution_requirements": [
        "Execution on non-judicial stamp paper of prescribed denomination under the State Stamp Act",
        "Attestation before a Notary Public or two independent witnesses",
    ],
    "legal_query": "indemnity bond contract of indemnity section 124 obligor obligee hold harmless India",
    "parties": [
        {"id": "indemnifier", "role": "Indemnifier / Obligor", "name_field": "indemnifier_name",
         "type_field": "indemnifier_type", "address_field": "indemnifier_address"},
        {"id": "indemnified", "role": "Indemnified / Obligee", "name_field": "indemnified_name",
         "type_field": "indemnified_type", "address_field": "indemnified_address"},
    ],
    "steps": [
        {"id": "type", "title": "Bond", "description": "Indemnity Bond.", "field_ids": ["document_title"]},
        {"id": "jurisdiction", "title": "Jurisdiction", "description": "Place.", "field_ids": ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"]},
        {"id": "parties", "title": "Parties", "description": "Obligor and Obligee.",
         "field_ids": ["indemnifier_name", "indemnifier_address", "indemnified_name", "indemnified_address"]},
        {"id": "matter", "title": "Subject of Indemnity", "description": "Matter and amount.",
         "field_ids": ["indemnity_subject", "max_indemnity_amount", "effective_date"]},
        {"id": "review", "title": "Review", "description": "Review before generation.", "field_ids": []},
    ],
    "fields": [
        _field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
        *_jurisdiction_fields(),
        _field("indemnifier_name", "Indemnifier full name", "INDEMNIFIER NAME", "text", "required", "parties"),
        _field("indemnifier_address", "Indemnifier address", "INDEMNIFIER ADDRESS", "textarea", "required", "parties"),
        _field("indemnified_name", "Indemnified entity / authority name", "INDEMNIFIED NAME", "text", "required", "parties"),
        _field("indemnified_address", "Indemnified office address", "INDEMNIFIED ADDRESS", "textarea", "required", "parties"),
        _field("indemnity_subject", "Purpose / subject matter of indemnity", "INDEMNITY PURPOSE", "textarea", "required", "matter"),
        _field("max_indemnity_amount", "Maximum indemnity limit in INR", "MAX INDEMNITY LIMIT", "currency", "required", "matter", min=1000),
        _field("effective_date", "Date of bond", "BOND DATE", "date", "required", "matter"),
    ],
    "clauses": [
        {
            "id": "title",
            "title": "Title and Preamble",
            "required": True,
            "provision_class": "required",
            "body": (
                "INDEMNITY BOND\n\n"
                "THIS INDEMNITY BOND is executed on this {effective_date} at {governing_law_seat}, {jurisdiction_region}."
            ),
        },
        {
            "id": "parties",
            "title": "Parties",
            "required": True,
            "provision_class": "required",
            "body": (
                "BY:\n\n"
                "{indemnifier_name}, residing at {indemnifier_address} (hereinafter called the \"INDEMNIFIER / OBLIGOR\");\n\n"
                "IN FAVOUR OF:\n\n"
                "{indemnified_name}, having office at {indemnified_address} (hereinafter called the \"INDEMNIFIED / OBLIGEE\")."
            ),
        },
        {
            "id": "recitals",
            "title": "Recitals and Covenant of Indemnity",
            "required": True,
            "provision_class": "required",
            "body": (
                "WHEREAS the Obligee has at the request of the Indemnifier agreed to proceed regarding: {indemnity_subject}.\n\n"
                "NOW THIS DEED WITNESSETH that in consideration of the premises, the Indemnifier does hereby bind themselves, "
                "their heirs, executors, and administrators to unconditionally indemnify, defend, and hold harmless the Obligee "
                "up to a sum of Rs. {max_indemnity_amount}/- (Rupees [AMOUNT IN WORDS]) against all losses, damages, claims, costs, and expenses."
            ),
        },
        {
            "id": "signatures",
            "title": "Execution and Signature",
            "required": True,
            "provision_class": "required",
            "include_signature": True,
            "body": (
                "IN WITNESS WHEREOF, the Indemnifier has signed and delivered this Indemnity Bond on the date first written above."
            ),
        },
    ],
}


# =============================================================================
# MODEL REGISTRY MAPPING
# =============================================================================
MODEL_TEMPLATES: dict[str, TemplateSpec] = {
    RENTAL_AGREEMENT_TAMIL_NADU_TEMPLATE["id"]: RENTAL_AGREEMENT_TAMIL_NADU_TEMPLATE,
    SALE_DEED_TEMPLATE["id"]: SALE_DEED_TEMPLATE,
    GENERAL_POWER_OF_ATTORNEY_TEMPLATE["id"]: GENERAL_POWER_OF_ATTORNEY_TEMPLATE,
    SPECIAL_POWER_OF_ATTORNEY_TEMPLATE["id"]: SPECIAL_POWER_OF_ATTORNEY_TEMPLATE,
    GIFT_DEED_TEMPLATE["id"]: GIFT_DEED_TEMPLATE,
    RELEASE_DEED_TEMPLATE["id"]: RELEASE_DEED_TEMPLATE,
    COMMERCIAL_LEASE_TEMPLATE["id"]: COMMERCIAL_LEASE_TEMPLATE,
    LEAVE_LICENSE_TEMPLATE["id"]: LEAVE_LICENSE_TEMPLATE,
    LOAN_AGREEMENT_TEMPLATE["id"]: LOAN_AGREEMENT_TEMPLATE,
    RTI_APPLICATION_TEMPLATE["id"]: RTI_APPLICATION_TEMPLATE,
    LEGAL_AID_APPLICATION_TEMPLATE["id"]: LEGAL_AID_APPLICATION_TEMPLATE,
    PAYMENT_DEMAND_NOTICE_TEMPLATE["id"]: PAYMENT_DEMAND_NOTICE_TEMPLATE,
    EVICTION_NOTICE_TEMPLATE["id"]: EVICTION_NOTICE_TEMPLATE,
    FOUNDER_AGREEMENT_TEMPLATE["id"]: FOUNDER_AGREEMENT_TEMPLATE,
    NAME_CHANGE_AFFIDAVIT_TEMPLATE["id"]: NAME_CHANGE_AFFIDAVIT_TEMPLATE,
    INDEMNITY_BOND_TEMPLATE["id"]: INDEMNITY_BOND_TEMPLATE,
}

