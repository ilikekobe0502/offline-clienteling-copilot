"""Stage I reference backends: whisper.cpp for speech-to-text, Ollama for the language model.

Model sizes are chosen to match what the Hailo-10H accelerator runs on-device
(Whisper small-class STT, 1B-4B instruction models), so laptop numbers are a realistic proxy.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import urllib.request

WHISPER_BIN = os.environ.get("OCC_WHISPER_BIN", "/opt/homebrew/bin/whisper-cli")
FFMPEG_BIN = os.environ.get("OCC_FFMPEG_BIN", "/opt/homebrew/bin/ffmpeg")
OLLAMA_URL = os.environ.get("OCC_OLLAMA_URL", "http://127.0.0.1:11434")

# Biases Whisper toward Traditional Chinese output (Taiwan usage) without a conversion library.
ZH_TW_PROMPT = "以下是台灣業務的客戶備忘錄，使用繁體中文。"


class WhisperCpp:
    def __init__(self, model_path: str, language: str = "zh", threads: int = 8):
        self.model_path = model_path
        self.language = language
        self.threads = threads
        self.name = f"whisper.cpp/{os.path.basename(model_path)}"

    def transcribe(self, audio_path: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            wav = os.path.join(tmp, "in.wav")
            subprocess.run([FFMPEG_BIN, "-y", "-loglevel", "error", "-i", audio_path, "-ar", "16000", "-ac", "1", wav], check=True)
            out_base = os.path.join(tmp, "out")
            subprocess.run(
                [WHISPER_BIN, "-m", self.model_path, "-l", self.language, "-t", str(self.threads),
                 "--prompt", ZH_TW_PROMPT, "-nt", "-otxt", "-of", out_base, "-f", wav],
                check=True, capture_output=True,
            )
            with open(out_base + ".txt", encoding="utf-8") as f:
                return " ".join(line.strip() for line in f if line.strip())


class Ollama:
    def __init__(self, model: str, temperature: float = 0.1):
        self.model = model
        self.temperature = temperature
        self.name = f"ollama/{model}"

    def generate_json(self, prompt: str, schema: dict) -> dict:
        body = json.dumps({
            "model": self.model,
            "prompt": prompt,
            "format": schema,          # constrained decoding to the JSON schema
            "stream": False,
            # 4k context: a 30-second memo plus the schema fits easily, and it mirrors the accelerator's memory budget
            "options": {"temperature": self.temperature, "num_ctx": 4096, "num_predict": 1536},
        }).encode()
        req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            text = json.load(resp)["response"]
        return json.loads(text)
