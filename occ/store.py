"""On-device storage. A single SQLite file; nothing is synced to a server."""
from __future__ import annotations

import json
import sqlite3
import time

DDL = """
CREATE TABLE IF NOT EXISTS memos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at REAL NOT NULL,
  client_name TEXT,
  transcript TEXT NOT NULL,
  record_json TEXT NOT NULL,
  stt_model TEXT, llm_model TEXT, total_s REAL
);
"""


class Store:
    def __init__(self, path: str = "occ.sqlite3"):
        self.db = sqlite3.connect(path)
        self.db.execute(DDL)

    def save(self, result) -> int:
        cur = self.db.execute(
            "INSERT INTO memos (created_at, client_name, transcript, record_json, stt_model, llm_model, total_s) VALUES (?,?,?,?,?,?,?)",
            (time.time(), result.record.get("clientName"), result.transcript, json.dumps(result.record, ensure_ascii=False),
             result.stt_model, result.llm_model, result.timing.total_s),
        )
        self.db.commit()
        return cur.lastrowid
