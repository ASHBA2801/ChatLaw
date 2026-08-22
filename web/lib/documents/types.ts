export type Requirement = "required" | "optional" | "recommended";
export type ProvisionClass = "required" | "recommended" | "user_specific";
export type FieldType =
  | "text"
  | "textarea"
  | "select"
  | "date"
  | "number"
  | "currency"
  | "checkbox"
  | "email"
  | "tel";
export type DocumentCategory = "agreement" | "legal_document";
export type DocumentStatus = "draft" | "review" | "final";

export type FieldOption = { value: string; label: string };

export type ClauseCondition =
  | { equals: [string, string | boolean] }
  | { truthy: string }
  | { has_value: string };

export interface FieldSpec {
  id: string;
  label: string;
  placeholderLabel: string;
  type: FieldType;
  requirement: Requirement;
  step: string;
  help?: string;
  options?: FieldOption[];
  min?: number;
  max?: number;
}

export interface StepSpec {
  id: string;
  title: string;
  description: string;
  fieldIds: string[];
}

export interface PartySpec {
  id: string;
  role: string;
  nameField: string;
  typeField: string;
  addressField: string;
}

export interface ClauseSpec {
  id: string;
  title: string;
  required: boolean;
  provisionClass?: ProvisionClass;
  needsLegalContext?: boolean;
  includeSignature?: boolean;
  condition?: ClauseCondition;
}

export interface TemplateSpec {
  id: string;
  category: DocumentCategory;
  title: string;
  description: string;
  documentType: string;
  jurisdictionCountry: "IN";
  parties: PartySpec[];
  steps: StepSpec[];
  fields: FieldSpec[];
  clauses: ClauseSpec[];
}

export interface FieldIssue {
  fieldId: string;
  level: "error" | "recommended";
  message: string;
}

export interface DocumentSection {
  id: string;
  title: string;
  body: string;
  required: boolean;
  provision_class?: ProvisionClass;
  needs_legal_context?: boolean;
  review_required?: boolean;
  citation_ids?: number[];
  legal_basis?: Array<{
    citation_id: number;
    label: string;
    document?: string | null;
    section?: string | null;
    chunk_id?: string;
  }>;
  include_signature?: boolean;
  number?: number | null;
}

export interface DocumentWarning {
  code: string;
  message: string;
}

export interface SignatureBlock {
  party_id: string;
  role: string;
  name: string;
  lines: string[];
}

export interface GeneratedDocumentPayload {
  template_id: string;
  title: string;
  document_type: string;
  jurisdiction_country: string;
  jurisdiction_region: string;
  sections: DocumentSection[];
  signatures: SignatureBlock[];
  warnings: DocumentWarning[];
  citations: Array<Record<string, unknown>>;
  model_used?: boolean;
  disclaimer?: string;
}

export type DocumentValues = Record<string, string | number | boolean | "">;
