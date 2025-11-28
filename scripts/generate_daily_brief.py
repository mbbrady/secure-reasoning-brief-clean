#!/usr/bin/env python3
"""
Generate concise daily executive briefs from article JSON files.

Runs as part of pipeline or standalone for backfilling.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError as e:
    print(f"ERROR: Could not import GeminiClient: {e}")
    GEMINI_AVAILABLE = False


def extract_brief_id(json_path: Path):
    """Extract brief ID from filename (e.g., '2025-11-22_morning')."""
    stem = json_path.stem  # e.g., '2025-11-22_0900_articles'
    parts = stem.split('_')
    date = parts[0]  # 2025-11-22
    time = parts[1] if len(parts) > 1 else '0000'  # 0900

    # Determine time of day
    hour = int(time[:2]) if time.isdigit() and len(time) >= 2 else 0
    if 6 <= hour < 15:
        time_of_day = 'morning'
    else:
        time_of_day = 'evening'

    return f"{date}_{time_of_day}"


def count_by_significance(articles):
    """Count articles by significance level."""
    counts = Counter()
    for article in articles:
        sig = article.get('gemini_analysis', {}).get('significance', 'incremental')
        counts[sig] += 1
    return counts


def get_top_tags(articles, limit=5):
    """Get most common tags across articles."""
    tag_counter = Counter()
    for article in articles:
        tags = article.get('tags', [])
        tag_counter.update(tags)
    return tag_counter.most_common(limit)


def prepare_article_summaries(articles):
    """Prepare condensed article summaries for Gemini."""
    summaries = []
    for idx, article in enumerate(articles, 1):
        gemini = article.get('gemini_analysis', {})

        tech_summary = article.get('technical_summary', 'N/A')
        if len(tech_summary) > 200:
            tech_summary = tech_summary[:200] + '...'

        summary = f"""
[{idx}] {article.get('title', 'Untitled')}
Source: {article.get('source', 'Unknown')}
Link: {article.get('link', 'N/A')}
Summary: {tech_summary}
Tags: {', '.join(article.get('tags', [])[:5])}
Significance: {gemini.get('significance', 'N/A')} | Relevance: {gemini.get('relevance_score', 0):.2f}
Key Insight: {gemini.get('key_insight', 'N/A')[:150]}
"""
        summaries.append(summary)

    return '\n'.join(summaries)


def build_daily_brief_prompt(articles, breakdown, tags, date):
    """Build Gemini prompt for daily brief generation."""

    # Get high priority papers (breakthrough or important)
    high_priority = [a for a in articles if
                     a.get('gemini_analysis', {}).get('significance') in ['breakthrough', 'important']]

    # Format top tags
    top_tags_str = ' • '.join([f"#{tag} ({count})" for tag, count in tags])

    # Prepare article summaries
    articles_text = prepare_article_summaries(articles)

    prompt = f"""You are writing a DAILY executive brief for the Resonant Knowledge Lab's
"Secure Reasoning Research Brief."

AUDIENCE: Busy AI practitioners, researchers, and governance professionals who need quick daily updates.

YOUR TASK: Create a scannable 2-3 minute read highlighting today's most important findings.

TODAY'S COLLECTION ({date}):
- Total papers: {len(articles)}
- Breakdown: {dict(breakdown)}
- Top tags: {top_tags_str}
- High priority: {len(high_priority)} papers

YOUR DAILY BRIEF SHOULD FOLLOW THIS STRUCTURE:

1. **Title** (compelling headline summarizing the day's theme)
   - One concise sentence capturing what matters most today
   - Examples: "Three Breakthroughs in Alignment Emerge" or "Robustness Research Dominates Today's Papers"

2. **Key Takeaways** (3-5 bullet points at the top)
   - The most important insights from today's collection
   - What practitioners need to know RIGHT NOW
   - Each bullet: one sentence, action-oriented
   - This section answers: "What's the signal in today's noise?"
   - Examples:
     * "New adversarial attack defeats current defenses - review your safety margins"
     * "Alignment research shows convergence on constitutional approaches"
     * "Three papers warn of emergent capabilities in smaller models"

3. **Must Read Papers** (2-3 papers max)
   - ONLY select breakthrough or important papers
   - For each paper: Title, why it matters (1 sentence), practical insight (1 sentence), link
   - Keep it ultra-brief (2-3 sentences per paper)

4. **Worth Tracking** (brief section)
   - Identify 1-2 emerging patterns (e.g., "3 papers exploring adversarial robustness")
   - List 3-5 other notable papers with one-line takeaways
   - Quick bullets only

CRITICAL STYLE REQUIREMENTS:
- Ultra-concise: Each paper gets 2-3 sentences MAX
- Focus on "why this matters" not technical details
- Use active voice and clear language
- Be selective - don't list everything
- Professional but conversational tone
- Use markdown formatting (## headers, bullets, **bold** for emphasis)

DO NOT:
- Write long technical explanations
- List every paper
- Use academic jargon without context
- Write more than 800 words total

---

ARTICLES FROM TODAY:

{articles_text}

---

Write the daily brief in clean markdown format following this exact structure:

1. Title (# heading - compelling, theme-focused)
2. Key Takeaways section (## heading with 3-5 bullets)
3. Must Read Papers section (## heading)
4. Worth Tracking section (## heading)

The Key Takeaways should be the FIRST thing readers see after the title.
"""

    return prompt


def generate_daily_brief(json_path: Path, output_path: Path = None):
    """Generate daily executive brief from article JSON."""

    if not GEMINI_AVAILABLE:
        print("ERROR: Gemini client not available")
        return False

    # Load articles
    with open(json_path) as f:
        brief_data = json.load(f)
        articles = brief_data.get('articles', [])

    if not articles:
        print(f"No articles found in {json_path}")
        return False

    # Extract metadata
    brief_id = extract_brief_id(json_path)
    date_str = brief_id.split('_')[0]
    time_of_day = brief_id.split('_')[1]

    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        date_formatted = date_obj.strftime("%B %d, %Y")
    except ValueError:
        date_formatted = date_str

    # Count significance levels
    breakdown = count_by_significance(articles)

    # Get top tags
    top_tags = get_top_tags(articles, limit=5)

    print(f"\nGenerating daily brief for {date_formatted} ({time_of_day})")
    print(f"  Articles: {len(articles)}")
    print(f"  Breakdown: {dict(breakdown)}")

    # Build prompt
    prompt = build_daily_brief_prompt(articles, breakdown, top_tags, date_formatted)

    # Call Gemini
    gem_client = GeminiClient()

    print("  Asking Gemini for daily synthesis...")

    response = gem_client.generate(
        prompt,
        system_prompt="You are a senior AI researcher writing concise daily updates for busy practitioners.",
        temperature=0.5,  # Lower for consistency
        max_tokens=1500,  # Shorter output
        agent_id="daily_brief_writer",
        session_id=f"daily-{brief_id}",
        turn_id=0,
        task_type="daily_brief"
    )

    brief_content = response.strip()

    # Clean markdown fences if present
    import re
    if brief_content.startswith("```"):
        match = re.search(r'```(?:markdown)?\s*\n?(.*?)\n?```', brief_content, re.DOTALL)
        if match:
            brief_content = match.group(1).strip()

    # Add header with metadata
    header = f"""---
date: {date_str}
time_of_day: {time_of_day}
brief_id: {brief_id}
papers_count: {len(articles)}
high_priority: {breakdown.get('breakthrough', 0) + breakdown.get('important', 0)}
data_source: {json_path.name}
---

"""

    # Add footer (no links to raw data for website publication)
    footer = f"""

---

*Generated by RKL Secure Reasoning Brief Agent • Type III Compliance • Powered by Gemini 2.0*

*Note: Raw article data and detailed technical analysis remain on local systems only, demonstrating Type III secure reasoning principles.*
"""

    final_content = header + brief_content + footer

    # Determine output path
    if output_path is None:
        output_path = json_path.parent / f"{brief_id}_DAILY.md"

    # Write output
    with open(output_path, 'w') as f:
        f.write(final_content)

    print(f"✅ Daily brief written to: {output_path}")
    print(f"   Length: {len(final_content)} characters\n")

    return True


def main():
    """Generate daily brief from JSON file."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate daily executive brief')
    parser.add_argument('json_file', type=str, help='Path to articles JSON file')
    parser.add_argument('--output', type=str, help='Output markdown file (optional)')

    args = parser.parse_args()

    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"ERROR: File not found: {json_path}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else None

    success = generate_daily_brief(json_path, output_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
