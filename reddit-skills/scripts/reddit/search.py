"""Reddit keyword search and monitoring."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import praw


def search_posts(
    reddit: praw.Reddit,
    query: str,
    subreddit: str | None = None,
    sort: str = "relevance",
    time_filter: str = "week",
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search Reddit posts by keyword.

    Args:
        reddit: Authenticated PRAW instance.
        query: Search query string.
        subreddit: Restrict search to subreddit (None = all).
        sort: One of relevance, hot, top, new, comments.
        time_filter: One of all, day, hour, month, week, year.
        limit: Max results to return.

    Returns:
        List of post dicts with id, title, subreddit, score, url, etc.
    """
    target = reddit.subreddit(subreddit) if subreddit else reddit.subreddit("all")
    results = []

    for submission in target.search(query, sort=sort, time_filter=time_filter, limit=limit):
        results.append(_submission_to_dict(submission))

    return results


def monitor_keywords(
    reddit: praw.Reddit,
    keywords: list[str],
    subreddits: list[str] | None = None,
    time_filter: str = "day",
    limit_per_keyword: int = 10,
) -> dict[str, list[dict[str, Any]]]:
    """Monitor multiple keywords across subreddits.

    Returns a dict mapping each keyword to its matching posts.
    """
    results: dict[str, list[dict[str, Any]]] = {}

    for keyword in keywords:
        keyword_results = []
        subs = subreddits or [None]
        seen_ids: set[str] = set()

        for sub in subs:
            posts = search_posts(
                reddit, keyword, subreddit=sub, time_filter=time_filter, limit=limit_per_keyword
            )
            for post in posts:
                if post["id"] not in seen_ids:
                    seen_ids.add(post["id"])
                    keyword_results.append(post)

        results[keyword] = keyword_results

    return results


def _submission_to_dict(submission: praw.models.Submission) -> dict[str, Any]:
    """Convert a PRAW submission to a serializable dict."""
    created = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
    return {
        "id": submission.id,
        "title": submission.title,
        "selftext": submission.selftext[:500] if submission.selftext else "",
        "subreddit": str(submission.subreddit),
        "author": str(submission.author) if submission.author else "[deleted]",
        "score": submission.score,
        "upvote_ratio": submission.upvote_ratio,
        "num_comments": submission.num_comments,
        "url": f"https://reddit.com{submission.permalink}",
        "permalink": submission.permalink,
        "created_utc": created.isoformat(),
        "is_self": submission.is_self,
        "link_flair_text": submission.link_flair_text,
        "over_18": submission.over_18,
    }
