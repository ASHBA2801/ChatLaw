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
export {
  normalizeTextForSpeech,
  normalizeCurrency,
  normalizeLegalSections,
  normalizeLegalAbbreviations,
  numberToIndianWords,
  stripCitationsAndTechnicalMarkers,
  stripMarkdownFormatting,
  cleanPunctuationArtifacts,
} from "./speechNormalizer";
export { canStartVoiceListening, canTransition, isVoiceBusy, voiceStateLabel } from "./voiceState";
export {
  AudioRecorderSession,
  getSupportedAudioMimeType,
  isAudioRecordingSupported,
} from "./audioRecorder";
export type { AudioRecordingResult, AudioRecorderCallbacks } from "./audioRecorder";
export { transcribeAudio } from "./transcribe";
export type { TranscribeAudioResult } from "./transcribe";
export { synthesizeSpeechAudio, playSynthesizedAudio } from "./synthesize";
export type { SynthesizedAudioResult, AudioPlayHandle, PlaySpeechOptions } from "./synthesize";
export { SpeechInputSession } from "./SpeechInputSession";
export { SpeechOutputSession } from "./SpeechOutputSession";
export { useSpeechInput } from "./useSpeechInput";
export { useVoiceChat } from "./useVoiceChat";
export type { VoiceChatSendResult, UseVoiceChatOptions, UseVoiceChatResult } from "./useVoiceChat";
export { useAnswerPlayback } from "./useAnswerPlayback";
export type { AnswerPlaybackStatus, UseAnswerPlaybackResult } from "./useAnswerPlayback";
