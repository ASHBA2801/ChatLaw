import Link from "next/link";

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="paper-grid pointer-events-none absolute inset-0 opacity-70" />
      <nav className="relative mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-7 lg:px-10">
        <Link href="/" className="flex items-center gap-3 font-bold tracking-tight">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--forest)] text-sm text-[var(--lime)]">CL</span>
          <span className="text-lg">ChatLaw</span>
        </Link>
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <Link href="/chat" className="text-[var(--ink-muted)] hover:text-[var(--foreground)]">
            Chat
          </Link>
          <Link href="/documents" className="text-[var(--ink-muted)] hover:text-[var(--foreground)]">
            Documents
          </Link>
          <Link href="/cases" className="text-[var(--ink-muted)] hover:text-[var(--foreground)]">
            Cases
          </Link>
          <Link href="/research" className="text-[var(--ink-muted)] hover:text-[var(--foreground)]">
            Research
          </Link>
        </div>
      </nav>
      <section className="relative mx-auto grid min-h-[calc(100vh-88px)] max-w-7xl items-center gap-16 px-6 pb-20 pt-10 lg:grid-cols-[1.1fr_0.9fr] lg:px-10 lg:pt-0">
        <div className="max-w-3xl">
          <p className="mb-7 flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--forest)]">
            <span className="h-px w-10 bg-[var(--warm)]" />
            Understand Indian law in your own language
          </p>
          <h1 className="max-w-3xl text-5xl font-bold leading-[0.98] tracking-[-0.055em] sm:text-6xl lg:text-[5.5rem]">
            ChatLaw
            <br />
            <span className="text-[var(--forest)]">Your legal assistant.</span>
          </h1>
          <p className="mt-8 max-w-xl text-lg leading-8 text-[var(--ink-muted)]">
            Describe your situation in English or an Indian language. ChatLaw asks focused follow-ups, then explains the
            law in plain language with sources you can check.
          </p>
          <div className="mt-10 flex flex-wrap gap-3">
            <Link
              href="/chat"
              className="inline-flex items-center gap-5 rounded-full bg-[var(--forest)] px-7 py-4 font-semibold text-white transition-transform hover:-translate-y-1"
            >
              Start with Chat <span className="text-xl text-[var(--lime)]">↗</span>
            </Link>
            <Link
              href="/research"
              className="inline-flex items-center rounded-full border border-[var(--line)] bg-white px-7 py-4 font-semibold text-[var(--forest)]"
            >
              Search sources
            </Link>
            <Link
              href="/documents"
              className="inline-flex items-center rounded-full border border-[var(--line)] bg-white px-7 py-4 font-semibold text-[var(--forest)]"
            >
              Draft a document
            </Link>
          </div>
          <p className="mt-5 text-xs text-[var(--ink-muted)]">
            Informational assistance only — not a substitute for a lawyer or court.
          </p>
        </div>
        <div className="relative mx-auto w-full max-w-md lg:mr-5">
          <div className="absolute -right-5 -top-5 h-28 w-28 rounded-full bg-[var(--lime)]" />
          <div className="relative rounded-[2rem] border border-[var(--line)] bg-white/80 p-5 shadow-[0_24px_70px_rgba(23,73,54,0.12)] backdrop-blur">
            <div className="flex items-center justify-between border-b border-[var(--line)] pb-5">
              <span className="font-semibold">Guided legal chat</span>
              <span className="rounded-full bg-[#eef5d0] px-3 py-1 text-xs font-semibold text-[var(--forest)]">22+ languages</span>
            </div>
            <div className="space-y-4 py-8">
              <div className="ml-auto max-w-[78%] rounded-2xl rounded-br-sm bg-[var(--forest)] px-4 py-3 text-sm leading-6 text-white">
                My landlord is refusing to return my deposit.
              </div>
              <div className="max-w-[86%] rounded-2xl rounded-bl-sm bg-[#edf2ec] px-4 py-3 text-sm leading-6 text-[var(--foreground)]">
                Which state are you in, and has the tenancy ended?
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-xl border border-[var(--line)] px-4 py-3 text-sm text-[var(--ink-muted)]">
              Chat · Documents · Cases · Research
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
