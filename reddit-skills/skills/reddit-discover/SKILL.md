---
name: reddit-discover
description: Discover relevant Reddit threads and subreddits for product marketing
version: 0.1.0
---

# Reddit Thread Discovery

Find the best threads and subreddits for product engagement.

## When to Use

- User wants to find relevant communities (e.g., "find subreddits for our product")
- User wants engagement opportunities (e.g., "find threads where I can mention Supio")
- User needs to understand a subreddit's culture before engaging

## Workflow

### 1. Discover Relevant Subreddits
```bash
cd reddit-skills && python scripts/cli.py discover-subs --query "personal injury law" --limit 10
```

### 2. Scout Subreddit Activity
For each promising subreddit, check activity patterns:
```bash
python scripts/cli.py hot --subreddit "legaltech" --limit 15
python scripts/cli.py rising --subreddit "legaltech" --limit 10
python scripts/cli.py new --subreddit "legaltech" --limit 10
```

**Priority**: Rising threads are the best engagement targets (growing visibility, few comments).

### 3. Search for Product-Relevant Threads
```bash
python scripts/cli.py search \
  --query "case management software" \
  --subreddit "legaltech" \
  --sort relevance \
  --time-filter month \
  --limit 20
```

### 4. Analyze Thread Context
Before engaging, read the full thread:
```bash
python scripts/cli.py post-detail --post-id "1abc23" --comment-limit 30 --comment-sort best
```

Check:
- Is the community receptive to product mentions?
- What's the thread's tone (asking for recommendations vs venting)?
- Are competitors already mentioned?
- Is the thread still active (new comments)?

### 5. Present Opportunities
Rank threads by engagement potential:
- **Score**: High-score threads = more visibility
- **Comment count**: Low comments = more room for engagement
- **Recency**: Fresh threads get more attention
- **Relevance**: Direct product-fit threads first
