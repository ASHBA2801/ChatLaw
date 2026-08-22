"use client";

import Link from "next/link";
import { ReactNode, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import type { ChatResponse, Citation, InterviewState } from "@/lib/api/rag";
import { isCaseDocumentCitation } from "@/lib/api/rag";
import {
  domainToDocumentTemplate,
  hasSimpleTermsSection,
  parseLegalAnswerSections,
} from "@/lib/chat/answerSections";
import { searchLandmarkCases } from "@/lib/legal-data/landmarkCases";
import AnswerPlaybackControls from "@/components/chat/AnswerPlaybackControls";
import CaseIntelligencePanel from "@/components/case-intelligence/CaseIntelligencePanel";
import type { UseAnswerPlaybackResult } from "@/lib/speech/useAnswerPlayback";

function CitationReference({
  citation,
  onOpen,
}: {
  citation: Citation;
  onOpen: (citation: Citation) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onOpen(citation)}
      className="mx-0.5 inline-flex min-h-7 items-center gap-1 rounded-md border border-[var(--line)] bg-[#eef5d0] px-2 py-0.5 align-baseline text-xs font-semibold text-[var(--forest)] hover:bg-[#e5f0bd] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
      title={citation.document || "Source"}
      aria-label={`Open evidence for citation ${citation.id}`}
    >
      <span>[{citation.id}]</span>
    </button>
  );
}

function renderCitationReferences(
  text: string,
  citations: Citation[],
  onOpen: (citation: Citation) => void,
): ReactNode {
  const parts = text.split(/(\[(\d+)\])/g);
  return parts.map((part, index) => {
    const match = part.match(/^\[(\d+)\]$/);
    if (!match) return part;
    const citation = citations.find((item) => item.id === Number(match[1]));
    return citation ? <CitationReference key={`${citation.id}-${index}`} citation={citation} onOpen={onOpen} /> : part;
  });
}

function MarkdownBody({
  answer,
  citations,
  onOpenCitation,
}: {
  answer: string;
  citations: Citation[];
  onOpenCitation: (citation: Citation) => void;
}) {
  return (
    <div className="space-y-3 text-[0.95rem] leading-7 [&_a]:font-medium [&_a]:text-[var(--forest)] [&_a]:underline [&_a]:underline-offset-2 [&_li]:ml-5 [&_li]:list-disc [&_ol>li]:list-decimal [&_strong]:font-semibold">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          text: ({ children }) => <>{renderCitationReferences(String(children), citations, onOpenCitation)}</>,
        }}
      >
        {answer}
      </ReactMarkdown>
    </div>
  );
}

export function ClarificationCard({ content }: { content: string }) {
  return (
    <div className="rounded-2xl border border-[var(--line)] bg-[#fbfcf8] p-4">
      <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--forest)]">Need a bit more</p>
      <p className="mt-3 text-[0.95rem] leading-7">{content}</p>
      <p className="mt-3 text-xs text-[var(--ink-muted)]">Answer this so ChatLaw can retrieve the right legal sources.</p>
    </div>
  );
}

export function DocumentDraftCard({
  content,
  response,
  generating,
}: {
  content: string;
  response: ChatResponse;
  generating?: boolean;
}) {
  const kind = response.response_kind;
  const templateId = response.document_draft?.template_id;
  const title =
    kind === "document_ready"
      ? "Ready to draft"
      : kind === "document_unsupported"
        ? "Document type not supported"
        : "Document drafting";
  return (
    <div className="rounded-2xl border border-[var(--line)] bg-[#fbfcf8] p-4">
      <p className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--forest)]">{title}</p>
      <p className="mt-3 text-[0.95rem] leading-7">{content}</p>
      {kind === "document_clarification" ? (
        <p className="mt-3 text-xs text-[var(--ink-muted)]">
          Only required facts are asked before opening the document workspace. Jurisdiction will not be guessed.
        </p>
      ) : null}
      {kind === "document_ready" ? (
        <p className="mt-3 text-sm text-[var(--ink-muted)]">
          {generating ? "Generating your draft and opening the workspace…" : "Your editable draft workspace will open next."}
        </p>
      ) : null}
      {kind === "document_unsupported" && templateId ? (
        <Link href={`/documents/new?template=${templateId}`} className="mt-3 inline-flex min-h-11 items-center text-sm font-semibold text-[var(--forest)] underline-offset-2 hover:underline">
          Open document builder
        </Link>
      ) : null}
      {kind === "document_unsupported" && !templateId ? (
        <div className="mt-3 flex flex-wrap gap-3 text-sm">
          <Link href="/documents/new" className="font-semibold text-[var(--forest)] underline-offset-2 hover:underline">Browse templates</Link>
          <Link href="/research" className="font-semibold text-[var(--forest)] underline-offset-2 hover:underline">Open Research</Link>
        </div>
      ) : null}
    </div>
  );
}

export function LegalAnswerCard({
  messageId,
  content,
  response,
  priorUserText,
  onOpenCitation,
  playback,
  chatMode,
  disabledPlayback,
}: {
  messageId: string;
  content: string;
  response: ChatResponse;
  priorUserText: string;
  onOpenCitation: (citation: Citation) => void;
  playback: UseAnswerPlaybackResult;
  chatMode: "text" | "voice";
  disabledPlayback: boolean;
}) {
  const sections = useMemo(() => parseLegalAnswerSections(content), [content]);
  const [showSimple, setShowSimple] = useState(false);
  const canSimplify = hasSimpleTermsSection(sections);
  const visibleSections = sections.filter((section) => section.id !== "simple" || showSimple);
  const interview = response.interview as InterviewState | null | undefined;
  const template = domainToDocumentTemplate(interview?.domain);
  const researchQuery = encodeURIComponent((interview?.original_query || priorUserText || "").slice(0, 200));
  const landmarkCases = useMemo(
    () => searchLandmarkCases(interview?.original_query || priorUserText || "", 3),
    [interview?.original_query, priorUserText],
  );

  return (
    <div className="space-y-4">
      {visibleSections.length > 0 ? (
        visibleSections.map((section) => (
          <section key={`${section.id}-${section.title}`} className="space-y-2">
            <h3 className="text-sm font-semibold text-[var(--forest)]">{section.title}</h3>
            <MarkdownBody answer={section.body} citations={response.citations} onOpenCitation={onOpenCitation} />
          </section>
        ))
      ) : (
        <MarkdownBody answer={content} citations={response.citations} onOpenCitation={onOpenCitation} />
      )}

      {response.has_context && response.citations.length > 0 ? (
        <div className="border-t border-[var(--line)] pt-4">
          <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--ink-muted)]">Sources</h3>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {response.citations.map((citation) => (
              <button
                key={`${citation.id}-${citation.chunk_id}`}
                type="button"
                onClick={() => onOpenCitation(citation)}
                className="rounded-xl border border-[var(--line)] bg-white px-3 py-3 text-left text-xs hover:border-[var(--forest)]"
              >
                <p className="font-semibold">
                  [{citation.id}]{" "}
                  {isCaseDocumentCitation(citation) ? "Case Document" : citation.document || "Source"}
                </p>
                <p className="mt-1 text-[var(--ink-muted)]">
                  {citation.section ? `Section ${citation.section}` : citation.page != null ? `Page ${citation.page}` : "Passage"}
                </p>
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {landmarkCases.length > 0 ? (
        <div className="border-t border-[var(--line)] pt-4">
          <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--ink-muted)]">Relevant cases</h3>
          <ul className="mt-3 space-y-2">
            {landmarkCases.map((item) => (
              <li key={item.id} className="rounded-xl border border-[var(--line)] bg-[var(--background)] px-3 py-3 text-sm">
                <p className="font-semibold">{item.title}</p>
                <p className="mt-1 text-xs text-[var(--ink-muted)]">
                  {item.court} · {item.year} · {item.citation}
                </p>
                <p className="mt-2 text-xs leading-5 text-[var(--ink-muted)]">{item.why_relevant}</p>
              </li>
            ))}
          </ul>
          <Link
            href={`/research?q=${researchQuery}`}
            className="mt-3 inline-flex min-h-10 items-center text-sm font-semibold text-[var(--forest)] underline-offset-2 hover:underline"
          >
            View all in Research →
          </Link>
        </div>
      ) : response.has_context && response.citations.length > 0 ? (
        <div className="border-t border-[var(--line)] pt-4">
          <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--ink-muted)]">Relevant sources</h3>
          <ul className="mt-3 space-y-2">
            {response.citations.slice(0, 3).map((citation) => {
              const courtLike = citation.source?.source_type === "court";
              return (
                <li key={`rel-${citation.id}`} className="rounded-xl border border-[var(--line)] bg-[var(--background)] px-3 py-3 text-sm">
                  <p className="font-semibold">{citation.document || "Legal source"}</p>
                  <p className="mt-1 text-xs text-[var(--ink-muted)]">
                    {courtLike ? "Court-related source" : "Statute / legal source"}
                    {citation.section ? ` · Section ${citation.section}` : ""}
                  </p>
                </li>
              );
            })}
          </ul>
          <Link
            href={`/research?q=${researchQuery}`}
            className="mt-3 inline-flex min-h-10 items-center text-sm font-semibold text-[var(--forest)] underline-offset-2 hover:underline"
          >
            View in Research →
          </Link>
        </div>
      ) : null}

      {response.no_relevant_context ? (
        <div className="rounded-lg border border-[var(--line)] bg-[var(--background)] p-3 text-sm">
          <p className="font-medium">I couldn&apos;t find sufficiently relevant legal sources for this question.</p>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-[var(--ink-muted)]">
            <li>Add your state or city if location matters.</li>
            <li>Name the document or Act if you know it.</li>
            <li>Try Research for keyword search across the corpus.</li>
          </ul>
        </div>
      ) : null}

      <div className="flex flex-wrap gap-2 border-t border-[var(--line)] pt-4">
        {response.has_context ? (
          <button
            type="button"
            onClick={() => {
              const first = response.citations[0];
              if (first) onOpenCitation(first);
            }}
            className="min-h-10 rounded-full border border-[var(--line)] px-3 text-xs font-semibold"
          >
            View sources
          </button>
        ) : null}
        <Link
          href={`/research?q=${researchQuery}`}
          className="inline-flex min-h-10 items-center rounded-full border border-[var(--line)] px-3 text-xs font-semibold"
        >
          Find relevant sources
        </Link>
        {template ? (
          <Link
            href={`/documents/new?template=${template}`}
            className="inline-flex min-h-10 items-center rounded-full border border-[var(--line)] px-3 text-xs font-semibold"
          >
            Create legal document
          </Link>
        ) : null}
        {canSimplify ? (
          <button
            type="button"
            onClick={() => setShowSimple(true)}
            className="min-h-10 rounded-full border border-[var(--line)] px-3 text-xs font-semibold"
          >
            Explain more simply
          </button>
        ) : null}
        <button
          type="button"
          onClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" })}
          className="min-h-10 rounded-full bg-[var(--forest)] px-3 text-xs font-semibold text-white"
        >
          Ask another question
        </button>
      </div>

      {response.has_context ? <CaseIntelligencePanel query={priorUserText} /> : null}

      {chatMode === "text" ? (
        <AnswerPlaybackControls
          messageId={messageId}
          text={content}
          status={playback.status}
          activeMessageId={playback.activeMessageId}
          supported={playback.supported}
          disabled={disabledPlayback}
          onPlay={playback.play}
          onPause={playback.pause}
          onResume={playback.resume}
          onStop={playback.stop}
        />
      ) : null}
    </div>
  );
}
