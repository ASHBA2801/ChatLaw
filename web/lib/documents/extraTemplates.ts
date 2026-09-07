import { DISPUTE_OPTIONS, INDIA_REGIONS, PARTY_TYPE_OPTIONS } from "./constants";
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

export const EMPLOYMENT_AGREEMENT_TEMPLATE: TemplateSpec = {
  id: "employment_agreement",
  category: "agreement",
  title: "Employment Agreement",
  description: "An employment contract draft between an employer and an employee in India.",
  documentType: "Employment Agreement",
  jurisdictionCountry: "IN",
  parties: [
    { id: "employer", role: "Employer", nameField: "employer_name", typeField: "employer_type", addressField: "employer_address" },
    { id: "employee", role: "Employee", nameField: "employee_name", typeField: "employee_type", addressField: "employee_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the agreement you need.", fieldIds: ["document_title"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Where employment is intended to operate.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Parties", description: "Identify the employer and the employee.", fieldIds: ["employer_name", "employer_type", "employer_address", "employee_name", "employee_type", "employee_address"] },
    { id: "role", title: "Role and start", description: "Job title, duties, and start date.", fieldIds: ["job_title", "duties", "place_of_work", "effective_date"] },
    { id: "financial", title: "Compensation", description: "Record pay only if agreed.", fieldIds: ["salary_amount", "salary_currency", "salary_frequency", "probation_months"] },
    { id: "duration", title: "Hours and ending", description: "Working hours and how employment may end.", fieldIds: ["working_hours", "termination_notice_days", "include_confidentiality"] },
    { id: "conditions", title: "Other terms", description: "Disputes and extra agreed terms.", fieldIds: ["dispute_resolution", "special_conditions"] },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
    ...jurisdictionFields(),
    field("employer_name", "Employer name", "EMPLOYER NAME", "text", "required", "parties"),
    field("employer_type", "Employer type", "EMPLOYER TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("employer_address", "Employer address", "EMPLOYER ADDRESS", "textarea", "required", "parties"),
    field("employee_name", "Employee name", "EMPLOYEE NAME", "text", "required", "parties"),
    field("employee_type", "Employee type", "EMPLOYEE TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("employee_address", "Employee address", "EMPLOYEE ADDRESS", "textarea", "required", "parties"),
    field("job_title", "Job title", "JOB TITLE", "text", "required", "role"),
    field("duties", "Duties / role description", "DUTIES", "textarea", "required", "role"),
    field("place_of_work", "Place of work", "PLACE OF WORK", "text", "recommended", "role"),
    field("effective_date", "Start date", "START DATE", "date", "required", "role"),
    field("salary_amount", "Salary / wages", "SALARY AMOUNT", "currency", "recommended", "financial", {
      help: "Leave blank if pay is still to be agreed.",
      min: 0,
    }),
    field("salary_currency", "Currency", "CURRENCY", "select", "optional", "financial", {
      options: [{ value: "INR", label: "INR" }],
    }),
    field("salary_frequency", "Pay frequency", "PAY FREQUENCY", "select", "optional", "financial", {
      options: [
        { value: "monthly", label: "Monthly" },
        { value: "fortnightly", label: "Fortnightly" },
        { value: "weekly", label: "Weekly" },
      ],
    }),
    field("probation_months", "Probation (months)", "PROBATION MONTHS", "number", "optional", "financial", {
      min: 0,
      max: 24,
    }),
    field("working_hours", "Working hours", "WORKING HOURS", "textarea", "recommended", "duration"),
    field("termination_notice_days", "Notice period (days)", "NOTICE DAYS", "number", "recommended", "duration", {
      min: 1,
      max: 365,
    }),
    field("include_confidentiality", "Include confidentiality", "CONFIDENTIALITY", "checkbox", "recommended", "duration"),
    field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions", {
      options: DISPUTE_OPTIONS,
    }),
    field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true, provisionClass: "required" },
    { id: "parties", title: "Parties", required: true, provisionClass: "required" },
    { id: "recitals", title: "Background", required: true, provisionClass: "recommended" },
    { id: "definitions", title: "Definitions", required: true, provisionClass: "recommended" },
    { id: "role", title: "Position and duties", required: true, provisionClass: "required" },
    { id: "start", title: "Commencement", required: true, provisionClass: "required" },
    { id: "compensation", title: "Remuneration", required: false, provisionClass: "user_specific", condition: { has_value: "salary_amount" } },
    { id: "hours", title: "Working hours", required: true, provisionClass: "recommended" },
    { id: "obligations", title: "Employee obligations", required: true, provisionClass: "required" },
    { id: "employer_obligations", title: "Employer obligations", required: true, provisionClass: "required" },
    { id: "confidentiality", title: "Confidentiality", required: false, provisionClass: "recommended", condition: { truthy: "include_confidentiality" } },
    { id: "termination", title: "Termination", required: false, provisionClass: "recommended", condition: { has_value: "termination_notice_days" } },
    { id: "dispute_resolution", title: "Dispute resolution", required: true, provisionClass: "required" },
    { id: "governing_law", title: "Governing law", required: true, provisionClass: "required", needsLegalContext: true },
    { id: "miscellaneous", title: "General", required: true, provisionClass: "user_specific" },
    { id: "signatures", title: "Signatures", required: true, provisionClass: "required", includeSignature: true },
  ],
};

export const PARTNERSHIP_AGREEMENT_TEMPLATE: TemplateSpec = {
  id: "partnership_agreement",
  category: "agreement",
  title: "Partnership Agreement",
  description: "A partnership deed draft for partners carrying on business together in India.",
  documentType: "Partnership Agreement",
  jurisdictionCountry: "IN",
  parties: [
    { id: "partner_a", role: "Partner A", nameField: "partner_a_name", typeField: "partner_a_type", addressField: "partner_a_address" },
    { id: "partner_b", role: "Partner B", nameField: "partner_b_name", typeField: "partner_b_type", addressField: "partner_b_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the agreement you need.", fieldIds: ["document_title", "firm_name"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Where the firm is intended to operate.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    {
      id: "parties",
      title: "Partners",
      description: "Identify the partners.",
      fieldIds: ["partner_a_name", "partner_a_type", "partner_a_address", "partner_b_name", "partner_b_type", "partner_b_address"],
    },
    { id: "business", title: "Business", description: "Describe the firm and business.", fieldIds: ["business_nature", "principal_place", "effective_date"] },
    {
      id: "financial",
      title: "Capital and profit",
      description: "Record contributions and sharing only if agreed.",
      fieldIds: ["capital_a", "capital_b", "profit_share_a", "profit_share_b", "capital_currency"],
    },
    {
      id: "duration",
      title: "Management and ending",
      description: "Management, banking, and dissolution notice.",
      fieldIds: ["management_rules", "termination_notice_days", "include_confidentiality"],
    },
    { id: "conditions", title: "Other terms", description: "Disputes and extra terms.", fieldIds: ["dispute_resolution", "special_conditions"] },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
    field("firm_name", "Firm name", "FIRM NAME", "text", "required", "type"),
    ...jurisdictionFields(),
    field("partner_a_name", "Partner A name", "PARTNER A NAME", "text", "required", "parties"),
    field("partner_a_type", "Partner A type", "PARTNER A TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("partner_a_address", "Partner A address", "PARTNER A ADDRESS", "textarea", "required", "parties"),
    field("partner_b_name", "Partner B name", "PARTNER B NAME", "text", "required", "parties"),
    field("partner_b_type", "Partner B type", "PARTNER B TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("partner_b_address", "Partner B address", "PARTNER B ADDRESS", "textarea", "required", "parties"),
    field("business_nature", "Nature of business", "NATURE OF BUSINESS", "textarea", "required", "business"),
    field("principal_place", "Principal place of business", "PRINCIPAL PLACE", "text", "required", "business"),
    field("effective_date", "Commencement date", "COMMENCEMENT DATE", "date", "required", "business"),
    field("capital_a", "Partner A capital contribution", "PARTNER A CAPITAL", "currency", "recommended", "financial", { min: 0 }),
    field("capital_b", "Partner B capital contribution", "PARTNER B CAPITAL", "currency", "recommended", "financial", { min: 0 }),
    field("capital_currency", "Currency", "CURRENCY", "select", "optional", "financial", {
      options: [{ value: "INR", label: "INR" }],
    }),
    field("profit_share_a", "Partner A profit share (%)", "PARTNER A PROFIT SHARE", "number", "recommended", "financial", {
      min: 0,
      max: 100,
    }),
    field("profit_share_b", "Partner B profit share (%)", "PARTNER B PROFIT SHARE", "number", "recommended", "financial", {
      min: 0,
      max: 100,
    }),
    field("management_rules", "Management / decision rules", "MANAGEMENT RULES", "textarea", "recommended", "duration"),
    field("termination_notice_days", "Notice to dissolve / retire (days)", "NOTICE DAYS", "number", "recommended", "duration", {
      min: 1,
      max: 365,
    }),
    field("include_confidentiality", "Include confidentiality", "CONFIDENTIALITY", "checkbox", "recommended", "duration"),
    field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions", {
      options: DISPUTE_OPTIONS,
    }),
    field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true, provisionClass: "required" },
    { id: "parties", title: "Parties", required: true, provisionClass: "required" },
    { id: "recitals", title: "Background", required: true, provisionClass: "recommended" },
    { id: "definitions", title: "Definitions", required: true, provisionClass: "recommended" },
    { id: "business", title: "Business and place", required: true, provisionClass: "required" },
    { id: "commencement", title: "Commencement", required: true, provisionClass: "required" },
    { id: "capital", title: "Capital", required: false, provisionClass: "user_specific", condition: { has_value: "capital_a" } },
    { id: "profit", title: "Profit and loss", required: false, provisionClass: "user_specific", condition: { has_value: "profit_share_a" } },
    { id: "management", title: "Management", required: true, provisionClass: "recommended" },
    { id: "obligations", title: "Partner obligations", required: true, provisionClass: "required" },
    { id: "confidentiality", title: "Confidentiality", required: false, provisionClass: "recommended", condition: { truthy: "include_confidentiality" } },
    { id: "termination", title: "Retirement and dissolution", required: false, provisionClass: "recommended", condition: { has_value: "termination_notice_days" } },
    { id: "dispute_resolution", title: "Dispute resolution", required: true, provisionClass: "required" },
    { id: "governing_law", title: "Governing law", required: true, provisionClass: "required", needsLegalContext: true },
    { id: "schedules", title: "Schedules", required: false, provisionClass: "user_specific", condition: { has_value: "special_conditions" } },
    { id: "signatures", title: "Signatures", required: true, provisionClass: "required", includeSignature: true },
  ],
};

export const SALE_AGREEMENT_TEMPLATE: TemplateSpec = {
  id: "sale_agreement",
  category: "agreement",
  title: "Sale Agreement",
  description: "A sale of goods or assets draft between a seller and a buyer in India.",
  documentType: "Sale Agreement",
  jurisdictionCountry: "IN",
  parties: [
    { id: "seller", role: "Seller", nameField: "seller_name", typeField: "seller_type", addressField: "seller_address" },
    { id: "buyer", role: "Buyer", nameField: "buyer_name", typeField: "buyer_type", addressField: "buyer_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the agreement you need.", fieldIds: ["document_title", "asset_type"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Where the sale is intended to operate.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Parties", description: "Identify the seller and the buyer.", fieldIds: ["seller_name", "seller_type", "seller_address", "buyer_name", "buyer_type", "buyer_address"] },
    { id: "goods", title: "Subject of sale", description: "Describe what is being sold.", fieldIds: ["goods_description", "delivery_place", "effective_date"] },
    { id: "financial", title: "Price and payment", description: "Record price only if agreed.", fieldIds: ["price_amount", "price_currency", "payment_schedule", "delivery_date"] },
    {
      id: "conditions",
      title: "Risk, warranties, ending",
      description: "Optional protections and disputes.",
      fieldIds: ["include_warranties", "termination_notice_days", "dispute_resolution", "special_conditions"],
    },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
    field("asset_type", "What is being sold", "ASSET TYPE", "select", "required", "type", {
      options: [
        { value: "goods", label: "Goods / movable property" },
        { value: "other_assets", label: "Other assets (describe in goods description)" },
      ],
    }),
    ...jurisdictionFields(),
    field("seller_name", "Seller name", "SELLER NAME", "text", "required", "parties"),
    field("seller_type", "Seller type", "SELLER TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("seller_address", "Seller address", "SELLER ADDRESS", "textarea", "required", "parties"),
    field("buyer_name", "Buyer name", "BUYER NAME", "text", "required", "parties"),
    field("buyer_type", "Buyer type", "BUYER TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("buyer_address", "Buyer address", "BUYER ADDRESS", "textarea", "required", "parties"),
    field("goods_description", "Description of goods / assets", "GOODS DESCRIPTION", "textarea", "required", "goods"),
    field("delivery_place", "Place of delivery", "DELIVERY PLACE", "text", "recommended", "goods"),
    field("effective_date", "Agreement date", "AGREEMENT DATE", "date", "required", "goods"),
    field("price_amount", "Sale price", "SALE PRICE", "currency", "recommended", "financial", {
      help: "Leave blank if price is still to be agreed.",
      min: 0,
    }),
    field("price_currency", "Currency", "CURRENCY", "select", "optional", "financial", {
      options: [
        { value: "INR", label: "INR" },
        { value: "USD", label: "USD" },
      ],
    }),
    field("payment_schedule", "Payment schedule", "PAYMENT SCHEDULE", "textarea", "optional", "financial"),
    field("delivery_date", "Delivery date", "DELIVERY DATE", "date", "recommended", "financial"),
    field("include_warranties", "Include limited title / quality warranties", "WARRANTIES", "checkbox", "recommended", "conditions"),
    field("termination_notice_days", "Cancellation notice (days)", "CANCELLATION NOTICE", "number", "optional", "conditions", {
      min: 1,
      max: 365,
    }),
    field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions", {
      options: DISPUTE_OPTIONS,
    }),
    field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true, provisionClass: "required" },
    { id: "parties", title: "Parties", required: true, provisionClass: "required" },
    { id: "recitals", title: "Background", required: true, provisionClass: "recommended" },
    { id: "definitions", title: "Definitions", required: true, provisionClass: "recommended" },
    { id: "sale", title: "Sale and transfer", required: true, provisionClass: "required" },
    { id: "price", title: "Price and payment", required: false, provisionClass: "user_specific", condition: { has_value: "price_amount" } },
    { id: "delivery", title: "Delivery", required: true, provisionClass: "required" },
    { id: "seller_obligations", title: "Seller obligations", required: true, provisionClass: "required" },
    { id: "buyer_obligations", title: "Buyer obligations", required: true, provisionClass: "required" },
    { id: "warranties", title: "Warranties", required: false, provisionClass: "recommended", condition: { truthy: "include_warranties" } },
    { id: "termination", title: "Cancellation", required: false, provisionClass: "recommended", condition: { has_value: "termination_notice_days" } },
    { id: "dispute_resolution", title: "Dispute resolution", required: true, provisionClass: "required" },
    { id: "governing_law", title: "Governing law", required: true, provisionClass: "required", needsLegalContext: true },
    { id: "schedules", title: "Annexures", required: false, provisionClass: "user_specific", condition: { has_value: "special_conditions" } },
    { id: "signatures", title: "Signatures", required: true, provisionClass: "required", includeSignature: true },
  ],
};

export const MOU_TEMPLATE: TemplateSpec = {
  id: "mou",
  category: "agreement",
  title: "Memorandum of Understanding",
  description: "A non-binding or limited-binding MoU draft recording intended cooperation in India.",
  documentType: "Memorandum of Understanding",
  jurisdictionCountry: "IN",
  parties: [
    { id: "party_a", role: "Party A", nameField: "party_a_name", typeField: "party_a_type", addressField: "party_a_address" },
    { id: "party_b", role: "Party B", nameField: "party_b_name", typeField: "party_b_type", addressField: "party_b_address" },
  ],
  steps: [
    { id: "type", title: "Document type", description: "Confirm the MoU you need.", fieldIds: ["document_title", "binding_intent"] },
    { id: "jurisdiction", title: "Jurisdiction", description: "Where cooperation is intended.", fieldIds: ["jurisdiction_country", "jurisdiction_region", "governing_law_seat"] },
    { id: "parties", title: "Parties", description: "Identify the parties.", fieldIds: ["party_a_name", "party_a_type", "party_a_address", "party_b_name", "party_b_type", "party_b_address"] },
    { id: "purpose", title: "Purpose and scope", description: "What the parties intend to do together.", fieldIds: ["purpose", "scope", "effective_date", "end_date"] },
    {
      id: "conditions",
      title: "Confidentiality and process",
      description: "Optional protections and disputes.",
      fieldIds: ["include_confidentiality", "termination_notice_days", "dispute_resolution", "special_conditions"],
    },
    { id: "review", title: "Review", description: "Check the details before generating a draft.", fieldIds: [] },
  ],
  fields: [
    field("document_title", "Document title", "DOCUMENT TITLE", "text", "optional", "type"),
    field("binding_intent", "Intended legal effect", "BINDING INTENT", "select", "required", "type", {
      options: [
        { value: "non_binding", label: "Generally non-binding (record of intent)" },
        { value: "partly_binding", label: "Partly binding (e.g. confidentiality / costs)" },
      ],
    }),
    ...jurisdictionFields(),
    field("party_a_name", "Party A name", "PARTY A NAME", "text", "required", "parties"),
    field("party_a_type", "Party A type", "PARTY A TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("party_a_address", "Party A address", "PARTY A ADDRESS", "textarea", "required", "parties"),
    field("party_b_name", "Party B name", "PARTY B NAME", "text", "required", "parties"),
    field("party_b_type", "Party B type", "PARTY B TYPE", "select", "required", "parties", { options: PARTY_TYPE_OPTIONS }),
    field("party_b_address", "Party B address", "PARTY B ADDRESS", "textarea", "required", "parties"),
    field("purpose", "Purpose of MoU", "PURPOSE", "textarea", "required", "purpose"),
    field("scope", "Scope of cooperation", "SCOPE", "textarea", "required", "purpose"),
    field("effective_date", "Start date", "START DATE", "date", "required", "purpose"),
    field("end_date", "End date", "END DATE", "date", "recommended", "purpose"),
    field("include_confidentiality", "Include confidentiality", "CONFIDENTIALITY", "checkbox", "recommended", "conditions"),
    field("termination_notice_days", "Notice to end (days)", "NOTICE DAYS", "number", "optional", "conditions", {
      min: 1,
      max: 365,
    }),
    field("dispute_resolution", "Dispute resolution", "DISPUTE RESOLUTION", "select", "recommended", "conditions", {
      options: DISPUTE_OPTIONS,
    }),
    field("special_conditions", "Other agreed conditions", "SPECIAL CONDITIONS", "textarea", "optional", "conditions"),
  ],
  clauses: [
    { id: "title", title: "Title", required: true, provisionClass: "required" },
    { id: "parties", title: "Parties", required: true, provisionClass: "required" },
    { id: "recitals", title: "Background", required: true, provisionClass: "recommended" },
    { id: "purpose", title: "Purpose and scope", required: true, provisionClass: "required" },
    { id: "status", title: "Legal status", required: true, provisionClass: "required" },
    { id: "obligations", title: "Cooperation", required: true, provisionClass: "recommended" },
    { id: "confidentiality", title: "Confidentiality", required: false, provisionClass: "recommended", condition: { truthy: "include_confidentiality" } },
    { id: "term", title: "Term", required: true, provisionClass: "required" },
    { id: "termination", title: "Ending", required: false, provisionClass: "recommended", condition: { has_value: "termination_notice_days" } },
    { id: "dispute_resolution", title: "Dispute resolution", required: true, provisionClass: "required" },
    { id: "governing_law", title: "Governing law", required: true, provisionClass: "required", needsLegalContext: true },
    { id: "miscellaneous", title: "General", required: true, provisionClass: "user_specific" },
    { id: "signatures", title: "Signatures", required: true, provisionClass: "required", includeSignature: true },
  ],
};

export const EXTRA_TEMPLATES: Record<string, TemplateSpec> = {
  [EMPLOYMENT_AGREEMENT_TEMPLATE.id]: EMPLOYMENT_AGREEMENT_TEMPLATE,
  [PARTNERSHIP_AGREEMENT_TEMPLATE.id]: PARTNERSHIP_AGREEMENT_TEMPLATE,
  [SALE_AGREEMENT_TEMPLATE.id]: SALE_AGREEMENT_TEMPLATE,
  [MOU_TEMPLATE.id]: MOU_TEMPLATE,
};
