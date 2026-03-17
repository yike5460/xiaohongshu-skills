---
name: reddit-skills
description: Reddit marketing automation — keyword monitoring, thread discovery, AI comment generation
version: 0.1.0
metadata:
  openclaw:
    requires: [python3, uv]
    emoji: "🔴"
    os: [darwin, linux]
---

# Reddit Marketing Automation Skills

Three-stage pipeline for Reddit digital marketing:

1. **Monitor Keywords** — Track brand/competitor keywords, get daily digest
2. **Discover Threads** — Find relevant subreddits and threads for your product
3. **Generate Comments** — AI-generated comments matching community tone and guidelines

## Architecture

```
scripts/cli.py              # Unified CLI (13 subcommands, JSON output)
scripts/auto_marketing.py   # Full-auto marketing pipeline
scripts/reddit/
  auth.py                   # OAuth2 via PRAW
  search.py                 # Keyword search & monitoring
  discover.py               # Subreddit & thread discovery
  comment.py                # AI comment generation (Bedrock/Gemini) & posting
  rate_limit.py             # Rate-limit tracking & safety
```

## Setup

```bash
cd reddit-skills
uv sync
cp .env.example .env       # Fill in Reddit API credentials
```

## CLI Commands

| Command | Auth | Description |
|---------|------|-------------|
| `check-auth` | read | Verify API credentials |
| `search --query Q` | read | Search posts by keyword |
| `monitor --keywords K1,K2` | read | Monitor multiple keywords |
| `discover-subs --query Q` | read | Find relevant subreddits |
| `hot --subreddit SUB` | read | Get hot threads |
| `new --subreddit SUB` | read | Get new threads |
| `rising --subreddit SUB` | read | Get rising threads (early opportunities) |
| `post-detail --post-id ID` | read | Get post with comments |
| `generate-comment --title T` | none | AI-generate a comment |
| `post-comment --post-id ID --text T` | write | Post a comment |
| `reply-comment --comment-id ID --text T` | write | Reply to a comment |
| `rate-status` | none | Check rate-limit status |

## Safety Constraints

- **Rate limiting**: Max 50 comments/day, 15/hour, 2-min interval between comments
- **Deduplication**: Never comment on the same post twice
- **NSFW filter**: Auto-skip NSFW content
- **Dry run**: Always test with `--dry-run` first
- **Comment quality**: AI generates contextual comments, never generic spam
