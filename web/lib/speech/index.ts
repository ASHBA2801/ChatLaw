export type {
  SpeechInputStatus,
  SpeechLanguageCode,
  SpeechLanguageOption,
  VoiceChatState,
  ChatInputMode,
} from "./types";
export { mapSpeechError } from "./errors";
export {
  DEFAULT_SPEECH_LANGUAGE,
  SPEECH_LANGUAGE_OPTIONS,
  getEnabledSpeechLanguages,
  getSpeechRecognitionConstructor,
  getSpeechRecognitionUnavailableMessage,
  isBraveBrowser,
  isSpeechRecognitionSupported,
  chatLanguageToSpeechCode,
  speechCodeToChatLanguage,
  isSpeechLocaleLikelySupported,
  resolveSpeechLocale,
} from "./support";
export { extractTranscriptParts, mergeTranscript } from "./transcript";
export {
  prepareTextForSpeech,
  segmentSpeechText,
  SPEECH_SEGMENT_MAX_CHARS,
  stripCitationMarkers,
  stripMarkdown,
  stripUrls,
} from "./speechText";
export { canStartVoiceListening, canTransition, isVoiceBusy, voiceStateLabel } from "./voiceState";
export { SpeechInputSession } from "./SpeechInputSession";
export { SpeechOutputSession } from "./SpeechOutputSession";
export { useSpeechInput } from "./useSpeechInput";
export { useVoiceChat } from "./useVoiceChat";
export type { VoiceChatSendResult, UseVoiceChatOptions, UseVoiceChatResult } from "./useVoiceChat";
export { useAnswerPlayback } from "./useAnswerPlayback";
export type { AnswerPlaybackStatus, UseAnswerPlaybackResult } from "./useAnswerPlayback";
