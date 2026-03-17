# Social Media Promoter

Automated social media and community promotion pipeline for Claude Code. Generate platform-specific content for X, Discord, Xiaohongshu, Reddit, Product Hunt, and Zhihu from a single product brief.

## Overview

This skill automates the full product promotion workflow:

1. **Product Brief Intake** - Gather product details into a structured JSON brief
2. **Campaign Configuration** - Choose platforms, tone, scheduling, and languages
3. **Content Generation** - AI generates platform-native content using Bedrock Claude
4. **Content Review** - Human-in-the-loop approval before publishing
5. **Publishing** - Automated posting (or formatted output for manual platforms)
6. **Engagement Tracking** - Reply templates and follow-up guidance

## Quick Start

```bash
# 1. Set up the virtual environment
SKILL_DIR=".claude/skills/social-media-promoter"
python3 -m venv "$SKILL_DIR/.venv"
"$SKILL_DIR/.venv/bin/pip" install boto3 requests pyyaml tweepy praw -q

# 2. Copy and fill in environment variables
cp "$SKILL_DIR/.env.example" .env
# Edit .env with your API keys

# 3. Create campaign output directory
mkdir -p ./campaign-output

# 4. Copy and customize the product brief and campaign config
cp "$SKILL_DIR/templates/product_brief.json" ./campaign-output/product_brief.json
cp "$SKILL_DIR/templates/campaign_config.yaml" ./campaign-output/campaign_config.yaml
# Edit both files with your product details

# 5. Generate content
PYTHON="$SKILL_DIR/.venv/bin/python"
$PYTHON "$SKILL_DIR/scripts/content_generator.py" \
    ./campaign-output/product_brief.json \
    ./campaign-output/campaign_config.yaml \
    ./campaign-output

# 6. Review and approve content, then run the campaign (dry-run first)
$PYTHON "$SKILL_DIR/scripts/campaign_orchestrator.py" \
    ./campaign-output/campaign_config.yaml \
    ./campaign-output \
    --dry-run
```

## Platform Setup

### AWS Bedrock (Required)

Content generation uses Amazon Bedrock with Claude. Ensure you have:
- AWS credentials configured (via environment variables, AWS profile, or IAM role)
- Access enabled for `us.anthropic.claude-sonnet-4-6-v1` in your Bedrock console

### X / Twitter

1. Apply for a developer account at https://developer.x.com
2. Create a project and app in the Developer Portal
3. Generate OAuth 1.0a keys (API Key, API Secret, Access Token, Access Secret)
4. Set `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_SECRET` in `.env`

### Discord

1. Open your Discord server settings
2. Go to Integrations > Webhooks > New Webhook
3. Copy the webhook URL
4. Set `DISCORD_WEBHOOK_URL` in `.env`

### Reddit

1. Go to https://www.reddit.com/prefs/apps
2. Create a new app (select "script" type)
3. Note the client ID (under the app name) and client secret
4. Set `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`, `REDDIT_PASSWORD` in `.env`

### Product Hunt

No API keys required. Content is generated and formatted for manual submission at https://www.producthunt.com/posts/new

### Xiaohongshu

No API available. Content is generated in Chinese and formatted for manual copy-paste posting.

### Zhihu

No API available. Content is generated in Chinese as a long-form article for manual posting.

## Usage

### Scripts

| Script | Purpose |
|--------|---------|
| `content_generator.py` | Generate platform-specific content from a product brief |
| `platform_poster.py` | Post content to a single platform |
| `campaign_orchestrator.py` | Orchestrate posting across all campaign platforms |

### Content Generator

```bash
python scripts/content_generator.py <product_brief.json> <campaign_config.yaml> <output_dir> \
    [--templates-dir DIR]
```

### Platform Poster

```bash
python scripts/platform_poster.py <platform> <content_file.json> [--dry-run]
```

Supported platforms: `x`, `discord`, `reddit`, `producthunt`, `xiaohongshu`, `zhihu`

### Campaign Orchestrator

```bash
python scripts/campaign_orchestrator.py <campaign_config.yaml> <content_dir> [--dry-run]
```

## Architecture

```
User Input                     AI Generation                  Publishing
+-----------------+           +------------------+           +------------------+
| product_brief   |  ------>  | content_generator|  ------>  | platform_poster  |
| .json           |           | (Bedrock Claude) |           | (per platform)   |
+-----------------+           +------------------+           +------------------+
                                     |                              |
+-----------------+                  |                              |
| campaign_config |  ---------------+---->  campaign_orchestrator --+
| .yaml           |                         (ties it all together)
+-----------------+

Templates (structural guides for each platform)
+-- x_thread.md
+-- discord_announcement.md
+-- reddit_post.md
+-- producthunt_launch.md
+-- xiaohongshu_post.md
+-- zhihu_article.md
```

## File Structure

```
social-media-promoter/
  SKILL.md                          # Skill definition for Claude Code
  README.md                         # This file
  .env.example                      # Environment variable template
  scripts/
    content_generator.py            # AI content generation via Bedrock
    platform_poster.py              # Platform-specific posting adapters
    campaign_orchestrator.py        # Multi-platform campaign runner
  templates/
    product_brief.json              # Example product brief
    campaign_config.yaml            # Example campaign configuration
    x_thread.md                     # X/Twitter thread template
    discord_announcement.md         # Discord announcement template
    reddit_post.md                  # Reddit post template (3 variants)
    producthunt_launch.md           # Product Hunt launch template
    xiaohongshu_post.md             # Xiaohongshu post template (Chinese)
    zhihu_article.md                # Zhihu article template (Chinese)
    STRATEGY.md                     # Platform strategy and timing guide

Campaign Output (generated at runtime):
  campaign-output/
    product_brief.json              # Product information
    campaign_config.yaml            # Campaign settings
    all_content.json                # All generated content combined
    <platform>_content.json         # Per-platform generated content
    <platform>_approved.json        # User-approved content
    posting_results.json            # Posting status per platform
    reply_templates.json            # Engagement reply templates
```

## Supported Platforms

| Platform | Auto-Post | Language | API Required |
|----------|-----------|----------|-------------|
| X (Twitter) | Yes | en | X API v2 keys |
| Discord | Yes | en | Webhook URL |
| Reddit | Yes | en | Reddit API credentials |
| Product Hunt | Manual | en | - |
| Xiaohongshu | Manual | zh | - |
| Zhihu | Manual | zh | - |
