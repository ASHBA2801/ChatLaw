import Link from "next/link";

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="paper-grid pointer-events-none absolute inset-0 opacity-70" />
      <nav className="relative mx-auto flex max-w-7xl items-center justify-between px-6 py-7 lg:px-10">
        <Link href="/" className="flex items-center gap-3 font-bold tracking-tight">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--forest)] text-sm text-[var(--lime)]">CL</span>
          <span className="text-lg">ChatLaw</span>
        </Link>
        <span className="hidden text-sm text-[var(--ink-muted)] sm:block">A clearer way to begin</span>
      </nav>
      <section className="relative mx-auto grid min-h-[calc(100vh-88px)] max-w-7xl items-center gap-16 px-6 pb-20 pt-10 lg:grid-cols-[1.1fr_0.9fr] lg:px-10 lg:pt-0">
        <div className="max-w-3xl">
          <p className="mb-7 flex items-center gap-3 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--forest)]"><span className="h-px w-10 bg-[var(--warm)]" />Indian legal information</p>
          <h1 className="max-w-3xl text-6xl font-bold leading-[0.98] tracking-[-0.055em] sm:text-7xl lg:text-[6.5rem]">Understand the law.<br /><span className="text-[var(--forest)]">Know your next step.</span></h1>
          <p className="mt-8 max-w-xl text-lg leading-8 text-[var(--ink-muted)]">Your multilingual AI assistant for understanding Indian law and legal rights.</p>
          <Link href="/chat" className="mt-10 inline-flex items-center gap-5 rounded-full bg-[var(--forest)] px-7 py-4 font-semibold text-white transition-transform hover:-translate-y-1">Start Chatting <span className="text-xl text-[var(--lime)]">↗</span></Link>
          <p className="mt-5 text-xs text-[var(--ink-muted)]">A starting point for information, not a substitute for professional advice.</p>
        </div>
        <div className="relative mx-auto w-full max-w-md lg:mr-5">
          <div className="absolute -right-5 -top-5 h-28 w-28 rounded-full bg-[var(--lime)]" />
          <div className="relative rounded-[2rem] border border-[var(--line)] bg-white/80 p-5 shadow-[0_24px_70px_rgba(23,73,54,0.12)] backdrop-blur">
            <div className="flex items-center justify-between border-b border-[var(--line)] pb-5"><span className="font-semibold">Ask ChatLaw</span><span className="rounded-full bg-[#eef5d0] px-3 py-1 text-xs font-semibold text-[var(--forest)]">Ready when you are</span></div>
            <div className="space-y-4 py-8"><div className="ml-auto max-w-[78%] rounded-2xl rounded-br-sm bg-[var(--forest)] px-4 py-3 text-sm leading-6 text-white">What does a legal notice mean?</div><div className="max-w-[86%] rounded-2xl rounded-bl-sm bg-[#edf2ec] px-4 py-3 text-sm leading-6 text-[var(--foreground)]">Start with the basics, in a language that works for you.</div></div>
            <div className="flex items-center gap-3 rounded-xl border border-[var(--line)] px-4 py-3 text-sm text-[var(--ink-muted)]">Type a question <span className="ml-auto text-lg text-[var(--forest)]">→</span></div>
          </div>
          <div className="absolute -bottom-8 -left-8 hidden rounded-2xl bg-[var(--warm)] px-5 py-4 text-sm font-semibold shadow-lg sm:block">Built for everyday questions.</div>
        </div>
      </section>
    </main>
  );
}
