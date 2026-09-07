import type { VoiceChatState } from "./types";

/** Whether voice listening may begin without an existing conversation id. */
export function canStartVoiceListening(
  conversationId: string | null,
  allowWithoutConversation: boolean,
): boolean {
  return Boolean(conversationId) || allowWithoutConversation;
}

/** Valid voice chat transitions — mutually exclusive active phases. */
export function canTransition(from: VoiceChatState, to: VoiceChatState): boolean {
  if (from === to) return true;
  if (to === "error") return from !== "error";
  if (to === "idle") {
    return from !== "idle";
  }

  const allowed: Record<VoiceChatState, VoiceChatState[]> = {
    idle: ["listening", "speaking", "error"],
    listening: ["transcribing", "idle", "error"],
    transcribing: ["ready_to_send", "idle", "error"],
    ready_to_send: ["thinking", "listening", "idle", "error"],
    thinking: ["speaking", "idle", "error"],
    speaking: ["idle", "paused", "listening", "error"],
    paused: ["speaking", "idle", "listening", "error"],
    error: ["idle", "listening"],
  };

  return allowed[from]?.includes(to) ?? false;
}

export function voiceStateLabel(state: VoiceChatState): string {
  switch (state) {
    case "idle":
      return "Ready";
    case "listening":
      return "Listening…";
    case "transcribing":
      return "Transcribing…";
    case "ready_to_send":
      return "Review transcript";
    case "thinking":
      return "Researching…";
    case "speaking":
      return "Speaking…";
    case "paused":
      return "Paused";
    case "error":
      return "Voice error";
    default:
      return "Ready";
  }
}

export function isVoiceBusy(state: VoiceChatState): boolean {
  return (
    state === "listening"
    || state === "transcribing"
    || state === "thinking"
    || state === "speaking"
  );
}
