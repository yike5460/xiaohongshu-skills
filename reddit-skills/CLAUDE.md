# reddit-skills

Reddit marketing automation Claude Code Skills, using PRAW (Python Reddit API Wrapper).

## Dev Commands

```bash
cd reddit-skills
uv sync                    # Install dependencies
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run pytest              # Tests
```

## Architecture

Dual-layer: `scripts/` is the Python automation engine, `skills/` are Claude Code Skill definitions.

- `scripts/reddit/` — Core library (modular, one file per feature)
- `scripts/cli.py` — Unified CLI, 13 subcommands, JSON output
- `scripts/auto_marketing.py` — Full-auto pipeline
- `skills/*/SKILL.md` — Guide Claude on how to invoke scripts

### Invocation

```bash
python scripts/cli.py check-auth --readonly
python scripts/cli.py search --query "legal AI" --subreddit "legaltech"
python scripts/cli.py monitor --keywords "supio,legal ai,case management"
python scripts/auto_marketing.py --keywords "legal AI" --product-info "Supio" --dry-run
```

## Code Rules

- Line length max 100 chars
- Type hints with `from __future__ import annotations`
- CLI exit code: 0=success, 1=auth-error, 2=error
- JSON output with `ensure_ascii=False`
- Rate-limit state in `~/.reddit-skills/state/`

## CLI Subcommand Reference

| CLI | Category |
|-----|----------|
| `check-auth` | Auth |
| `search` | Discovery |
| `monitor` | Monitoring |
| `discover-subs` | Discovery |
| `hot` / `new` / `rising` | Discovery |
| `post-detail` | Discovery |
| `generate-comment` | AI Generation |
| `post-comment` | Engagement |
| `reply-comment` | Engagement |
| `rate-status` | Safety |
| `commented-posts` | Safety |
