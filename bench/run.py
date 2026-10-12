"""Benchmark: transcribe each memo once, then score every LLM field by field.

Usage: /opt/homebrew/bin/python3 -m bench.run   (from the repo root)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import time

from occ.backends.laptop import Ollama, WhisperCpp
from occ.schema import EXTRACTION_SCHEMA, build_prompt, normalize

HERE = os.path.dirname(__file__)
TODAY = dt.date(2026, 10, 12)  # fixed so relative dates are reproducible
MODELS = ["gemma3:1b", "gemma3:4b", "llama3.2:3b"]
ALIASES = {"11": ["11", "十一"], "40": ["40", "四十"], "十五萬": ["十五萬", "15萬", "150000", "150,000"],
           "十萬": ["十萬", "10萬", "100000", "100,000"], "M": ["M"], "無香": ["無香"]}


def hit(keyword: str, text: str) -> bool:
    return any(a.lower() in text.lower() for a in ALIASES.get(keyword, [keyword]))


def score(rec: dict, exp: dict) -> dict:
    prefs = " ".join(p["value"] for p in rec["preferences"])
    wish = " ".join(w.get("item", "") for w in rec["wishlist"])
    dates = {(d["month"], d["day"]) for d in rec["importantDates"]}
    rems = {(r["date"], r["repeat"]) for r in rec["reminders"]}
    rem_dates = {r["date"] for r in rec["reminders"]}
    parts = {
        "name": (1 if exp["clientName"] in rec["clientName"] or rec["clientName"] in exp["clientName"] and rec["clientName"] else 0, 1),
        "dates": (sum(tuple(d) in dates for d in exp["dates"]), len(exp["dates"])),
        "reminder_date": (sum(r[0] in rem_dates for r in exp["reminders"]), len(exp["reminders"])),
        "reminder_repeat": (sum(tuple(r) in rems for r in exp["reminders"]), len(exp["reminders"])),
        "prefs": (sum(hit(k, prefs) for k in exp["prefs"]), len(exp["prefs"])),
        "wish": (sum(hit(k, wish) for k in exp["wish"]), len(exp["wish"])),
    }
    return parts


def main() -> None:
    cases = json.load(open(os.path.join(HERE, "cases.json"), encoding="utf-8"))
    stt = WhisperCpp(os.path.join(HERE, "..", "models", "ggml-small.bin"))
    transcripts, stt_times = {}, []
    for c in cases:
        t0 = time.perf_counter()
        transcripts[c["id"]] = stt.transcribe(os.path.join(HERE, f"{c['id']}.m4a"))
        stt_times.append(time.perf_counter() - t0)
        print(f"[stt] {c['id']}: {transcripts[c['id']]}", flush=True)

    report = {"today": TODAY.isoformat(), "stt": stt.name, "stt_avg_s": round(sum(stt_times) / len(stt_times), 2), "models": {}}
    for m in MODELS:
        llm = Ollama(m)
        llm.generate_json(build_prompt("測試", TODAY), EXTRACTION_SCHEMA)  # warm-up, loads weights
        totals: dict[str, list[int]] = {}
        times, failures, outputs = [], 0, {}
        for c in cases:
            t0 = time.perf_counter()
            try:
                rec = normalize(llm.generate_json(build_prompt(transcripts[c["id"]], TODAY), EXTRACTION_SCHEMA), TODAY)
            except Exception as e:  # invalid JSON etc.
                failures += 1
                rec = normalize({}, TODAY)
                print(f"  [{m}] {c['id']} failed: {e}")
            times.append(time.perf_counter() - t0)
            outputs[c["id"]] = rec
            for k, (got, total) in score(rec, c["expect"]).items():
                agg = totals.setdefault(k, [0, 0])
                agg[0] += got
                agg[1] += total
        fields = {k: round(g / t, 3) if t else None for k, (g, t) in totals.items()}
        overall_g = sum(g for g, _ in totals.values())
        overall_t = sum(t for _, t in totals.values())
        report["models"][m] = {"field_recall": fields, "overall": round(overall_g / overall_t, 3),
                               "llm_avg_s": round(sum(times) / len(times), 2), "json_failures": failures, "outputs": outputs}
        print(f"[{m}] overall {report['models'][m]['overall']}  avg {report['models'][m]['llm_avg_s']}s  {fields}", flush=True)

    report["transcripts"] = transcripts
    json.dump(report, open(os.path.join(HERE, "results.json"), "w"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
