"""Deterministic date parsing for Mandarin sales memos.

Small on-device models are unreliable at calendar arithmetic ("next Wednesday"), while the
phrases themselves are regular. So dates are resolved here, in code, and the LLM is only
asked what each follow-up is about.
"""
from __future__ import annotations

import datetime as dt
import re

_DIGITS = {"零": 0, "〇": 0, "一": 1, "二": 2, "兩": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
_WEEKDAY = {"一": 0, "二": 1, "三": 2, "四": 3, "五": 4, "六": 5, "日": 6, "天": 6}


def cn_number(s: str) -> int | None:
    """'11' / '十一' / '二十二' / '三十' → int (1–31)."""
    if s.isdigit():
        return int(s)
    if s == "十":
        return 10
    if "十" in s:
        tens, _, ones = s.partition("十")
        t = _DIGITS.get(tens, 1) if tens else 1
        o = _DIGITS.get(ones, 0) if ones else 0
        return t * 10 + o
    return _DIGITS.get(s)


NUM = r"(\d{1,2}|[一二兩三四五六七八九十]{1,3})"
MONTH_DAY = re.compile(NUM + r"\s*月\s*" + NUM + r"\s*[號日]")
RELATIVE = re.compile(r"(下下|下個|下|這個|這|本)?\s*(?:週|周|禮拜|星期)([一二三四五六日天])")
DATE_WORDS = ("生日", "紀念", "週年", "周年")


def _forward(month: int, day: int, today: dt.date) -> dt.date | None:
    for year in (today.year, today.year + 1):
        try:
            d = dt.date(year, month, day)
        except ValueError:
            continue
        if d >= today:
            return d
    return None


def explicit_dates(text: str, today: dt.date) -> list[tuple[int, dt.date, bool]]:
    """[(position, next occurrence, is_birthday_or_anniversary)] for every 'X月Y號' in the text."""
    out = []
    for m in MONTH_DAY.finditer(text):
        mo, dy = cn_number(m.group(1)), cn_number(m.group(2))
        if not mo or not dy or not (1 <= mo <= 12 and 1 <= dy <= 31):
            continue
        d = _forward(mo, dy, today)
        if d:
            before = text[max(0, m.start() - 8):m.start()]
            out.append((m.start(), d, any(w in before for w in DATE_WORDS)))
    return out


def relative_dates(text: str, today: dt.date) -> list[tuple[int, dt.date]]:
    out = []
    for m in RELATIVE.finditer(text):
        prefix, wd = m.group(1) or "", _WEEKDAY[m.group(2)]
        monday = today - dt.timedelta(days=today.weekday())
        weeks = 2 if prefix == "下下" else 1 if prefix.startswith("下") else 0
        d = monday + dt.timedelta(weeks=weeks, days=wd)
        if weeks == 0 and d < today:  # "週三" already passed this week → next week
            d += dt.timedelta(weeks=1)
        out.append((m.start(), d))
    for word, days in (("明天", 1), ("後天", 2)):
        for m in re.finditer(word, text):
            out.append((m.start(), today + dt.timedelta(days=days)))
    return out


def followup_dates(text: str, today: dt.date) -> list[dt.date]:
    """Dates that should become reminders: relative dates plus explicit dates not tied to a birthday/anniversary."""
    found = [(p, d) for p, d, annual in explicit_dates(text, today) if not annual] + relative_dates(text, today)
    seen, out = set(), []
    for _, d in sorted(found):
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out
