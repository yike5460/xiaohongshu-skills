#!/usr/bin/env python3
"""Post content to a specific platform.

Usage:
    python platform_poster.py <platform> <content_file.json> [--dry-run]

Supports: x, discord, reddit, producthunt, xiaohongshu, zhihu.
For platforms without API support (producthunt, xiaohongshu, zhihu),
outputs formatted content for manual posting.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

SUPPORTED_PLATFORMS = {"x", "discord", "reddit", "producthunt", "xiaohongshu", "zhihu"}
MANUAL_PLATFORMS = {"producthunt", "xiaohongshu", "zhihu"}


def check_env_vars(required: list, platform: str) -> None:
    """Check that all required environment variables are set.

    Raises:
        SystemExit: If any required env vars are missing.
    """
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        logger.error(
            "Missing environment variables for %s: %s. "
            "Set them in your .env file or export them.",
            platform, ", ".join(missing),
        )
        sys.exit(1)


def post_to_x(content: dict | list | str, dry_run: bool) -> dict:
    """Post a thread to X/Twitter using tweepy."""
    if not dry_run:
        # Support Bearer-token-only auth or full OAuth 1.0a
        has_oauth = all(os.environ.get(v) for v in
                        ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"])
        has_bearer = bool(os.environ.get("X_BEARER_TOKEN"))
        if not has_oauth and not has_bearer:
            check_env_vars(
                ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"],
                "X/Twitter",
            )

    # Normalize content to a list of tweet strings
    if isinstance(content, str):
        tweets = [content]
    elif isinstance(content, list):
        tweets = content
    elif isinstance(content, dict) and "tweets" in content:
        tweets = content["tweets"]
    else:
        tweets = [json.dumps(content)]

    if dry_run:
        for i, tweet in enumerate(tweets, 1):
            logger.info("[DRY RUN] X Tweet %d/%d (%d chars): %s",
                        i, len(tweets), len(tweet), tweet[:100])
        return {"status": "dry_run", "tweet_count": len(tweets)}

    import tweepy

    # Prefer OAuth 1.0a (user context), fall back to Bearer token
    has_oauth = all(os.environ.get(v) for v in
                    ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"])
    if has_oauth:
        client_v2 = tweepy.Client(
            consumer_key=os.environ["X_API_KEY"],
            consumer_secret=os.environ["X_API_SECRET"],
            access_token=os.environ["X_ACCESS_TOKEN"],
            access_token_secret=os.environ["X_ACCESS_SECRET"],
        )
    else:
        client_v2 = tweepy.Client(bearer_token=os.environ["X_BEARER_TOKEN"])

    prev_id = None
    posted_ids = []
    for i, tweet_text in enumerate(tweets, 1):
        resp = client_v2.create_tweet(text=tweet_text, in_reply_to_tweet_id=prev_id)
        tweet_id = resp.data["id"]
        posted_ids.append(tweet_id)
        prev_id = tweet_id
        logger.info("Posted tweet %d/%d (id: %s)", i, len(tweets), tweet_id)

    return {"status": "posted", "tweet_ids": posted_ids}


def post_to_discord(content: dict | str, dry_run: bool) -> dict:
    """Post a message to Discord via webhook URL."""
    if not dry_run:
        required_vars = ["DISCORD_WEBHOOK_URL"]
        check_env_vars(required_vars, "Discord")

    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]

    if isinstance(content, str):
        message = content
    elif isinstance(content, dict) and "message" in content:
        message = content["message"]
    else:
        message = json.dumps(content, ensure_ascii=False)

    if dry_run:
        logger.info("[DRY RUN] Discord message (%d chars): %s",
                    len(message), message[:200])
        return {"status": "dry_run", "content_length": len(message)}

    import requests

    payload = {"content": message}

    # Support rich embeds if content provides them
    if isinstance(content, dict) and "embeds" in content:
        payload = {"content": content.get("content", ""), "embeds": content["embeds"]}

    resp = requests.post(webhook_url, json=payload)
    resp.raise_for_status()

    logger.info("Posted to Discord webhook")
    return {"status": "posted"}


def post_to_reddit(content: dict, dry_run: bool) -> dict:
    """Post to Reddit using praw with proper OAuth2 script-app auth.

    Follows Reddit API rules:
    - OAuth2 mandatory (handled by PRAW's password flow for script apps)
    - Descriptive User-Agent: <platform>:<app_id>:<version> (by /u/<username>)
    - Rate limit: 60 req/min (PRAW handles automatically)
    - 2FA supported: append :TOTP_TOKEN to password if enabled
    """
    if not dry_run:
        required_vars = [
            "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET",
            "REDDIT_USERNAME", "REDDIT_PASSWORD",
        ]
        check_env_vars(required_vars, "Reddit")

    title = content.get("title", "")
    body = content.get("body", "")
    subreddits = content.get("suggested_subreddits", ["SideProject"])

    # Strip r/ prefix if present (content generator may include it)
    subreddits = [s.removeprefix("r/") for s in subreddits]

    # Validate title length (Reddit max 300 chars)
    if len(title) > 300:
        logger.warning("Reddit title exceeds 300 chars (%d), truncating", len(title))
        title = title[:297] + "..."

    if dry_run:
        logger.info("[DRY RUN] Reddit post to r/%s", ", r/".join(subreddits))
        logger.info("[DRY RUN] Title (%d chars): %s", len(title), title[:100])
        logger.info("[DRY RUN] Body (%d chars): %s", len(body), body[:200])
        return {"status": "dry_run", "subreddits": subreddits}

    import praw

    username = os.environ["REDDIT_USERNAME"]

    # Reddit API requires a descriptive user-agent; generic agents get rate-limited
    # Format: <platform>:<app_id>:<version> (by /u/<username>)
    user_agent = f"python:social-media-promoter:v1.0.0 (by /u/{username})"

    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=username,
        password=os.environ["REDDIT_PASSWORD"],
        user_agent=user_agent,
    )

    # Verify authentication before posting
    try:
        me = reddit.user.me()
        logger.info("Authenticated as u/%s", me.name)
    except Exception as exc:
        raise RuntimeError(
            f"Reddit authentication failed: {exc}. "
            "If 2FA is enabled, set REDDIT_PASSWORD to 'password:TOTP_TOKEN'."
        ) from exc

    posted = []
    for sub_name in subreddits:
        try:
            subreddit = reddit.subreddit(sub_name)
            submission = subreddit.submit(title=title, selftext=body)
            url = f"https://www.reddit.com{submission.permalink}"
            posted.append({"subreddit": sub_name, "id": submission.id, "url": url})
            logger.info("Posted to r/%s: %s", sub_name, url)
        except Exception as exc:
            logger.error("Failed to post to r/%s: %s", sub_name, exc)
            posted.append({"subreddit": sub_name, "error": str(exc)})

    return {"status": "posted", "submissions": posted}


def output_manual_content(platform: str, content: dict | str, dry_run: bool) -> dict:
    """Output formatted content for manual posting (producthunt, xiaohongshu, zhihu)."""
    platform_labels = {
        "producthunt": "Product Hunt",
        "xiaohongshu": "Xiaohongshu (Little Red Book)",
        "zhihu": "Zhihu (知乎)",
    }
    label = platform_labels.get(platform, platform)
    prefix = "[DRY RUN] " if dry_run else ""

    logger.info(
        "%s%s: Automated posting not supported. Content formatted for manual submission:",
        prefix, label,
    )

    if isinstance(content, str):
        formatted = content
    else:
        formatted = json.dumps(content, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"  {label} - Content for Manual Posting")
    print(f"{'=' * 60}")
    print(formatted)
    print(f"{'=' * 60}\n")

    if platform == "producthunt":
        logger.info("Submit at: https://www.producthunt.com/posts/new")

    status = "dry_run" if dry_run else "manual"
    return {"status": status, "platform": platform, "content_length": len(formatted)}


PLATFORM_ADAPTERS = {
    "x": post_to_x,
    "discord": post_to_discord,
    "reddit": post_to_reddit,
}


def post_content(platform: str, content_file: Path, dry_run: bool) -> dict:
    """Route content to the appropriate platform adapter.

    Returns:
        Result dict with status and platform-specific details.
    """
    with open(content_file, encoding="utf-8") as f:
        content = json.load(f)

    if platform in MANUAL_PLATFORMS:
        return output_manual_content(platform, content, dry_run)

    adapter = PLATFORM_ADAPTERS.get(platform)
    if not adapter:
        logger.error("No adapter for platform: %s", platform)
        return {"status": "error", "error": f"Unsupported platform: {platform}"}

    return adapter(content, dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post content to a social media platform")
    parser.add_argument(
        "platform",
        choices=sorted(SUPPORTED_PLATFORMS),
        help="Target platform",
    )
    parser.add_argument("content_file", type=Path, help="Path to content JSON file")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    args = parser.parse_args()

    if not args.content_file.exists():
        logger.error("Content file not found: %s", args.content_file)
        sys.exit(1)

    result = post_content(args.platform, args.content_file, args.dry_run)
    print(json.dumps(result, indent=2))
