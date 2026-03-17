#!/usr/bin/env python3
"""Auto-marketing pipeline for Reddit.

Full-auto flow: monitor keywords -> discover threads -> generate & post comments.
Mirrors xiaohongshu-skills/scripts/auto_marketing.py pattern.
"""

from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reddit.auth import get_reddit
from reddit.comment import generate_comment, get_commented_posts, post_comment
from reddit.rate_limit import check_rate_limit, record_comment
from reddit.search import search_posts

STATE_DIR = Path.home() / ".reddit-skills" / "state"


def run_marketing(
    keywords: list[str],
    subreddits: list[str] | None = None,
    product_info: str | None = None,
    promo_ratio: float = 0.5,
    max_comments: int = 5,
    time_filter: str = "day",
    limit_per_keyword: int = 10,
    dry_run: bool = False,
    min_score: int = 2,
) -> dict:
    """Run the full auto-marketing pipeline.

    Args:
        keywords: Keywords to search for.
        subreddits: Target subreddits (None = search all).
        product_info: Product info for promo comments.
        promo_ratio: Fraction of comments that include product mention (0.0-1.0).
        max_comments: Max comments to post per run.
        time_filter: Time filter for search (day, week, month).
        limit_per_keyword: Max posts per keyword to consider.
        dry_run: If True, generate but don't post comments.
        min_score: Minimum post score to consider (skip low-quality).
    """
    results = {
        "keywords_searched": [],
        "posts_found": 0,
        "posts_skipped": 0,
        "comments_generated": [],
        "comments_posted": [],
        "errors": [],
    }

    # Check rate limit before starting
    rl = check_rate_limit()
    if rl["status"] == "blocked":
        results["errors"].append(f"Rate limited: {rl['reason']}")
        return results

    commented_posts = get_commented_posts()
    reddit_ro = get_reddit(readonly=True)
    reddit_rw = get_reddit(readonly=False) if not dry_run else None
    comments_posted = 0

    for keyword in keywords:
        results["keywords_searched"].append(keyword)
        subs = subreddits or [None]

        for sub in subs:
            posts = search_posts(
                reddit_ro, keyword, subreddit=sub,
                sort="relevance", time_filter=time_filter,
                limit=limit_per_keyword,
            )
            results["posts_found"] += len(posts)

            for post in posts:
                if comments_posted >= max_comments:
                    break

                # Skip if already commented
                if post["id"] in commented_posts:
                    results["posts_skipped"] += 1
                    continue

                # Skip low-score posts
                if post["score"] < min_score:
                    results["posts_skipped"] += 1
                    continue

                # Skip NSFW
                if post.get("over_18"):
                    results["posts_skipped"] += 1
                    continue

                # Check rate limit
                rl = check_rate_limit()
                if rl["status"] == "blocked":
                    results["errors"].append(f"Rate limited mid-run: {rl['reason']}")
                    return results

                # Decide promo vs organic
                is_promo = random.random() < promo_ratio and product_info

                # Generate comment
                try:
                    comment_text = generate_comment(
                        title=post["title"],
                        content=post.get("selftext", ""),
                        subreddit=post["subreddit"],
                        author=post["author"],
                        product_info=product_info if is_promo else None,
                        is_promo=bool(is_promo),
                    )
                except Exception as e:
                    results["errors"].append(f"Generate failed for {post['id']}: {e}")
                    continue

                entry = {
                    "post_id": post["id"],
                    "post_title": post["title"],
                    "subreddit": post["subreddit"],
                    "comment": comment_text,
                    "is_promo": bool(is_promo),
                }
                results["comments_generated"].append(entry)

                if dry_run:
                    entry["status"] = "dry_run"
                    continue

                # Post the comment
                try:
                    assert reddit_rw is not None  # guarded by dry_run check above
                    post_result = post_comment(reddit_rw, post["id"], comment_text)
                    if post_result["status"] == "ok":
                        record_comment()
                        commented_posts.add(post["id"])
                        comments_posted += 1
                        entry["status"] = "posted"
                        entry["comment_id"] = post_result["comment_id"]
                        entry["permalink"] = post_result.get("permalink", "")
                        results["comments_posted"].append(entry)

                        # Random delay between comments (2-5 minutes)
                        if comments_posted < max_comments:
                            delay = random.randint(120, 300)
                            print(
                                f"  Posted comment {comments_posted}/{max_comments}. "
                                f"Waiting {delay}s...",
                                file=sys.stderr,
                            )
                            time.sleep(delay)
                    else:
                        entry["status"] = "failed"
                        entry["error"] = post_result.get("message", "")
                        results["errors"].append(
                            f"Post failed for {post['id']}: {post_result.get('message')}"
                        )
                except Exception as e:
                    entry["status"] = "error"
                    results["errors"].append(f"Post error for {post['id']}: {e}")

            if comments_posted >= max_comments:
                break
        if comments_posted >= max_comments:
            break

    results["total_comments_posted"] = comments_posted
    return results


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Reddit auto-marketing pipeline")
    parser.add_argument("--keywords", required=True, help="Comma-separated keywords")
    parser.add_argument("--subreddits", default=None, help="Comma-separated subreddits")
    parser.add_argument("--product-info", default=None, help="Product info for promo comments")
    parser.add_argument("--promo-ratio", type=float, default=0.5)
    parser.add_argument("--max-comments", type=int, default=5)
    parser.add_argument("--time-filter", default="day")
    parser.add_argument("--limit-per-keyword", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true", help="Generate but don't post")
    parser.add_argument("--min-score", type=int, default=2)

    args = parser.parse_args()
    keywords = [k.strip() for k in args.keywords.split(",")]
    subreddits = [s.strip() for s in args.subreddits.split(",")] if args.subreddits else None

    results = run_marketing(
        keywords=keywords,
        subreddits=subreddits,
        product_info=args.product_info,
        promo_ratio=args.promo_ratio,
        max_comments=args.max_comments,
        time_filter=args.time_filter,
        limit_per_keyword=args.limit_per_keyword,
        dry_run=args.dry_run,
        min_score=args.min_score,
    )

    print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
    return 0 if not results["errors"] else 2


if __name__ == "__main__":
    sys.exit(main())
