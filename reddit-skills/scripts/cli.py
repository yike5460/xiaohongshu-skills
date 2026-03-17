#!/usr/bin/env python3
"""Unified CLI for Reddit marketing automation.

All commands output JSON. Exit codes: 0=success, 1=auth-error, 2=error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from reddit.auth import check_auth, get_reddit
from reddit.comment import (
    generate_comment,
    get_commented_posts,
    post_comment,
    reply_to_comment,
)
from reddit.discover import (
    discover_subreddits,
    get_hot_threads,
    get_new_threads,
    get_post_detail,
    get_rising_threads,
)
from reddit.rate_limit import check_rate_limit, record_comment
from reddit.search import monitor_keywords, search_posts


def _json_out(data: dict | list) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def cmd_check_auth(args: argparse.Namespace) -> int:
    result = check_auth(readonly=args.readonly)
    _json_out(result)
    return 0 if result["status"] == "ok" else 1


def cmd_search(args: argparse.Namespace) -> int:
    reddit = get_reddit(readonly=True)
    results = search_posts(
        reddit,
        query=args.query,
        subreddit=args.subreddit,
        sort=args.sort,
        time_filter=args.time_filter,
        limit=args.limit,
    )
    _json_out({"count": len(results), "posts": results})
    return 0


def cmd_monitor(args: argparse.Namespace) -> int:
    reddit = get_reddit(readonly=True)
    keywords = [k.strip() for k in args.keywords.split(",")]
    subreddits = [s.strip() for s in args.subreddits.split(",")] if args.subreddits else None
    results = monitor_keywords(
        reddit,
        keywords=keywords,
        subreddits=subreddits,
        time_filter=args.time_filter,
        limit_per_keyword=args.limit,
    )
    total = sum(len(v) for v in results.values())
    _json_out({"total_posts": total, "by_keyword": results})
    return 0


def cmd_discover_subs(args: argparse.Namespace) -> int:
    reddit = get_reddit(readonly=True)
    results = discover_subreddits(reddit, query=args.query, limit=args.limit)
    _json_out({"count": len(results), "subreddits": results})
    return 0


def cmd_hot(args: argparse.Namespace) -> int:
    reddit = get_reddit(readonly=True)
    results = get_hot_threads(reddit, subreddit=args.subreddit, limit=args.limit)
    _json_out({"subreddit": args.subreddit, "count": len(results), "posts": results})
    return 0


def cmd_new(args: argparse.Namespace) -> int:
    reddit = get_reddit(readonly=True)
    results = get_new_threads(reddit, subreddit=args.subreddit, limit=args.limit)
    _json_out({"subreddit": args.subreddit, "count": len(results), "posts": results})
    return 0


def cmd_rising(args: argparse.Namespace) -> int:
    reddit = get_reddit(readonly=True)
    results = get_rising_threads(reddit, subreddit=args.subreddit, limit=args.limit)
    _json_out({"subreddit": args.subreddit, "count": len(results), "posts": results})
    return 0


def cmd_post_detail(args: argparse.Namespace) -> int:
    reddit = get_reddit(readonly=True)
    result = get_post_detail(
        reddit,
        post_id=args.post_id,
        comment_limit=args.comment_limit,
        comment_sort=args.comment_sort,
    )
    _json_out(result)
    return 0


def cmd_generate_comment(args: argparse.Namespace) -> int:
    comment = generate_comment(
        title=args.title,
        content=args.content or "",
        subreddit=args.subreddit or "general",
        author=args.author or "unknown",
        product_info=args.product_info,
        is_promo=bool(args.product_info),
    )
    _json_out({"comment": comment})
    return 0


def cmd_post_comment(args: argparse.Namespace) -> int:
    # Check rate limit first
    rl = check_rate_limit()
    if rl["status"] == "blocked":
        _json_out({"status": "rate_limited", "reason": rl["reason"], "rate_limit": rl})
        return 2

    reddit = get_reddit(readonly=False)
    result = post_comment(reddit, post_id=args.post_id, comment_text=args.text)
    if result["status"] == "ok":
        record_comment()
    _json_out(result)
    return 0 if result["status"] == "ok" else 2


def cmd_reply_comment(args: argparse.Namespace) -> int:
    rl = check_rate_limit()
    if rl["status"] == "blocked":
        _json_out({"status": "rate_limited", "reason": rl["reason"]})
        return 2

    reddit = get_reddit(readonly=False)
    result = reply_to_comment(reddit, comment_id=args.comment_id, reply_text=args.text)
    if result["status"] == "ok":
        record_comment()
    _json_out(result)
    return 0 if result["status"] == "ok" else 2


def cmd_rate_status(_args: argparse.Namespace) -> int:
    _json_out(check_rate_limit())
    return 0


def cmd_commented_posts(_args: argparse.Namespace) -> int:
    posts = get_commented_posts()
    _json_out({"count": len(posts), "post_ids": sorted(posts)})
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Reddit marketing CLI")
    sub = parser.add_subparsers(dest="command")

    # Auth
    p = sub.add_parser("check-auth", help="Check authentication status")
    p.add_argument("--readonly", action="store_true")

    # Search
    p = sub.add_parser("search", help="Search posts by keyword")
    p.add_argument("--query", required=True)
    p.add_argument("--subreddit", default=None)
    p.add_argument("--sort", default="relevance", choices=["relevance", "hot", "top", "new", "comments"])
    p.add_argument("--time-filter", default="week", choices=["all", "day", "hour", "month", "week", "year"])
    p.add_argument("--limit", type=int, default=20)

    # Monitor
    p = sub.add_parser("monitor", help="Monitor multiple keywords")
    p.add_argument("--keywords", required=True, help="Comma-separated keywords")
    p.add_argument("--subreddits", default=None, help="Comma-separated subreddits")
    p.add_argument("--time-filter", default="day")
    p.add_argument("--limit", type=int, default=10)

    # Discover subreddits
    p = sub.add_parser("discover-subs", help="Find relevant subreddits")
    p.add_argument("--query", required=True)
    p.add_argument("--limit", type=int, default=10)

    # Hot/New/Rising threads
    for name in ("hot", "new", "rising"):
        p = sub.add_parser(name, help=f"Get {name} threads from subreddit")
        p.add_argument("--subreddit", required=True)
        p.add_argument("--limit", type=int, default=25)

    # Post detail
    p = sub.add_parser("post-detail", help="Get full post with comments")
    p.add_argument("--post-id", required=True)
    p.add_argument("--comment-limit", type=int, default=20)
    p.add_argument("--comment-sort", default="best")

    # Generate comment (AI)
    p = sub.add_parser("generate-comment", help="AI-generate a comment")
    p.add_argument("--title", required=True)
    p.add_argument("--content", default="")
    p.add_argument("--subreddit", default="general")
    p.add_argument("--author", default="unknown")
    p.add_argument("--product-info", default=None)

    # Post comment
    p = sub.add_parser("post-comment", help="Post a comment on a thread")
    p.add_argument("--post-id", required=True)
    p.add_argument("--text", required=True)

    # Reply to comment
    p = sub.add_parser("reply-comment", help="Reply to a comment")
    p.add_argument("--comment-id", required=True)
    p.add_argument("--text", required=True)

    # Rate limit status
    sub.add_parser("rate-status", help="Check rate-limit status")

    # Commented posts
    sub.add_parser("commented-posts", help="List posts already commented on")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 2

    handlers = {
        "check-auth": cmd_check_auth,
        "search": cmd_search,
        "monitor": cmd_monitor,
        "discover-subs": cmd_discover_subs,
        "hot": cmd_hot,
        "new": cmd_new,
        "rising": cmd_rising,
        "post-detail": cmd_post_detail,
        "generate-comment": cmd_generate_comment,
        "post-comment": cmd_post_comment,
        "reply-comment": cmd_reply_comment,
        "rate-status": cmd_rate_status,
        "commented-posts": cmd_commented_posts,
    }

    try:
        return handlers[args.command](args)
    except Exception as e:
        _json_out({"status": "error", "message": str(e)})
        return 2


if __name__ == "__main__":
    sys.exit(main())
