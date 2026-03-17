---
name: social-media-promoter
description: Automated social media and community promotion pipeline. Generate platform-specific content for X, Discord, Xiaohongshu, Reddit, Product Hunt, and Zhihu from a product brief. Use when user wants to "promote product", "launch on social media", "create marketing campaign", "post to Reddit/X/Discord", "social media promotion", "product launch", "community marketing", "推广产品", "社交媒体营销".
---

# Social Media Promoter

Generate and publish platform-specific promotional content across X, Discord, Xiaohongshu, Reddit, Product Hunt, and Zhihu from a single product brief.

## Prerequisites

Before starting, ensure the venv exists and dependencies are installed:

```bash
SKILL_DIR=".claude/skills/social-media-promoter"
if [ ! -d "$SKILL_DIR/.venv" ]; then
  python3 -m venv "$SKILL_DIR/.venv"
  "$SKILL_DIR/.venv/bin/pip" install boto3 requests pyyaml tweepy praw -q
fi
PYTHON="$SKILL_DIR/.venv/bin/python"
```

Load environment variables (only needed for platforms you intend to post to):

```bash
source <(grep -E '^(AWS_REGION|AWS_PROFILE|AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|X_API_KEY|X_API_SECRET|X_ACCESS_TOKEN|X_ACCESS_SECRET|DISCORD_WEBHOOK_URL|REDDIT_CLIENT_ID|REDDIT_CLIENT_SECRET|REDDIT_USERNAME|REDDIT_PASSWORD|PRODUCTHUNT_API_TOKEN|ZHIHU_COOKIE|XIAOHONGSHU_COOKIE)=' .env 2>/dev/null | sed 's/^/export /' | sed 's/"//g')
```

## Workflow

### Step 1: Product Brief Intake

Gather product information from the user. Ask for the following (or accept a JSON file):

- **Product name** (required)
- **Tagline** - one-line pitch (required)
- **Description** - 2-3 sentence summary (required)
- **Key features** - list of 3-5 features with short descriptions
- **Target audience** - who is this for
- **Links** - homepage URL, GitHub repo, demo URL, etc.
- **Assets** - logo path, screenshot paths, video URL
- **Pricing** - free / freemium / paid with details
- **Launch context** - new launch, feature update, milestone, event

If the user provides a JSON file, validate it against the template:

```python
import json, sys

brief_path = sys.argv[1]
with open(brief_path) as f:
    brief = json.load(f)

required = ["product_name", "tagline", "description"]
missing = [k for k in required if not brief.get(k)]
if missing:
    print(f"Missing required fields: {', '.join(missing)}", file=sys.stderr)
    sys.exit(1)

print(json.dumps(brief, indent=2))
```

If no file is provided, interactively gather information and save to `./campaign-output/product_brief.json`.

### Step 2: Campaign Configuration

Ask the user to configure the campaign (or accept a YAML config file):

- **Campaign type**: `launch` | `update` | `engagement` | `event`
- **Target platforms**: subset of `[x, discord, xiaohongshu, reddit, producthunt, zhihu]`
- **Languages**: `en`, `zh`, or both
- **Tone**: `professional` | `casual` | `technical` | `enthusiastic`
- **Scheduling**: `immediate` | `staggered` (posts spread over hours)
- **Dry run**: `true` | `false` (preview only, no posting)

Save config to `./campaign-output/campaign_config.yaml`.

```bash
mkdir -p ./campaign-output
```

### Step 3: Content Generation

Write and run a Python script to call Bedrock Claude for platform-specific content generation:

```python
import boto3, json, sys, yaml
from botocore.config import Config

boto_config = Config(read_timeout=300, retries={"max_attempts": 2})
client = boto3.client("bedrock-runtime", region_name="us-east-1", config=boto_config)
model_id = "us.anthropic.claude-sonnet-4-6-v1"

brief_path = sys.argv[1]
config_path = sys.argv[2]
output_dir = sys.argv[3]

with open(brief_path) as f:
    brief = json.load(f)
with open(config_path) as f:
    config = yaml.safe_load(f)

platforms = config.get("platforms", ["x", "discord", "reddit"])
campaign_type = config.get("campaign_type", "launch")
tone = config.get("tone", "professional")
languages = config.get("languages", ["en"])

platform_specs = {
    "x": {
        "name": "X (Twitter)",
        "constraints": "Max 280 characters per tweet. Use a thread (up to 5 tweets) for longer content. Include relevant hashtags (2-4). Mention @handles if relevant. No markdown.",
        "format": "Thread array with each tweet as a string."
    },
    "discord": {
        "name": "Discord",
        "constraints": "Max 2000 characters. Use Discord markdown (bold, code blocks, embeds). Include emoji for visual appeal. Structure with sections. Add a call-to-action.",
        "format": "Single message string with Discord markdown."
    },
    "xiaohongshu": {
        "name": "Xiaohongshu (小红书)",
        "constraints": "Write in Chinese. Max 1000 characters. Use emoji heavily. Include relevant hashtag topics (话题标签). Conversational, personal tone. Focus on user experience and visual appeal.",
        "format": "Object with title (max 20 chars) and body string."
    },
    "reddit": {
        "name": "Reddit",
        "constraints": "Title max 300 characters. Body uses Reddit markdown. Be authentic and non-promotional in tone. Include technical details. Suggest 2-3 relevant subreddits. Add a TL;DR.",
        "format": "Object with title, body, and suggested_subreddits array."
    },
    "producthunt": {
        "name": "Product Hunt",
        "constraints": "Tagline max 60 characters. Description is concise and benefit-focused. Include maker comment (personal, behind-the-scenes). List 3 key features. First comment should tell the story.",
        "format": "Object with tagline, description, topics array, and maker_comment."
    },
    "zhihu": {
        "name": "Zhihu (知乎)",
        "constraints": "Write in Chinese. Long-form article style. Technical depth expected. Use markdown formatting. Include analysis and comparison with alternatives. 800-2000 characters.",
        "format": "Object with title and body string."
    }
}

results = {}

for platform in platforms:
    if platform not in platform_specs:
        print(f"Skipping unknown platform: {platform}", file=sys.stderr)
        continue

    spec = platform_specs[platform]

    for lang in languages:
        lang_instruction = "Write in Chinese (Simplified)." if lang == "zh" else "Write in English."
        if platform in ("xiaohongshu", "zhihu"):
            lang_instruction = "Write in Chinese (Simplified)."
        elif platform in ("producthunt",):
            lang_instruction = "Write in English."

        system_prompt = f"""You are an expert social media marketer. Generate promotional content for {spec['name']}.

Campaign type: {campaign_type}
Tone: {tone}
{lang_instruction}

Platform constraints:
{spec['constraints']}

Output format: Return ONLY valid JSON matching this format: {spec['format']}
Do not include any text outside the JSON."""

        user_msg = f"""Product: {brief['product_name']}
Tagline: {brief['tagline']}
Description: {brief['description']}
Features: {json.dumps(brief.get('features', []))}
Audience: {brief.get('target_audience', 'developers and tech enthusiasts')}
Links: {json.dumps(brief.get('links', {{}}))}
Pricing: {brief.get('pricing', 'free')}"""

        response = client.converse(
            modelId=model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_msg}]}],
            inferenceConfig={"maxTokens": 2048, "temperature": 0.7}
        )

        text = response["output"]["message"]["content"][0]["text"]
        key = f"{platform}_{lang}" if len(languages) > 1 else platform
        results[key] = {"raw": text, "platform": platform, "language": lang}

        # Save individual platform output
        with open(f"{output_dir}/{key}_content.json", "w") as f:
            f.write(text)

        print(f"Generated content for {spec['name']} ({lang})")

# Save combined results
with open(f"{output_dir}/all_content.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nAll content saved to {output_dir}/")
```

Run the content generator:

```bash
$PYTHON /tmp/content_generator.py ./campaign-output/product_brief.json ./campaign-output/campaign_config.yaml ./campaign-output
```

### Step 4: Content Review

Display the generated content for each platform to the user. For each platform:

1. Show the formatted content with platform name as header
2. Ask the user to **approve**, **edit**, or **regenerate** for that platform
3. If editing, accept the user's changes and save the updated version
4. If regenerating, call the content generator again with adjusted instructions

Save approved content to `./campaign-output/<platform>_approved.json`.

This is a mandatory human-in-the-loop checkpoint. Do not proceed to publishing without explicit approval for each platform.

### Step 5: Publishing

Call the campaign orchestrator to post approved content. Always default to dry-run mode unless the user explicitly requests live posting.

```python
import json, sys, yaml, os, time

config_path = sys.argv[1]
content_dir = sys.argv[2]
dry_run = "--dry-run" in sys.argv

with open(config_path) as f:
    config = yaml.safe_load(f)

platforms = config.get("platforms", [])
scheduling = config.get("scheduling", "immediate")
results = {}

for platform in platforms:
    approved_file = f"{content_dir}/{platform}_approved.json"
    if not os.path.exists(approved_file):
        print(f"SKIP {platform}: no approved content found")
        results[platform] = {"status": "skipped", "reason": "no approved content"}
        continue

    with open(approved_file) as f:
        content = json.load(f)

    if dry_run:
        print(f"DRY RUN {platform}: would post content ({len(json.dumps(content))} chars)")
        results[platform] = {"status": "dry_run", "content_length": len(json.dumps(content))}
        continue

    # Platform-specific posting logic
    try:
        if platform == "x":
            post_to_x(content)
        elif platform == "discord":
            post_to_discord(content)
        elif platform == "reddit":
            post_to_reddit(content)
        elif platform == "producthunt":
            post_to_producthunt(content)
        elif platform in ("xiaohongshu", "zhihu"):
            print(f"NOTE {platform}: automated posting not supported. Content saved for manual posting.")
            results[platform] = {"status": "manual", "file": approved_file}
            continue

        results[platform] = {"status": "posted"}
        print(f"POSTED {platform}: success")

    except Exception as e:
        results[platform] = {"status": "error", "error": str(e)}
        print(f"ERROR {platform}: {e}")

    if scheduling == "staggered" and platform != platforms[-1]:
        delay = config.get("stagger_delay_minutes", 30) * 60
        print(f"Waiting {delay // 60} minutes before next post...")
        time.sleep(delay)

# Save posting results
with open(f"{content_dir}/posting_results.json", "w") as f:
    json.dump(results, f, indent=2)

print(f"\nPosting complete. Results saved to {content_dir}/posting_results.json")


def post_to_x(content):
    """Post thread to X using tweepy."""
    import tweepy
    auth = tweepy.OAuth1UserHandler(
        os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
        os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"]
    )
    api = tweepy.API(auth)
    client_v2 = tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"]
    )
    tweets = content if isinstance(content, list) else [content]
    prev_id = None
    for tweet_text in tweets:
        resp = client_v2.create_tweet(text=tweet_text, in_reply_to_tweet_id=prev_id)
        prev_id = resp.data["id"]


def post_to_discord(content):
    """Post message to Discord via webhook."""
    import requests
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    message = content if isinstance(content, str) else json.dumps(content)
    resp = requests.post(webhook_url, json={"content": message})
    resp.raise_for_status()


def post_to_reddit(content):
    """Post to Reddit using praw."""
    import praw
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent="social-media-promoter/1.0"
    )
    subreddits = content.get("suggested_subreddits", ["SideProject"])
    for sub_name in subreddits:
        subreddit = reddit.subreddit(sub_name)
        subreddit.submit(title=content["title"], selftext=content["body"])


def post_to_producthunt(content):
    """Product Hunt requires manual submission via their website. Save content for copy-paste."""
    print("Product Hunt: automated posting not available. Use the generated content to submit manually at producthunt.com/posts/new")
```

Run the orchestrator:

```bash
# Dry run (default - always do this first)
$PYTHON /tmp/campaign_orchestrator.py ./campaign-output/campaign_config.yaml ./campaign-output --dry-run

# Live posting (only after user confirms dry run output)
$PYTHON /tmp/campaign_orchestrator.py ./campaign-output/campaign_config.yaml ./campaign-output
```

### Step 6: Engagement Tracking

After posting, help the user prepare for engagement:

1. Generate reply templates for common questions:
   - "What does this do?" - elevator pitch response
   - "How is this different from X?" - competitive differentiation
   - "Is this open source?" - licensing response
   - "How do I get started?" - quickstart response
   - "What's the pricing?" - pricing response

2. Save templates to `./campaign-output/reply_templates.json`

3. Suggest follow-up actions:
   - Monitor posted threads for comments in the first 2 hours
   - Respond to questions within 30 minutes
   - Cross-reference engagement across platforms
   - Schedule a follow-up post in 1-2 weeks with usage metrics or testimonials

## Output Structure

```
./campaign-output/
  product_brief.json          # Product information
  campaign_config.yaml        # Campaign settings
  all_content.json            # All generated content
  <platform>_content.json     # Per-platform generated content
  <platform>_approved.json    # User-approved content
  posting_results.json        # Posting status per platform
  reply_templates.json        # Engagement reply templates
```

## Error Handling

- If Bedrock is unavailable, fall back to asking the user to provide content manually
- If a platform API fails during posting, log the error and continue with remaining platforms
- If content generation produces invalid JSON, retry once with a stricter prompt
- Always save generated content even if posting fails - the user can post manually
- For Xiaohongshu and Zhihu, automated posting is not supported - save content for manual posting

## Supported Platforms

| Platform | Auto-Post | Language | API Required |
|----------|-----------|----------|-------------|
| X (Twitter) | Yes | en | X API v2 keys |
| Discord | Yes | en | Webhook URL |
| Reddit | Yes | en | Reddit API credentials |
| Product Hunt | Manual | en | - |
| Xiaohongshu | Manual | zh | - |
| Zhihu | Manual | zh | - |
