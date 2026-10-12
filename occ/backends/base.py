"""Backend interfaces. Each runtime (laptop, Hailo-10H, Intel Arc) implements these two stages."""
from __future__ import annotations

from typing import Protocol


class SpeechToText(Protocol):
    name: str

    def transcribe(self, audio_path: str) -> str: ...


class LanguageModel(Protocol):
    name: str

    def generate_json(self, prompt: str, schema: dict) -> dict: ...
