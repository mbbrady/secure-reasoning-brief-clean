#!/usr/bin/env python3
"""
Generate blog post from brief JSON using Gemini as the writer.

Instead of filling templates, Gemini reads the brief data and writes
a cohesive blog post with narrative flow, theme synthesis, and expert
recommendations.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

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


def generate_blog_post(brief_json_path: Path, output_path: Path):
    """Generate blog post using Gemini as the writer."""

    # Load brief data
    with open(brief_json_path) as f:
        brief_data = json.load(f)

    articles = brief_data.get('articles', [])
    session_id = brief_data.get('session_id', 'unknown')
    generated_at = brief_data.get('generated_at', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))

    print(f"Loaded {len(articles)} articles from {brief_json_path}")

    # Prepare article summaries for Gemini
    articles_summary = []
    for idx, article in enumerate(articles, 1):
        gemini_analysis = article.get('gemini_analysis', {})

        article_text = f"""
Article {idx}: {article.get('title', 'Untitled')}
Source: {article.get('source', 'Unknown')} | Date: {article.get('date', 'Unknown')}
Link: {article.get('link', 'N/A')}
Tags: {', '.join(article.get('tags', []))}

Technical Summary (Ollama):
{article.get('technical_summary', 'N/A')}

Lay Explanation (Ollama):
{article.get('lay_explanation', 'N/A')}

Your Prior Analysis:
- Relevance Score: {gemini_analysis.get('relevance_score', 0):.2f} / 1.0
- Significance: {gemini_analysis.get('significance', 'N/A')}
- Recommendation: {gemini_analysis.get('recommendation', 'N/A')}
- Key Insight: {gemini_analysis.get('key_insight', 'N/A')}
- Secure Reasoning Connection: {gemini_analysis.get('relevance_rationale', 'N/A')}
- Practical Value: {gemini_analysis.get('practical_value', 'N/A')}
"""
        articles_summary.append(article_text)

    # Create prompt for Gemini to write the blog
    blog_writing_prompt = f"""You are writing a daily blog post for the Resonant Knowledge Lab's "Secure Reasoning Research Brief."

AUDIENCE: AI practitioners, researchers, and governance professionals who need to stay current on trustworthy AI research.

YOUR TASK: Write a cohesive, engaging blog post that:

1. **Opens with context** - What happened today in secure reasoning research? Any notable patterns or themes?

2. **Features key articles** - Present the most important research with:
   - Clear explanation of what the research does
   - Why it matters to secure reasoning (provenance, auditability, interpretability, alignment, verification, governance)
   - Practical implications for organizations

3. **Synthesizes themes** - What are the connecting threads? What trends are emerging?

4. **Provides recommendations** - What should practitioners pay attention to? What actions should organizations consider?

5. **Maintains expert tone** - You're a senior AI safety researcher, not a generic news aggregator. Add insight and critical analysis.

STRUCTURE:
- Brief introduction (2-3 paragraphs setting up today's digest)
- Featured articles section (highlight 3-5 most significant with detailed analysis)
- Additional notable research (briefly mention others worth tracking)
- Themes and trends synthesis
- Recommendations for practitioners
- Closing note about the automated system

STYLE:
- Professional but accessible
- Use specific technical terms when needed, but explain significance
- Focus on "why this matters" not just "what happened"
- Be honest about limitations (these are based on abstracts/excerpts)

---

TODAY'S DATA ({len(articles)} articles):

{chr(10).join(articles_summary)}

---

Write the complete blog post in markdown format. Make it engaging and insightful, synthesizing the research rather than just listing it. Your goal is to help practitioners quickly understand what matters and why.

Include at the end:
- Session ID: {session_id}
- Generated timestamp: {generated_at}
- Note that this is automated with Phase-0 telemetry
"""

    print("Asking Gemini to write the blog post...")

    # Call Gemini to write the blog
    gem_client = GeminiClient()

    response = gem_client.generate(
        blog_writing_prompt,
        system_prompt="You are a senior AI safety researcher and excellent technical writer. You write engaging, insightful blog posts about secure reasoning research for practitioners.",
        temperature=0.7,  # Slightly higher for creative writing
        max_tokens=4096,  # Need room for full blog post
        agent_id="blog_writer",
        session_id=session_id,
        turn_id=0,
        task_type="blog_writing"
    )

    blog_content = response.strip()

    # Clean markdown fences if present
    if blog_content.startswith("```"):
        import re
        match = re.search(r'```(?:markdown)?\s*\n?(.*?)\n?```', blog_content, re.DOTALL)
        if match:
            blog_content = match.group(1).strip()

    # Write to output file
    with open(output_path, 'w') as f:
        f.write(blog_content)

    print(f"✅ Blog post written to: {output_path}")
    print(f"   Length: {len(blog_content)} characters")


def main():
    """Generate blog post from latest brief."""

    if not GEMINI_AVAILABLE:
        print("ERROR: Gemini client not available")
        sys.exit(1)

    # Find latest brief
    content_dir = script_dir.parent / "content" / "briefs"

    # Allow command line argument for specific brief
    if len(sys.argv) > 1:
        brief_path = Path(sys.argv[1])
    else:
        # Find most recent brief
        briefs = sorted(content_dir.glob("*_articles.json"), reverse=True)
        if not briefs:
            print("ERROR: No briefs found in content/briefs/")
            sys.exit(1)
        brief_path = briefs[0]

    if not brief_path.exists():
        print(f"ERROR: Brief not found: {brief_path}")
        sys.exit(1)

    # Output path: same name but _BLOG.md
    output_path = brief_path.parent / brief_path.name.replace("_articles.json", "_BLOG.md")

    print(f"Generating blog post from: {brief_path}")
    generate_blog_post(brief_path, output_path)

    print("\nTo view the blog post:")
    print(f"  cat {output_path}")


if __name__ == "__main__":
    main()
