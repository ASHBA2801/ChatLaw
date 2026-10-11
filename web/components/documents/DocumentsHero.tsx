"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import CategoryIcon from "@/components/documents/CategoryIcon";

const EXAMPLE_PROMPTS = [
  {
    label: "Rental Agreement in Coimbatore (₹18,000/mo)",
    prompt: "I need a residential rental agreement for a flat in Coimbatore. Rent is ₹18,000 per month, deposit is ₹1 Lakh for 11 months.",
  },
  {
    label: "Cheque Bounce Notice (Section 138 NI Act)",
    prompt: "Draft a legal notice under Section 138 NI Act for a bounced cheque of ₹2,50,000 returned with memo funds insufficient.",
  },
  {
    label: "Absolute Sale Deed for Property",
    prompt: "Draft an absolute sale deed for a residential property with schedule of boundaries and vendor indemnity.",
  },
  {
    label: "General Power of Attorney (GPA)",
    prompt: "I need a General Power of Attorney authorizing my agent to manage my property and represent in legal matters.",
  },
  {
    label: "Mutual Non-Disclosure Agreement (NDA)",
    prompt: "Mutual NDA between two companies for confidential discussions and evaluation of business partnership.",
  },
  {
    label: "Consumer Court Complaint (Sec 35)",
    prompt: "Consumer complaint before District Commission for defective electronic goods and refusal of warranty refund.",
  },
];

const CATEGORIES = [
  {
    id: "agreement",
    title: "Agreements & Contracts",
    description: "Rental agreements, commercial leases, NDAs, employment, founder & loan contracts.",
    badge: "11 Templates",
    icon: "agreement",
    examples: "Rental, Lease, NDA, Employment, Loan",
  },
  {
    id: "deed",
    title: "Deeds & Conveyance",
    description: "Absolute sale deeds, gift deeds, release & relinquishment deeds, General & Special POA.",
    badge: "6 Templates",
    icon: "deed",
    examples: "Sale Deed, GPA, SPA, Gift Deed, Release",
  },
  {
    id: "notice",
    title: "Legal Notices",
    description: "Section 138 cheque bounce demand, tenant eviction notice, and breach cure notices.",
    badge: "4 Templates",
    icon: "notice",
    examples: "Sec 138 NI Act, Eviction, Demand",
  },
  {
    id: "complaint",
    title: "Complaints & Petitions",
    description: "Consumer forum complaints under CPA 2019, police complaints, and FIR narratives.",
    badge: "2 Templates",
    icon: "complaint",
    examples: "Consumer Court, Police / FIR",
  },
  {
    id: "affidavit",
    title: "Affidavits & Declarations",
    description: "Sworn affidavits for notaries, name change declarations, and indemnity bonds.",
    badge: "3 Templates",
    icon: "affidavit",
    examples: "Name Change, Notary Affidavit, Indemnity",
  },
  {
    id: "application",
    title: "Statutory Applications",
    description: "Form A RTI applications under RTI Act 2005, and NALSA free legal aid petitions.",
    badge: "2 Templates",
    icon: "application",
    examples: "RTI Form A, NALSA Legal Aid",
  },
];

export default function DocumentsHero() {
  const router = useRouter();
  const [prompt, setPrompt] = useState("");

  const handleStart = (textToUse?: string) => {
    const finalPrompt = (textToUse ?? prompt).trim();
    if (!finalPrompt) {
      router.push("/documents/new");
      return;
    }
    router.push(`/documents/new?prompt=${encodeURIComponent(finalPrompt)}`);
  };

  const handleCategoryClick = (categoryId: string) => {
    router.push(`/documents/new?category=${encodeURIComponent(categoryId)}`);
  };

  return (
    <div className="mx-auto w-full max-w-6xl space-y-10">
      <section className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-5 shadow-[var(--shadow-soft)] sm:p-8">
        <div className="max-w-2xl">
          <span className="inline-flex items-center gap-2 rounded-full bg-[var(--accent-soft)] px-3 py-1 text-xs font-semibold text-[var(--accent)]">
            AI-assisted drafting · Indian law templates
          </span>
          <h2 className="mt-4 text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            What legal document do you need?
          </h2>
          <p className="mt-3 text-[15px] leading-7 text-[var(--ink-muted)]">
            Describe it in plain English or Tamil. ChatLaw picks the matching template, pulls out the terms you gave,
            asks only what it still needs, and structures a draft you can edit.
          </p>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-start">
          <div className="flex-1">
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  handleStart();
                }
              }}
              rows={3}
              aria-label="Describe the document you need"
              placeholder="e.g. I need an 11-month rental agreement for my flat in Coimbatore. Rent is ₹18,000/mo, deposit ₹1 Lakh, tenant is Vignesh..."
              className="w-full resize-none rounded-xl border border-[var(--line-strong)] bg-[var(--background)] p-3.5 text-[15px] leading-6 text-[var(--foreground)] placeholder:text-[var(--ink-faint)] focus:border-[var(--accent)] focus:bg-[var(--surface)] focus:outline-none"
            />
            <div className="mt-1.5 flex flex-wrap justify-between gap-x-4 text-xs text-[var(--ink-faint)]">
              <span>Supports English and regional terms (e.g. வாடகை ஒப்பந்தம்)</span>
              <span>Ctrl+Enter to start</span>
            </div>
          </div>
          <button onClick={() => handleStart()} className="btn-primary w-full sm:w-auto">
            Start drafting
          </button>
        </div>

        <div className="mt-6 border-t border-[var(--line)] pt-5">
          <p className="text-xs font-semibold text-[var(--ink-muted)]">Quick starts</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {EXAMPLE_PROMPTS.map((item) => (
              <button
                key={item.label}
                onClick={() => {
                  setPrompt(item.prompt);
                  handleStart(item.prompt);
                }}
                className="min-h-9 rounded-full border border-[var(--line-strong)] bg-[var(--surface)] px-3.5 text-[13px] text-[var(--foreground)] hover:border-[var(--accent)] hover:bg-[var(--accent-soft)] hover:text-[var(--accent)]"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </section>

      <section aria-labelledby="doc-categories">
        <h3 id="doc-categories" className="text-xl font-semibold tracking-tight">
          Browse by category
        </h3>
        <p className="mt-1 text-sm text-[var(--ink-muted)]">Pick a category to see its templates, or start a targeted draft.</p>

        <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => handleCategoryClick(cat.id)}
              className="group flex flex-col rounded-xl border border-[var(--line)] bg-[var(--surface)] p-5 text-left shadow-[var(--shadow-soft)] hover:-translate-y-0.5 hover:border-[var(--accent)] hover:shadow-[var(--shadow-raised)]"
            >
              <span className="flex items-center justify-between">
                <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[var(--accent-soft)] text-[var(--accent)]">
                  <CategoryIcon kind={cat.icon} className="h-5 w-5" />
                </span>
                <span className="rounded-full bg-[var(--fill)] px-2.5 py-0.5 text-xs font-medium text-[var(--ink-muted)]">
                  {cat.badge}
                </span>
              </span>
              <span className="mt-4 text-base font-semibold group-hover:text-[var(--accent)]">{cat.title}</span>
              <span className="mt-1.5 text-sm leading-6 text-[var(--ink-muted)]">{cat.description}</span>
              <span className="mt-4 border-t border-[var(--line)] pt-3 text-xs text-[var(--ink-faint)]">{cat.examples}</span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
