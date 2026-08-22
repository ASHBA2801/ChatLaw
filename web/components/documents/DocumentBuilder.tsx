"use client";

import { FormEvent, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import DisclaimerBanner from "./DisclaimerBanner";
import TemplateField from "./TemplateField";
import { defaultValues, getTemplate, listTemplates } from "@/lib/documents/templates";
import { activeClauses, validateValues } from "@/lib/documents/validation";
import type { DocumentValues, TemplateSpec } from "@/lib/documents/types";
import { useLanguage } from "@/lib/i18n/LanguageProvider";

export default function DocumentBuilder() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { language } = useLanguage();
  const templates = listTemplates();
  const initialTemplate = searchParams.get("template");
  const [templateId, setTemplateId] = useState(() => {
    if (initialTemplate && templates.some((item) => item.id === initialTemplate)) {
      return initialTemplate;
    }
    return templates[0]?.id ?? "nda";
  });
  const template = useMemo(() => getTemplate(templateId), [templateId]);
  const [stepIndex, setStepIndex] = useState(0);
  const [values, setValues] = useState<DocumentValues>(() => {
    const base = defaultValues(template);
    const prefillRaw = searchParams.get("prefill");
    if (!prefillRaw) return base;
    try {
      const parsed = JSON.parse(prefillRaw) as DocumentValues;
      return { ...base, ...parsed };
    } catch {
      return base;
    }
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validation = validateValues(template, values);
  const steps = template.steps;
  const step = steps[stepIndex];
  const isReview = step?.id === "review";
  const clauses = activeClauses(template, values);

  function selectTemplate(next: TemplateSpec) {
    setTemplateId(next.id);
    setValues(defaultValues(next));
    setStepIndex(0);
    setError(null);
  }

  function updateField(fieldId: string, value: string | boolean | number) {
    setValues((current) => ({ ...current, [fieldId]: value }));
  }

  async function generate(event: FormEvent) {
    event.preventDefault();
    if (!validation.canGenerate) {
      setError("Required information is missing. Complete the highlighted fields before generating.");
      const firstError = validation.blocking[0];
      if (firstError) {
        const field = template.fields.find((item) => item.id === firstError.fieldId);
        const index = template.steps.findIndex((item) => item.fieldIds.includes(firstError.fieldId) || item.id === field?.step);
        if (index >= 0) setStepIndex(index);
      }
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/documents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          templateId: template.id,
          values: { ...values, draft_language: language },
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error || "Generation stopped because required information is missing or unavailable.");
      }
      router.push(`/documents/${payload.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={generate} className="grid gap-6 lg:grid-cols-[240px_minmax(0,1fr)]">
      <aside className="rounded-2xl border border-[var(--line)] bg-white p-4">
        <h2 className="text-sm font-semibold">Build steps</h2>
        <nav aria-label="Document build steps">
          <ol className="mt-4 space-y-1">
            {steps.map((item, index) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => setStepIndex(index)}
                  aria-current={index === stepIndex ? "step" : undefined}
                  className={`flex min-h-11 w-full items-center justify-between rounded-xl px-3 text-left text-sm ${index === stepIndex ? "bg-[var(--forest)] text-white" : "text-[var(--foreground)] hover:bg-[#edf2ec]"}`}
                >
                  <span>{item.title}</span>
                  <span className={`text-xs ${index === stepIndex ? "text-[var(--lime)]" : "text-[var(--ink-muted)]"}`}>{index + 1}/{steps.length}</span>
                </button>
              </li>
            ))}
          </ol>
        </nav>
      </aside>

      <div className="space-y-6">
        <section className="rounded-2xl border border-[var(--line)] bg-white p-5 sm:p-6">
          <h1 className="text-2xl font-semibold tracking-tight">New legal document</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--ink-muted)]">
            Choose a supported template and complete only the details that apply. ChatLaw will not invent missing parties, dates, or amounts.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            {templates.map((item) => {
              const selected = item.id === template.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => selectTemplate(item)}
                  aria-pressed={selected}
                  className={`min-h-24 rounded-2xl border px-4 py-3 text-left ${selected ? "border-[var(--forest)] bg-[#eef5d0]" : "border-[var(--line)] bg-[var(--background)]"}`}
                >
                  <span className="block font-semibold">{item.title}</span>
                  <span className="mt-1 block text-xs leading-5 text-[var(--ink-muted)]">{item.description}</span>
                </button>
              );
            })}
          </div>
        </section>

        <section className="rounded-2xl border border-[var(--line)] bg-white p-5 sm:p-6">
          <h2 className="text-xl font-semibold">{step.title}</h2>
          <p className="mt-1 text-sm text-[var(--ink-muted)]">{step.description}</p>
          <div className="mt-6 space-y-5">
            {isReview ? (
              <div className="space-y-4">
                <dl className="grid gap-3 sm:grid-cols-2">
                  {template.fields.filter((field) => values[field.id] !== "" && values[field.id] !== false).map((field) => (
                    <div key={field.id} className="min-w-0">
                      <dt className="text-xs text-[var(--ink-muted)]">{field.label}</dt>
                      <dd className="break-words text-sm">{String(values[field.id])}</dd>
                    </div>
                  ))}
                </dl>
                <div>
                  <h3 className="text-sm font-semibold">Clauses that will be included</h3>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
                    {clauses.map((clause) => (
                      <li key={clause.id}>{clause.title}{clause.needsLegalContext ? " — legal context requested" : ""}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              template.fields.filter((field) => step.fieldIds.includes(field.id)).map((field) => (
                <TemplateField
                  key={field.id}
                  field={field}
                  value={values[field.id]}
                  issues={validation.issues.filter((issue) => issue.fieldId === field.id)}
                  onChange={updateField}
                />
              ))
            )}
          </div>
        </section>

        <DisclaimerBanner compact />

        {error ? <p role="alert" className="text-sm text-[#8a3b2b]">{error}</p> : null}

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            disabled={stepIndex === 0}
            onClick={() => setStepIndex((index) => Math.max(0, index - 1))}
            className="min-h-11 rounded-full border border-[var(--line)] bg-white px-5 text-sm font-medium disabled:opacity-50"
          >
            Back
          </button>
          {stepIndex < steps.length - 1 ? (
            <button
              type="button"
              onClick={() => setStepIndex((index) => Math.min(steps.length - 1, index + 1))}
              className="min-h-11 rounded-full bg-[var(--forest)] px-5 text-sm font-semibold text-white"
            >
              Continue
            </button>
          ) : (
            <button
              type="submit"
              disabled={busy}
              aria-busy={busy}
              className="min-h-11 rounded-full bg-[var(--forest)] px-5 text-sm font-semibold text-white disabled:opacity-60"
            >
              {busy ? "Generating draft…" : "Generate draft"}
            </button>
          )}
        </div>
      </div>
    </form>
  );
}
