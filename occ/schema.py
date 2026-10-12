"""Extraction schema, prompt and post-processing for a salesperson's voice memo."""
from __future__ import annotations

import datetime as dt
import re

REPEATS = ["NONE", "YEARLY", "HALF_YEARLY", "QUARTERLY", "MONTHLY"]
REMIND_TYPES = ["BIRTHDAY", "ANNIVERSARY", "FOLLOW_UP", "MAINTENANCE", "VISIT"]
PREF_CATEGORIES = ["STYLE", "SIZE", "BUDGET", "MATERIAL", "LIFESTYLE", "AVOID", "OTHER"]

# JSON Schema handed to the runtime for constrained decoding, so even a 1B model returns valid JSON.
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "clientName": {"type": "string"},
        "summary": {"type": "string"},
        "preferences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"category": {"type": "string", "enum": PREF_CATEGORIES}, "value": {"type": "string"}},
                "required": ["category", "value"],
            },
        },
        "wishlist": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"item": {"type": "string"}, "hesitation": {"type": "string"}, "occasion": {"type": "string"}},
                "required": ["item"],
            },
        },
        "importantDates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"label": {"type": "string"}, "month": {"type": "integer"}, "day": {"type": "integer"}},
                "required": ["label", "month", "day"],
            },
        },
        "reminders": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "type": {"type": "string", "enum": REMIND_TYPES},
                    "date": {"type": "string"},
                    "repeat": {"type": "string", "enum": REPEATS},
                },
                "required": ["title", "type", "date", "repeat"],
            },
        },
    },
    "required": ["clientName", "summary", "preferences", "wishlist", "importantDates", "reminders"],
}


def build_prompt(transcript: str, today: dt.date) -> str:
    return f"""You are an assistant for a retail sales consultant in Taiwan.
Extract client information from the consultant's spoken memo (Traditional Chinese) and return JSON only.

Today is {today.isoformat()}.

Rules:
- Write every text value in Traditional Chinese (Taiwan usage).
- clientName: the client's name or nickname as spoken.
- summary: one short sentence describing the interaction.
- preferences: tastes, sizes, budget, habits or things to avoid that help future service. Never record religion, politics, health conditions or sexual orientation.
- wishlist: items the client is interested in but has not bought, with the reason for hesitating if mentioned.
- importantDates: birthdays and anniversaries (month and day) — these repeat every year.
- reminders: follow-ups that have a concrete date. Convert relative dates ("next Wednesday", "11/15") into YYYY-MM-DD, never earlier than today.
  repeat = YEARLY / HALF_YEARLY / QUARTERLY / MONTHLY only when the memo says "every year / every six months / every quarter / every month", otherwise NONE.
- Omit anything not mentioned. Do not invent information.

Memo:
\"\"\"{transcript}\"\"\"
"""


def _iso(d: dt.date) -> str:
    return d.isoformat()


def _next_occurrence(month: int, day: int, today: dt.date) -> dt.date | None:
    for year in (today.year, today.year + 1):
        try:
            cand = dt.date(year, month, day)
        except ValueError:  # e.g. Feb 29 in a common year
            cand = dt.date(year, month, 28)
        if cand >= today:
            return cand
    return None


def normalize(raw: dict, today: dt.date) -> dict:
    """Validate and clean model output: drop malformed items, clamp enums, fix dates."""
    out = {
        "clientName": str(raw.get("clientName") or "").strip(),
        "summary": str(raw.get("summary") or "").strip(),
        "preferences": [],
        "wishlist": [],
        "importantDates": [],
        "reminders": [],
    }
    for p in raw.get("preferences") or []:
        val = str(p.get("value") or "").strip()
        if val:
            cat = p.get("category") if p.get("category") in PREF_CATEGORIES else "OTHER"
            out["preferences"].append({"category": cat, "value": val})
    for w in raw.get("wishlist") or []:
        item = str(w.get("item") or "").strip()
        if item:
            out["wishlist"].append({k: str(w[k]).strip() for k in ("item", "hesitation", "occasion") if w.get(k)})
    for d in raw.get("importantDates") or []:
        try:
            m, day = int(d.get("month")), int(d.get("day"))
        except (TypeError, ValueError):
            continue
        nxt = _next_occurrence(m, day, today) if 1 <= m <= 12 and 1 <= day <= 31 else None
        if nxt:
            out["importantDates"].append({"label": str(d.get("label") or "紀念日").strip(), "month": m, "day": day, "next": _iso(nxt)})
    for r in raw.get("reminders") or []:
        title = str(r.get("title") or "").strip()
        date = str(r.get("date") or "")
        if not title or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            continue
        try:
            when = dt.date.fromisoformat(date)
        except ValueError:
            continue
        if when < today:  # model guessed the wrong year
            try:
                when = when.replace(year=when.year + 1)
            except ValueError:
                continue
        out["reminders"].append({
            "title": title,
            "type": r.get("type") if r.get("type") in REMIND_TYPES else "FOLLOW_UP",
            "date": _iso(when),
            "repeat": r.get("repeat") if r.get("repeat") in REPEATS else "NONE",
        })
    # Important dates already repeat yearly; drop duplicate birthday/anniversary reminders.
    known = {(d["month"], d["day"]) for d in out["importantDates"]}
    out["reminders"] = [
        r for r in out["reminders"]
        if not (r["type"] in ("BIRTHDAY", "ANNIVERSARY") and (int(r["date"][5:7]), int(r["date"][8:10])) in known)
    ]
    return out
