"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

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
    icon: "📄",
    examples: "Rental, Lease, NDA, Employment, Loan",
  },
  {
    id: "deed",
    title: "Deeds & Conveyance",
    description: "Absolute sale deeds, gift deeds, release & relinquishment deeds, General & Special POA.",
    badge: "6 Templates",
    icon: "📜",
    examples: "Sale Deed, GPA, SPA, Gift Deed, Release",
  },
  {
    id: "notice",
    title: "Legal Notices",
    description: "Section 138 cheque bounce demand, tenant eviction notice, and breach cure notices.",
    badge: "4 Templates",
    icon: "⚖️",
    examples: "Sec 138 NI Act, Eviction, Demand",
  },
  {
    id: "complaint",
    title: "Complaints & Petitions",
    description: "Consumer forum complaints under CPA 2019, police complaints, and FIR narratives.",
    badge: "2 Templates",
    icon: "🏛️",
    examples: "Consumer Court, Police / FIR",
  },
  {
    id: "affidavit",
    title: "Affidavits & Declarations",
    description: "Sworn affidavits for notaries, name change declarations, and indemnity bonds.",
    badge: "3 Templates",
    icon: "✍️",
    examples: "Name Change, Notary Affidavit, Indemnity",
  },
  {
    id: "application",
    title: "Statutory Applications",
    description: "Form A RTI applications under RTI Act 2005, and NALSA free legal aid petitions.",
    badge: "2 Templates",
    icon: "📋",
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
    <div className="space-y-8">
      {/* Hero Conversational Intake Card */}
      <div className="rounded-sm border border-[var(--line)] bg-white p-6 shadow-xs sm:p-8">
        <div className="max-w-2xl">
          <span className="inline-flex items-center rounded-xs bg-[var(--module-fill)] px-2.5 py-1 text-xs font-medium text-[var(--forest)]">
            AI-Assisted Legal Drafting • Indian Law Models
          </span>
          <h2 className="mt-3 text-2xl font-bold tracking-tight text-[var(--foreground)] sm:text-3xl">
            What legal document do you need?
          </h2>
          <p className="mt-2 text-sm leading-6 text-[var(--ink-muted)]">
            Describe your document in natural English or Tamil. ChatLaw identifies the model template, extracts terms, asks only necessary clarification questions, and structures an authentic legal draft.
          </p>
        </div>

        {/* Input area */}
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <div className="relative flex-1">
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
              placeholder="e.g. I need an 11-month rental agreement for my flat in Coimbatore. Rent is ₹18,000/mo, deposit ₹1 Lakh, tenant is Vignesh..."
              className="w-full resize-none rounded-sm border border-[var(--line)] bg-[var(--canvas)] p-3.5 text-sm text-[var(--foreground)] placeholder:text-[var(--ink-muted)] focus:border-[var(--forest)] focus:bg-white focus:outline-none"
            />
            <div className="mt-1 flex justify-between text-xs text-[var(--ink-muted)]">
              <span>Supports English & regional terms (e.g. வாடகை ஒப்பந்தம்)</span>
              <span>Press Ctrl+Enter to start</span>
            </div>
          </div>
          <div className="flex sm:flex-col sm:justify-start">
            <button
              onClick={() => handleStart()}
              className="flex min-h-11 w-full items-center justify-center rounded-sm bg-[var(--forest)] px-6 text-sm font-semibold text-white shadow-xs hover:opacity-95 focus:outline-none"
            >
              Start Drafting
            </button>
          </div>
        </div>

        {/* Quick-Prompt suggestions */}
        <div className="mt-5 border-t border-[var(--line)] pt-4">
          <p className="text-xs font-medium uppercase tracking-wider text-[var(--ink-muted)]">
            Common Quick Starts:
          </p>
          <div className="mt-2.5 flex flex-wrap gap-2">
            {EXAMPLE_PROMPTS.map((item) => (
              <button
                key={item.label}
                onClick={() => {
                  setPrompt(item.prompt);
                  handleStart(item.prompt);
                }}
                className="rounded-xs border border-[var(--line)] bg-[var(--module-fill)] px-2.5 py-1.5 text-xs text-[var(--foreground)] hover:border-[var(--forest)] hover:bg-white transition-colors"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Category Quick-Start Cards */}
      <div>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold tracking-tight text-[var(--foreground)]">
              Document Categories
            </h3>
            <p className="text-xs text-[var(--ink-muted)]">
              Select a category to browse templates or start a targeted legal draft
            </p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CATEGORIES.map((cat) => (
            <div
              key={cat.id}
              onClick={() => handleCategoryClick(cat.id)}
              className="group cursor-pointer rounded-sm border border-[var(--line)] bg-white p-5 transition-all hover:border-[var(--forest)] hover:shadow-xs"
            >
              <div className="flex items-center justify-between">
                <span className="text-2xl">{cat.icon}</span>
                <span className="rounded-xs bg-[var(--module-fill)] px-2 py-0.5 text-xs font-medium text-[var(--ink-muted)] group-hover:text-[var(--forest)]">
                  {cat.badge}
                </span>
              </div>
              <h4 className="mt-3 text-base font-semibold text-[var(--foreground)] group-hover:text-[var(--forest)]">
                {cat.title}
              </h4>
              <p className="mt-1 text-xs leading-5 text-[var(--ink-muted)]">
                {cat.description}
              </p>
              <div className="mt-3 border-t border-[var(--line)] pt-2.5 text-xs text-[var(--ink-muted)]">
                <span className="font-medium text-[var(--foreground)]">Formats:</span> {cat.examples}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
