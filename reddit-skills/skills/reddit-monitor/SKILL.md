---
name: reddit-monitor
description: Monitor brand/competitor keywords on Reddit and report daily findings
version: 0.1.0
---

# Reddit Keyword Monitor

Track keywords across Reddit and surface the latest relevant threads.

## When to Use

- User wants to track brand mentions (e.g., "monitor Supio mentions on Reddit")
- User wants competitor intelligence (e.g., "what are people saying about EvenUp")
- User wants daily keyword digest

## Workflow

### 1. Expand Keywords
Generalize the user's intent into 3-8 search keywords:

**Example:**
- User: "Track what people say about legal AI tools"
- Keywords: `legal AI,legal tech,AI case management,litigation software,law firm automation,AI legal research`

### 2. Identify Target Subreddits (Optional)
```bash
cd reddit-skills && python scripts/cli.py discover-subs --query "legal technology" --limit 10
```

### 3. Run Keyword Monitor
```bash
python scripts/cli.py monitor \
  --keywords "legal AI,legal tech,AI case management" \
  --subreddits "legaltech,lawfirm,legal" \
  --time-filter day \
  --limit 10
```

### 4. Deep-Dive on Interesting Posts
```bash
python scripts/cli.py post-detail --post-id "1abc23" --comment-limit 30
```

### 5. Present Results
Format findings as a digest:
- **Trending**: Posts with high score/comment ratio
- **New Opportunities**: Rising threads with few comments
- **Competitor Mentions**: Posts mentioning competitor products
- **Sentiment**: Overall tone (positive/negative/neutral)

## Output Format

Present as a structured report with links and key quotes.
