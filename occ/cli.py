"""Usage: python3 -m occ.cli <audio file> [--llm gemma3:4b] [--whisper models/ggml-small.bin] [--save]"""
from __future__ import annotations

import argparse

from .backends.laptop import Ollama, WhisperCpp
from .pipeline import Pipeline, to_json
from .store import Store


def main() -> None:
    ap = argparse.ArgumentParser(description="Offline Clienteling Copilot — voice memo to client record, fully on-device.")
    ap.add_argument("audio")
    ap.add_argument("--llm", default="gemma3:4b")
    ap.add_argument("--whisper", default="models/ggml-small.bin")
    ap.add_argument("--save", action="store_true", help="store the result in the local SQLite file")
    args = ap.parse_args()

    result = Pipeline(WhisperCpp(args.whisper), Ollama(args.llm)).run(args.audio)
    print(to_json(result))
    if args.save:
        print(f"saved as memo #{Store().save(result)} (local SQLite only)")


if __name__ == "__main__":
    main()
