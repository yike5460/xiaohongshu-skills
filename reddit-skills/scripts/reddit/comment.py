"""Reddit comment generation (AI) and posting."""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any

import praw

# State directory for dedup and rate tracking
STATE_DIR = Path.home() / ".reddit-skills" / "state"


def generate_comment(
    title: str,
    content: str,
    subreddit: str,
    author: str,
    product_info: str | None = None,
    is_promo: bool = False,
) -> str:
    """Generate a context-aware comment using AI.

    Tries Bedrock Claude first, then Gemini Flash as fallback.

    Args:
        title: Post title.
        content: Post body text (first 500 chars).
        subreddit: Subreddit name for tone matching.
        author: Post author username.
        product_info: Product/brand info to weave in (for promo comments).
        is_promo: Whether this is a promotional comment.
    """
    if is_promo and product_info:
        system_prompt = (
            "You are a Reddit user browsing posts and leaving comments. "
            "Your comment must:\n"
            "1. Be natural, conversational, and match the subreddit's tone\n"
            "2. First genuinely respond to the post (agree, ask a question, share experience)\n"
            "3. Then naturally mention the product/tool, as if sharing personal experience\n"
            "4. Length: 50-200 characters\n"
            "5. No marketing language ('best', 'amazing', 'check out', '#ad')\n"
            "6. Sound like a real user sharing a tip, not an advertisement\n"
            "7. Use Reddit conventions (casual tone, occasional humor)\n"
            f"\nProduct info to weave in naturally: {product_info}\n"
            "IMPORTANT: The comment must relate to the post content. "
            "The product mention should feel like a natural continuation."
        )
    else:
        system_prompt = (
            "You are a Reddit user browsing posts and leaving genuine comments. "
            "Your comment must:\n"
            "1. Be natural and match the subreddit's tone\n"
            "2. Add value: share experience, ask thoughtful question, or offer insight\n"
            "3. Length: 30-150 characters\n"
            "4. Use Reddit conventions (casual tone, occasional humor)\n"
            "5. No generic comments like 'great post' or 'thanks for sharing'\n"
            "6. Be specific to the post content"
        )

    user_prompt = (
        f"Subreddit: r/{subreddit}\n"
        f"Post title: {title}\n"
        f"Post content: {content[:500]}\n"
        f"Author: u/{author}\n\n"
        "Generate one comment:"
    )

    # Try Bedrock Claude first
    comment = _try_bedrock(system_prompt, user_prompt)
    if comment:
        return comment

    # Fallback: Gemini Flash
    comment = _try_gemini(system_prompt, user_prompt)
    if comment:
        return comment

    # Final fallback: template
    return _template_comment(title, is_promo, product_info)


def _try_bedrock(system_prompt: str, user_prompt: str) -> str | None:
    """Try generating via AWS Bedrock Claude."""
    try:
        import boto3

        client = boto3.client("bedrock-runtime", region_name="us-west-2")
        response = client.converse(
            modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={"maxTokens": 200},
        )
        return response["output"]["message"]["content"][0]["text"].strip()
    except Exception:
        return None


def _try_gemini(system_prompt: str, user_prompt: str) -> str | None:
    """Try generating via Google Gemini Flash."""
    try:
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            env_file = Path(__file__).parent.parent.parent / ".env"
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
        if not api_key:
            return None

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_prompt}\n\n{user_prompt}",
        )
        return response.text.strip()
    except Exception:
        return None


def _template_comment(title: str, is_promo: bool, product_info: str | None) -> str:
    """Fallback template comments."""
    organic = [
        "This is really insightful, thanks for putting this together.",
        "I've been thinking about this too. Would love to hear more perspectives.",
        "Solid points here. My experience has been pretty similar.",
        "Interesting take. What sources are you drawing from?",
    ]
    return random.choice(organic)


def post_comment(
    reddit: praw.Reddit,
    post_id: str,
    comment_text: str,
) -> dict[str, Any]:
    """Post a comment on a Reddit thread.

    Args:
        reddit: Authenticated PRAW instance (needs username/password).
        post_id: Reddit post ID.
        comment_text: The comment to post.

    Returns:
        Dict with comment details or error.
    """
    try:
        submission = reddit.submission(id=post_id)
        comment = submission.reply(comment_text)
        _record_comment(post_id, comment.id, comment_text)
        return {
            "status": "ok",
            "comment_id": comment.id,
            "post_id": post_id,
            "text": comment_text,
            "permalink": f"https://reddit.com{comment.permalink}",
        }
    except praw.exceptions.RedditAPIException as e:
        return {"status": "error", "message": str(e), "post_id": post_id}
    except Exception as e:
        return {"status": "error", "message": str(e), "post_id": post_id}


def reply_to_comment(
    reddit: praw.Reddit,
    comment_id: str,
    reply_text: str,
) -> dict[str, Any]:
    """Reply to a specific comment."""
    try:
        comment = reddit.comment(id=comment_id)
        reply = comment.reply(reply_text)
        return {
            "status": "ok",
            "reply_id": reply.id,
            "parent_comment_id": comment_id,
            "text": reply_text,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _record_comment(post_id: str, comment_id: str, text: str) -> None:
    """Record comment for deduplication."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    log_file = STATE_DIR / "comment_log.jsonl"
    entry = {
        "post_id": post_id,
        "comment_id": comment_id,
        "text": text[:100],
        "timestamp": time.time(),
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(entry) + "\n")


def get_commented_posts() -> set[str]:
    """Get set of post IDs we've already commented on."""
    log_file = STATE_DIR / "comment_log.jsonl"
    if not log_file.exists():
        return set()
    ids = set()
    for line in log_file.read_text().splitlines():
        try:
            entry = json.loads(line)
            ids.add(entry["post_id"])
        except (json.JSONDecodeError, KeyError):
            continue
    return ids
