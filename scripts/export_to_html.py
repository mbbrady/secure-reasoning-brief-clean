#!/usr/bin/env python3
"""
Export markdown briefs to standalone HTML with RKL branding.

Creates self-contained HTML files for competition demo.
"""

import markdown
from pathlib import Path
from datetime import datetime
import argparse

# RKL Brand Colors (from website config)
RKL_NAVY = "#0a2342"
RKL_CORAL = "#ff8b7b"
RKL_WHITE = "#ffffff"
RKL_GREY = "#5C5A5A"
RKL_WHITE_OFFSET = "#f9f9fb"


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} | Resonant Knowledge Lab</title>
    <style>
        /* RKL Brand Styling */
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Source Sans Pro', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            line-height: 1.7;
            color: {navy};
            background: {white_offset};
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: {white};
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}

        /* Header */
        header {{
            border-bottom: 3px solid {coral};
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .site-title {{
            font-family: 'Playfair Display', Georgia, serif;
            font-size: 1.5em;
            color: {navy};
            margin-bottom: 5px;
        }}

        .site-subtitle {{
            color: {grey};
            font-size: 0.9em;
        }}

        /* Content */
        h1 {{
            font-family: 'Playfair Display', Georgia, serif;
            color: {navy};
            font-size: 2.2em;
            margin: 30px 0 20px 0;
            line-height: 1.3;
        }}

        h2 {{
            font-family: 'Playfair Display', Georgia, serif;
            color: {navy};
            font-size: 1.6em;
            margin: 30px 0 15px 0;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }}

        h3 {{
            color: {navy};
            font-size: 1.3em;
            margin: 25px 0 15px 0;
        }}

        p {{
            margin: 15px 0;
        }}

        a {{
            color: {coral};
            text-decoration: none;
            transition: color 0.2s;
        }}

        a:hover {{
            color: {navy};
            text-decoration: underline;
        }}

        /* Lists */
        ul, ol {{
            margin: 15px 0 15px 30px;
        }}

        li {{
            margin: 8px 0;
        }}

        /* Code and pre */
        code {{
            background: {white_offset};
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}

        pre {{
            background: {white_offset};
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            margin: 15px 0;
        }}

        /* Horizontal rule */
        hr {{
            border: none;
            border-top: 2px solid {coral};
            margin: 40px 0;
        }}

        /* Metadata */
        .metadata {{
            background: {white_offset};
            padding: 15px 20px;
            border-left: 4px solid {coral};
            margin: 20px 0;
            font-size: 0.95em;
        }}

        .metadata strong {{
            color: {navy};
        }}

        /* Footer */
        footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid {coral};
            text-align: center;
            color: {grey};
            font-size: 0.9em;
        }}

        footer a {{
            color: {grey};
        }}

        /* Blockquotes */
        blockquote {{
            border-left: 4px solid {coral};
            padding-left: 20px;
            margin: 20px 0;
            font-style: italic;
            color: {grey};
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}

        th {{
            background: {white_offset};
            color: {navy};
            font-weight: 600;
        }}

        /* Navigation */
        .nav {{
            margin: 20px 0;
        }}

        .nav a {{
            display: inline-block;
            padding: 8px 15px;
            margin: 5px;
            background: {white_offset};
            border-radius: 5px;
            font-size: 0.9em;
        }}

        .nav a:hover {{
            background: {coral};
            color: {white};
            text-decoration: none;
        }}

        /* Responsive */
        @media (max-width: 768px) {{
            .container {{
                padding: 20px;
            }}

            h1 {{
                font-size: 1.8em;
            }}

            h2 {{
                font-size: 1.4em;
            }}
        }}
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Source+Sans+Pro:wght@400;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <div class="site-title">Resonant Knowledge Lab</div>
            <div class="site-subtitle">Secure Reasoning Research Brief</div>
        </header>

        {navigation}

        <main>
            {content}
        </main>

        <footer>
            <p>
                <strong>Resonant Knowledge Lab</strong> • Secure Reasoning Research Brief<br>
                Generated with Type III Compliance • Local AI Processing<br>
                <a href="https://resonantknowledgelab.org">resonantknowledgelab.org</a>
            </p>
            <p style="margin-top: 15px; font-size: 0.85em;">
                Competition Demo • Kaggle 5-Day AI Agents Intensive Capstone<br>
                Generated: {generated_time}
            </p>
        </footer>
    </div>
</body>
</html>
"""


def create_navigation(current_type='index'):
    """Create navigation links."""
    nav_items = {
        'index': ('index.html', 'Overview'),
        'daily': ('daily_briefs.html', 'Daily Briefs'),
        'weekly': ('weekly_synthesis.html', 'Weekly Synthesis'),
    }

    nav_html = '<nav class="nav">'
    for key, (url, label) in nav_items.items():
        if key == current_type:
            nav_html += f'<a href="{url}" style="font-weight: bold; background: {RKL_CORAL}; color: {RKL_WHITE};">{label}</a>'
        else:
            nav_html += f'<a href="{url}">{label}</a>'
    nav_html += '</nav>'

    return nav_html


def markdown_to_html(md_content, title, nav_type='index'):
    """Convert markdown to styled HTML."""

    # Convert markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'extra',
            'codehilite',
            'tables',
            'toc'
        ]
    )

    # Generate navigation
    navigation = create_navigation(nav_type)

    # Fill template
    html = HTML_TEMPLATE.format(
        title=title,
        navigation=navigation,
        content=html_content,
        navy=RKL_NAVY,
        coral=RKL_CORAL,
        white=RKL_WHITE,
        grey=RKL_GREY,
        white_offset=RKL_WHITE_OFFSET,
        generated_time=datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    )

    return html


def create_index_page(output_dir: Path):
    """Create overview/landing page."""

    index_md = """
# Secure Reasoning Research Brief - Demo

## Multi-Agent AI System with Phase-0 Telemetry

This demo showcases an automated research brief system that demonstrates **Type III compliance** —
local AI processing with secure data handling.

### System Overview

**Architecture:**
- **18-agent system** collecting and analyzing AI safety research
- **Local processing:** Ollama (llama3.2:3b) on worker cluster
- **Cloud analysis:** Gemini (2.0-flash) for expert synthesis
- **Type III compliance:** Raw data never exposed to external models

**Output Formats:**
- **Daily Briefs:** Quick 2-3 minute summaries (2x daily)
- **Weekly Synthesis:** Deep analysis with IEEE citations (weekly)

### Demo Contents

📄 **[Daily Briefs](daily_briefs.html)** - See quick executive summaries

📊 **[Weekly Synthesis](weekly_synthesis.html)** - See comprehensive analysis

---

## Key Features Demonstrated

### 1. Multi-Agent Coordination
- Feed monitoring → Content filtering → Summarization → Analysis
- 18 specialized agents working in pipeline
- Full reasoning traces in Phase-0 telemetry

### 2. Type III Compliance
- Raw article content processed locally only (Ollama)
- Cloud APIs receive only derived summaries
- Governance ledger documents all data handling
- Audit trail proves no raw data exposure

### 3. Academic Rigor
- IEEE-style citations for all referenced papers
- Verifiable claims (all links included)
- Professional synthesis by domain expert (Gemini)

### 4. Automation
- Runs 2x daily via cron (9 AM, 9 PM)
- Weekly synthesis auto-generates (Sunday 10 PM)
- No human intervention required

---

## Technical Stack

**Local AI:**
- Ollama API (Betty cluster worker node)
- llama3.2:3b model
- 8000 char context windows

**Cloud AI:**
- Google Gemini API (gemini-2.0-flash)
- Expert analysis and synthesis
- Quality validation

**Telemetry:**
- Phase-0 Research Telemetry (Parquet format)
- 4 artifact types: execution context, reasoning graph, governance ledger, artifact lineage
- Full audit trail for compliance verification

**Infrastructure:**
- Python 3.11
- Cron automation
- RSS feed monitoring (ArXiv, AI Alignment Forum, Google AI Blog)

---

## Competition Context

**Kaggle 5-Day AI Agents Intensive - Capstone Competition**

This system demonstrates:
- ✅ Multi-agent architecture
- ✅ Secure reasoning principles
- ✅ Phase-0 telemetry integration
- ✅ Real-world application (research monitoring)
- ✅ Type III compliance (data governance)

---

## Next: Explore the Briefs

Choose your reading format:

- **[Daily Briefs →](daily_briefs.html)** - Quick daily updates (2-3 minutes)
- **[Weekly Synthesis →](weekly_synthesis.html)** - Deep weekly analysis (10-15 minutes)

---

*Generated for Kaggle Competition Submission • November 2025*
"""

    html = markdown_to_html(index_md, "Secure Reasoning Brief Demo", 'index')

    output_file = output_dir / "index.html"
    output_file.write_text(html)
    print(f"✅ Created: {output_file}")


def create_daily_briefs_page(briefs_dir: Path, output_dir: Path):
    """Create page with all daily briefs."""

    # Find all daily briefs
    daily_briefs = sorted(briefs_dir.glob("*_DAILY.md"), reverse=True)

    if not daily_briefs:
        print("⚠️  No daily briefs found")
        return

    # Build combined markdown
    md_content = """
# Daily Briefs

Quick executive summaries of AI safety research, generated twice daily.

**Format:** 2-3 minute read • Key highlights • High-priority papers only

---

"""

    for brief_path in daily_briefs:
        # Read the brief
        brief_md = brief_path.read_text()

        # Remove YAML frontmatter if present
        if brief_md.startswith('---'):
            parts = brief_md.split('---', 2)
            if len(parts) >= 3:
                brief_md = parts[2].strip()

        # Add to combined content
        md_content += f"\n\n{brief_md}\n\n---\n\n"

    html = markdown_to_html(md_content, "Daily Briefs", 'daily')

    output_file = output_dir / "daily_briefs.html"
    output_file.write_text(html)
    print(f"✅ Created: {output_file}")
    print(f"   Included {len(daily_briefs)} daily briefs")


def create_weekly_synthesis_page(briefs_dir: Path, output_dir: Path):
    """Create page with weekly synthesis."""

    # Find weekly blogs
    weekly_blogs = sorted(briefs_dir.glob("*_WEEKLY_BLOG.md"), reverse=True)

    if not weekly_blogs:
        print("⚠️  No weekly blogs found")
        return

    # Use the most recent one
    latest_blog = weekly_blogs[0]

    blog_md = latest_blog.read_text()

    # Remove YAML frontmatter if present
    if blog_md.startswith('---'):
        parts = blog_md.split('---', 2)
        if len(parts) >= 3:
            blog_md = parts[2].strip()

    # Add intro
    intro = """
# Weekly Synthesis

Comprehensive analysis of the week's AI safety research with expert insights and IEEE citations.

**Format:** 10-15 minute read • Trend analysis • Academic citations

---

"""

    md_content = intro + blog_md

    html = markdown_to_html(md_content, "Weekly Synthesis", 'weekly')

    output_file = output_dir / "weekly_synthesis.html"
    output_file.write_text(html)
    print(f"✅ Created: {output_file}")
    print(f"   Source: {latest_blog.name}")


def main():
    parser = argparse.ArgumentParser(description='Export briefs to HTML')
    parser.add_argument('--briefs-dir', type=str,
                       default='content/briefs',
                       help='Directory containing markdown briefs')
    parser.add_argument('--output-dir', type=str,
                       default='demo',
                       help='Output directory for HTML files')

    args = parser.parse_args()

    script_dir = Path(__file__).parent
    briefs_dir = script_dir.parent / args.briefs_dir
    output_dir = script_dir.parent / args.output_dir

    # Create output directory
    output_dir.mkdir(exist_ok=True, parents=True)

    print("\n🎨 Exporting briefs to HTML with RKL branding...\n")

    # Create pages
    create_index_page(output_dir)
    create_daily_briefs_page(briefs_dir, output_dir)
    create_weekly_synthesis_page(briefs_dir, output_dir)

    print(f"\n✅ HTML demo created in: {output_dir}")
    print(f"\nTo view:")
    print(f"  open {output_dir}/index.html")
    print(f"\nOr:")
    print(f"  cd {output_dir} && python -m http.server 8000")
    print(f"  Then visit: http://localhost:8000\n")


if __name__ == "__main__":
    main()
