"""SQLite storage for reviewer decisions and timed evaluation sessions.

Decisions are append-only: there is no update or delete function on purpose.
A new connection is opened per call, so no connection is shared across threads.
"""
from __future__ import annotations

import os
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("RASD_DB_PATH", Path(__file__).resolve().parents[1] / "rasd.db"))

DECISIONS = ("CLEAR", "NEEDS_MORE_INFORMATION", "REFER_FOR_INTERNAL_REVIEW")
MODES = ("manual", "assisted")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tender_id TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('CLEAR','NEEDS_MORE_INFORMATION','REFER_FOR_INTERNAL_REVIEW')),
  reason TEXT NOT NULL,
  reviewer TEXT NOT NULL,
  priority_at_decision TEXT NOT NULL,
  alert_codes TEXT NOT NULL,
  engine_version TEXT NOT NULL,
  include_stretch INTEGER NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS timing_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tender_id TEXT NOT NULL,
  reviewer TEXT NOT NULL,
  mode TEXT NOT NULL CHECK (mode IN ('manual','assisted')),
  started_at TEXT NOT NULL,
  ended_at TEXT,
  seconds REAL
);
"""

MIN_REASON_CHARS = 10


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(_SCHEMA)
    conn.close()


def save_decision(tender_id: str, decision: str, reason: str, reviewer: str, priority_at_decision: str,
                  alert_codes: list[str] | str, engine_version: str, include_stretch: bool) -> dict:
    """Append one decision and return it as stored. Raises ValueError on invalid input."""
    reason = (reason or "").strip()
    reviewer = (reviewer or "").strip()
    if decision not in DECISIONS:
        raise ValueError(f"unknown decision {decision!r}")
    if len(reason) < MIN_REASON_CHARS:
        raise ValueError(f"reason must be at least {MIN_REASON_CHARS} characters")
    if not reviewer:
        raise ValueError("reviewer name is required")
    codes = alert_codes if isinstance(alert_codes, str) else ",".join(alert_codes)
    init_db()
    created = _now()
    conn = _connect()
    with conn:
        cur = conn.execute(
            "INSERT INTO decisions (tender_id, decision, reason, reviewer, priority_at_decision, alert_codes,"
            " engine_version, include_stretch, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (tender_id, decision, reason, reviewer, priority_at_decision, codes, engine_version,
             int(bool(include_stretch)), created),
        )
        row = conn.execute("SELECT * FROM decisions WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


def list_decisions(tender_id: str | None = None) -> list[dict]:
    """All decisions, newest first (optionally for one tender)."""
    init_db()
    conn = _connect()
    if tender_id is None:
        rows = conn.execute("SELECT * FROM decisions ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM decisions WHERE tender_id = ? ORDER BY id DESC", (tender_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def latest_decision(tender_id: str) -> dict | None:
    init_db()
    conn = _connect()
    row = conn.execute("SELECT * FROM decisions WHERE tender_id = ? ORDER BY id DESC LIMIT 1", (tender_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def start_timer(tender_id: str, reviewer: str, mode: str) -> int:
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    init_db()
    conn = _connect()
    with conn:
        cur = conn.execute(
            "INSERT INTO timing_sessions (tender_id, reviewer, mode, started_at) VALUES (?, ?, ?, ?)",
            (tender_id, reviewer or "", mode, _now()),
        )
    conn.close()
    return int(cur.lastrowid)


def stop_timer(session_id: int) -> float | None:
    """Close a timing session and return its duration in seconds (None if unknown or already closed)."""
    init_db()
    conn = _connect()
    row = conn.execute("SELECT started_at, ended_at FROM timing_sessions WHERE id = ?", (session_id,)).fetchone()
    if row is None or row["ended_at"] is not None:
        conn.close()
        return None
    ended = datetime.now(timezone.utc)
    seconds = (ended - datetime.fromisoformat(row["started_at"])).total_seconds()
    with conn:
        conn.execute("UPDATE timing_sessions SET ended_at = ?, seconds = ? WHERE id = ?",
                     (ended.isoformat(timespec="seconds"), seconds, session_id))
    conn.close()
    return seconds


def timing_summary() -> dict:
    """Median seconds per mode over completed sessions, and % reduction when both modes have data."""
    init_db()
    conn = _connect()
    rows = conn.execute("SELECT mode, seconds FROM timing_sessions WHERE seconds IS NOT NULL").fetchall()
    conn.close()
    by_mode = {m: [r["seconds"] for r in rows if r["mode"] == m] for m in MODES}
    out = {
        "n_manual": len(by_mode["manual"]),
        "n_assisted": len(by_mode["assisted"]),
        "median_manual": statistics.median(by_mode["manual"]) if by_mode["manual"] else None,
        "median_assisted": statistics.median(by_mode["assisted"]) if by_mode["assisted"] else None,
        "reduction_pct": None,
    }
    if out["median_manual"] and out["median_assisted"] is not None:
        out["reduction_pct"] = (out["median_manual"] - out["median_assisted"]) / out["median_manual"] * 100
    return out
