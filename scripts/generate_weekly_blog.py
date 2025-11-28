#!/usr/bin/env python3
"""
Generate weekly blog post from past week's daily briefs.

Runs Monday 10 AM to synthesize the previous week's research into a cohesive
weekly digest with trends, highlights, and recommendations.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from gemini_client import GeminiClient
    GEMINI_AVAILABLE = True
except ImportError as e:
    print(f"ERROR: Could not import GeminiClient: {e}")
    GEMINI_AVAILABLE = False
    sys.exit(1)


def load_past_week_briefs(content_dir: Path, days: int = 7):
    """Load all daily briefs from the past week."""

    cutoff_date = datetime.now() - timedelta(days=days)

    # Find all brief JSON files
    all_briefs = sorted(content_dir.glob("*_articles.json"))

    # Filter to past week
    recent_briefs = []
    for brief_path in all_briefs:
        # Extract date from filename (YYYY-MM-DD_HHMM_articles.json)
        filename = brief_path.stem  # Remove .json
        date_str = filename.split('_')[0]  # Get YYYY-MM-DD part

        try:
            brief_date = datetime.strptime(date_str, "%Y-%m-%d")
            if brief_date >= cutoff_date:
                recent_briefs.append(brief_path)
        except ValueError:
            continue

    print(f"Found {len(recent_briefs)} briefs from past {days} days")

    # Load all briefs
    all_articles = []
    for brief_path in recent_briefs:
        with open(brief_path) as f:
            brief_data = json.load(f)
            articles = brief_data.get('articles', [])

            # Add metadata about which brief this came from
            for article in articles:
                article['_brief_date'] = brief_path.stem.split('_')[0]
                article['_brief_file'] = brief_path.name

            all_articles.extend(articles)

    print(f"Loaded {len(all_articles)} total articles from past week")

    return all_articles, recent_briefs


def generate_weekly_blog(all_articles, output_path: Path):
    """Generate Gemini-written weekly blog synthesizing past week's research."""

    if len(all_articles) == 0:
        print("ERROR: No articles to synthesize")
        return

    # Prepare condensed article summaries for Gemini
    articles_summary = []
    for idx, article in enumerate(all_articles, 1):
        gemini_analysis = article.get('gemini_analysis', {})

        # Condensed format to fit more articles in context
        # NOTE: Only includes Ollama summaries (NOT raw_content_excerpt)
        tech_summary = article.get('technical_summary', 'N/A')
        if len(tech_summary) > 300:
            tech_summary = tech_summary[:300] + '...'

        article_text = f"""
[{idx}] {article.get('title', 'Untitled')} ({article.get('_brief_date', 'Unknown date')})
Source: {article.get('source', 'Unknown')}
Link: {article.get('link', 'N/A')}
Summary (by Ollama): {tech_summary}
Tags: {', '.join(article.get('tags', []))}
Significance: {gemini_analysis.get('significance', 'N/A')}
Relevance: {gemini_analysis.get('relevance_score', 0):.2f}
Key Insight: {gemini_analysis.get('key_insight', 'N/A')[:200]}...
"""
        articles_summary.append(article_text)

    # Group articles by significance for context
    by_significance = {}
    for article in all_articles:
        sig = article.get('gemini_analysis', {}).get('significance', 'incremental')
        if sig not in by_significance:
            by_significance[sig] = []
        by_significance[sig].append(article)

    significance_summary = "\n".join([
        f"- {sig}: {len(articles)} articles"
        for sig, articles in sorted(by_significance.items())
    ])

    # Create prompt for weekly synthesis
    week_start = (datetime.now() - timedelta(days=7)).strftime("%B %d")
    week_end = datetime.now().strftime("%B %d, %Y")

    weekly_prompt = f"""You are writing a WEEKLY digest for the Resonant Knowledge Lab's "Secure Reasoning Research Brief."

AUDIENCE: AI practitioners, researchers, and governance professionals tracking trustworthy AI developments.

YOUR TASK: Synthesize the past week's research into a cohesive weekly digest.

You have {len(all_articles)} articles from the past 7 days with your prior expert analysis.

Article distribution:
{significance_summary}

YOUR WEEKLY DIGEST SHOULD:

1. **Opening Context** (2-3 paragraphs)
   - What was the big picture this week in secure reasoning research?
   - What major themes or trends emerged?
   - How does this week compare to typical weeks?

2. **Top Papers of the Week** (3-5 papers)
   - Feature the most significant contributions (breakthrough/important papers)
   - For each: title, why it matters, practical implications
   - Focus on papers that advance secure reasoning meaningfully
   - IMPORTANT: Cite papers using [N] format where N is the article number from the list above

3. **Emerging Trends** (2-3 trends)
   - What patterns do you see across multiple papers?
   - Are researchers converging on certain approaches?
   - What aspects of secure reasoning are getting attention?
   - Examples: "provenance tracking methods", "alignment through diverse feedback", etc.
   - Cite papers using [N] format when referencing specific work

4. **Notable Mentions** (brief list)
   - Other papers worth tracking (useful/incremental)
   - Quick highlights without deep analysis
   - Cite papers using [N] format

5. **What's Missing** (1 paragraph)
   - What aspects of secure reasoning are under-researched this week?
   - What gaps should the community address?

6. **Weekly Recommendations** (3-5 concrete actions)
   - What should practitioners focus on based on this week's research?
   - What capabilities are becoming more mature?
   - What risks need attention?

7. **Looking Ahead** (closing paragraph)
   - What to watch for in coming weeks
   - What questions remain open

STYLE:
- Professional but engaging weekly newsletter tone
- Synthesize across papers, don't just list them
- Show connections and patterns
- Be honest about abstract-only limitations
- Focus on "what this means" not just "what happened"

---

ARTICLES FROM PAST WEEK ({week_start} - {week_end}):

{chr(10).join(articles_summary[:100])}  # Limit to first 100 to fit context

---

Write the complete weekly blog post in markdown format. Make it insightful and synthesizing, helping practitioners understand the week's developments and their implications.

Title it: "Secure Reasoning Research - Weekly Brief: {week_start} - {week_end}"

Include at end:
- Total articles reviewed: {len(all_articles)}
- Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- Coverage period: {week_start} - {week_end}
- Note: Automated weekly synthesis with Phase-0 telemetry
"""

    print("Asking Gemini to write weekly blog synthesis...")

    # Call Gemini to write the weekly blog
    if not GEMINI_AVAILABLE:
        raise RuntimeError("Gemini client not available")

    gem_client = GeminiClient()

    response = gem_client.generate(
        weekly_prompt,
        system_prompt="You are a senior AI safety researcher and excellent technical writer. You write insightful weekly digests synthesizing trends in secure reasoning research for practitioners.",
        temperature=0.7,  # Slightly higher for creative synthesis
        max_tokens=6000,  # Need more room for weekly synthesis
        agent_id="weekly_blog_writer",
        session_id=f"weekly-{datetime.now().strftime('%Y-%m-%d')}",
        turn_id=0,
        task_type="weekly_blog_synthesis"
    )

    blog_content = response.strip()

    # Clean markdown fences if present
    import re
    if blog_content.startswith("```"):
        match = re.search(r'```(?:markdown)?\s*\n?(.*?)\n?```', blog_content, re.DOTALL)
        if match:
            blog_content = match.group(1).strip()

    # Extract cited paper numbers from blog content
    # Handles both [N] and [N, M, P] formats
    cited_numbers = set()
    for match in re.finditer(r'\[([0-9, ]+)\]', blog_content):
        # Split by comma and extract all numbers
        nums_str = match.group(1)
        for num_str in nums_str.split(','):
            num_str = num_str.strip()
            if num_str.isdigit():
                cited_numbers.add(int(num_str))

    # Generate references section with IEEE-style citations
    # NOTE: Citations use only metadata (title, link, date, source)
    # They do NOT include raw_content_excerpt - only public metadata
    if cited_numbers:
        references = "\n\n---\n\n## References\n\n"
        for num in sorted(cited_numbers):
            # Article numbers are 1-indexed
            if 1 <= num <= len(all_articles):
                article = all_articles[num - 1]
                title = article.get('title', 'Untitled')
                link = article.get('link', '')
                date = article.get('date', 'n.d.')
                source = article.get('source', 'Unknown')

                # IEEE-style citation format
                # [N] Title, Source, Date. [Online]. Available: URL
                if link:
                    citation = f"[{num}] {title}, *{source}*, {date}. [Online]. Available: {link}\n\n"
                else:
                    citation = f"[{num}] {title}, *{source}*, {date}.\n\n"

                references += citation

        blog_content += references
        print(f"   Added {len(cited_numbers)} references")

    # Write to output file
    with open(output_path, 'w') as f:
        f.write(blog_content)

    print(f"✅ Weekly blog written to: {output_path}")
    print(f"   Length: {len(blog_content)} characters")
    print(f"   Articles synthesized: {len(all_articles)}")


def main():
    """Generate weekly blog from past week's briefs."""

    if not GEMINI_AVAILABLE:
        print("ERROR: Gemini client not available")
        sys.exit(1)

    # Load content directory
    content_dir = script_dir.parent / "content" / "briefs"

    if not content_dir.exists():
        print(f"ERROR: Content directory not found: {content_dir}")
        sys.exit(1)

    # Load past week's briefs
    all_articles, brief_files = load_past_week_briefs(content_dir, days=7)

    if len(all_articles) == 0:
        print("ERROR: No articles found from past week")
        sys.exit(1)

    # Output path: YYYY-MM-DD_WEEKLY_BLOG.md
    week_date = datetime.now().strftime("%Y-%m-%d")
    output_path = content_dir / f"{week_date}_WEEKLY_BLOG.md"

    print(f"\nGenerating weekly blog for week ending {week_date}")
    print(f"Synthesizing {len(brief_files)} daily briefs ({len(all_articles)} articles)")

    generate_weekly_blog(all_articles, output_path)

    print("\nTo view the weekly blog:")
    print(f"  cat {output_path}")


if __name__ == "__main__":
    main()
