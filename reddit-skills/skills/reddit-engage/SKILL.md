---
name: reddit-engage
description: Generate and post contextual comments on Reddit threads
version: 0.1.0
---

# Reddit Engagement

Generate high-quality, contextual comments and post them on Reddit threads.

## When to Use

- User wants to engage with specific threads
- User wants AI-generated comments for review before posting
- User wants to reply to specific comments

## Safety Rules

1. **Always generate before posting** — show the user the AI comment for approval
2. **Check rate limits** before every action: `python scripts/cli.py rate-status`
3. **Never spam** — respect 2-min minimum between comments
4. **Match community tone** — casual in meme subs, professional in industry subs
5. **Disclose when required** — some subreddits require disclosure of affiliations

## Workflow

### 1. Check Rate Limits
```bash
cd reddit-skills && python scripts/cli.py rate-status
```

### 2. Generate Comment (Review First)
```bash
python scripts/cli.py generate-comment \
  --title "Best case management tools for small firms?" \
  --content "Looking for recommendations..." \
  --subreddit "legaltech" \
  --author "some_user" \
  --product-info "Supio - AI-powered legal case management"
```

**Show the generated comment to the user for approval before posting.**

### 3. Post Comment (After Approval)
```bash
python scripts/cli.py post-comment \
  --post-id "1abc23" \
  --text "The approved comment text here"
```

### 4. Reply to a Comment
```bash
python scripts/cli.py reply-comment \
  --comment-id "xyz789" \
  --text "Reply text here"
```

### 5. Check Dedup Status
```bash
python scripts/cli.py commented-posts
```

## Comment Quality Guidelines

- **Organic comments**: Add genuine value — share experience, ask questions, offer insights
- **Promo comments**: Must relate to post content; product mention feels like personal experience
- **Length**: 50-200 chars. Too short = low effort. Too long = TL;DR
- **Avoid**: Marketing buzzwords, links in first comment, "check out", "highly recommend"
