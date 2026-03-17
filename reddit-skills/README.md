# reddit-skills

Reddit marketing automation Claude Code Skills using PRAW (Python Reddit API Wrapper).

Three-stage pipeline:
1. **Monitor Keywords** - Track brand/competitor keywords daily
2. **Discover Threads** - Find relevant subreddits and threads
3. **Generate Comments** - AI-generated contextual comments (Bedrock Claude / Gemini Flash)

## Quick Start

```bash
cd reddit-skills
uv sync
cp .env.example .env  # Add your Reddit API credentials
python scripts/cli.py check-auth --readonly
python scripts/cli.py search --query "legal AI" --subreddit "legaltech"
python scripts/auto_marketing.py --keywords "legal AI" --product-info "Your Product" --dry-run
```

## Skills

| Skill | Description |
|-------|-------------|
| `reddit-monitor` | Daily keyword monitoring and digest |
| `reddit-discover` | Subreddit and thread discovery |
| `reddit-engage` | AI comment generation and posting |
| `reddit-auto-marketing` | Full-auto pipeline with safety controls |
