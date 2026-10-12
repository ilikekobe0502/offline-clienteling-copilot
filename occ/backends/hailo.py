"""Stage II target: ASUS UGen300 (Hailo-10H, 40 TOPS INT4, 8 GB on-module memory).

Plan:
  * Speech-to-text  — Whisper (small-class) compiled to HEF via the Hailo Model Zoo GenAI pipeline.
  * Extraction LLM  — a 1B-class instruction model (Gemma / Llama family) served by HailoRT GenAI,
                      with the same JSON-schema-constrained prompt used on the laptop.
  * The host CPU only handles audio decoding, prompt assembly, validation and SQLite storage.

These classes keep the exact interface of backends/laptop.py so pipeline.py does not change.
They are implemented once the shortlisted team receives the UGen300 (Stage II, from 2026-11-06).
"""
from __future__ import annotations


class HailoWhisper:
    name = "hailo/whisper-small"

    def __init__(self, hef_path: str):
        self.hef_path = hef_path

    def transcribe(self, audio_path: str) -> str:  # pragma: no cover - requires UGen300
        raise NotImplementedError("Implemented in Stage II on ASUS UGen300 (HailoRT GenAI).")


class HailoLLM:
    name = "hailo/llm-1b"

    def __init__(self, hef_path: str):
        self.hef_path = hef_path

    def generate_json(self, prompt: str, schema: dict) -> dict:  # pragma: no cover - requires UGen300
        raise NotImplementedError("Implemented in Stage II on ASUS UGen300 (HailoRT GenAI).")
