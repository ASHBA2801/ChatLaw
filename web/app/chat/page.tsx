import Link from "next/link";

export default function ChatPage() {
  return (
    <main className="min-h-screen bg-white">
      <header className="border-b border-[var(--line)] px-5 py-5 sm:px-8">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <Link href="/" className="flex items-center gap-3 font-bold tracking-tight"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--forest)] text-sm text-[var(--lime)]">CL</span>ChatLaw</Link>
          <span className="text-xs font-semibold uppercase tracking-[0.14em] text-[var(--ink-muted)]">Early foundation</span>
        </div>
      </header>
      <section className="mx-auto flex min-h-[calc(100vh-82px)] max-w-5xl flex-col px-5 py-8 sm:px-8">
        <div className="flex items-start justify-between gap-4"><div><h1 className="text-2xl font-bold tracking-tight">Your legal questions, clarified.</h1><p className="mt-2 text-sm text-[var(--ink-muted)]">Chat is not connected yet. This is the initial experience.</p></div><span className="hidden rounded-full bg-[#fff4e5] px-3 py-1.5 text-xs font-semibold text-[#935a1e] sm:block">AI unavailable</span></div>
        <div className="my-8 flex flex-1 items-center justify-center rounded-3xl border border-dashed border-[var(--line)] bg-[var(--background)] px-6 py-16 text-center"><div className="max-w-sm"><div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--forest)] text-2xl text-[var(--lime)]">?</div><h2 className="mt-6 text-xl font-bold">Start with a question</h2><p className="mt-3 text-sm leading-6 text-[var(--ink-muted)]">Ask about a legal term, process, or right. AI responses will be available in a future phase.</p></div></div>
        <div className="rounded-2xl border border-[var(--line)] bg-white p-3 shadow-[0_12px_35px_rgba(23,73,54,0.08)]"><div className="flex items-center gap-3"><input disabled aria-label="Message input" placeholder="Type your question here..." className="min-w-0 flex-1 bg-transparent px-3 py-3 text-sm outline-none placeholder:text-[var(--ink-muted)] disabled:cursor-not-allowed" /><button type="button" disabled aria-label="Voice input unavailable" className="rounded-xl border border-[var(--line)] px-3 py-3 text-sm text-[var(--ink-muted)]" title="Voice input is not available yet">⌁ <span className="hidden sm:inline">Voice</span></button><select disabled aria-label="Language selector" defaultValue="English" className="hidden rounded-xl border border-[var(--line)] bg-white px-3 py-3 text-sm text-[var(--ink-muted)] sm:block"><option>English</option><option>Hindi — coming soon</option></select><button type="button" disabled className="rounded-xl bg-[var(--forest)] px-5 py-3 text-sm font-semibold text-white opacity-45" title="Sending is not available yet">Send</button></div></div>
        <p className="mt-4 text-center text-xs text-[var(--ink-muted)]">Language options, voice input, and AI answers will be added in later phases.</p>
      </section>
    </main>
  );
}
