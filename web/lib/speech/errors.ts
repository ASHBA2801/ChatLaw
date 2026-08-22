/** Map browser speech errors to calm, actionable copy. Never expose raw internals. */

export function mapSpeechError(errorCode: string | null | undefined): string {
  switch (errorCode) {
    case "not-allowed":
    case "service-not-allowed":
      return "Microphone access was denied. Allow microphone permission, then try again.";
    case "audio-capture":
      return "No microphone is available. Check your device settings and try again.";
    case "network":
      return "Voice recognition could not reach the speech service. Check your connection and try again.";
    case "no-speech":
      return "No speech was detected. Please try again.";
    case "aborted":
      return "Voice input was cancelled.";
    case "bad-grammar":
    case "language-not-supported":
      return "Voice input could not use that language in this browser. Try English instead.";
    case "unsupported":
      return "Voice input isn't supported in this browser. You can continue using the keyboard.";
    case "busy":
      return "The microphone is already in use. Close other apps using it, then try again.";
    case "empty":
      return "Nothing was transcribed. Please try speaking again.";
    default:
      return "Unable to recognize speech. Please try again or type your question.";
  }
}
