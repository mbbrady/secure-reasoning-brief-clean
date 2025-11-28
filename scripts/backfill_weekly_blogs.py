#!/usr/bin/env python3
"""
Backfill weekly blog posts from historical data.

Usage:
    python backfill_weekly_blogs.py --week 2025-11-17  # Generate for week of Nov 17-23
    python backfill_weekly_blogs.py --all              # Generate all possible weeks
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import argparse

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from generate_weekly_blog import generate_weekly_blog, load_past_week_briefs


def find_available_weeks(content_dir: Path):
    """Find all weeks for which we have sufficient data."""

    # Get all brief files
    all_briefs = sorted(content_dir.glob("*_articles.json"))

    if not all_briefs:
        print("No brief files found")
        return []

    # Group by week
    weeks = {}
    for brief_path in all_briefs:
        try:
            # Extract date from filename
            filename = brief_path.stem
            date_str = filename.split('_')[0]
            date = datetime.strptime(date_str, "%Y-%m-%d")

            # Get Sunday of that week (ISO week ends on Sunday)
            # Python weekday: Monday=0, Sunday=6
            days_until_sunday = (6 - date.weekday()) % 7
            if days_until_sunday == 0 and date.hour < 21:
                # If it's Sunday before 9 PM, belongs to previous week
                week_end = date - timedelta(days=7)
            else:
                week_end = date + timedelta(days=days_until_sunday)

            week_key = week_end.strftime("%Y-%m-%d")

            if week_key not in weeks:
                weeks[week_key] = []
            weeks[week_key].append(brief_path)
        except (ValueError, IndexError):
            continue

    # Filter to weeks with at least 5 briefs (reasonable data)
    sufficient_weeks = {k: v for k, v in weeks.items() if len(v) >= 5}

    return sufficient_weeks


def generate_week(week_end_date: str, content_dir: Path, force: bool = False):
    """Generate weekly blog for a specific week."""

    week_end = datetime.strptime(week_end_date, "%Y-%m-%d")
    week_start = week_end - timedelta(days=6)

    output_file = content_dir / f"{week_end_date}_WEEKLY_BLOG.md"

    if output_file.exists() and not force:
        print(f"⚠️  Weekly blog already exists: {output_file}")
        print(f"    Use --force to regenerate")
        return False

    print(f"\n{'='*60}")
    print(f"Generating weekly blog for {week_start.strftime('%B %d')} - {week_end.strftime('%B %d, %Y')}")
    print(f"{'='*60}\n")

    # Load articles from this week
    all_articles = []
    cutoff_date = week_start

    all_briefs = sorted(content_dir.glob("*_articles.json"))

    for brief_path in all_briefs:
        try:
            filename = brief_path.stem
            date_str = filename.split('_')[0]
            brief_date = datetime.strptime(date_str, "%Y-%m-%d")

            # Include if within week range
            if week_start <= brief_date <= week_end:
                print(f"  Including: {brief_path.name}")
                with open(brief_path) as f:
                    brief_data = json.load(f)
                    articles = brief_data.get('articles', [])

                    for article in articles:
                        article['_brief_date'] = brief_path.stem.split('_')[0]
                        article['_brief_file'] = brief_path.name

                    all_articles.extend(articles)
        except (ValueError, IndexError):
            continue

    if len(all_articles) == 0:
        print(f"❌ No articles found for week ending {week_end_date}")
        return False

    print(f"\n📊 Total articles: {len(all_articles)}")

    # Generate the weekly blog
    try:
        generate_weekly_blog(all_articles, output_file)
        print(f"\n✅ Generated: {output_file}")
        return True
    except Exception as e:
        print(f"\n❌ Error generating blog: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description='Backfill weekly blog posts')
    parser.add_argument('--week', type=str, help='Week end date (YYYY-MM-DD format, Sunday)')
    parser.add_argument('--all', action='store_true', help='Generate all available weeks')
    parser.add_argument('--force', action='store_true', help='Overwrite existing blogs')
    parser.add_argument('--list', action='store_true', help='List available weeks')

    args = parser.parse_args()

    content_dir = script_dir.parent / "content" / "briefs"

    if not content_dir.exists():
        print(f"ERROR: Content directory not found: {content_dir}")
        sys.exit(1)

    # Find available weeks
    available_weeks = find_available_weeks(content_dir)

    if args.list:
        print("\nAvailable weeks with sufficient data:\n")
        for week_end, briefs in sorted(available_weeks.items()):
            week_end_dt = datetime.strptime(week_end, "%Y-%m-%d")
            week_start_dt = week_end_dt - timedelta(days=6)
            print(f"  {week_start_dt.strftime('%b %d')} - {week_end_dt.strftime('%b %d, %Y')}: "
                  f"{len(briefs)} briefs")
        print()
        return

    if args.all:
        print(f"\nGenerating weekly blogs for {len(available_weeks)} weeks...")
        success_count = 0
        for week_end in sorted(available_weeks.keys()):
            if generate_week(week_end, content_dir, args.force):
                success_count += 1
        print(f"\n✅ Generated {success_count}/{len(available_weeks)} weekly blogs")
        return

    if args.week:
        # Validate date format
        try:
            week_date = datetime.strptime(args.week, "%Y-%m-%d")
            # Check if it's a Sunday
            if week_date.weekday() != 6:
                print(f"⚠️  Warning: {args.week} is not a Sunday")
                print(f"   Proceeding anyway...")
        except ValueError:
            print(f"ERROR: Invalid date format: {args.week}")
            print(f"       Use YYYY-MM-DD format")
            sys.exit(1)

        generate_week(args.week, content_dir, args.force)
        return

    # No arguments - show help
    parser.print_help()
    print("\nAvailable weeks:")
    for week_end, briefs in sorted(available_weeks.items()):
        week_end_dt = datetime.strptime(week_end, "%Y-%m-%d")
        week_start_dt = week_end_dt - timedelta(days=6)
        print(f"  {week_start_dt.strftime('%b %d')} - {week_end_dt.strftime('%b %d, %Y')}: "
              f"{len(briefs)} briefs")


if __name__ == "__main__":
    main()
