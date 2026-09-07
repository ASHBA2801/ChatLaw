"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import DocumentBuilder from "./DocumentBuilder";
import {
  askLegalQuestion,
  ChatResponse,
  createConversation,
  DocumentDraftState,
  sendConversationMessage,
} from "@/lib/api/rag";
import { getTemplate, listTemplates } from "@/lib/documents/templates";
import type { DocumentValues, TemplateSpec } from "@/lib/documents/types";
import { validateValues } from "@/lib/documents/validation";
import { useLanguage } from "@/lib/i18n/LanguageProvider";
import {
  AudioRecorderSession,
  isAudioRecordingSupported,
  transcribeAudio,
  SpeechOutputSession,
  chatLanguageToSpeechCode,
} from "@/lib/speech";

interface MessageItem {
  id: string;
  role: "user" | "assistant";
  content: string;
  draftState?: DocumentDraftState | null;
}

export default function ConversationalDrafting() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { language } = useLanguage();

  const initialPrompt = searchParams.get("prompt") || "";
  const initialCategory = searchParams.get("category") || "";
  const initialTemplateParam = searchParams.get("template") || "";

  const [mode, setMode] = useState<"conversational" | "form">("conversational");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Voice drafting states
  const [isRecording, setIsRecording] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState<string | null>(null);
  const [autoSpeakQuestions, setAutoSpeakQuestions] = useState(true);
  const recorderRef = useRef<AudioRecorderSession | null>(null);
  const outputSessionRef = useRef<SpeechOutputSession | null>(null);
  const speechLang = useMemo(() => chatLanguageToSpeechCode(language), [language]);

  // Progressive draft state
  const [currentDraft, setCurrentDraft] = useState<DocumentDraftState | null>(null);

  // Auto-scroll chat window
  const chatBottomRef = useRef<HTMLDivElement>(null);
  const hasInitialized = useRef(false);

  // Current template if identified
  const activeTemplate: TemplateSpec | null = useMemo(() => {
    const tId = currentDraft?.template_id || initialTemplateParam;
    if (!tId) return null;
    try {
      return getTemplate(tId);
    } catch {
      return null;
    }
  }, [currentDraft?.template_id, initialTemplateParam]);

  // Client-side validation of currently accumulated values
  const validation = useMemo(() => {
    if (!activeTemplate) return null;
    return validateValues(activeTemplate, currentDraft?.values || {});
  }, [activeTemplate, currentDraft?.values]);

  const canGenerate = Boolean(
    activeTemplate && (validation?.canGenerate || currentDraft?.round && currentDraft.round > 0),
  );

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  // Initial prompt handling on mount
  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    if (initialPrompt.trim()) {
      void sendPrompt(initialPrompt.trim());
    } else if (initialTemplateParam) {
      try {
        const tmpl = getTemplate(initialTemplateParam);
        setCurrentDraft({
          mode: "document_drafting",
          template_id: tmpl.id,
          values: { jurisdiction_country: "IN" },
        });
        setMessages([
          {
            id: "welcome",
            role: "assistant",
            content: `I'm ready to draft a **${tmpl.title}**. Please describe the key details: parties, property/work description, amounts, and dates.`,
          },
        ]);
      } catch {
        // Fall back to clean state
      }
    }
  }, []);

  useEffect(() => {
    outputSessionRef.current = new SpeechOutputSession({
      onStart: () => {},
      onEnd: () => setIsSpeaking(null),
      onPause: () => {},
      onResume: () => {},
      onError: () => setIsSpeaking(null),
    });

    return () => {
      recorderRef.current?.cancel();
      outputSessionRef.current?.dispose();
    };
  }, []);

  function speakMessage(id: string, text: string) {
    if (isSpeaking === id) {
      outputSessionRef.current?.stop();
      setIsSpeaking(null);
      return;
    }
    setIsSpeaking(id);
    outputSessionRef.current?.speak(text, speechLang);
  }

  async function toggleRecording() {
    if (isRecording) {
      setIsRecording(false);
      setBusy(true);
      try {
        const recordingResult = await recorderRef.current?.stop();
        if (recordingResult?.blob && recordingResult.blob.size > 0) {
          const stt = await transcribeAudio(recordingResult.blob, speechLang);
          if (stt.transcript) {
            setInputMessage(stt.transcript);
            void sendPrompt(stt.transcript);
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Voice input error.");
      } finally {
        setBusy(false);
      }
      return;
    }

    if (!isAudioRecordingSupported()) {
      setError("Microphone recording is not supported on this device/browser.");
      return;
    }

    outputSessionRef.current?.stop();
    setIsSpeaking(null);
    setError(null);

    const recorder = new AudioRecorderSession({
      onStart: () => setIsRecording(true),
      onError: (msg) => {
        setIsRecording(false);
        setError(msg);
      },
    });
    recorderRef.current = recorder;
    await recorder.start();
  }

  async function sendPrompt(textToSend: string) {
    if (!textToSend.trim() || busy) return;
    setError(null);
    setBusy(true);

    const userMsgId = `user-${Date.now()}`;
    const userMsg: MessageItem = {
      id: userMsgId,
      role: "user",
      content: textToSend,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");

    try {
      let convId = conversationId;
      let response: ChatResponse;

      if (!convId) {
        try {
          const conv = await createConversation();
          convId = conv.id;
          setConversationId(conv.id);
          const convRes = await sendConversationMessage(conv.id, {
            message: textToSend,
            language,
          });
          response = convRes;
        } catch {
          // If conversation creation fails, fall back to standalone chat
          response = await askLegalQuestion({
            message: textToSend,
            language,
          });
        }
      } else {
        const convRes = await sendConversationMessage(convId, {
          message: textToSend,
          language,
        });
        response = convRes;
      }

      const assistantMsg: MessageItem = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.message || response.answer,
        draftState: response.document_draft,
      };

      setMessages((prev) => [...prev, assistantMsg]);

      // Spoken question output
      const assistantText = response.message || response.answer;
      if (autoSpeakQuestions && assistantText) {
        outputSessionRef.current?.speak(assistantText, speechLang);
        setIsSpeaking(assistantMsg.id);
      }

      if (response.document_draft) {
        setCurrentDraft(response.document_draft);

        // If ready, user can either generate or review
        if (response.response_kind === "document_ready") {
          // The draft state is ready for one-click generation
        }
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not connect to ChatLaw drafting engine. Please check your network and try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleGenerateDocument() {
    if (!activeTemplate) return;
    setGenerating(true);
    setError(null);

    const valuesToSubmit: DocumentValues = {
      ...(currentDraft?.values || {}),
      jurisdiction_country: "IN",
      draft_language: language,
    };

    try {
      const response = await fetch("/api/documents", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          templateId: activeTemplate.id,
          values: valuesToSubmit,
          conversationId,
        }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(
          payload.error || "Generation stopped because required information is missing.",
        );
      }

      router.push(`/documents/${payload.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Document generation failed.");
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* View Toggle Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--line)] pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">
            New Legal Document
          </h1>
          <p className="mt-1 text-sm text-[var(--ink-muted)]">
            Draft an authentic Indian legal document conversationally, or switch to the structured form.
          </p>
        </div>

        <div className="flex rounded-sm border border-[var(--line)] bg-[var(--module-fill)] p-1">
          <button
            type="button"
            onClick={() => setMode("conversational")}
            className={`rounded-xs px-3.5 py-1.5 text-xs font-medium transition-colors ${
              mode === "conversational"
                ? "bg-white text-[var(--foreground)] shadow-xs"
                : "text-[var(--ink-muted)] hover:text-[var(--foreground)]"
            }`}
          >
            💬 Conversational Drafter
          </button>
          <button
            type="button"
            onClick={() => setMode("form")}
            className={`rounded-xs px-3.5 py-1.5 text-xs font-medium transition-colors ${
              mode === "form"
                ? "bg-white text-[var(--foreground)] shadow-xs"
                : "text-[var(--ink-muted)] hover:text-[var(--foreground)]"
            }`}
          >
            📋 Manual Form
          </button>
        </div>
      </div>

      {mode === "form" ? (
        <DocumentBuilder />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
          {/* Main Conversational Thread */}
          <div className="flex min-h-[580px] flex-col rounded-sm border border-[var(--line)] bg-white shadow-xs">
            {/* Thread Header */}
            <div className="border-b border-[var(--line)] px-5 py-3.5 flex items-center justify-between bg-[var(--module-fill)]">
              <div className="flex items-center gap-2">
                <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-600 animate-pulse" />
                <span className="text-xs font-semibold text-[var(--foreground)]">
                  ChatLaw Legal Drafting Engine
                </span>
              </div>
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-1.5 text-xs text-[var(--ink-muted)] cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoSpeakQuestions}
                    onChange={(e) => setAutoSpeakQuestions(e.target.checked)}
                    className="h-3.5 w-3.5 rounded border-[var(--line)] text-[var(--forest)]"
                  />
                  <span>🔊 Spoken questions</span>
                </label>
                {activeTemplate && (
                  <span className="rounded-xs bg-white px-2 py-0.5 text-xs font-medium text-[var(--forest)] border border-[var(--line)]">
                    {activeTemplate.documentType}
                  </span>
                )}
              </div>
            </div>

            {/* Messages Scroll Area */}
            <div className="flex-1 space-y-4 overflow-y-auto p-5">
              {messages.length === 0 ? (
                <div className="py-12 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[var(--module-fill)] text-2xl">
                    ⚖️
                  </div>
                  <h3 className="mt-3 text-base font-semibold text-[var(--foreground)]">
                    Describe what legal document you need
                  </h3>
                  <p className="mx-auto mt-1 max-w-md text-xs leading-5 text-[var(--ink-muted)]">
                    Provide the parties, terms, amounts, dates, and place in natural language or voice. ChatLaw will extract the facts and only ask for whatever is missing.
                  </p>
                </div>
              ) : (
                messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-sm p-4 text-sm leading-relaxed ${
                        msg.role === "user"
                          ? "bg-[var(--forest)] text-white"
                          : "border border-[var(--line)] bg-[var(--canvas)] text-[var(--foreground)] whitespace-pre-wrap"
                      }`}
                    >
                      {msg.content}
                    </div>
                    {msg.role === "assistant" && (
                      <div className="mt-1 flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => speakMessage(msg.id, msg.content)}
                          className="text-xs font-medium text-[var(--forest)] hover:underline flex items-center gap-1"
                          aria-label={isSpeaking === msg.id ? "Stop reading" : "Read aloud"}
                        >
                          <span>{isSpeaking === msg.id ? "⏹️ Stop" : "🔊 Listen"}</span>
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}

              {busy && (
                <div className="flex justify-start">
                  <div className="rounded-sm border border-[var(--line)] bg-[var(--canvas)] px-4 py-3 text-xs text-[var(--ink-muted)] flex items-center gap-2">
                    <span className="inline-block h-2 w-2 rounded-full bg-[var(--forest)] animate-bounce" />
                    Analyzing legal requirements & extracting terms...
                  </div>
                </div>
              )}

              <div ref={chatBottomRef} />
            </div>

            {/* Input Box with Voice & Text */}
            <div className="border-t border-[var(--line)] p-4 bg-white">
              {error && (
                <div className="mb-3 rounded-xs border border-red-200 bg-red-50 p-2.5 text-xs text-red-700">
                  {error}
                </div>
              )}

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void sendPrompt(inputMessage);
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder={
                    activeTemplate
                      ? "Reply with missing details (or use microphone)..."
                      : "e.g. Rental agreement for Coimbatore flat at ₹18,000/mo..."
                  }
                  disabled={busy || generating}
                  className="flex-1 rounded-sm border border-[var(--line)] bg-[var(--canvas)] px-3.5 py-2.5 text-sm text-[var(--foreground)] placeholder:text-[var(--ink-muted)] focus:border-[var(--forest)] focus:bg-white focus:outline-none"
                />
                <button
                  type="button"
                  onClick={toggleRecording}
                  disabled={busy || generating}
                  className={`min-h-10 rounded-sm px-3.5 py-2 text-sm font-semibold transition-colors flex items-center gap-1.5 ${
                    isRecording
                      ? "bg-red-600 text-white animate-pulse"
                      : "border border-[var(--line)] bg-[var(--canvas)] text-[var(--foreground)] hover:border-[var(--forest)]"
                  }`}
                  title={isRecording ? "Stop recording" : "Speak your answers"}
                  aria-label={isRecording ? "Stop voice recording" : "Start voice recording"}
                >
                  <span>{isRecording ? "⏹️" : "🎙️"}</span>
                  <span className="hidden sm:inline">{isRecording ? "Done" : "Voice"}</span>
                </button>
                <button
                  type="submit"
                  disabled={busy || !inputMessage.trim() || generating}
                  className="rounded-sm bg-[var(--forest)] px-5 py-2.5 text-sm font-semibold text-white hover:opacity-95 disabled:opacity-50"
                >
                  Send
                </button>
              </form>
            </div>
          </div>

          {/* Right Sidebar: Extracted Legal Slots & Generation Control */}
          <div className="space-y-4">
            <div className="rounded-sm border border-[var(--line)] bg-white p-5 shadow-xs">
              <h3 className="text-sm font-semibold text-[var(--foreground)] border-b border-[var(--line)] pb-2.5">
                Draft Specification
              </h3>

              {activeTemplate ? (
                <div className="mt-3.5 space-y-3.5">
                  <div>
                    <span className="text-xs uppercase tracking-wider text-[var(--ink-muted)] font-medium">
                      Identified Model
                    </span>
                    <p className="mt-0.5 text-sm font-semibold text-[var(--foreground)]">
                      {activeTemplate.title}
                    </p>
                    {activeTemplate.source && (
                      <p className="mt-0.5 text-xs text-[var(--forest)]">
                        Model: {activeTemplate.source.authority}
                      </p>
                    )}
                  </div>

                  <div>
                    <span className="text-xs uppercase tracking-wider text-[var(--ink-muted)] font-medium">
                      Jurisdiction
                    </span>
                    <p className="mt-0.5 text-xs text-[var(--foreground)]">
                      India — {currentDraft?.values?.jurisdiction_region || "Generic India"}
                    </p>
                  </div>

                  {/* Recorded parameters summary */}
                  <div>
                    <span className="text-xs uppercase tracking-wider text-[var(--ink-muted)] font-medium">
                      Recorded Parameters
                    </span>
                    <div className="mt-1.5 space-y-1.5 max-h-48 overflow-y-auto text-xs">
                      {Object.entries(currentDraft?.values || {})
                        .filter(([k, v]) => Boolean(v) && k !== "jurisdiction_country" && k !== "draft_language")
                        .map(([k, v]) => {
                          const field = activeTemplate.fields.find((f) => f.id === k);
                          const label = field?.label || k.replace(/_/g, " ");
                          return (
                            <div key={k} className="flex justify-between rounded-xs bg-[var(--canvas)] p-2">
                              <span className="font-medium text-[var(--foreground)]">{label}:</span>
                              <span className="text-[var(--ink-muted)] truncate max-w-[140px] text-right">
                                {typeof v === "number" && (k.includes("rent") || k.includes("deposit") || k.includes("salary") || k.includes("price") || k.includes("amount"))
                                  ? `₹${v.toLocaleString("en-IN")}`
                                  : String(v)}
                              </span>
                            </div>
                          );
                        })}
                    </div>
                  </div>

                  {/* Required Checklist Status */}
                  <div className="pt-2 border-t border-[var(--line)]">
                    <span className="text-xs uppercase tracking-wider text-[var(--ink-muted)] font-medium">
                      Draft Completeness
                    </span>
                    {validation && (
                      <div className="mt-2 space-y-1.5">
                        <div className="flex items-center justify-between text-xs">
                          <span>Required items:</span>
                          <span className={validation.canGenerate ? "font-semibold text-emerald-700" : "font-semibold text-amber-700"}>
                            {validation.canGenerate
                              ? "Ready to draft"
                              : `${validation.blocking.length} missing`}
                          </span>
                        </div>
                        {validation.blocking.length > 0 && (
                          <div className="mt-1 space-y-1 text-xs text-amber-800 bg-amber-50 rounded-xs p-2">
                            <span className="font-medium">Needed:</span>
                            {validation.blocking.slice(0, 3).map((b) => (
                              <p key={b.fieldId}>• {b.message}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* One-Click Generate CTA */}
                  <div className="pt-3">
                    <button
                      type="button"
                      onClick={() => void handleGenerateDocument()}
                      disabled={generating || busy}
                      className="w-full flex items-center justify-center gap-2 rounded-sm bg-[var(--forest)] py-3 px-4 text-sm font-semibold text-white shadow-xs hover:opacity-95 disabled:opacity-50"
                    >
                      {generating ? (
                        <>
                          <span className="inline-block h-3 w-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                          Generating Draft...
                        </>
                      ) : (
                        "✨ Generate Legal Document Draft"
                      )}
                    </button>
                    <p className="mt-2 text-center text-xs text-[var(--ink-muted)]">
                      Opens in full A4 editor with clause tools
                    </p>
                  </div>
                </div>
              ) : (
                <div className="mt-6 py-6 text-center text-xs text-[var(--ink-muted)]">
                  Enter your document description to identify the template and view captured legal parameters.
                </div>
              )}
            </div>

            {/* Legal Safety Notice */}
            <div className="rounded-sm border border-[var(--line)] bg-[var(--module-fill)] p-4 text-xs leading-5 text-[var(--ink-muted)]">
              <span className="font-medium text-[var(--foreground)]">Legal Notice:</span> AI-assisted drafts provide structural models under Indian law. They are not legal advice and do not constitute an official court filing.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
