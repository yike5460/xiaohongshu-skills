"""Reddit authentication via PRAW (OAuth2)."""

from __future__ import annotations

import os
from pathlib import Path

import praw

_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


def _load_env() -> None:
    """Load .env file into os.environ if present."""
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


def get_reddit(readonly: bool = False) -> praw.Reddit:
    """Create an authenticated PRAW Reddit instance.

    Args:
        readonly: If True, use read-only (app-only) auth.
                  If False, use script-type auth with username/password.
    """
    _load_env()

    client_id = os.environ.get("REDDIT_CLIENT_ID", "")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "")
    user_agent = os.environ.get("REDDIT_USER_AGENT", "reddit-skills/0.1.0")

    if not client_id or not client_secret:
        raise RuntimeError("REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET must be set in .env")

    if readonly:
        return praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

    username = os.environ.get("REDDIT_USERNAME", "")
    password = os.environ.get("REDDIT_PASSWORD", "")

    if not username or not password:
        raise RuntimeError(
            "REDDIT_USERNAME and REDDIT_PASSWORD required for authenticated actions. "
            "Set them in .env or use --readonly for read-only operations."
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
        username=username,
        password=password,
    )


def check_auth(readonly: bool = False) -> dict:
    """Check authentication status."""
    try:
        reddit = get_reddit(readonly=readonly)
        if readonly:
            # Test with a simple API call
            reddit.subreddit("test").id
            return {"status": "ok", "mode": "readonly", "message": "Read-only auth successful"}
        else:
            user = reddit.user.me()
            return {
                "status": "ok",
                "mode": "authenticated",
                "username": str(user),
                "karma": {"comment": user.comment_karma, "link": user.link_karma},
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
