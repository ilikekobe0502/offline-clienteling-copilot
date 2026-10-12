# Offline Clienteling Copilot

**ASUS UGen AI League 2026 · Workplace AI · Battlefield Lightning (ASUS UGen300 / Hailo-10H)**

An on-device AI assistant for retail and financial sales consultants. The consultant speaks a 30-second memo after a client leaves; the system turns it into a structured client record — preferences, wishlist, important dates and reminders — **without any audio, transcript or client data leaving the device**.

## Why on-device

Voice capture is the note-taking feature sales consultants value most, but employers in insurance, luxury retail and automotive ask one question first: *where does the recording go?* Personal-data regulation, client trust and unreliable store networks all make cloud processing a blocker. Running speech recognition and the language model on an ASUS UGen300 at the counter removes the cloud from the loop.

## Architecture

```
 microphone ──► host PC ─────────────────────────────────► local SQLite
               │ audio decode (16 kHz) · prompt · JSON validation · date & recurrence rules
               │
               └──► ASUS UGen300 (Hailo-10H, 40 TOPS INT4, 8 GB on-module)
                     ① Whisper speech-to-text (small-class)
                     ② Gemma 3 4B instruction LLM (1B fallback), JSON-schema-constrained decoding
```

- **Swappable backends** (`occ/backends/`): `laptop.py` (whisper.cpp + Ollama) for Stage I; `hailo.py` keeps the same interface for the UGen300 port in Stage II, so `occ/pipeline.py` does not change.
- **Schema-constrained decoding** (`occ/schema.py`): the runtime is given a JSON Schema, so even a 1B model returns valid, parseable output.
- **Rules where rules win**: recurrence ("every six months", "every quarter") and birthday/anniversary detection are decided by deterministic keyword rules on the transcript; the LLM handles open-ended extraction. Dates are normalised so reminders are never in the past.
- **Privacy guard**: the prompt forbids recording religion, politics or health details; audio is discarded after transcription.

## Models (Stage I)

| Stage | Model | Origin | Why |
|---|---|---|---|
| Speech-to-text | Whisper small (via whisper.cpp) | OpenAI | Small enough to sit beside the LLM in on-module memory; host-CPU fallback if the port slips |
| Extraction | Gemma 3 4B (selected), Gemma 3 1B (fallback), Llama 3.2 3B (compared) | Google / Meta | Size class that fits the 8 GB on-module memory |

## Run it

Requirements: macOS or Linux, `ffmpeg`, `whisper-cpp`, `ollama`, Python 3.10+. No Python packages beyond the standard library.

```bash
# models
curl -L -o models/ggml-small.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
ollama pull gemma3:4b

# one memo → client record (add --save to store it in the local SQLite file)
python3 -m occ.cli bench/watch-1.m4a --llm gemma3:4b

# benchmark: 8 sales memos × 3 models, field-level scoring
python3 -m bench.run          # writes bench/results.json
```

## Stage I benchmark

Eight Taiwanese-Mandarin sales memos (jewelry, watches, insurance, cars, real estate, beauty, fashion) with hand-written expected answers, synthesised to audio. Scored per field: client name, important dates, reminder date, reminder recurrence, preferences, wishlist. See `bench/results.json` for every transcript and model output.

| Language model | Fields correct, from audio | Fields correct, clean text | Seconds per memo (LLM) | Invalid outputs |
|---|---|---|---|---|
| Gemma 3 1B | 70.4% | 74.1% | 1.0 | 0 / 8 |
| **Gemma 3 4B (selected)** | **77.8%** | **79.6%** | **2.2** | **0 / 8** |
| Llama 3.2 3B | 70.4% | 66.7% | 5.6 | 2 / 8 |

Whisper-small transcription averages **0.83 s** per memo; a full memo-to-record run on the laptop takes about **3.1 s**. Gemma 3 4B scores 100% on important dates, reminder dates and recurrence; preferences and wishlist items (50–60%) are the main Stage II target. The gap between audio and clean text is speech-recognition error (e.g. product names), which is why the consultant confirms each record before it is saved.

**Design lesson.** In the first run the model also had to compute dates ("next Wednesday") and recurrence. Gemma 3 1B scored 33%. Moving that arithmetic into deterministic code (`occ/dates.py`, `detect_repeat`) raised it to 65% at the same speed (measured on our first synthesised audio set; on the current set it scores 70%) — the decision that makes a 1B-class model viable on edge hardware.

Measured on an Apple M2 Max laptop as a proxy, with models of the size class the Hailo-10H targets. Audio was synthesised from scripted memos with Gemini text-to-speech, alternating a female and a male voice; Stage II will add real field recordings.

## Stage II plan (Nov 6 – Dec 4)

1. Bring up UGen300 + HailoRT; run Whisper on Hailo-10H and match laptop transcripts (fallback: Whisper on the host CPU).
2. Deploy Gemma 3 4B on Hailo-10H (Gemma 3 1B as fallback); port the schema-constrained prompt.
3. End-to-end on device; review UI; latency and power tuning (target ≤ 10 s from end of memo to record).
4. Expanded test set with real field recordings; offline field test; final README, benchmarks and demo video.

## Third-party models and licences

This repository contains only our own code and benchmark data. **No model weights are included or redistributed**: the run instructions download each model from its original publisher, and anyone running the project accepts that publisher's terms.

| Component | Used for | Licence | What it requires of us |
|---|---|---|---|
| Whisper small (OpenAI) | Speech-to-text | MIT (code and weights) | Keep the copyright and licence notice |
| whisper.cpp / ggml (ggml-org) | Whisper runtime and `ggml-small.bin` conversion | MIT | Keep the copyright and licence notice |
| Gemma 3 1B / 4B (Google) | Extraction (selected model) | [Gemma Terms of Use](https://ai.google.dev/gemma/terms) and [Prohibited Use Policy](https://ai.google.dev/gemma/prohibited_use_policy) | Commercial use allowed; pass the use restrictions on to anyone we redistribute Gemma or a derivative to |
| Llama 3.2 3B (Meta) | Comparison only in the Stage I benchmark | [Llama 3.2 Community License](https://www.llama.com/llama3_2/license/) and [Acceptable Use Policy](https://www.llama.com/llama3_2/use-policy/) | Commercial use allowed below 700M monthly users; show "Built with Llama" if a distributed product includes it |
| Ollama | Local model runtime (Stage I laptop) | MIT | Keep the copyright and licence notice |
| Remotion | Rendering the demo video (`video/`) | [Remotion License](https://www.remotion.dev/license) | Free for individuals and companies of up to 3 people |

The Stage II build on the UGen300 is planned around Whisper and Gemma 3 only, so the shipped system carries MIT and Gemma terms; Llama 3.2 is used for comparison and is not part of the deliverable.

The benchmark audio in `bench/*.m4a` and the demo video's narration were generated from our own scripts with Gemini API text-to-speech (`bench/tts.py`, `video/tts.py`). Both are test and presentation material, not part of the system.

## Team

Team HueiHe — HueiHe Tech (暉和智慧科技), Taipei.

## License

Copyright 2026 HueiHe Tech (暉和智慧科技).

Licensed under the [Apache License, Version 2.0](LICENSE). Third-party models keep their own licences, listed above.
