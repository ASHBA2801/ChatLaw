"""Configurable Gemini generation adapter."""

from dataclasses import dataclass
import os
import time

from .prompt import build_prompt


@dataclass(frozen=True)
class GenerationResult:
    answer: str
    model: str
    latency_seconds: float


class GeminiGenerator:
    def __init__(self, *, model: str | None = None):
        self.model = (model or os.getenv("GEMINI_GENERATION_MODEL", "").strip())
        if not self.model:
            raise ValueError("GEMINI_GENERATION_MODEL is required for grounded generation")
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for grounded generation")
        try:
            from google import genai  # type: ignore
            from google.genai import types  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Grounded generation requires the google-genai package") from exc
        timeout = float(os.getenv("GEMINI_REQUEST_TIMEOUT_SECONDS", "60"))
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(timeout * 1000)),
        )
        self._types = types

    def generate(
        self,
        question: str,
        context: str,
        history: str = "",
        *,
        language: str = "en",
        simplicity: str = "standard",
    ) -> GenerationResult:
        return self.generate_text(
            build_prompt(question, context, history, language=language, simplicity=simplicity)
        )

    def generate_text(self, prompt: str, *, temperature: float = 0.0) -> GenerationResult:
        started = time.perf_counter()
        response = self._client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=self._types.GenerateContentConfig(temperature=temperature),
        )
        answer = getattr(response, "text", None)
        if not answer or not answer.strip():
            raise RuntimeError("Gemini returned an empty grounded answer")
        return GenerationResult(answer=answer.strip(), model=self.model,
                                latency_seconds=time.perf_counter() - started)
