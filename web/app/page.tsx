import Image from "next/image";
import Link from "next/link";
import type { ComponentType } from "react";

import { ArrowUpIcon } from "@/components/chat/ChatIcons";
import BrandMark from "@/components/layout/BrandMark";
import { CasesNavIcon, ChatNavIcon, DocumentsNavIcon, ResearchNavIcon } from "@/components/layout/NavIcons";
import { LANGUAGES } from "@/lib/i18n/languages";

const TOP_LINKS = [
  { href: "/chat", label: "Chat" },
  { href: "/documents", label: "Documents" },
  { href: "/cases", label: "Cases" },
  { href: "/research", label: "Research" },
] as const;

const STARTER_QUESTIONS = [
  "My landlord is refusing to return my deposit.",
  "What is the punishment for theft?",
  "When can police arrest without a warrant?",
  "Explain Section 303 of the Bharatiya Nyaya Sanhita.",
] as const;

const STEPS = [
  {
    title: "Describe what happened",
    body: "Write or speak in English or an Indian language. No legal vocabulary needed.",
  },
  {
    title: "Answer a few questions",
    body: "ChatLaw asks only what it needs, such as your state or whether the tenancy has ended.",
  },
  {
    title: "Read the answer and its sources",
    body: "You get a plain-language explanation with section-level citations you can open and check.",
  },
] as const;

const WORKSPACES: ReadonlyArray<{
  href: string;
  title: string;
  body: string;
  Icon: ComponentType<{ className?: string }>;
}> = [
  {
    href: "/chat",
    title: "Ask",
    body: "Describe a problem in your own words. ChatLaw asks a few focused questions before it answers.",
    Icon: ChatNavIcon,
  },
  {
    href: "/documents",
    title: "Draft",
    body: "Fill in a guided form and get a structured legal document you can edit, export as PDF or Word, and review.",
    Icon: DocumentsNavIcon,
  },
  {
    href: "/cases",
    title: "Organise",
    body: "Keep each matter's papers, dates and timeline in one private workspace tied to your account.",
    Icon: CasesNavIcon,
  },
  {
    href: "/research",
    title: "Check",
    body: "Search statutes and sources directly when you want to read the law itself, not a summary.",
    Icon: ResearchNavIcon,
  },
];

const INDIAN_LANGUAGES = LANGUAGES.filter((language) => language.code !== "en");

export default function Home() {
  return (
    <main className="flex min-h-dvh flex-col bg-[var(--surface)]">
      <header className="sticky top-0 z-30 border-b border-[var(--line)] bg-[var(--surface)]">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
          <BrandMark />
          <nav aria-label="Primary" className="flex items-center gap-1">
            <div className="hidden items-center gap-1 md:flex">
              {TOP_LINKS.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="rounded-lg px-3 py-2 text-sm font-medium text-[var(--ink-muted)] hover:bg-[var(--fill)] hover:text-[var(--foreground)]"
                >
                  {link.label}
                </Link>
              ))}
            </div>
            <Link href="/signin" className="btn-secondary ml-2 !min-h-10 !px-4">
              Sign in
            </Link>
            <Link href="/chat" className="btn-primary !min-h-10 !px-4 max-sm:hidden">
              Start chatting
            </Link>
          </nav>
        </div>
      </header>

      <section className="px-4 pb-16 pt-14 text-center sm:px-6 sm:pb-20 sm:pt-20 lg:pb-24 lg:pt-24">
        <div className="mx-auto max-w-3xl">
          <p className="rise-in inline-flex items-center gap-2 rounded-full border border-[var(--line)] bg-[var(--surface)] px-3 py-1 text-xs font-medium text-[var(--ink-muted)]">
            <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
            Indian law, in 22+ languages
          </p>
          <h1 className="rise-in rise-in-delay-1 mt-6 text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl lg:text-[3.5rem]">
            Understand your legal situation in plain language.
          </h1>
          <p className="rise-in rise-in-delay-2 mx-auto mt-5 max-w-2xl text-base leading-7 text-[var(--ink-muted)] sm:text-lg sm:leading-8">
            Describe what happened in English or an Indian language. ChatLaw asks focused follow-up questions, then
            explains the law with section-level sources you can check yourself.
          </p>

          <form
            action="/chat"
            className="rise-in rise-in-delay-3 mx-auto mt-9 flex w-full max-w-2xl items-center gap-2 rounded-full border border-[var(--line-strong)] bg-[var(--surface)] p-1.5 pl-5 text-left shadow-[var(--shadow-raised)] focus-within:border-[var(--accent)] sm:pl-6"
          >
            <label htmlFor="home-question" className="sr-only">
              Describe your legal situation
            </label>
            <input
              id="home-question"
              name="q"
              type="text"
              maxLength={2000}
              autoComplete="off"
              placeholder="Describe your situation in your own words…"
              className="min-w-0 flex-1 bg-transparent py-3 text-base outline-none placeholder:text-[var(--ink-muted)]"
            />
            <button
              type="submit"
              className="inline-flex h-12 shrink-0 items-center gap-2 rounded-full bg-[var(--accent)] px-5 text-[15px] font-semibold text-[var(--on-accent)] hover:bg-[var(--accent-strong)]"
            >
              Ask
              <ArrowUpIcon className="h-4 w-4" />
            </button>
          </form>

          <ul className="mx-auto mt-5 flex max-w-2xl flex-wrap justify-center gap-2" aria-label="Example questions">
            {STARTER_QUESTIONS.map((question) => (
              <li key={question}>
                <Link
                  href={`/chat?q=${encodeURIComponent(question)}`}
                  className="inline-flex min-h-10 items-center rounded-full border border-[var(--line)] bg-[var(--surface)] px-4 py-2 text-left text-sm text-[var(--foreground)] hover:bg-[var(--fill)]"
                >
                  {question}
                </Link>
              </li>
            ))}
          </ul>

          <p className="mx-auto mt-6 max-w-md text-xs leading-5 text-[var(--ink-faint)]">
            Informational assistance only — not a substitute for a lawyer or court.
          </p>
        </div>
      </section>

      <section className="border-y border-[var(--line)] bg-[var(--background)]">
        <div className="mx-auto grid w-full max-w-6xl items-center gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] lg:gap-16 lg:px-8 lg:py-24">
          <div>
            <h2 className="text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
              A conversation, not a form.
            </h2>
            <p className="mt-4 max-w-md text-base leading-7 text-[var(--ink-muted)]">
              ChatLaw works like a careful interview. It finds out what it needs before it points you to the law.
            </p>
            <ol className="mt-8 space-y-6">
              {STEPS.map((step, index) => (
                <li key={step.title} className="flex gap-4">
                  <span
                    aria-hidden="true"
                    className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[var(--accent-soft)] text-sm font-semibold text-[var(--accent)]"
                  >
                    {index + 1}
                  </span>
                  <div>
                    <h3 className="text-base font-semibold">{step.title}</h3>
                    <p className="mt-1 text-sm leading-6 text-[var(--ink-muted)]">{step.body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <figure
            className="rounded-3xl border border-[var(--line)] bg-[var(--surface)] p-5 shadow-[var(--shadow-raised)] sm:p-7"
            aria-label="Example conversation"
          >
            <div className="flex items-center justify-between border-b border-[var(--line)] pb-4">
              <span className="text-sm font-semibold">Example conversation</span>
              <span className="text-xs text-[var(--ink-muted)]">Step 2 of 3</span>
            </div>
            <div className="space-y-5 pt-5">
              <p className="ml-auto w-fit max-w-[88%] rounded-3xl bg-[var(--fill)] px-5 py-3 text-[15px] leading-6">
                My landlord is refusing to return my deposit.
              </p>
              <div className="flex gap-3">
                <Image
                  src="/ChatLaw Logo.png"
                  alt=""
                  width={56}
                  height={56}
                  className="mt-0.5 h-7 w-7 shrink-0 rounded-full object-contain max-sm:hidden"
                />
                <div className="min-w-0 flex-1">
                  <p className="text-[15px] leading-7">
                    Which state are you in, and has the tenancy ended? After that I can point to the sections that
                    usually govern deposit return.
                  </p>
                  <div className="mt-4 border-t border-[var(--line)] pt-4">
                    <p className="text-xs font-semibold text-[var(--ink-muted)]">Sources it will check</p>
                    <ul className="mt-2 divide-y divide-[var(--line)] text-sm">
                      <li className="flex items-center justify-between gap-3 py-2.5">
                        <span>Transfer of Property Act · tenancy terms</span>
                        <span className="shrink-0 rounded-full bg-[var(--accent-soft)] px-2 py-0.5 text-xs font-medium text-[var(--accent)]">
                          Act
                        </span>
                      </li>
                      <li className="flex items-center justify-between gap-3 py-2.5">
                        <span>State rent and tenancy rules</span>
                        <span className="shrink-0 rounded-full bg-[var(--fill)] px-2 py-0.5 text-xs font-medium text-[var(--ink-muted)]">
                          After location
                        </span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </figure>
        </div>
      </section>

      <section>
        <div className="mx-auto w-full max-w-6xl px-4 py-16 sm:px-6 lg:px-8 lg:py-24">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
              Everything for one matter, in one place.
            </h2>
            <p className="mt-4 text-base leading-7 text-[var(--ink-muted)]">
              Ask a question, draft the paperwork, keep your records and read the sources — without switching tools.
            </p>
          </div>
          <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {WORKSPACES.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="group flex flex-col rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-6 hover:border-[var(--line-strong)] hover:bg-[var(--background)]"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                  <item.Icon className="h-5 w-5" />
                </span>
                <h3 className="mt-5 flex items-center justify-between text-lg font-semibold">
                  {item.title}
                  <span
                    aria-hidden="true"
                    className="text-[var(--ink-faint)] transition-transform group-hover:translate-x-0.5 group-hover:text-[var(--accent)]"
                  >
                    →
                  </span>
                </h3>
                <p className="mt-2 text-sm leading-6 text-[var(--ink-muted)]">{item.body}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="border-y border-[var(--line)] bg-[var(--background)]">
        <div className="mx-auto w-full max-w-4xl px-4 py-16 text-center sm:px-6 lg:py-20">
          <h2 className="text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            Ask in the language you think in.
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-base leading-7 text-[var(--ink-muted)]">
            Chat in English or any of the 22 scheduled Indian languages. You can also speak your question and listen to
            the answer. Official Act and section names stay in their authoritative form.
          </p>
          <ul className="mt-8 flex flex-wrap justify-center gap-2" aria-label="Supported languages">
            {INDIAN_LANGUAGES.map((language) => (
              <li
                key={language.code}
                lang={language.bcp47}
                title={language.name}
                className="rounded-full border border-[var(--line)] bg-[var(--surface)] px-3.5 py-1.5 text-sm"
              >
                {language.nativeName}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="px-4 py-16 text-center sm:px-6 lg:py-24">
        <div className="mx-auto max-w-2xl">
          <h2 className="text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">
            Start with your question.
          </h2>
          <p className="mt-4 text-base leading-7 text-[var(--ink-muted)]">
            Describe your situation and see what the law says, with the sources next to it.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link href="/chat" className="btn-primary !min-h-12 !px-6 !text-[15px]">
              Start a conversation
            </Link>
            <Link href="/documents" className="btn-secondary !min-h-12 !px-6 !text-[15px]">
              Draft a document
            </Link>
          </div>
        </div>
      </section>

      <footer className="mt-auto border-t border-[var(--line)] bg-[var(--background)]">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 py-8 sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <div className="space-y-2">
            <BrandMark />
            <p className="max-w-md text-xs leading-5 text-[var(--ink-muted)]">
              Informational assistance only — not a substitute for a lawyer or court.
            </p>
          </div>
          <nav aria-label="Footer" className="flex flex-wrap gap-x-6 gap-y-2 text-sm">
            {[...TOP_LINKS, { href: "/signin", label: "Sign in" }].map((link) => (
              <Link key={link.href} href={link.href} className="text-[var(--ink-muted)] hover:text-[var(--foreground)]">
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </footer>
    </main>
  );
}
