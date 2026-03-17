"""Reddit thread and subreddit discovery."""

from __future__ import annotations

from typing import Any

import praw

from .search import _submission_to_dict


def discover_subreddits(
    reddit: praw.Reddit,
    query: str,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Discover relevant subreddits by keyword.

    Returns list of subreddit dicts with name, subscribers, description.
    """
    results = []
    for sub in reddit.subreddits.search(query, limit=limit):
        results.append({
            "name": sub.display_name,
            "title": sub.title,
            "subscribers": sub.subscribers,
            "description": (sub.public_description or "")[:300],
            "url": f"https://reddit.com/r/{sub.display_name}",
            "over_18": sub.over18,
            "created_utc": sub.created_utc,
        })
    return results


def get_hot_threads(
    reddit: praw.Reddit,
    subreddit: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Get hot threads from a subreddit."""
    results = []
    for submission in reddit.subreddit(subreddit).hot(limit=limit):
        results.append(_submission_to_dict(submission))
    return results


def get_new_threads(
    reddit: praw.Reddit,
    subreddit: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Get new threads from a subreddit."""
    results = []
    for submission in reddit.subreddit(subreddit).new(limit=limit):
        results.append(_submission_to_dict(submission))
    return results


def get_rising_threads(
    reddit: praw.Reddit,
    subreddit: str,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Get rising threads from a subreddit (early engagement opportunities)."""
    results = []
    for submission in reddit.subreddit(subreddit).rising(limit=limit):
        results.append(_submission_to_dict(submission))
    return results


def get_post_detail(
    reddit: praw.Reddit,
    post_id: str,
    comment_limit: int = 20,
    comment_sort: str = "best",
) -> dict[str, Any]:
    """Get full post detail including top comments.

    Args:
        post_id: Reddit post ID (e.g., "1abc23").
        comment_limit: Max top-level comments to load.
        comment_sort: Sort order: best, top, new, controversial, old, q&a.
    """
    submission = reddit.submission(id=post_id)
    submission.comment_sort = comment_sort
    submission.comments.replace_more(limit=0)

    comments = []
    for comment in submission.comments[:comment_limit]:
        if hasattr(comment, "body"):
            comments.append({
                "id": comment.id,
                "author": str(comment.author) if comment.author else "[deleted]",
                "body": comment.body[:500],
                "score": comment.score,
                "created_utc": comment.created_utc,
                "is_submitter": comment.is_submitter,
                "replies_count": len(comment.replies),
            })

    post = _submission_to_dict(submission)
    post["selftext_full"] = submission.selftext
    post["comments"] = comments
    return post
