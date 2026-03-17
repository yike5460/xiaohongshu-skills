---
name: reddit-auto-marketing
description: Full-auto Reddit marketing pipeline with safety controls
version: 0.1.0
---

# Reddit Auto-Marketing

Automated pipeline: search keywords -> find threads -> generate AI comments -> post.

## Risk Warning

Automated commenting can lead to Reddit account suspension if done carelessly. Always:
- Start with `--dry-run` to review generated comments
- Keep `--max-comments` low (3-5 per run)
- Use conservative `--promo-ratio` (0.3-0.5)
- Run at most once per day

## Safety Protections

| Protection | Setting |
|-----------|---------|
| Daily comment limit | 50 |
| Hourly comment limit | 15 |
| Min interval between comments | 2 minutes |
| Post deduplication | Never comment twice on same post |
| NSFW filter | Auto-skip |
| Min post score | Configurable (default: 2) |

## Workflow

### 1. Dry Run First
```bash
cd reddit-skills && python scripts/auto_marketing.py \
  --keywords "legal AI,case management software" \
  --subreddits "legaltech,lawfirm" \
  --product-info "Supio - AI-powered legal case management for personal injury firms" \
  --promo-ratio 0.4 \
  --max-comments 5 \
  --time-filter day \
  --dry-run
```

Review the generated comments in the output.

### 2. Live Run (After Review)
```bash
python scripts/auto_marketing.py \
  --keywords "legal AI,case management software" \
  --subreddits "legaltech,lawfirm" \
  --product-info "Supio - AI-powered legal case management for personal injury firms" \
  --promo-ratio 0.4 \
  --max-comments 3 \
  --time-filter day
```

### 3. Check Results
```bash
python scripts/cli.py rate-status
python scripts/cli.py commented-posts
```

## Keyword Generalization

When the user gives a broad topic, expand to specific search terms:

**Example:** "Promote Supio to personal injury lawyers"
```
Keywords: personal injury software,PI case management,demand generation legal,
          legal AI tools,settlement calculator,case intake automation
Subreddits: legaltech,lawfirm,legal,personalinjury
```

## State Files

- `~/.reddit-skills/state/rate_limit.json` — Rate tracking
- `~/.reddit-skills/state/comment_log.jsonl` — Comment history for dedup
