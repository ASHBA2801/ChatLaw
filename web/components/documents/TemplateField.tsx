"use client";

import type { DocumentValues, FieldIssue, FieldSpec } from "@/lib/documents/types";

const requirementLabel = {
  required: "Required",
  optional: "Optional",
  recommended: "Recommended",
} as const;

export default function TemplateField({
  field,
  value,
  issues,
  onChange,
}: {
  field: FieldSpec;
  value: DocumentValues[string];
  issues: FieldIssue[];
  onChange: (fieldId: string, value: string | boolean | number) => void;
}) {
  const error = issues.find((issue) => issue.level === "error");
  const recommended = issues.find((issue) => issue.level === "recommended");
  const describedBy = [error ? `${field.id}-error` : null, recommended ? `${field.id}-hint` : null, field.help ? `${field.id}-help` : null]
    .filter(Boolean)
    .join(" ") || undefined;
  const className = `min-h-11 w-full rounded-xl border bg-white px-3 text-sm text-[var(--foreground)] ${error ? "border-[#8a3b2b]" : "border-[var(--line)]"}`;

  if (field.type === "checkbox") {
    return (
      <div className="space-y-1">
        <label className="flex min-h-11 items-start gap-3 text-sm">
          <input
            id={field.id}
            name={field.id}
            type="checkbox"
            checked={Boolean(value)}
            onChange={(event) => onChange(field.id, event.target.checked)}
            aria-describedby={describedBy}
            className="mt-1 h-4 w-4 accent-[var(--forest)]"
          />
          <span>
            <span className="font-medium">{field.label}</span>
            <span className="ml-2 text-xs text-[var(--ink-muted)]">{requirementLabel[field.requirement]}</span>
          </span>
        </label>
        {field.help ? <p id={`${field.id}-help`} className="text-xs text-[var(--ink-muted)]">{field.help}</p> : null}
        {error ? <p id={`${field.id}-error`} role="alert" className="text-sm text-[#8a3b2b]">{error.message}</p> : null}
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <label htmlFor={field.id} className="flex flex-wrap items-baseline gap-2 text-sm font-medium">
        <span>{field.label}</span>
        <span className="text-xs font-normal text-[var(--ink-muted)]">{requirementLabel[field.requirement]}</span>
      </label>
      {field.type === "textarea" ? (
        <textarea
          id={field.id}
          name={field.id}
          rows={4}
          value={String(value ?? "")}
          onChange={(event) => onChange(field.id, event.target.value)}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={describedBy}
          aria-required={field.requirement === "required" || undefined}
          className={`${className} py-3`}
        />
      ) : field.type === "select" ? (
        <select
          id={field.id}
          name={field.id}
          value={String(value ?? "")}
          onChange={(event) => onChange(field.id, event.target.value)}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={describedBy}
          aria-required={field.requirement === "required" || undefined}
          className={className}
        >
          <option value="">Select</option>
          {field.options?.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      ) : (
        <input
          id={field.id}
          name={field.id}
          type={field.type === "currency" ? "number" : field.type}
          min={field.min}
          max={field.max}
          step={field.type === "currency" ? "0.01" : undefined}
          value={value === false ? "" : String(value ?? "")}
          onChange={(event) => onChange(field.id, event.target.value)}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={describedBy}
          aria-required={field.requirement === "required" || undefined}
          className={className}
        />
      )}
      {field.help ? <p id={`${field.id}-help`} className="text-xs text-[var(--ink-muted)]">{field.help}</p> : null}
      {recommended && !error ? <p id={`${field.id}-hint`} className="text-xs text-[var(--ink-muted)]">{recommended.message}</p> : null}
      {error ? <p id={`${field.id}-error`} role="alert" className="text-sm text-[#8a3b2b]">{error.message}</p> : null}
    </div>
  );
}
