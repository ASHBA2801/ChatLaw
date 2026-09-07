/**
 * Resilient client-side audio recording using MediaRecorder with dynamic MIME negotiation.
 * Works across Chrome, Brave, Edge, Safari, Android browsers, and installed PWAs.
 */

export interface AudioRecordingResult {
  blob: Blob;
  mimeType: string;
  durationMs: number;
}

export interface AudioRecorderCallbacks {
  onStart?: () => void;
  onStop?: (result: AudioRecordingResult) => void;
  onError?: (message: string) => void;
  onLevel?: (level: number) => void; // 0.0 to 1.0 for visualizers
}

const PREFERRED_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/mp4",
  "audio/ogg;codecs=opus",
  "audio/ogg",
  "audio/wav",
] as const;

/**
 * Determine the most suitable supported audio recording MIME type for this browser.
 */
export function getSupportedAudioMimeType(
  mediaRecorderCtor: typeof MediaRecorder | undefined = typeof MediaRecorder !== "undefined"
    ? MediaRecorder
    : undefined,
): string {
  if (!mediaRecorderCtor) return "";
  for (const mime of PREFERRED_MIME_TYPES) {
    try {
      if (
        typeof mediaRecorderCtor.isTypeSupported === "function" &&
        mediaRecorderCtor.isTypeSupported(mime)
      ) {
        return mime;
      }
    } catch {
      // isTypeSupported might throw on older or restricted browsers
    }
  }
  return "";
}

export function isAudioRecordingSupported(
  win: Window | undefined = typeof window !== "undefined" ? window : undefined,
): boolean {
  if (!win) return false;
  const hasMediaDevices = Boolean(win.navigator?.mediaDevices?.getUserMedia);
  const hasMediaRecorder = typeof (win as Window & { MediaRecorder?: unknown }).MediaRecorder !== "undefined"
    || typeof MediaRecorder !== "undefined";
  return hasMediaDevices && hasMediaRecorder;
}

export class AudioRecorderSession {
  private stream: MediaStream | null = null;
  private recorder: MediaRecorder | null = null;
  private chunks: Blob[] = [];
  private startTime = 0;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private audioCtx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private animFrameId: number | null = null;
  private resolvedMimeType = "";
  private isRecording = false;

  constructor(
    private readonly callbacks: AudioRecorderCallbacks = {},
    private readonly maxDurationMs = 60_000, // 60s safe limit
    private readonly win: Window | undefined = typeof window !== "undefined" ? window : undefined,
  ) {}

  public get active(): boolean {
    return this.isRecording;
  }

  public async start(): Promise<void> {
    if (this.isRecording) return;

    const currentWin = this.win ?? (typeof window !== "undefined" ? window : undefined);
    if (!currentWin) {
      this.callbacks.onError?.("Audio recording is not supported in this environment.");
      return;
    }

    if (
      currentWin.isSecureContext === false &&
      currentWin.location?.hostname !== "localhost" &&
      currentWin.location?.hostname !== "127.0.0.1"
    ) {
      this.callbacks.onError?.(
        "Microphone access requires a secure connection (HTTPS). Please open ChatLaw over HTTPS.",
      );
      return;
    }

    const nav = currentWin.navigator;
    const mediaDevices = nav?.mediaDevices;
    const RecorderCtor =
      (currentWin as unknown as { MediaRecorder?: typeof MediaRecorder }).MediaRecorder ??
      (typeof MediaRecorder !== "undefined" ? MediaRecorder : undefined);

    if (!mediaDevices?.getUserMedia || !RecorderCtor) {
      this.callbacks.onError?.(
        "Voice recording is not supported by your current browser. Please try Chrome, Edge, or Brave on HTTPS.",
      );
      return;
    }

    try {
      this.stream = await mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
    } catch (err) {
      this.cleanup();
      const message = this.mapMediaStreamError(err);
      this.callbacks.onError?.(message);
      return;
    }

    this.resolvedMimeType = getSupportedAudioMimeType(RecorderCtor);
    const options: MediaRecorderOptions = {};
    if (this.resolvedMimeType) {
      options.mimeType = this.resolvedMimeType;
    }

    try {
      this.recorder = new RecorderCtor(this.stream, options);
    } catch {
      // Fallback without explicit mimeType
      try {
        this.recorder = new RecorderCtor(this.stream);
        this.resolvedMimeType = this.recorder.mimeType || "audio/webm";
      } catch {
        this.cleanup();
        this.callbacks.onError?.("Failed to initialize the audio recorder on this device.");
        return;
      }
    }

    this.chunks = [];
    this.recorder.ondataavailable = (event: BlobEvent) => {
      if (event.data && event.data.size > 0) {
        this.chunks.push(event.data);
      }
    };

    this.recorder.onerror = () => {
      this.cleanup();
      this.callbacks.onError?.("An error occurred during audio recording. Please try again.");
    };

    // Setup audio visualizer level analyzer if supported
    this.setupLevelAnalyzer(currentWin);

    this.isRecording = true;
    this.startTime = Date.now();
    this.recorder.start(250); // collect chunks every 250ms
    this.callbacks.onStart?.();

    // Auto-stop at max duration
    this.timer = setTimeout(() => {
      if (this.isRecording) {
        void this.stop();
      }
    }, this.maxDurationMs);
  }

  public async stop(): Promise<AudioRecordingResult | null> {
    if (!this.isRecording || !this.recorder) {
      this.cleanup();
      return null;
    }

    return new Promise((resolve) => {
      const recorder = this.recorder!;
      const stream = this.stream;
      const durationMs = Math.max(1, Date.now() - this.startTime);

      recorder.onstop = () => {
        const mimeType = this.resolvedMimeType || recorder.mimeType || "audio/webm";
        const blob = new Blob(this.chunks, { type: mimeType });
        this.cleanup();

        const result: AudioRecordingResult = {
          blob,
          mimeType,
          durationMs,
        };

        this.callbacks.onStop?.(result);
        resolve(result);
      };

      try {
        if (recorder.state !== "inactive") {
          recorder.stop();
        }
      } catch {
        this.cleanup();
        resolve(null);
      }

      // Stop stream tracks
      if (stream) {
        for (const track of stream.getTracks()) {
          try {
            track.stop();
          } catch {
            // ignore
          }
        }
      }
    });
  }

  public cancel(): void {
    if (this.recorder && this.recorder.state !== "inactive") {
      try {
        this.recorder.stop();
      } catch {
        // ignore
      }
    }
    this.cleanup();
  }

  private cleanup(): void {
    this.isRecording = false;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
    if (this.animFrameId !== null) {
      if (typeof cancelAnimationFrame === "function") {
        cancelAnimationFrame(this.animFrameId);
      }
      this.animFrameId = null;
    }
    if (this.stream) {
      for (const track of this.stream.getTracks()) {
        try {
          track.stop();
        } catch {
          // ignore
        }
      }
      this.stream = null;
    }
    if (this.audioCtx) {
      try {
        void this.audioCtx.close();
      } catch {
        // ignore
      }
      this.audioCtx = null;
    }
    this.analyser = null;
    this.recorder = null;
    this.chunks = [];
  }

  private setupLevelAnalyzer(currentWin: Window): void {
    if (!this.stream || !this.callbacks.onLevel) return;
    try {
      const AudioCtx =
        currentWin.AudioContext ||
        (currentWin as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!AudioCtx) return;
      this.audioCtx = new AudioCtx();
      const source = this.audioCtx.createMediaStreamSource(this.stream);
      this.analyser = this.audioCtx.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);

      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      const updateLevel = () => {
        if (!this.isRecording || !this.analyser) return;
        this.analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
          sum += dataArray[i];
        }
        const avg = sum / dataArray.length;
        const normalized = Math.min(1.0, avg / 128);
        this.callbacks.onLevel?.(normalized);
        if (typeof requestAnimationFrame === "function") {
          this.animFrameId = requestAnimationFrame(updateLevel);
        }
      };

      if (typeof requestAnimationFrame === "function") {
        this.animFrameId = requestAnimationFrame(updateLevel);
      }
    } catch {
      // AudioContext may be restricted by autoplay policy; non-critical
    }
  }

  private mapMediaStreamError(err: unknown): string {
    if (err && typeof err === "object" && "name" in err) {
      const name = (err as { name: string }).name;
      switch (name) {
        case "NotAllowedError":
        case "PermissionDeniedError":
          return "ChatLaw cannot access your microphone. Please click the permissions icon in your browser address bar, allow microphone access, and try again.";
        case "NotFoundError":
        case "DevicesNotFoundError":
          return "No microphone was detected on this device. Please connect an audio input device and try again.";
        case "NotReadableError":
        case "TrackStartError":
          return "Your microphone is currently in use by another application. Please close other apps using the microphone and try again.";
        case "SecurityError":
          return "Microphone access was blocked for security reasons. Please ensure you are accessing ChatLaw securely via HTTPS.";
        case "OverconstrainedError":
          return "The requested microphone settings are not supported by your hardware.";
      }
    }
    return "Could not initialize microphone. Please check your browser audio permissions.";
  }
}
