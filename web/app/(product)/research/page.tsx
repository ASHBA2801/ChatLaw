import ResearchWorkspace from "@/components/research/ResearchWorkspace";

export default async function ResearchPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string }>;
}) {
  const { q } = await searchParams;
  return (
    <section className="mx-auto w-full max-w-[1200px] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-semibold tracking-tight">Research</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--ink-muted)]">
          Search statute passages from the ChatLaw corpus and a curated set of landmark cases with verified citations.
          Case results are not exhaustive and are never invented.
        </p>
      </div>
      <ResearchWorkspace initialQuery={q ?? ""} />
    </section>
  );
}
