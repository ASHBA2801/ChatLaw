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
import { searchLandmarkCases } from "@/lib/legal-data/landmarkCases";

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
  const landmarkCases = useMemo(
    () => (intentResult.requiresCases ? searchLandmarkCases(queryText, 3, 2) : []),
    [intentResult.requiresCases, queryText],
  );



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



      {landmarkCases.length > 0 ? (

        <div className="border-t border-[var(--line)] pt-4">

          <h3 className="text-xs font-bold uppercase tracking-[0.14em] text-[var(--ink-muted)]">Relevant cases</h3>

          <ul className="mt-3 space-y-2">

            {landmarkCases.map((item) => {

              const sourceUrl = isSafeExternalUrl(item.source_url);

              return (

                <li key={item.id} className="rounded-sm border border-[var(--line)] bg-[var(--background)] px-3 py-3 text-sm">

                  <div className="flex flex-wrap items-start justify-between gap-3">

                    <div className="min-w-0">

                      <p className="font-semibold">{item.title}</p>

                      <p className="mt-1 text-xs text-[var(--ink-muted)]">

                        {item.court} · {item.year} · {item.citation}

                      </p>

                    </div>

                    {sourceUrl ? (

                      <a

                        href={sourceUrl}

                        target="_blank"

                        rel="noreferrer"

                        className="min-h-10 shrink-0 rounded-sm border border-[var(--line)] px-3 text-xs font-medium text-[var(--forest)] hover:border-[var(--forest)]"

                      >

                        Open source

                      </a>

                    ) : null}

                  </div>

                  <p className="mt-2 text-xs leading-5 text-[var(--ink-muted)]">{item.why_relevant}</p>

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

