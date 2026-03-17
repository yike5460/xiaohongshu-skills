#!/usr/bin/env python3
"""Generate platform-specific promotional content from a product brief.

Usage:
    python content_generator.py product_brief.json campaign_config.yaml output_dir
        [--templates-dir DIR]

Reads the product brief and campaign config, loads platform templates,
and calls Bedrock Claude to generate content for each target platform.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

import boto3
import yaml
from botocore.config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

MODEL_ID = "us.anthropic.claude-sonnet-4-6"
MAX_RETRIES = 2

PLATFORM_SPECS = {
    "x": {
        "name": "X (Twitter)",
        "constraints": (
            "Max 280 characters per tweet. Use a thread (up to 5 tweets) for "
            "longer content. Include relevant hashtags (2-4). Mention @handles "
            "if relevant. No markdown."
        ),
        "format": "Thread array with each tweet as a string.",
        "template_file": "x_thread.md",
    },
    "discord": {
        "name": "Discord",
        "constraints": (
            "Max 2000 characters. Use Discord markdown (bold, code blocks, embeds). "
            "Include emoji for visual appeal. Structure with sections. Add a call-to-action."
        ),
        "format": "Single message string with Discord markdown.",
        "template_file": "discord_announcement.md",
    },
    "xiaohongshu": {
        "name": "Xiaohongshu (Little Red Book)",
        "constraints": (
            "Write in Chinese. Max 1000 characters. Use emoji heavily. Include "
            "relevant hashtag topics. Conversational, personal tone. Focus on "
            "user experience and visual appeal."
        ),
        "format": 'Object with "title" (max 20 chars) and "body" string.',
        "template_file": "xiaohongshu_post.md",
    },
    "reddit": {
        "name": "Reddit",
        "constraints": (
            "Title max 300 characters. Body uses Reddit markdown. Be authentic "
            "and non-promotional in tone. Include technical details. Suggest 2-3 "
            "relevant subreddits. Add a TL;DR."
        ),
        "format": 'Object with "title", "body", and "suggested_subreddits" array.',
        "template_file": "reddit_post.md",
    },
    "producthunt": {
        "name": "Product Hunt",
        "constraints": (
            "Tagline max 60 characters. Description is concise and benefit-focused. "
            "Include maker comment (personal, behind-the-scenes). List 3 key features. "
            "First comment should tell the story."
        ),
        "format": 'Object with "tagline", "description", "topics" array, and "maker_comment".',
        "template_file": "producthunt_launch.md",
    },
    "zhihu": {
        "name": "Zhihu (知乎)",
        "constraints": (
            "Write in Chinese. Long-form article style. Technical depth expected. "
            "Use markdown formatting. Include analysis and comparison with "
            "alternatives. 800-2000 characters."
        ),
        "format": 'Object with "title" and "body" string.',
        "template_file": "zhihu_article.md",
    },
}

CHINESE_PLATFORMS = {"xiaohongshu", "zhihu"}
ENGLISH_ONLY_PLATFORMS = {"producthunt"}


def load_template(templates_dir: Path, filename: str) -> str:
    """Load a template file, returning empty string if not found."""
    path = templates_dir / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning("Template not found: %s", path)
    return ""


def build_prompt(platform: str, brief: dict, config: dict, template: str) -> tuple:
    """Build system and user prompts for a given platform.

    Returns:
        (system_prompt, user_message) tuple.
    """
    spec = PLATFORM_SPECS[platform]
    campaign_type = config.get("campaign_type", "launch")
    tone = config.get("tone", "professional")
    languages = config.get("languages", ["en"])

    if platform in CHINESE_PLATFORMS:
        lang_instruction = "Write in Chinese (Simplified)."
    elif platform in ENGLISH_ONLY_PLATFORMS:
        lang_instruction = "Write in English."
    else:
        lang_instruction = (
            "Write in Chinese (Simplified)." if "zh" in languages and "en" not in languages
            else "Write in English."
        )

    template_section = ""
    if template:
        template_section = (
            f"\n\nUse the following template as a structural guide for the content. "
            f"Follow its structure, tone guidance, and formatting conventions, but "
            f"fill in the actual product details:\n\n{template}"
        )

    system_prompt = (
        f"You are an expert social media marketer. Generate promotional content "
        f"for {spec['name']}.\n\n"
        f"Campaign type: {campaign_type}\n"
        f"Tone: {tone}\n"
        f"{lang_instruction}\n\n"
        f"Platform constraints:\n{spec['constraints']}\n\n"
        f"Output format: Return ONLY valid JSON matching this format: {spec['format']}\n"
        f"Do not include any text outside the JSON."
        f"{template_section}"
    )

    user_msg = (
        f"Product: {brief['product_name']}\n"
        f"Tagline: {brief['tagline']}\n"
        f"Description: {brief['description']}\n"
        f"Features: {json.dumps(brief.get('features', []), ensure_ascii=False)}\n"
        f"Audience: {brief.get('target_audience', 'developers and tech enthusiasts')}\n"
        f"Links: {json.dumps(brief.get('links', {}), ensure_ascii=False)}\n"
        f"Pricing: {brief.get('pricing', 'free')}\n"
        f"Launch context: {brief.get('launch_context', 'new_launch')}"
    )

    return system_prompt, user_msg


def call_bedrock(client, system_prompt: str, user_msg: str) -> str:
    """Call Bedrock Claude with retry logic.

    Returns:
        The text content from the model response.

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.converse(
                modelId=MODEL_ID,
                system=[{"text": system_prompt}],
                messages=[{"role": "user", "content": [{"text": user_msg}]}],
                inferenceConfig={"maxTokens": 2048, "temperature": 0.7},
            )
            return response["output"]["message"]["content"][0]["text"]
        except Exception as exc:
            last_error = exc
            logger.warning(
                "Bedrock API call failed (attempt %d/%d): %s",
                attempt, MAX_RETRIES, exc,
            )
            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)

    raise RuntimeError(f"Bedrock API failed after {MAX_RETRIES} retries: {last_error}")


def validate_json_response(text: str, platform: str) -> str:
    """Validate that the response is valid JSON.

    Returns the cleaned text (strips markdown fences if present).

    Raises:
        ValueError: If the response is not valid JSON.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove opening and closing fence lines
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    json.loads(cleaned)  # validate
    return cleaned


def generate_content(brief_path: Path, config_path: Path, output_dir: Path,
                     templates_dir: Path) -> None:
    """Generate content for all platforms in the campaign config."""
    with open(brief_path, encoding="utf-8") as f:
        brief = json.load(f)

    required = ["product_name", "tagline", "description"]
    missing = [k for k in required if not brief.get(k)]
    if missing:
        logger.error("Missing required fields in product brief: %s", ", ".join(missing))
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    platforms = config.get("platforms", ["x", "discord", "reddit"])
    region = os.environ.get("AWS_REGION", "us-east-1")

    boto_config = Config(read_timeout=300, retries={"max_attempts": 2})
    client = boto3.client("bedrock-runtime", region_name=region, config=boto_config)

    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for platform in platforms:
        if platform not in PLATFORM_SPECS:
            logger.warning("Skipping unknown platform: %s", platform)
            continue

        spec = PLATFORM_SPECS[platform]
        template = load_template(templates_dir, spec["template_file"])
        system_prompt, user_msg = build_prompt(platform, brief, config, template)

        logger.info("Generating content for %s...", spec["name"])

        try:
            raw_text = call_bedrock(client, system_prompt, user_msg)
        except RuntimeError as exc:
            logger.error("Failed to generate content for %s: %s", platform, exc)
            results[platform] = {"status": "error", "error": str(exc)}
            continue

        # Validate JSON and retry once with stricter prompt if invalid
        try:
            cleaned = validate_json_response(raw_text, platform)
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "Invalid JSON from %s, retrying with stricter prompt...", platform
            )
            strict_suffix = (
                "\n\nIMPORTANT: Your previous response was not valid JSON. "
                "Return ONLY a valid JSON object or array. No markdown, no explanation."
            )
            try:
                raw_text = call_bedrock(client, system_prompt + strict_suffix, user_msg)
                cleaned = validate_json_response(raw_text, platform)
            except (RuntimeError, json.JSONDecodeError, ValueError) as exc:
                logger.error("Failed to get valid JSON for %s: %s", platform, exc)
                # Save raw output anyway for manual use
                cleaned = raw_text

        # Save per-platform output
        out_file = output_dir / f"{platform}_content.json"
        out_file.write_text(cleaned, encoding="utf-8")

        results[platform] = {
            "raw": cleaned,
            "platform": platform,
            "language": "zh" if platform in CHINESE_PLATFORMS else "en",
        }

        logger.info("Saved content for %s -> %s", spec["name"], out_file)

    # Save combined results
    all_content_path = output_dir / "all_content.json"
    with open(all_content_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("All content saved to %s", output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate platform-specific promotional content"
    )
    parser.add_argument("product_brief", type=Path, help="Path to product_brief.json")
    parser.add_argument("campaign_config", type=Path, help="Path to campaign_config.yaml")
    parser.add_argument("output_dir", type=Path, help="Output directory for generated content")
    parser.add_argument(
        "--templates-dir",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "templates",
        help="Directory containing platform templates (default: skill templates/ dir)",
    )
    args = parser.parse_args()

    if not args.product_brief.exists():
        logger.error("Product brief not found: %s", args.product_brief)
        sys.exit(1)
    if not args.campaign_config.exists():
        logger.error("Campaign config not found: %s", args.campaign_config)
        sys.exit(1)

    generate_content(args.product_brief, args.campaign_config, args.output_dir,
                     args.templates_dir)
