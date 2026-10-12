"""
Offline Clienteling Copilot — on-device pipeline.

Voice memo  ->  speech-to-text (Whisper)  ->  structured client record (small LLM)  ->  local SQLite.
No audio, transcript or client data ever leaves the device.

The two model stages sit behind small backend interfaces so the same pipeline runs on
  * a laptop (whisper.cpp + Ollama) for Stage I prototyping, and
  * ASUS UGen300 / Hailo-10H (HailoRT GenAI) in Stage II — see backends/hailo.py.
"""
from __future__ import annotations

import datetime as dt
import json
import time
from dataclasses import dataclass, field

from .backends import base
from .schema import EXTRACTION_SCHEMA, build_prompt, normalize


@dataclass
class StageTiming:
    stt_s: float = 0.0
    llm_s: float = 0.0

    @property
    def total_s(self) -> float:
        return self.stt_s + self.llm_s


@dataclass
class PipelineResult:
    transcript: str
    record: dict
    timing: StageTiming = field(default_factory=StageTiming)
    stt_model: str = ""
    llm_model: str = ""


class Pipeline:
    def __init__(self, stt: base.SpeechToText, llm: base.LanguageModel):
        self.stt = stt
        self.llm = llm

    def run(self, audio_path: str, today: dt.date | None = None) -> PipelineResult:
        today = today or dt.date.today()
        timing = StageTiming()

        t0 = time.perf_counter()
        transcript = self.stt.transcribe(audio_path)
        timing.stt_s = time.perf_counter() - t0

        t1 = time.perf_counter()
        raw = self.llm.generate_json(build_prompt(transcript, today), EXTRACTION_SCHEMA)
        timing.llm_s = time.perf_counter() - t1

        record = normalize(raw, today)
        return PipelineResult(transcript, record, timing, self.stt.name, self.llm.name)


def to_json(result: PipelineResult) -> str:
    return json.dumps(
        {
            "transcript": result.transcript,
            "record": result.record,
            "timing": {"stt_s": round(result.timing.stt_s, 2), "llm_s": round(result.timing.llm_s, 2), "total_s": round(result.timing.total_s, 2)},
            "models": {"stt": result.stt_model, "llm": result.llm_model},
        },
        ensure_ascii=False,
        indent=2,
    )
