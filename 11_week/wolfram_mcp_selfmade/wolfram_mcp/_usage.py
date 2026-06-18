"""
wolfram_mcp._usage
==================

A tiny, best-effort usage tracker for the free Wolfram quota
(2,000 non-commercial calls/month; ~100/day is the commonly observed soft cap).

Design goals
------------
* **Never break a query.** Every operation is wrapped so a tracking failure
  (read-only FS, race, corrupt file) is swallowed and tracking simply degrades.
* **Approximate, local, advisory.** This is *not* authoritative billing — only
  Wolfram knows your real count. It just helps you avoid surprises.

State is a small JSON file. Path resolution order:
1. ``WOLFRAM_USAGE_FILE`` env var, if set.
2. ``$XDG_STATE_HOME/wolfram-mcp/usage.json`` if XDG is set.
3. ``~/.local/state/wolfram-mcp/usage.json``.

Set ``WOLFRAM_USAGE_FILE=off`` (or ``WOLFRAM_TRACK_USAGE=0``) to disable.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import threading
from pathlib import Path
from typing import Any

# Default free-tier limits (override via env if your plan differs).
MONTHLY_LIMIT = int(os.environ.get("WOLFRAM_MONTHLY_LIMIT", "2000"))
DAILY_LIMIT = int(os.environ.get("WOLFRAM_DAILY_LIMIT", "100"))

_LOCK = threading.Lock()


def _enabled() -> bool:
    if os.environ.get("WOLFRAM_TRACK_USAGE", "1") in ("0", "false", "False"):
        return False
    if os.environ.get("WOLFRAM_USAGE_FILE", "").lower() == "off":
        return False
    return True


def _path() -> Path:
    env = os.environ.get("WOLFRAM_USAGE_FILE")
    if env:
        return Path(env).expanduser()
    xdg = os.environ.get("XDG_STATE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".local" / "state"
    return base / "wolfram-mcp" / "usage.json"


def _today() -> str:
    return _dt.date.today().isoformat()


def _month() -> str:
    return _dt.date.today().strftime("%Y-%m")


def _load(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data))
    tmp.replace(path)


def record(endpoint: str = "") -> None:
    """Increment today's and this month's counters. Never raises."""
    if not _enabled():
        return
    try:
        with _LOCK:
            path = _path()
            data = _load(path)
            day, month = _today(), _month()
            if data.get("day") != day:
                data["day"] = day
                data["day_count"] = 0
            if data.get("month") != month:
                data["month"] = month
                data["month_count"] = 0
            data["day_count"] = int(data.get("day_count", 0)) + 1
            data["month_count"] = int(data.get("month_count", 0)) + 1
            by_ep = data.setdefault("by_endpoint", {})
            if endpoint:
                by_ep[endpoint] = int(by_ep.get(endpoint, 0)) + 1
            _save(path, data)
    except Exception:
        # Tracking is advisory; swallow everything.
        pass


def stats() -> dict[str, Any]:
    """Return current advisory usage stats. Never raises."""
    if not _enabled():
        return {"tracking": False}
    try:
        data = _load(_path())
        day, month = _today(), _month()
        day_count = int(data.get("day_count", 0)) if data.get("day") == day else 0
        month_count = (
            int(data.get("month_count", 0)) if data.get("month") == month else 0
        )
        return {
            "tracking": True,
            "today": day,
            "month": month,
            "calls_today": day_count,
            "calls_this_month": month_count,
            "daily_limit": DAILY_LIMIT,
            "monthly_limit": MONTHLY_LIMIT,
            "remaining_today": max(DAILY_LIMIT - day_count, 0),
            "remaining_this_month": max(MONTHLY_LIMIT - month_count, 0),
            "by_endpoint": data.get("by_endpoint", {}) if data.get("month") == month else {},
            "note": "Advisory local estimate only; Wolfram is the source of truth.",
        }
    except Exception:
        return {"tracking": False}


def warning() -> str:
    """Return a short warning string if near a limit, else empty string."""
    s = stats()
    if not s.get("tracking"):
        return ""
    msgs = []
    if s["remaining_this_month"] <= 0:
        msgs.append("Monthly free quota (2,000) appears exhausted.")
    elif s["remaining_this_month"] <= 100:
        msgs.append(f"Only ~{s['remaining_this_month']} monthly free calls left.")
    if s["remaining_today"] <= 0:
        msgs.append("Daily soft cap (~100) appears reached.")
    elif s["remaining_today"] <= 10:
        msgs.append(f"Only ~{s['remaining_today']} calls left today.")
    return " ".join(msgs)
