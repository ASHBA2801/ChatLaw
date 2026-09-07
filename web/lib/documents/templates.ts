import { DISPUTE_OPTIONS, INDIA_REGIONS, PARTY_TYPE_OPTIONS } from "./constants";
import { EXTRA_TEMPLATES } from "./extraTemplates";
import { MODEL_TEMPLATES } from "./modelTemplates";
import type { FieldSpec, TemplateSpec } from "./types";

const REGION_OPTIONS = INDIA_REGIONS.map((region) => ({ value: region, label: region }));

function field(
  id: string,
  label: string,
  placeholderLabel: string,
  type: FieldSpec["type"],
  requirement: FieldSpec["requirement"],
  step: string,
  extra: Partial<FieldSpec> = {},
): FieldSpec {
  return { id, label, placeholderLabel, type, requirement, step, ...extra };
}

function jurisdictionFields(step = "jurisdiction"): FieldSpec[] {
  return [
    field("jurisdiction_country", "Jurisdiction", "JURISDICTION", "select", "required", step, {
      help: "The generated draft retains this jurisdiction. Laws vary by place.",
      options: [{ value: "IN", label: "India" }],
    }),
    field("jurisdiction_region", "State / Union Territory", "STATE OR UNION TERRITORY", "select", "required", step, {
      help: "Required because contract and property rules can vary within India.",
      options: REGION_OPTIONS,
    }),
    field("governing_law_seat", "Seat / place for disputes", "DISPUTE SEAT", "text", "recommended", step, {
      help: "City or district where disputes are to be heard, if the parties have agreed one.",
    }),
  ];
}

export const NDA_TEMPLATE: TemplateSpec = {
  id: "nda",
  category: "agreement",
  title: "Non-Disclosure Agreement",
  description: "A mutual or one-way confidentiality agreement for sharing information in India.",
  documentType: "Non-Disclosure Agreement",
  jurisdictionCountry: "IN",
  parties: [
    { id: "disclosing", role: "Disclosing Party", nameField: "disclosing_party_name", typeField: "disclosing_party_type", addressField: "disclosing_party_address" },
    { id: "receiving", role: "Receiving Party", nameField: "receiving_party_name", typeField: "receiving_party_type", addressField: "receiving_party_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the agreement you need.", fieldIds: ["document_title"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Choose where this agreement is intended to operate.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Parties", description: "Identify who is disclosing and receiving information.", fieldIds: ["disclosing_party_name", "disclosing_party_type", "disclosing_party_address", "receiving_party_name", "receiving_party_type", "receiving_party_address", "mutual"] },
    { id: "purpose", title: "Purpose", description: "State why confidential information will be shared.", fieldIds: ["purpose", "effective_date"] },
    { id: "duration", title: "Duration", description: "How long confidentiality lasts.", fieldIds: ["duration_months"] },
    { id: "conditions", title: "Special conditions", description: "Optional protections the parties want in writing.", fieldIds: ["exclude_public_info", "include_non_solicit", "dispute_resolution", "special_conditions"] },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type", { help: "Leave blank to use the standard title." }),
    ...jurisdictionFields(),
    field("disclosing_party_name", "Disclosing party name", "DISCLOSING PARTY NAME", "text", "required", "parties"),
    field("disclosing_party_type", "Disclosing party type", "DISCLOSING PARTY TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("disclosing_party_address", "Disclosing party address", "DISCLOSING PARTY ADDRESS", "textarea", "required", "parties"),
    field("receiving_party_name", "Receiving party name", "RECEIVING PARTY NAME", "text", "required", "parties"),
    field("receiving_party_type", "Receiving party type", "RECEIVING PARTY TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("receiving_party_address", "Receiving party address", "RECEIVING PARTY ADDRESS", "textarea", "required", "parties"),
    field("mutual", "Mutual confidentiality", "MUTUAL CONFIDENTIALITY", "checkbox", "optional", "parties", { help: "If selected, both parties protect information they receive from each other." }),
    field("purpose", "Purpose of disclosure", "PURPOSE", "textarea", "required", "purpose", { help: "Describe the project or discussion. Do not invent a purpose if it is not yet agreed." }),
    field("effective_date", "Effective date", "EFFECTIVE DATE", "date", "required", "purpose"),
    field("duration_months", "Confidentiality period (months)", "CONFIDENTIALITY PERIOD", "number", "required", "duration", { help: "Number of months after the last disclosure.", min: 1, max: 120 }),
    field("exclude_public_info", "Exclude public and independently developed information", "PUBLIC INFORMATION EXCLUSION", "checkbox", "recommended", "conditions"),
    field("include_non_solicit", "Include a non-solicitation restriction", "NON-SOLICITATION", "checkbox", "optional", "conditions"),
    field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions", { options: DISPUTE_OPTIONS }),
    field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions", { help: "Only include terms the parties have actually discussed." }),
  ],
  clauses: [
    { id: "title", title: "Title", required: true },
    { id: "parties", title: "Parties", required: true },
    { id: "purpose", title: "Purpose", required: true },
    { id: "definitions", title: "Confidential Information", required: true },
    { id: "obligations", title: "Confidentiality obligations", required: true },
    { id: "exclusions", title: "Exclusions", required: false, condition: { truthy: "exclude_public_info" } },
    { id: "term", title: "Term", required: true },
    { id: "return", title: "Return and destruction", required: true },
    { id: "non_solicit", title: "Non-solicitation", required: false, condition: { truthy: "include_non_solicit" } },
    { id: "no_license", title: "No licence", required: true },
    { id: "remedies", title: "Remedies", required: true },
    { id: "dispute_resolution", title: "Dispute resolution", required: true },
    { id: "governing_law", title: "Governing law and jurisdiction", required: true, needsLegalContext: true },
    { id: "notices", title: "Notices", required: true },
    { id: "amendments", title: "Amendments", required: true },
    { id: "severability", title: "Severability", required: true },
    { id: "entire_agreement", title: "Entire agreement", required: true },
    { id: "signatures", title: "Signatures", required: true, includeSignature: true },
  ],
};

export const SERVICE_AGREEMENT_TEMPLATE: TemplateSpec = {
  id: "service_agreement",
  category: "agreement",
  title: "Service Agreement",
  description: "A services contract between a client and a service provider in India.",
  documentType: "Service Agreement",
  jurisdictionCountry: "IN",
  parties: [
    { id: "client", role: "Client", nameField: "client_name", typeField: "client_type", addressField: "client_address" },
    { id: "provider", role: "Service Provider", nameField: "provider_name", typeField: "provider_type", addressField: "provider_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the agreement you need.", fieldIds: ["document_title"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Choose where this agreement is intended to operate.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Parties", description: "Identify the client and the service provider.", fieldIds: ["client_name", "client_type", "client_address", "provider_name", "provider_type", "provider_address"] },
    { id: "purpose", title: "Services", description: "Describe the work to be performed.", fieldIds: ["purpose", "deliverables", "effective_date"] },
    { id: "financial", title: "Financial terms", description: "Record fees only if they have been agreed.", fieldIds: ["fee_amount", "fee_currency", "payment_schedule"] },
    { id: "duration", title: "Duration and ending", description: "How long the services last and how they may end.", fieldIds: ["end_date", "termination_notice_days"] },
    { id: "conditions", title: "Rights and conditions", description: "Confidentiality, disputes, and extra terms.", fieldIds: ["include_confidentiality", "dispute_resolution", "special_conditions"] },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
    ...jurisdictionFields(),
    field("client_name", "Client name", "CLIENT NAME", "text", "required", "parties"),
    field("client_type", "Client type", "CLIENT TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("client_address", "Client address", "CLIENT ADDRESS", "textarea", "required", "parties"),
    field("provider_name", "Service provider name", "SERVICE PROVIDER NAME", "text", "required", "parties"),
    field("provider_type", "Service provider type", "SERVICE PROVIDER TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("provider_address", "Service provider address", "SERVICE PROVIDER ADDRESS", "textarea", "required", "parties"),
    field("purpose", "Description of services", "SERVICES DESCRIPTION", "textarea", "required", "purpose"),
    field("deliverables", "Deliverables", "DELIVERABLES", "textarea", "recommended", "purpose"),
    field("effective_date", "Start date", "START DATE", "date", "required", "purpose"),
    field("fee_amount", "Fee amount", "FEE AMOUNT", "currency", "recommended", "financial", { help: "Leave blank if fees are still to be agreed.", min: 0 }),
    field("fee_currency", "Currency", "CURRENCY", "select", "optional", "financial", { options: [{ value: "INR", label: "INR" }, { value: "USD", label: "USD" }, { value: "EUR", label: "EUR" }] }),
    field("payment_schedule", "Payment schedule", "PAYMENT SCHEDULE", "textarea", "optional", "financial"),
    field("end_date", "End date", "END DATE", "date", "recommended", "duration"),
    field("termination_notice_days", "Termination notice (days)", "TERMINATION NOTICE DAYS", "number", "optional", "duration", { min: 1, max: 365 }),
    field("include_confidentiality", "Include confidentiality obligations", "CONFIDENTIALITY", "checkbox", "recommended", "conditions"),
    field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions", { options: DISPUTE_OPTIONS }),
    field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true },
    { id: "parties", title: "Parties", required: true },
    { id: "services", title: "Services", required: true },
    { id: "client_obligations", title: "Client obligations", required: true },
    { id: "provider_obligations", title: "Service Provider obligations", required: true },
    { id: "fees", title: "Fees and payment", required: false, condition: { has_value: "fee_amount" } },
    { id: "term", title: "Term", required: true },
    { id: "termination", title: "Termination", required: false, condition: { has_value: "termination_notice_days" } },
    { id: "confidentiality", title: "Confidentiality", required: false, condition: { truthy: "include_confidentiality" } },
    { id: "intellectual_property", title: "Intellectual property", required: true },
    { id: "indemnification", title: "Indemnity and liability", required: true },
    { id: "force_majeure", title: "Force majeure", required: true },
    { id: "dispute_resolution", title: "Dispute resolution", required: true },
    { id: "governing_law", title: "Governing law", required: true, needsLegalContext: true },
    { id: "notices", title: "Notices", required: true },
    { id: "miscellaneous", title: "General", required: true },
    { id: "signatures", title: "Signatures", required: true, includeSignature: true },
  ],
};

export const RENT_LEASE_TEMPLATE: TemplateSpec = {
  id: "rent_lease",
  category: "agreement",
  title: "Rent / Lease Agreement",
  description: "A residential or commercial lease draft for property in India.",
  documentType: "Rent / Lease Agreement",
  jurisdictionCountry: "IN",
  parties: [
    { id: "landlord", role: "Landlord / Lessor", nameField: "landlord_name", typeField: "landlord_type", addressField: "landlord_address" },
    { id: "tenant", role: "Tenant / Lessee", nameField: "tenant_name", typeField: "tenant_type", addressField: "tenant_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the agreement you need.", fieldIds: ["document_title", "property_use"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "The property's location governs many lease rules.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Parties", description: "Identify the landlord and the tenant.", fieldIds: ["landlord_name", "landlord_type", "landlord_address", "tenant_name", "tenant_type", "tenant_address"] },
    { id: "purpose", title: "Property", description: "Describe the premises being let.", fieldIds: ["property_address", "property_description", "effective_date"] },
    { id: "financial", title: "Rent and deposit", description: "Record amounts only if they have been agreed.", fieldIds: ["rent_amount", "rent_currency", "rent_frequency", "deposit_amount"] },
    { id: "duration", title: "Term", description: "When the tenancy starts and ends.", fieldIds: ["end_date", "termination_notice_days"] },
    { id: "conditions", title: "Obligations and conditions", description: "Use, maintenance, and extra terms.", fieldIds: ["maintenance_responsibility", "dispute_resolution", "special_conditions"] },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
    field("property_use", "Intended use", "PROPERTY USE", "select", "required", "type", { options: [{ value: "residential", label: "Residential" }, { value: "commercial", label: "Commercial" }] }),
    ...jurisdictionFields(),
    field("landlord_name", "Landlord name", "LANDLORD NAME", "text", "required", "parties"),
    field("landlord_type", "Landlord type", "LANDLORD TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("landlord_address", "Landlord address", "LANDLORD ADDRESS", "textarea", "required", "parties"),
    field("tenant_name", "Tenant name", "TENANT NAME", "text", "required", "parties"),
    field("tenant_type", "Tenant type", "TENANT TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("tenant_address", "Tenant address for notices", "TENANT ADDRESS", "textarea", "required", "parties"),
    field("property_address", "Property address", "PROPERTY ADDRESS", "textarea", "required", "purpose"),
    field("property_description", "Description of premises", "PROPERTY DESCRIPTION", "textarea", "recommended", "purpose"),
    field("effective_date", "Lease start date", "LEASE START DATE", "date", "required", "purpose"),
    field("rent_amount", "Rent amount", "RENT AMOUNT", "currency", "recommended", "financial", { help: "Leave blank if rent is still to be agreed.", min: 0 }),
    field("rent_currency", "Currency", "CURRENCY", "select", "optional", "financial", { options: [{ value: "INR", label: "INR" }] }),
    field("rent_frequency", "Rent frequency", "RENT FREQUENCY", "select", "optional", "financial", { options: [{ value: "monthly", label: "Monthly" }, { value: "quarterly", label: "Quarterly" }, { value: "yearly", label: "Yearly" }] }),
    field("deposit_amount", "Security deposit", "SECURITY DEPOSIT", "currency", "optional", "financial", { min: 0 }),
    field("end_date", "Lease end date", "LEASE END DATE", "date", "required", "duration"),
    field("termination_notice_days", "Notice to end (days)", "TERMINATION NOTICE DAYS", "number", "recommended", "duration", { min: 1, max: 365 }),
    field("maintenance_responsibility", "Routine maintenance", "MAINTENANCE RESPONSIBILITY", "select", "recommended", "conditions", { options: [{ value: "tenant", label: "Tenant for routine upkeep" }, { value: "landlord", label: "Landlord for routine upkeep" }, { value: "shared", label: "Shared as described in special conditions" }] }),
    field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions", { options: DISPUTE_OPTIONS }),
    field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true },
    { id: "parties", title: "Parties", required: true },
    { id: "property", title: "Premises", required: true },
    { id: "term", title: "Term", required: true },
    { id: "rent", title: "Rent", required: false, condition: { has_value: "rent_amount" } },
    { id: "deposit", title: "Security deposit", required: false, condition: { has_value: "deposit_amount" } },
    { id: "tenant_obligations", title: "Tenant obligations", required: true },
    { id: "landlord_obligations", title: "Landlord obligations", required: true },
    { id: "maintenance", title: "Maintenance", required: true },
    { id: "termination", title: "Ending the tenancy", required: false, condition: { has_value: "termination_notice_days" } },
    { id: "dispute_resolution", title: "Dispute resolution", required: true },
    { id: "governing_law", title: "Governing law", required: true, needsLegalContext: true },
    { id: "notices", title: "Notices", required: true },
    { id: "miscellaneous", title: "General", required: true },
    { id: "signatures", title: "Signatures", required: true, includeSignature: true },
  ],
};

export const AFFIDAVIT_TEMPLATE: TemplateSpec = {
  id: "affidavit",
  category: "affidavit",
  title: "Affidavit",
  description: "A sworn statement of facts for use in India. Notary or oath formalities are not completed by this draft.",
  documentType: "Affidavit",
  jurisdictionCountry: "IN",
  parties: [
    { id: "deponent", role: "Deponent", nameField: "deponent_name", typeField: "deponent_type", addressField: "deponent_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the affidavit you need.", fieldIds: ["document_title"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Where this affidavit is intended to be used.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Deponent", description: "Identify the person who will swear the facts.", fieldIds: ["deponent_name", "deponent_type", "deponent_address", "deponent_age", "deponent_occupation"] },
    { id: "purpose", title: "Subject and facts", description: "State why the affidavit is needed and the facts to be sworn.", fieldIds: ["purpose", "facts", "effective_date", "place_of_swearing"] },
    { id: "conditions", title: "Extra details", description: "Optional supporting information.", fieldIds: ["special_conditions"] },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type", { help: "Leave blank to use the standard title." }),
    ...jurisdictionFields(),
    field("deponent_name", "Deponent name", "DEPONENT NAME", "text", "required", "parties"),
    field("deponent_type", "Deponent type", "DEPONENT TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("deponent_address", "Deponent address", "DEPONENT ADDRESS", "textarea", "required", "parties"),
    field("deponent_age", "Deponent age (years)", "DEPONENT AGE", "number", "recommended", "parties", { min: 18, max: 120 }),
    field("deponent_occupation", "Occupation", "DEPONENT OCCUPATION", "text", "optional", "parties"),
    field("purpose", "Purpose of affidavit", "PURPOSE", "textarea", "required", "purpose", { help: "State the proceeding or purpose. Do not invent a purpose." }),
    field("facts", "Facts to be sworn", "FACTS", "textarea", "required", "purpose", { help: "List only facts the deponent can personally affirm." }),
    field("effective_date", "Date of affidavit", "DATE OF AFFIDAVIT", "date", "required", "purpose"),
    field("place_of_swearing", "Place of swearing", "PLACE OF SWEARING", "text", "required", "purpose"),
    field("special_conditions", "Additional particulars", "ADDITIONAL PARTICULARS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true },
    { id: "parties", title: "Deponent", required: true },
    { id: "purpose", title: "Purpose", required: true },
    { id: "facts", title: "Facts", required: true },
    { id: "verification", title: "Verification", required: true },
    { id: "governing_law", title: "Jurisdiction note", required: true, needsLegalContext: true },
    { id: "signatures", title: "Signatures", required: true, includeSignature: true },
  ],
};

export const LEGAL_NOTICE_TEMPLATE: TemplateSpec = {
  id: "legal_notice",
  category: "notice",
  title: "Legal Notice",
  description: "A formal notice of demand or grievance under Indian practice. Sending and service formalities are not completed by this draft.",
  documentType: "Legal Notice",
  jurisdictionCountry: "IN",
  parties: [
    { id: "sender", role: "Sender", nameField: "sender_name", typeField: "sender_type", addressField: "sender_address" },
    { id: "recipient", role: "Recipient", nameField: "recipient_name", typeField: "recipient_type", addressField: "recipient_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the notice you need.", fieldIds: ["document_title"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Where the dispute or demand arises.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Parties", description: "Identify who is sending and receiving the notice.", fieldIds: ["sender_name", "sender_type", "sender_address", "recipient_name", "recipient_type", "recipient_address"] },
    { id: "purpose", title: "Subject and facts", description: "Describe the grievance and background.", fieldIds: ["purpose", "facts", "effective_date"] },
    { id: "demand", title: "Demand", description: "State what is demanded and by when.", fieldIds: ["relief_sought", "compliance_days"] },
    { id: "conditions", title: "Extra terms", description: "Optional additional particulars.", fieldIds: ["special_conditions"] },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
    ...jurisdictionFields(),
    field("sender_name", "Sender name", "SENDER NAME", "text", "required", "parties"),
    field("sender_type", "Sender type", "SENDER TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("sender_address", "Sender address", "SENDER ADDRESS", "textarea", "required", "parties"),
    field("recipient_name", "Recipient name", "RECIPIENT NAME", "text", "required", "parties"),
    field("recipient_type", "Recipient type", "RECIPIENT TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("recipient_address", "Recipient address", "RECIPIENT ADDRESS", "textarea", "required", "parties"),
    field("purpose", "Subject of notice", "SUBJECT", "textarea", "required", "purpose"),
    field("facts", "Background facts", "FACTS", "textarea", "required", "purpose"),
    field("effective_date", "Date of notice", "DATE OF NOTICE", "date", "required", "purpose"),
    field("relief_sought", "Demand / relief sought", "RELIEF SOUGHT", "textarea", "required", "demand"),
    field("compliance_days", "Days to comply", "COMPLIANCE DAYS", "number", "recommended", "demand", { min: 1, max: 365, help: "Leave blank if no fixed period is agreed." }),
    field("special_conditions", "Additional particulars", "ADDITIONAL PARTICULARS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true },
    { id: "parties", title: "Parties", required: true },
    { id: "subject", title: "Subject", required: true },
    { id: "facts", title: "Facts", required: true },
    { id: "demand", title: "Demand", required: true },
    { id: "consequences", title: "Consequences of non-compliance", required: false, condition: { has_value: "compliance_days" } },
    { id: "governing_law", title: "Jurisdiction note", required: true, needsLegalContext: true },
    { id: "signatures", title: "Signatures", required: true, includeSignature: true },
  ],
};

export const AUTHORIZATION_LETTER_TEMPLATE: TemplateSpec = {
  id: "authorization_letter",
  category: "affidavit",
  title: "Authorization Letter",
  description: "A letter authorizing another person to act on the principal's behalf in India for a stated purpose.",
  documentType: "Authorization Letter",
  jurisdictionCountry: "IN",
  parties: [
    { id: "principal", role: "Principal", nameField: "principal_name", typeField: "principal_type", addressField: "principal_address" },
    { id: "authorized", role: "Authorized Person", nameField: "authorized_name", typeField: "authorized_type", addressField: "authorized_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the authorization letter you need.", fieldIds: ["document_title"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Where the authorization is intended to operate.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Parties", description: "Identify the principal and the authorized person.", fieldIds: ["principal_name", "principal_type", "principal_address", "authorized_name", "authorized_type", "authorized_address"] },
    { id: "purpose", title: "Authority", description: "Describe what the authorized person may do.", fieldIds: ["purpose", "scope_of_authority", "effective_date", "end_date"] },
    { id: "conditions", title: "Limits and conditions", description: "Optional limits and extra terms.", fieldIds: ["special_conditions"] },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
    ...jurisdictionFields(),
    field("principal_name", "Principal name", "PRINCIPAL NAME", "text", "required", "parties"),
    field("principal_type", "Principal type", "PRINCIPAL TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("principal_address", "Principal address", "PRINCIPAL ADDRESS", "textarea", "required", "parties"),
    field("authorized_name", "Authorized person name", "AUTHORIZED PERSON NAME", "text", "required", "parties"),
    field("authorized_type", "Authorized person type", "AUTHORIZED PERSON TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("authorized_address", "Authorized person address", "AUTHORIZED PERSON ADDRESS", "textarea", "required", "parties"),
    field("purpose", "Purpose of authorization", "PURPOSE", "textarea", "required", "purpose"),
    field("scope_of_authority", "Scope of authority", "SCOPE OF AUTHORITY", "textarea", "required", "purpose", { help: "List only acts the principal intends to authorize." }),
    field("effective_date", "Effective date", "EFFECTIVE DATE", "date", "required", "purpose"),
    field("end_date", "End date", "END DATE", "date", "recommended", "purpose"),
    field("special_conditions", "Limits or other conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true },
    { id: "parties", title: "Parties", required: true },
    { id: "purpose", title: "Purpose", required: true },
    { id: "authority", title: "Authority granted", required: true },
    { id: "term", title: "Term", required: true },
    { id: "limits", title: "Limits", required: false, condition: { has_value: "special_conditions" } },
    { id: "governing_law", title: "Jurisdiction note", required: true, needsLegalContext: true },
    { id: "signatures", title: "Signatures", required: true, includeSignature: true },
  ],
};

export const CONSUMER_COMPLAINT_TEMPLATE: TemplateSpec = {
  id: "consumer_complaint",
  category: "complaint",
  title: "Consumer Complaint",
  description: "A consumer dispute complaint draft for India. Forum filing and fee formalities are not completed by this draft.",
  documentType: "Consumer Complaint",
  jurisdictionCountry: "IN",
  parties: [
    { id: "complainant", role: "Complainant", nameField: "complainant_name", typeField: "complainant_type", addressField: "complainant_address" },
    { id: "opposite", role: "Opposite Party", nameField: "opposite_party_name", typeField: "opposite_party_type", addressField: "opposite_party_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the consumer complaint you need.", fieldIds: ["document_title"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Where the transaction or dispute arose.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Parties", description: "Identify the complainant and the opposite party.", fieldIds: ["complainant_name", "complainant_type", "complainant_address", "opposite_party_name", "opposite_party_type", "opposite_party_address"] },
    { id: "purpose", title: "Transaction and grievance", description: "Describe the goods or services and what went wrong.", fieldIds: ["product_or_service", "transaction_date", "purpose", "facts", "effective_date"] },
    { id: "demand", title: "Relief", description: "State the relief sought and any amount claimed.", fieldIds: ["relief_sought", "claim_amount", "claim_currency"] },
    { id: "conditions", title: "Extra details", description: "Optional supporting information.", fieldIds: ["special_conditions"] },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
    ...jurisdictionFields(),
    field("complainant_name", "Complainant name", "COMPLAINANT NAME", "text", "required", "parties"),
    field("complainant_type", "Complainant type", "COMPLAINANT TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("complainant_address", "Complainant address", "COMPLAINANT ADDRESS", "textarea", "required", "parties"),
    field("opposite_party_name", "Opposite party name", "OPPOSITE PARTY NAME", "text", "required", "parties"),
    field("opposite_party_type", "Opposite party type", "OPPOSITE PARTY TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("opposite_party_address", "Opposite party address", "OPPOSITE PARTY ADDRESS", "textarea", "required", "parties"),
    field("product_or_service", "Goods or services", "PRODUCT OR SERVICE", "textarea", "required", "purpose"),
    field("transaction_date", "Transaction / purchase date", "TRANSACTION DATE", "date", "recommended", "purpose"),
    field("purpose", "Nature of complaint", "NATURE OF COMPLAINT", "textarea", "required", "purpose"),
    field("facts", "Detailed facts", "FACTS", "textarea", "required", "purpose"),
    field("effective_date", "Date of complaint", "DATE OF COMPLAINT", "date", "required", "purpose"),
    field("relief_sought", "Relief sought", "RELIEF SOUGHT", "textarea", "required", "demand"),
    field("claim_amount", "Amount claimed", "AMOUNT CLAIMED", "currency", "optional", "demand", { min: 0, help: "Leave blank if no specific amount is claimed." }),
    field("claim_currency", "Currency", "CURRENCY", "select", "optional", "demand", { options: [{ value: "INR", label: "INR" }] }),
    field("special_conditions", "Additional particulars", "ADDITIONAL PARTICULARS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true },
    { id: "parties", title: "Parties", required: true },
    { id: "transaction", title: "Transaction", required: true },
    { id: "facts", title: "Facts", required: true },
    { id: "cause", title: "Cause of action", required: true },
    { id: "relief", title: "Relief sought", required: true },
    { id: "claim_amount", title: "Amount claimed", required: false, condition: { has_value: "claim_amount" } },
    { id: "governing_law", title: "Jurisdiction note", required: true, needsLegalContext: true },
    { id: "signatures", title: "Signatures", required: true, includeSignature: true },
  ],
};

export const COMPLAINT_TEMPLATE: TemplateSpec = {
  id: "complaint",
  category: "complaint",
  title: "General Complaint / Police Complaint",
  description: "A draft complaint or police complaint narrative for India. Filing with police or any authority is not completed by this draft.",
  documentType: "Complaint",
  jurisdictionCountry: "IN",
  parties: [
    { id: "complainant", role: "Complainant", nameField: "complainant_name", typeField: "complainant_type", addressField: "complainant_address" },
    { id: "accused", role: "Accused / Opposite Party", nameField: "accused_name", typeField: "accused_type", addressField: "accused_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the complaint draft you need.", fieldIds: ["document_title", "complaint_kind"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Where the incident occurred or will be reported.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Parties", description: "Identify the complainant and the accused or opposite party.", fieldIds: ["complainant_name", "complainant_type", "complainant_address", "accused_name", "accused_type", "accused_address"] },
    { id: "purpose", title: "Incident", description: "Describe what happened and where it should be reported.", fieldIds: ["purpose", "facts", "incident_date", "incident_place", "police_station", "effective_date"] },
    { id: "demand", title: "Request", description: "State the action requested.", fieldIds: ["relief_sought"] },
    { id: "conditions", title: "Extra details", description: "Optional supporting information.", fieldIds: ["special_conditions"] },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
    field("complaint_kind", "Complaint kind", "COMPLAINT KIND", "select", "required", "type", {
      options: [
        { value: "police", label: "Police complaint / FIR narrative" },
        { value: "general", label: "General complaint to an authority" },
      ],
    }),
    ...jurisdictionFields(),
    field("complainant_name", "Complainant name", "COMPLAINANT NAME", "text", "required", "parties"),
    field("complainant_type", "Complainant type", "COMPLAINANT TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("complainant_address", "Complainant address", "COMPLAINANT ADDRESS", "textarea", "required", "parties"),
    field("accused_name", "Accused / opposite party name", "ACCUSED NAME", "text", "required", "parties"),
    field("accused_type", "Accused / opposite party type", "ACCUSED TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("accused_address", "Accused / opposite party address", "ACCUSED ADDRESS", "textarea", "recommended", "parties"),
    field("purpose", "Subject of complaint", "SUBJECT", "textarea", "required", "purpose"),
    field("facts", "Detailed facts of the incident", "FACTS", "textarea", "required", "purpose"),
    field("incident_date", "Date of incident", "INCIDENT DATE", "date", "required", "purpose"),
    field("incident_place", "Place of incident", "INCIDENT PLACE", "text", "required", "purpose"),
    field("police_station", "Police station / authority", "POLICE STATION OR AUTHORITY", "text", "recommended", "purpose"),
    field("effective_date", "Date of complaint", "DATE OF COMPLAINT", "date", "required", "purpose"),
    field("relief_sought", "Action requested", "ACTION REQUESTED", "textarea", "required", "demand"),
    field("special_conditions", "Additional particulars", "ADDITIONAL PARTICULARS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true },
    { id: "parties", title: "Parties", required: true },
    { id: "subject", title: "Subject", required: true },
    { id: "facts", title: "Facts", required: true },
    { id: "request", title: "Request", required: true },
    { id: "governing_law", title: "Jurisdiction note", required: true, needsLegalContext: true },
    { id: "signatures", title: "Signatures", required: true, includeSignature: true },
  ],
};

export const TEMPLATES: Record<string, TemplateSpec> = {
  [NDA_TEMPLATE.id]: NDA_TEMPLATE,
  [SERVICE_AGREEMENT_TEMPLATE.id]: SERVICE_AGREEMENT_TEMPLATE,
  [RENT_LEASE_TEMPLATE.id]: RENT_LEASE_TEMPLATE,
  [AFFIDAVIT_TEMPLATE.id]: AFFIDAVIT_TEMPLATE,
  [LEGAL_NOTICE_TEMPLATE.id]: LEGAL_NOTICE_TEMPLATE,
  [AUTHORIZATION_LETTER_TEMPLATE.id]: AUTHORIZATION_LETTER_TEMPLATE,
  [CONSUMER_COMPLAINT_TEMPLATE.id]: CONSUMER_COMPLAINT_TEMPLATE,
  [COMPLAINT_TEMPLATE.id]: COMPLAINT_TEMPLATE,
  ...EXTRA_TEMPLATES,
  ...MODEL_TEMPLATES,
};

export function listTemplates(): TemplateSpec[] {
  return Object.values(TEMPLATES);
}

export function getTemplate(templateId: string): TemplateSpec {
  const template = TEMPLATES[templateId];
  if (!template) {
    throw new Error(`Unknown document template: ${templateId}`);
  }
  return template;
}

export function defaultValues(template: TemplateSpec): Record<string, string | number | boolean | ""> {
  const values: Record<string, string | number | boolean | ""> = {
    jurisdiction_country: "IN",
  };
  for (const item of template.fields) {
    if (item.type === "checkbox") values[item.id] = false;
    else if (!(item.id in values)) values[item.id] = "";
  }
  return values;
}
