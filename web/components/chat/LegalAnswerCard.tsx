"use client";



import Link from "next/link";

import { Children, ReactNode, useMemo, useState } from "react";

import ReactMarkdown from "react-markdown";

import remarkGfm from "remark-gfm";



import type { ChatResponse, Citation, InterviewState } from "@/lib/api/rag";

import {

  domainToDocumentTemplate,

  hasSimpleTermsSection,

  parseLegalAnswerSections,

} from "@/lib/chat/answerSections";

import { detectCaseIntent } from "@/lib/cases/intent";
import { searchOfficialJudgments } from "@/lib/cases/official-cases";
import { extractLegalIssues } from "@/lib/cases/query-understanding";

import AnswerPlaybackControls from "@/components/chat/AnswerPlaybackControls";

import CaseIntelligencePanel from "@/components/case-intelligence/CaseIntelligencePanel";

import type { UseAnswerPlaybackResult } from "@/lib/speech/useAnswerPlayback";

import { isSafeExternalUrl } from "@/lib/urls/safeUrl";



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

      className="mx-0.5 inline-flex min-h-7 items-center gap-1 rounded-sm border border-[var(--line)] bg-[var(--signal-soft)] px-2 py-0.5 align-baseline text-xs font-semibold text-[var(--signal)] hover:bg-[var(--signal-mid)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]"

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



function processInlineChildren(

  children: ReactNode,

  citations: Citation[],

  onOpen: (citation: Citation) => void,

): ReactNode {

  return Children.map(children, (child) => {

    if (typeof child === "string") {

      return renderCitationReferences(child, citations, onOpen);

    }

    if (typeof child === "number") {

      return renderCitationReferences(String(child), citations, onOpen);

    }

    return child;

  });

}



function markdownComponents(citations: Citation[], onOpenCitation: (citation: Citation) => void) {

  const process = (children: ReactNode) => processInlineChildren(children, citations, onOpenCitation);

  return {

    p: ({ children }: { children?: ReactNode }) => <p>{process(children)}</p>,

    li: ({ children }: { children?: ReactNode }) => <li>{process(children)}</li>,

    strong: ({ children }: { children?: ReactNode }) => <strong>{process(children)}</strong>,

    em: ({ children }: { children?: ReactNode }) => <em>{process(children)}</em>,

    td: ({ children }: { children?: ReactNode }) => <td>{process(children)}</td>,

    th: ({ children }: { children?: ReactNode }) => <th>{process(children)}</th>,

    a: ({ href, children }: { href?: string; children?: ReactNode }) => {

      const safe = isSafeExternalUrl(href);

      if (!safe) return <span>{process(children)}</span>;

      return (

        <a href={safe} target="_blank" rel="noreferrer">

          {process(children)}

        </a>

      );

    },

  };

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

  const components = useMemo(

    () => markdownComponents(citations, onOpenCitation),

    [citations, onOpenCitation],

  );



  return (

    <div className="space-y-3 text-[0.95rem] leading-7 [&_a]:font-medium [&_a]:text-[var(--forest)] [&_a]:underline [&_a]:underline-offset-2 [&_li]:ml-5 [&_li]:list-disc [&_ol>li]:list-decimal [&_strong]:font-semibold">

      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>

        {answer}

      </ReactMarkdown>

    </div>

  );

}



export function ClarificationCard({ content }: { content: string }) {

  return (

    <div className="rounded-sm border border-[var(--line)] bg-[var(--surface)] p-4">

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

    <div className="rounded-sm border border-[var(--line)] bg-[var(--surface)] p-4">

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



function getRelevanceBadgeClass(level: string): string {
  switch (level) {
    case "Highly relevant":
      return "bg-[#e8f5e9] text-[#1b5e20] border-[#a5d6a7]";
    case "Relevant":
      return "bg-[#e3f2fd] text-[#0d47a1] border-[#90caf9]";
    default:
      return "bg-[#f5f5f5] text-[#424242] border-[#e0e0e0]";
  }
}

function formatJudgmentDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" });
  } catch {
    return dateStr;
  }
}

export function LegalAnswerCard({

  messageId,

  content,

  response,

  priorUserText,

  onOpenCitation,

  onAskAnother,

  playback,

  chatMode,

  disabledPlayback,

}: {

  messageId: string;

  content: string;

  response: ChatResponse;

  priorUserText: string;

  onOpenCitation: (citation: Citation) => void;

  onAskAnother?: () => void;

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

  const queryText = interview?.original_query || priorUserText || "";
  const researchQuery = encodeURIComponent(queryText.slice(0, 200));
  const intentResult = useMemo(() => detectCaseIntent(queryText, false), [queryText]);
  const issueRep = useMemo(() => extractLegalIssues(queryText), [queryText]);
  const shouldConsiderCases = intentResult.requiresCases || issueRep.isDisputeScenario;
  const officialJudgments = useMemo(
    () => (shouldConsiderCases ? searchOfficialJudgments(queryText, { limit: 3 }) : []),
    [shouldConsiderCases, queryText],
  );
  const showFallback = intentResult.requiresCases && officialJudgments.length === 0;



  return (

    <div className="space-y-3">

      <div className="border border-[var(--line)] bg-[var(--surface)]">

        <div className="module-tab">Structured answer</div>

        <div className="space-y-4 p-3 sm:p-4">

      {visibleSections.length > 0 ? (

        visibleSections.map((section) => (

          <section key={`${section.id}-${section.title}`} className="space-y-2">

            <h3 className="text-sm font-bold text-[var(--signal)]">{section.title}</h3>

            <MarkdownBody answer={section.body} citations={response.citations} onOpenCitation={onOpenCitation} />

          </section>

        ))

      ) : (

        <MarkdownBody answer={content} citations={response.citations} onOpenCitation={onOpenCitation} />

      )}

        </div>

      </div>



      {officialJudgments.length > 0 ? (
        <div className="border-t border-[var(--line)] pt-4">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--ink-muted)]">
              Relevant Official Judgments
            </h3>
            <span className="text-[11px] font-medium text-[var(--forest)]">
              Official Indian Judiciary
            </span>
          </div>
          <ul className="mt-3 space-y-3">
            {officialJudgments.map((item) => {
              const sourceUrl = isSafeExternalUrl(item.source_url);
              const badgeClass = getRelevanceBadgeClass(item.relevance_level);
              return (
                <li key={item.id} className="rounded-sm border border-[var(--line)] bg-[var(--background)] p-3 sm:p-4 text-sm space-y-2.5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h4 className="font-semibold text-base">{item.title}</h4>
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold border ${badgeClass}`}>
                          {item.relevance_score}% · {item.relevance_level}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-[var(--ink-muted)]">
                        {item.court} · {formatJudgmentDate(item.judgment_date)} · {item.citation}
                      </p>
                    </div>
                    {sourceUrl ? (
                      <a
                        href={sourceUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="min-h-9 shrink-0 inline-flex items-center rounded-sm border border-[var(--line)] px-3 text-xs font-medium text-[var(--forest)] hover:border-[var(--forest)] bg-white"
                      >
                        Official judgment ↗
                      </a>
                    ) : null}
                  </div>

                  <div className="pt-2 text-xs space-y-1.5 border-t border-[var(--line)] text-[var(--ink)]">
                    <div>
                      <span className="font-semibold text-[var(--signal)]">Relevant issue: </span>
                      <span>{item.legal_issue}</span>
                    </div>
                    <div>
                      <span className="font-semibold text-[var(--signal)]">Relevant law: </span>
                      <span className="text-[var(--ink-muted)]">{item.relevant_law}</span>
                    </div>
                    <div>
                      <span className="font-semibold text-[var(--signal)]">Why this case is relevant: </span>
                      <span className="leading-5 text-[var(--ink-muted)]">{item.why_relevant}</span>
                    </div>
                    <div className="text-[11px] text-[var(--ink-muted)]">
                      <span className="font-medium">Source: </span>
                      <span>{item.source_authority}</span>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
          <Link
            href={`/research?q=${researchQuery}`}
            className="mt-3 inline-flex min-h-10 items-center text-sm font-semibold text-[var(--forest)] underline-offset-2 hover:underline"
          >
            View all in Research →
          </Link>
        </div>
      ) : showFallback ? (
        <div className="border-t border-[var(--line)] pt-4">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--ink-muted)]">
              Relevant cases
            </h3>
            <span className="text-[11px] font-medium text-[var(--ink-muted)]">Official Sources</span>
          </div>
          <p className="mt-2 text-xs text-[var(--ink-muted)] rounded-sm border border-[var(--line)] bg-[var(--background)] p-3">
            No sufficiently relevant judgment was found in the available official case-law sources.
          </p>
        </div>
      ) : null}



      {response.no_relevant_context ? (

        <div className="rounded-sm border border-[var(--line)] bg-[var(--background)] p-3 text-sm">

          <p className="font-medium">The indexed library does not cover this topic yet.</p>

          <ul className="mt-2 list-disc space-y-1 pl-5 text-[var(--ink-muted)]">

            <li>ChatLaw currently covers selected Central Indian legislation across criminal, civil, commercial, family, tax, environment, labour, IP, cyber, and consumer domains.</li>

            <li>Ask a section, offence, procedure, or describe your scenario in plain language.</li>

            <li>State-specific laws and case law are not fully indexed in this library.</li>

          </ul>

        </div>

      ) : null}



      <div className="flex flex-wrap gap-2 border-t border-[var(--line)] pt-4">

        {researchQuery ? (

          <Link

            href={`/research?q=${researchQuery}`}

            className="inline-flex min-h-10 items-center rounded-sm border border-[var(--line)] px-3 text-xs font-semibold"

          >

            Find relevant sources

          </Link>

        ) : null}

        {template ? (

          <Link

            href={`/documents/new?template=${template}`}

            className="inline-flex min-h-10 items-center rounded-sm border border-[var(--line)] px-3 text-xs font-semibold"

          >

            Create legal document

          </Link>

        ) : null}

        {canSimplify ? (

          <button

            type="button"

            onClick={() => setShowSimple(true)}

            className="min-h-10 rounded-sm border border-[var(--line)] px-3 text-xs font-semibold"

          >

            Explain more simply

          </button>

        ) : null}

        <button

          type="button"

          onClick={() => onAskAnother?.()}

          className="min-h-10 rounded-sm bg-[var(--forest)] px-3 text-xs font-semibold text-white"

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

