import { clauseIsActive, hasValue } from "./conditions";
import { INDIA_REGIONS } from "./constants";
import type { DocumentValues, FieldIssue, FieldSpec, TemplateSpec } from "./types";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const ISO_DATE_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

function asString(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

export function validateField(field: FieldSpec, values: DocumentValues): FieldIssue[] {
  const present = hasValue(values, field.id);
  const raw = values[field.id];
  if (!present) {
    if (field.requirement === "required") {
      return [{ fieldId: field.id, level: "error", message: `${field.label} is required before a draft can be generated.` }];
    }
    if (field.requirement === "recommended") {
      return [{ fieldId: field.id, level: "recommended", message: `${field.label} is recommended.` }];
    }
    return [];
  }
  const issues: FieldIssue[] = [];
  if ((field.type === "text" || field.type === "textarea" || field.type === "tel") && !asString(raw)) {
    issues.push({ fieldId: field.id, level: "error", message: `${field.label} cannot be empty.` });
  }
  if (field.type === "email" && !EMAIL_RE.test(asString(raw))) {
    issues.push({ fieldId: field.id, level: "error", message: `${field.label} must be a valid email address.` });
  }
  if (field.type === "date") {
    const match = asString(raw).match(ISO_DATE_RE);
    const valid = Boolean(match && !Number.isNaN(Date.parse(`${match[1]}-${match[2]}-${match[3]}`)));
    if (!valid) issues.push({ fieldId: field.id, level: "error", message: `${field.label} must be a valid date.` });
  }
  if (field.type === "number" || field.type === "currency") {
    const number = typeof raw === "number" ? raw : Number(raw);
    if (!Number.isFinite(number)) {
      issues.push({ fieldId: field.id, level: "error", message: `${field.label} must be a number.` });
    } else {
      if (field.min !== undefined && number < field.min) {
        issues.push({ fieldId: field.id, level: "error", message: `${field.label} must be at least ${field.min}.` });
      }
      if (field.max !== undefined && number > field.max) {
        issues.push({ fieldId: field.id, level: "error", message: `${field.label} must be at most ${field.max}.` });
      }
    }
  }
  if (field.type === "select" && field.options && !field.options.some((option) => option.value === String(raw))) {
    issues.push({ fieldId: field.id, level: "error", message: `${field.label} must be one of the listed options.` });
  }
  if (field.id === "jurisdiction_country" && asString(raw) !== "IN") {
    issues.push({ fieldId: field.id, level: "error", message: "This generator currently supports India only." });
  }
  if (field.id === "jurisdiction_region" && !INDIA_REGIONS.includes(asString(raw) as (typeof INDIA_REGIONS)[number])) {
    issues.push({ fieldId: field.id, level: "error", message: "Select a State or Union Territory in India." });
  }
  return issues;
}

export function validateValues(template: TemplateSpec, values: DocumentValues) {
  const issues = template.fields.flatMap((item) => validateField(item, values));
  const start = asString(values.effective_date);
  const end = asString(values.end_date);
  if (start && end && ISO_DATE_RE.test(start) && ISO_DATE_RE.test(end) && end < start) {
    issues.push({ fieldId: "end_date", level: "error", message: "The end date cannot be earlier than the start date." });
  }
  const blocking = issues.filter((issue) => issue.level === "error");
  return { ok: blocking.length === 0, blocking, issues, canGenerate: blocking.length === 0 };
}

export function activeClauses(template: TemplateSpec, values: DocumentValues) {
  return template.clauses.filter((clause) => clauseIsActive(clause.condition, values));
}

export function placeholderFor(field: FieldSpec): string {
  return `[${field.placeholderLabel} REQUIRED]`;
}

export function stepHasErrors(template: TemplateSpec, stepId: string, values: DocumentValues): boolean {
  const step = template.steps.find((item) => item.id === stepId);
  if (!step) return false;
  return step.fieldIds.some((fieldId) => {
    const field = template.fields.find((item) => item.id === fieldId);
    return field ? validateField(field, values).some((issue) => issue.level === "error") : false;
  });
}
