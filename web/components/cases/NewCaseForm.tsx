"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

const FIELD_CLASS =
  "mt-1 h-11 w-full rounded-sm border border-[var(--line)] bg-white px-3 outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]";

export default function NewCaseForm() {
  const router = useRouter();
  const [form, setForm] = useState({
    title: "",
    description: "",
    category: "",
    city: "",
    state: "",
    country: "India",
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  function update(key: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    const response = await fetch("/api/cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const payload = await response.json();
    if (!response.ok) {
      setError(payload.error || "Unable to create case.");
      setSaving(false);
      return;
    }
    router.push(`/cases/${payload.case.id}`);
  }

  return (
    <form onSubmit={submit} className="mt-8 space-y-4 rounded-sm border border-[var(--line)] bg-white p-5 sm:p-6">
      <p className="text-sm text-[var(--ink-muted)]">
        Start with a clear title and optional location. You can upload documents and ask grounded questions after the case is created.
      </p>
      <label className="block text-sm font-medium">
        Case title
        <input
          required
          value={form.title}
          onChange={(event) => update("title", event.target.value)}
          className={FIELD_CLASS}
          maxLength={200}
          autoComplete="off"
        />
      </label>
      <label className="block text-sm font-medium">
        Description
        <textarea
          value={form.description}
          onChange={(event) => update("description", event.target.value)}
          rows={4}
          className="mt-1 w-full rounded-sm border border-[var(--line)] bg-white px-3 py-2 outline-none focus-visible:ring-2 focus-visible:ring-[var(--warm)]"
          maxLength={4000}
        />
      </label>
      <div className="grid gap-4 sm:grid-cols-2">
        {(
          [
            ["category", "Category"],
            ["city", "City"],
            ["state", "State"],
            ["country", "Country"],
          ] as const
        ).map(([key, label]) => (
          <label key={key} className="block text-sm font-medium">
            {label}
            <input
              value={form[key]}
              onChange={(event) => update(key, event.target.value)}
              className={FIELD_CLASS}
              maxLength={120}
            />
          </label>
        ))}
      </div>
      {error && (
        <p className="text-sm text-[var(--warn)]" role="alert">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={saving || !form.title.trim()}
        className="min-h-11 rounded-sm bg-[var(--forest)] px-5 text-sm font-semibold text-white disabled:opacity-50"
      >
        {saving ? "Creating..." : "Create case"}
      </button>
    </form>
  );
}
