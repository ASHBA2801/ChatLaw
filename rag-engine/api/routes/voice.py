"""Voice STT and TTS endpoint routes for ChatLaw."""

import json
import logging
import os
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["voice"])

LANGUAGE_MAP = {
    "ta": "Tamil",
    "hi": "Hindi",
    "te": "Telugu",
    "kn": "Kannada",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ur": "Urdu",
    "en": "English",
}


class SttResponse(BaseModel):
    transcript: str
    detected_language: str
    confidence: float


class TtsRequest(BaseModel):
    text: str
    language: Optional[str] = "en"
    voice: Optional[str] = None
    rate: Optional[str] = "+0%"


VOICE_MAP = {
    "ta": "ta-IN-ValluvarNeural",
    "ta-in": "ta-IN-ValluvarNeural",
    "hi": "hi-IN-MadhurNeural",
    "hi-in": "hi-IN-MadhurNeural",
    "te": "te-IN-MohanNeural",
    "te-in": "te-IN-MohanNeural",
    "kn": "kn-IN-GaganNeural",
    "kn-in": "kn-IN-GaganNeural",
    "ml": "ml-IN-MidhunNeural",
    "ml-in": "ml-IN-MidhunNeural",
    "mr": "mr-IN-ManoharNeural",
    "mr-in": "mr-IN-ManoharNeural",
    "bn": "bn-IN-BashkarNeural",
    "bn-in": "bn-IN-BashkarNeural",
    "gu": "gu-IN-NiranjanNeural",
    "gu-in": "gu-IN-NiranjanNeural",
    "ur": "ur-IN-SalmanNeural",
    "ur-in": "ur-IN-SalmanNeural",
    "pa": "hi-IN-MadhurNeural",
    "pa-in": "hi-IN-MadhurNeural",
    "en": "en-IN-NeerjaNeural",
    "en-in": "en-IN-NeerjaNeural",
    "en-us": "en-US-JennyNeural",
}


@router.post("/tts")
async def text_to_speech(payload: TtsRequest):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required for TTS")

    code = (payload.language or "en").lower().strip()
    if code in ("auto", "en", "en-in", "en-us") or not code:
        from conversation.language_detector import detect_language

        det = detect_language(text, input_type="text")
        if det["detected_language"] != "en":
            code = det["detected_language"]

    voice = payload.voice or VOICE_MAP.get(code) or VOICE_MAP.get(code.split("-")[0]) or "en-IN-NeerjaNeural"

    try:
        import edge_tts
        from fastapi.responses import Response

        comm = edge_tts.Communicate(text, voice, rate=payload.rate or "+0%")
        chunks = []
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        audio_data = b"".join(chunks)
        if not audio_data:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech audio")
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": 'inline; filename="speech.mp3"',
                "X-ChatLaw-Voice": voice,
                "X-ChatLaw-Language": code,
            },
        )
    except Exception as exc:
        logger.exception("Text to speech synthesis failed")
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(exc)}") from exc


@router.post("/stt", response_model=SttResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio payload")

    content_type = audio.content_type or "audio/webm"
    mime_type = content_type.split(";")[0].strip()

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        raw_hint = (language or "").strip()
        lang_hint = "" if raw_hint.lower() == "auto" else raw_hint
        lang_name = LANGUAGE_MAP.get(lang_hint[:2].lower(), "") if lang_hint else ""

        prompt = (
            "You are ChatLaw's Indian legal assistant multilingual speech recognition model.\n"
            "Transcribe the spoken audio verbatim in its authentic original language and script "
            "(Tamil in Tamil script, Hindi in Devanagari script, Telugu in Telugu script, etc.).\n"
            "Do NOT translate into English. Preserve exact legal terminology, numbers, and dates.\n"
            f"{f'Language hint: {lang_name} ({lang_hint}). Prioritize if matching.' if lang_name else ''}\n"
            "If the audio is silent or unintelligible, return an empty transcript.\n"
            "Return JSON matching: {\"transcript\": string, \"detected_language\": string, \"confidence\": float}."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.0,
            ),
        )

        text = getattr(response, "text", "") or "{}"
        data = json.loads(text)
        transcript = data.get("transcript", "").strip()
        from conversation.language_detector import detect_language
        script_det = detect_language(transcript, input_type="voice")
        detected_lang = (
            script_det["detected_language"]
            if script_det["detected_language"] != "en"
            else data.get("detected_language") or lang_hint or "en"
        ).lower()
        confidence = max(float(data.get("confidence", 0.95)), float(script_det["confidence"]))
        return SttResponse(
            transcript=transcript,
            detected_language=detected_lang,
            confidence=confidence,
        )
    except Exception as exc:
        logger.exception("Voice transcription failed")
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(exc)}") from exc
