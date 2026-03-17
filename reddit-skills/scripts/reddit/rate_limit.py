"""Rate-limit tracking for Reddit API calls."""

from __future__ import annotations

import json
import time
from pathlib import Path

STATE_DIR = Path.home() / ".reddit-skills" / "state"

# Reddit API limits: 100 requests/min for OAuth apps
MAX_REQUESTS_PER_MINUTE = 60  # conservative
MIN_COMMENT_INTERVAL_SECS = 120  # 2 min between comments (safety margin)
MAX_COMMENTS_PER_HOUR = 15
MAX_COMMENTS_PER_DAY = 50


def check_rate_limit() -> dict:
    """Check current rate-limit status.

    Returns dict with ok/blocked status and stats.
    """
    state = _load_state()
    now = time.time()

    # Clean old entries
    one_day_ago = now - 86400
    one_hour_ago = now - 3600
    state["comments"] = [t for t in state["comments"] if t > one_day_ago]

    comments_today = len(state["comments"])
    comments_this_hour = len([t for t in state["comments"] if t > one_hour_ago])

    last_comment = state["comments"][-1] if state["comments"] else 0
    secs_since_last = now - last_comment if last_comment else float("inf")

    blocked = False
    reason = ""

    if comments_today >= MAX_COMMENTS_PER_DAY:
        blocked = True
        reason = f"Daily limit reached ({comments_today}/{MAX_COMMENTS_PER_DAY})"
    elif comments_this_hour >= MAX_COMMENTS_PER_HOUR:
        blocked = True
        reason = f"Hourly limit reached ({comments_this_hour}/{MAX_COMMENTS_PER_HOUR})"
    elif secs_since_last < MIN_COMMENT_INTERVAL_SECS:
        blocked = True
        wait = int(MIN_COMMENT_INTERVAL_SECS - secs_since_last)
        reason = f"Too soon since last comment, wait {wait}s"

    _save_state(state)

    return {
        "status": "blocked" if blocked else "ok",
        "reason": reason,
        "comments_today": comments_today,
        "comments_this_hour": comments_this_hour,
        "secs_since_last_comment": int(secs_since_last) if secs_since_last != float("inf") else -1,
        "daily_limit": MAX_COMMENTS_PER_DAY,
        "hourly_limit": MAX_COMMENTS_PER_HOUR,
    }


def record_comment() -> None:
    """Record a comment action for rate tracking."""
    state = _load_state()
    state["comments"].append(time.time())
    _save_state(state)


def _load_state() -> dict:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / "rate_limit.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except json.JSONDecodeError:
            pass
    return {"comments": []}


def _save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / "rate_limit.json"
    state_file.write_text(json.dumps(state))
