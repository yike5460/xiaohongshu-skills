#!/usr/bin/env python3
"""Orchestrate posting across all campaign platforms.

Usage:
    python campaign_orchestrator.py campaign_config.yaml content_dir [--dry-run]

Reads the campaign config, finds approved (or generated) content for each
platform, and calls the platform poster for each one. Generates a campaign
report at content_dir/posting_results.json.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import yaml

from platform_poster import post_content

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def find_content_file(content_dir: Path, platform: str) -> Path | None:
    """Find the best content file for a platform.

    Prefers approved content, falls back to generated content.
    """
    approved = content_dir / f"{platform}_approved.json"
    if approved.exists():
        logger.info("Using approved content for %s: %s", platform, approved)
        return approved

    generated = content_dir / f"{platform}_content.json"
    if generated.exists():
        logger.info(
            "No approved content for %s, falling back to generated: %s",
            platform, generated,
        )
        return generated

    return None


def run_campaign(config_path: Path, content_dir: Path, dry_run: bool) -> None:
    """Run the campaign: post to each platform and generate a report."""
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    platforms = config.get("platforms", [])
    scheduling = config.get("scheduling", "immediate")
    stagger_delay = config.get("stagger_delay_minutes", 30) * 60

    if not platforms:
        logger.error("No platforms specified in campaign config")
        sys.exit(1)

    # Respect dry_run from config if CLI flag not set
    if config.get("dry_run", False) and not dry_run:
        logger.info("Config has dry_run=true, enabling dry-run mode")
        dry_run = True

    results = {}

    for i, platform in enumerate(platforms):
        content_file = find_content_file(content_dir, platform)

        if content_file is None:
            logger.warning("SKIP %s: no content found", platform)
            results[platform] = {"status": "skipped", "reason": "no content found"}
            continue

        try:
            result = post_content(platform, content_file, dry_run)
            results[platform] = result
            logger.info("Result for %s: %s", platform, result.get("status", "unknown"))
        except Exception as exc:
            logger.error("ERROR posting to %s: %s", platform, exc)
            results[platform] = {"status": "error", "error": str(exc)}

        # Staggered scheduling: wait between platforms (skip after last)
        if (scheduling == "staggered"
                and not dry_run
                and i < len(platforms) - 1
                and results[platform].get("status") == "posted"):
            logger.info(
                "Staggered scheduling: waiting %d minutes before next post...",
                stagger_delay // 60,
            )
            time.sleep(stagger_delay)

    # Save posting report
    report_path = content_dir / "posting_results.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info("Campaign complete. Report saved to %s", report_path)

    # Print summary
    posted = sum(1 for r in results.values() if r.get("status") == "posted")
    dry = sum(1 for r in results.values() if r.get("status") == "dry_run")
    manual = sum(1 for r in results.values() if r.get("status") == "manual")
    skipped = sum(1 for r in results.values() if r.get("status") == "skipped")
    errors = sum(1 for r in results.values() if r.get("status") == "error")

    logger.info(
        "Summary: %d posted, %d dry-run, %d manual, %d skipped, %d errors",
        posted, dry, manual, skipped, errors,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Orchestrate posting across campaign platforms"
    )
    parser.add_argument("campaign_config", type=Path, help="Path to campaign_config.yaml")
    parser.add_argument("content_dir", type=Path, help="Directory containing content files")
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    args = parser.parse_args()

    if not args.campaign_config.exists():
        logger.error("Campaign config not found: %s", args.campaign_config)
        sys.exit(1)
    if not args.content_dir.is_dir():
        logger.error("Content directory not found: %s", args.content_dir)
        sys.exit(1)

    run_campaign(args.campaign_config, args.content_dir, args.dry_run)
