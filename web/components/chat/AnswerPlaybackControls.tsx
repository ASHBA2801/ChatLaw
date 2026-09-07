"use client";

import type { AnswerPlaybackStatus } from "@/lib/speech/useAnswerPlayback";
import { PlayIcon } from "@/components/chat/ChatIcons";
export interface AnswerPlaybackControlsProps {
  messageId: string;
  text: string;
  status: AnswerPlaybackStatus;
  activeMessageId: string | null;
  supported: boolean;
  disabled?: boolean;
  onPlay: (messageId: string, text: string) => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
}

export default function AnswerPlaybackControls({
  messageId,
  text,
  status,
  activeMessageId,
  supported,
  disabled = false,
  onPlay,
  onPause,
  onResume,
  onStop,
}: AnswerPlaybackControlsProps) {
  const isActive = activeMessageId === messageId;
  const isSpeaking = isActive && status === "speaking";
  const isPaused = isActive && status === "paused";

  if (!supported) {
    return (
      <p className="mt-2 text-xs text-[var(--ink-muted)]">Voice playback isn&apos;t available.</p>
    );
  }

  return (
    <div className="mt-3 flex flex-wrap items-center gap-2" aria-label="Answer playback controls">
      {!isSpeaking && !isPaused && (
        <button
          type="button"
          onClick={() => onPlay(messageId, text)}
          disabled={disabled || !text.trim()}
          className="inline-flex min-h-10 items-center gap-1.5 rounded-sm border border-[var(--line)] px-3 text-xs font-medium text-[var(--foreground)] hover:border-[var(--forest)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)] disabled:opacity-50"
          aria-label="Play answer"
        >
          <PlayIcon className="h-3.5 w-3.5" />
          Listen
        </button>
      )}
      {isSpeaking && (
        <>
          <span className="text-xs font-medium text-[var(--forest)]" aria-live="polite">
            Speaking…
          </span>
          <button
            type="button"
            onClick={onPause}
            className="min-h-10 rounded-sm border border-[var(--line)] px-3 text-xs font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
            aria-label="Pause answer"
          >
            Pause
          </button>
          <button
            type="button"
            onClick={onStop}
            className="min-h-10 rounded-sm border border-[var(--line)] px-3 text-xs font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
            aria-label="Stop speech"
          >
            Stop
          </button>
        </>
      )}
      {isPaused && (
        <>
          <span className="text-xs font-medium text-[var(--ink-muted)]" aria-live="polite">
            Paused
          </span>
          <button
            type="button"
            onClick={onResume}
            className="min-h-10 rounded-sm border border-[var(--line)] px-3 text-xs font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
            aria-label="Resume answer"
          >
            Resume
          </button>
          <button
            type="button"
            onClick={onStop}
            className="min-h-10 rounded-sm border border-[var(--line)] px-3 text-xs font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--warm)]"
            aria-label="Stop speech"
          >
            Stop
          </button>
        </>
      )}
    </div>
  );
}
