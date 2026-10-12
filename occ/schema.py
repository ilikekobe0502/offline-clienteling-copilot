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
    return f"""你是台灣零售業務顧問的助理。請從業務口述的備忘錄中萃取客戶資訊，只回傳 JSON。

今天是 {today.isoformat()}。

規則：
- 所有文字一律用繁體中文（台灣用語）。
- clientName：客戶的稱呼或代號。
- summary：一句話描述這次互動。
- preferences：喜好、尺寸、預算、習慣、忌諱、過敏等對服務有幫助的資訊，每一項寫成單獨看得懂的完整描述（例如「戒圍 11 號」「不喜歡金色」）。不要記錄宗教、政治、病史。沒有就給空陣列，不要寫 N/A。
- wishlist：客戶有興趣但還沒買的商品，有提到猶豫原因就填 hesitation。
- importantDates：只有明確說到「生日」「紀念日」「週年」才放這裡（每年都會重複）；保養、回訪、續約日期不要放這裡。
- reminders：有具體日期的後續行動（回訪、保養、續約、通知、交貨）。日期轉成 YYYY-MM-DD，不可早於今天。type：FOLLOW_UP 跟進、MAINTENANCE 保養、VISIT 回訪或帶看。repeat 先填 NONE。
- 沒提到的不要編造。

範例：
備忘錄：「林小姐喜歡珍珠，預算三萬，她生日是六月一號，下週五再約她來試戴。」
輸出：{{"clientName":"林小姐","summary":"林小姐對珍珠飾品有興趣，約下週五試戴。","preferences":[{{"category":"STYLE","value":"喜歡珍珠"}},{{"category":"BUDGET","value":"預算約三萬"}}],"wishlist":[],"importantDates":[{{"label":"生日","month":6,"day":1}}],"reminders":[{{"title":"林小姐回店試戴","type":"VISIT","date":"(下週五的日期)","repeat":"NONE"}}]}}

備忘錄：
\"\"\"{transcript}\"\"\"
"""


# 週期用關鍵字判斷：「每半年」「每季」語意明確，規則比 1B–4B 模型可靠
REPEAT_RULES = [
    ("HALF_YEARLY", ["每半年", "半年一次", "每六個月"]),
    ("QUARTERLY", ["每季", "每一季", "每三個月", "每個季度"]),
    ("MONTHLY", ["每個月", "每月"]),
]  # 「每年」不列：年度事件由生日 / 紀念日處理，避免把同段話裡的一般跟進誤設為每年
DATE_WORDS = ["生日", "紀念", "週年", "周年"]
FILLER = {"n/a", "na", "none", "無", "不詳", "未知", "-"}


def detect_repeat(transcript: str) -> str:
    for code, words in REPEAT_RULES:
        if any(w in transcript for w in words):
            return code
    return "NONE"


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


def normalize(raw: dict, today: dt.date, transcript: str = "") -> dict:
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
        if val and val.lower() not in FILLER:
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
        if transcript and not any(w in transcript for w in DATE_WORDS):
            nxt = None  # 模型把保養日、回訪日誤當生日
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
            "repeat": "NONE",
        })
    if transcript:
        _apply_date_rules(out, transcript, today)
    # 週期以逐字稿關鍵字為準，只套在保養 / 回訪這類「固定服務」；一般跟進不會週期重複
    rep = detect_repeat(transcript) if transcript else "NONE"
    if rep != "NONE":
        for r in out["reminders"]:
            if r["type"] in ("MAINTENANCE", "VISIT"):
                r["repeat"] = rep
                break
    # Important dates already repeat yearly; drop duplicate birthday/anniversary reminders.
    known = {(d["month"], d["day"]) for d in out["importantDates"]}
    out["reminders"] = [
        r for r in out["reminders"]
        if not (r["type"] in ("BIRTHDAY", "ANNIVERSARY") and (int(r["date"][5:7]), int(r["date"][8:10])) in known)
    ]
    return out


def _guess_type(text: str, pos: int) -> str:
    around = text[max(0, pos - 14):pos + 14]
    if any(w in around for w in ("保養", "檢查", "回廠", "回倉", "維修")):
        return "MAINTENANCE"
    if any(w in around for w in ("帶看", "看房", "回店", "來店", "試戴", "試駕", "來一次")):
        return "VISIT"
    return "FOLLOW_UP"


def _apply_date_rules(out: dict, transcript: str, today: dt.date) -> None:
    """Replace model-guessed dates with dates parsed from the transcript (see occ/dates.py)."""
    from .dates import explicit_dates, followup_dates, relative_dates

    # 生日 / 紀念日：以逐字稿明確提到的為準，模型的標籤若對得上就沿用
    labels = {(d["month"], d["day"]): d["label"] for d in out["importantDates"]}
    annual = []
    for pos, d, is_annual in explicit_dates(transcript, today):
        if is_annual:
            before = transcript[max(0, pos - 8):pos]
            label = labels.get((d.month, d.day)) or ("生日" if "生日" in before else "結婚紀念日" if "結婚" in before else "紀念日")
            annual.append({"label": label, "month": d.month, "day": d.day, "next": _iso(d)})
    if annual or explicit_dates(transcript, today):
        out["importantDates"] = annual

    rule_dates = followup_dates(transcript, today)
    if not rule_dates:
        return
    positions = {d: p for p, d, a in explicit_dates(transcript, today) if not a}
    positions.update({d: p for p, d in relative_dates(transcript, today)})
    model = [r for r in out["reminders"] if r["type"] not in ("BIRTHDAY", "ANNIVERSARY")]
    fixed, unused = [], list(rule_dates)
    for r in model:  # 模型日期對得上就保留
        d = dt.date.fromisoformat(r["date"])
        if d in unused:
            unused.remove(d)
            fixed.append(r)
    for r in model:  # 對不上的，依序改成逐字稿裡尚未用到的日期
        if r in fixed or not unused:
            continue
        d = unused.pop(0)
        fixed.append({**r, "date": _iso(d)})
    name = out["clientName"] or "客戶"
    for d in unused:  # 模型漏掉的日期，補一筆跟進
        t = _guess_type(transcript, positions.get(d, 0))
        title = {"MAINTENANCE": f"{name} 保養", "VISIT": f"{name} 回訪"}.get(t, f"跟進 {name}")
        fixed.append({"title": title, "type": t, "date": _iso(d), "repeat": "NONE"})
    out["reminders"] = sorted(fixed, key=lambda r: r["date"])
