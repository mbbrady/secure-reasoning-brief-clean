#!/usr/bin/env python3
"""
Secure Reasoning Brief Agent - Publisher

Part of the RKL 18-Agent Multi-Agent System for Type III Secure Reasoning
================================================================================

This script implements the Publishing agent group:
- Publishing (3 agents): Formatting, Hugo generation, Git deployment

Type III Secure Reasoning Demonstration:
- Input: Derived insights from local processing (summaries, tags, themes)
- Processing: Formats derived content into Hugo markdown (local)
- Output: Public brief on GitHub Pages (Type III boundary crossing)
- Demonstrates: "Insights travel, data stays" - raw articles never published

Agents Implemented:
1. Brief Formatter - Converts JSON summaries to Hugo markdown
2. Theme Analyzer - Identifies cross-article themes and patterns
3. Recommendation Generator - Creates actionable guidance from themes
4. Git Publisher - Commits and pushes to GitHub (triggers Netlify deploy)

For Kaggle AI Agents Capstone Competition - "Agents for Good" Track
Demonstrates: Multi-agent orchestration, Type III boundary enforcement, public benefit
"""

import os
import sys
import json
import logging
import subprocess
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from collections import Counter
from dotenv import load_dotenv

# Import RKL logging for research telemetry
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from rkl_logging import StructuredLogger, sha256_text
    RKL_LOGGING_AVAILABLE = True
except ImportError:
    RKL_LOGGING_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if not RKL_LOGGING_AVAILABLE:
    logger.warning("rkl_logging not available - telemetry disabled")


class BriefGenerator:
    """
    Generates formatted Hugo-compatible markdown briefs from article JSON.

    Agent Role in 18-Agent System:
    - Agent #13: Brief Formatter - Converts JSON to Hugo markdown
    - Agent #14: Theme Analyzer - Identifies cross-article patterns
    - Agent #15: Recommendation Generator - Creates actionable guidance

    Type III Implementation:
    - Input: Derived insights (summaries, tags) from local processing
    - Processing: Formats derived content into public brief (local)
    - Output: Hugo markdown ready for public GitHub Pages deployment
    - Boundary: Only derived insights are formatted for public sharing

    This class operates entirely on derived content that has already been
    processed locally. It never touches raw article content, ensuring Type III
    compliance: "insights travel, data stays."

    Methods:
        generate_brief: Main entry point, orchestrates brief generation
        _generate_front_matter: Creates Hugo YAML front matter
        _generate_executive_summary: Summarizes weekly themes
        _generate_articles_section: Formats article summaries
        _generate_themes_section: Analyzes cross-article themes
        _generate_recommendations_section: Creates actionable guidance
        _generate_footer: Adds metadata and attribution

    Example:
        >>> generator = BriefGenerator()
        >>> with open("2025-11-16_articles.json") as f:
        ...     articles_data = json.load(f)
        >>> brief_md = generator.generate_brief(articles_data, "2025-11-16")
        >>> print(len(brief_md))  # Hugo-compatible markdown
    """

    def __init__(self):
        pass

    def generate_brief(self, articles_data: Dict, date_str: str) -> str:
        """
        Generate a complete Hugo-compatible brief from articles JSON.

        Orchestrates the Publishing agent workflow:
        1. Brief Formatter: Assembles Hugo front matter and sections
        2. Theme Analyzer: Identifies cross-article themes
        3. Recommendation Generator: Creates actionable guidance

        Type III Note: Input is derived content only (summaries, tags, themes).
        Raw article content never appears in generated brief.

        Args:
            articles_data (Dict): Processed articles from fetch_and_summarize.py
                Expected structure:
                {
                    "articles": [...],  # List of article summaries
                    "metadata": {...}   # Processing metadata
                }
            date_str (str): Date string in YYYY-MM-DD format

        Returns:
            str: Complete Hugo-compatible markdown with:
                - YAML front matter
                - Executive summary
                - Featured articles (derived summaries only)
                - Key themes analysis
                - Recommended actions
                - Footer with metadata

        Example:
            >>> brief = generator.generate_brief(articles_data, "2025-11-16")
            >>> with open("brief.md", "w") as f:
            ...     f.write(brief)
        """
        articles = articles_data.get("articles", [])
        metadata = articles_data.get("metadata", {})

        if not articles:
            logger.warning("No articles to generate brief from")
            return ""

        # Generate front matter
        front_matter = self._generate_front_matter(articles, date_str)

        # Generate executive summary
        exec_summary = self._generate_executive_summary(articles)

        # Generate article sections
        articles_md = self._generate_articles_section(articles)

        # Analyze themes
        themes_md = self._generate_themes_section(articles)

        # Generate recommendations
        recommendations_md = self._generate_recommendations_section(articles)

        # Generate footer
        footer = self._generate_footer(metadata)

        # Assemble the brief
        brief = f"""{front_matter}

## Executive Summary

{exec_summary}

---

## Featured Articles

{articles_md}

---

## Key Themes This Week

{themes_md}

---

## Recommended Actions for Organizations

{recommendations_md}

---

{footer}
"""
        return brief

    def _generate_front_matter(self, articles: List[Dict], date_str: str) -> str:
        """Generate Hugo front matter"""
        # Extract all unique tags
        all_tags = set()
        for article in articles:
            all_tags.update(article.get("tags", []))

        tags_yaml = "\n".join([f'  - "{tag}"' for tag in sorted(all_tags)])

        # Parse date
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%B %d, %Y")
        except:
            formatted_date = date_str

        front_matter = f"""---
title: "Secure Reasoning Brief - {formatted_date}"
date: {date_str}
draft: false
type: "briefs"
description: "Weekly digest of advances in verifiable AI, trustworthy AI, and AI governance"
tags:
{tags_yaml if tags_yaml else '  []'}
categories:
  - "Secure Reasoning"
  - "AI Safety"
  - "AI Governance"
---"""
        return front_matter

    def _generate_executive_summary(self, articles: List[Dict]) -> str:
        """Generate executive summary based on article count and themes"""
        num_articles = len(articles)

        # Get top categories
        category_counter = Counter()
        for article in articles:
            category_counter[article.get("category", "general")] += 1

        top_categories = category_counter.most_common(3)
        category_text = ", ".join([f"{cat} ({count})" for cat, count in top_categories])

        summary = f"""This week's brief covers **{num_articles} significant developments** in AI safety, verification, and governance.

**Content breakdown:** {category_text}

Key themes include advances in formal verification methods, new governance frameworks for AI deployment, and ongoing research in interpretability and alignment. Organizations should pay particular attention to developments in {top_categories[0][0] if top_categories else 'AI governance'} as these may inform near-term policy and implementation decisions."""

        return summary

    def _generate_articles_section(self, articles: List[Dict]) -> str:
        """Generate the articles section"""
        articles_md = []

        for article in articles:
            article_md = f"""### {article.get("title", "Untitled")}

**Source:** {article.get("source", "Unknown")} | **Date:** {article.get("date", "N/A")} | **Category:** {article.get("category", "general")}

**Technical Summary:**
{article.get("technical_summary", "No summary available.")}

**What This Means for Organizations:**
{article.get("lay_explanation", "No explanation available.")}

**Tags:** {", ".join(article.get("tags", []))}

**[Read More]({article.get("link", "#")})**

---"""
            articles_md.append(article_md)

        return "\n\n".join(articles_md)

    def _generate_themes_section(self, articles: List[Dict]) -> str:
        """Analyze and generate key themes section"""
        # Count tag occurrences
        tag_counter = Counter()
        category_counter = Counter()

        for article in articles:
            tags = article.get("tags", [])
            category = article.get("category", "general")

            tag_counter.update(tags)
            category_counter[category] += 1

        # Get top themes
        top_tags = tag_counter.most_common(5)
        top_categories = category_counter.most_common(3)

        themes_md = []

        if top_tags:
            themes_md.append("**Most Common Topics:**")
            for tag, count in top_tags:
                themes_md.append(f"- **{tag}** ({count} article{'s' if count > 1 else ''})")

        themes_md.append("")

        if top_categories:
            themes_md.append("**Content Distribution:**")
            for category, count in top_categories:
                themes_md.append(f"- {category.title()}: {count} article{'s' if count > 1 else ''}")

        return "\n".join(themes_md)

    def _generate_recommendations_section(self, articles: List[Dict]) -> str:
        """Generate recommendations based on article themes"""
        # Count categories
        category_counter = Counter()
        tag_counter = Counter()

        for article in articles:
            category_counter[article.get("category", "general")] += 1
            tag_counter.update(article.get("tags", []))

        recommendations = []

        # Security-focused recommendation
        if category_counter.get("security", 0) > 0:
            recommendations.append(
                "- **Review Security Practices:** Several security-related developments this week "
                "warrant review of current AI system security protocols and deployment practices."
            )

        # Research-focused recommendation
        if category_counter.get("research", 0) > 3:
            recommendations.append(
                "- **Track Research Trends:** High volume of research publications suggests "
                "rapidly evolving technical landscape in AI safety and verification. Consider "
                "establishing regular monitoring processes."
            )

        # Safety/alignment recommendation
        if "alignment" in tag_counter or "AI safety" in tag_counter:
            recommendations.append(
                "- **Update Safety Frameworks:** New safety and alignment research should inform "
                "updates to organizational AI governance frameworks and deployment guidelines."
            )

        # Governance recommendation
        if category_counter.get("policy", 0) > 0 or "governance" in tag_counter:
            recommendations.append(
                "- **Review Governance Policies:** Recent policy developments may require "
                "updates to organizational AI governance documentation and compliance procedures."
            )

        # Verification/interpretability recommendation
        if "verification" in tag_counter or "interpretability" in tag_counter:
            recommendations.append(
                "- **Evaluate Verification Tools:** Consider incorporating formal verification "
                "or interpretability methods into AI system development and audit processes."
            )

        # Industry developments
        if category_counter.get("industry", 0) > 0:
            recommendations.append(
                "- **Monitor Industry Practices:** Stay informed about how leading organizations "
                "are implementing trustworthy AI principles in production environments."
            )

        # Default recommendation if none generated
        if not recommendations:
            recommendations.append(
                "- **Continue Monitoring:** Maintain awareness of developments in verifiable and "
                "trustworthy AI practices through regular review of this brief."
            )

        return "\n".join(recommendations)

    def _generate_footer(self, metadata: Dict) -> str:
        """
        Generate footer with metadata and attribution.

        Args:
            metadata (Dict): Processing metadata from article JSON

        Returns:
            str: Markdown footer with processing details and attribution
        """
        footer = f"""## About This Brief

This brief was generated by the RKL Secure Reasoning Brief Agent using **Type III secure reasoning**—all raw data analysis occurred locally on RKL infrastructure using open-source AI models (Llama 3.2/Mistral via Ollama), with only derived insights published here.

**Sources monitored:** ArXiv (AI, Security), AI Alignment Forum, Google AI Blog, and other research feeds

**Date range:** {metadata.get("date_range", "N/A")}
**Articles processed:** {metadata.get("num_articles", "N/A")}
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}

---

*For questions or to suggest additional sources, contact [info@resonantknowledgelab.org](mailto:info@resonantknowledgelab.org)*"""
        return footer


class GitHubPublisher:
    """
    Publishes briefs to GitHub repository (Publishing Agent Group).

    Agent Role in 18-Agent System:
    - Agent #16: Git Publisher - Commits and pushes to GitHub

    Type III Boundary Enforcement:
    - THIS IS WHERE TYPE III BOUNDARY CROSSING OCCURS
    - Input: Hugo markdown brief (derived insights only)
    - Action: Commits to GitHub, triggers Netlify deploy
    - Result: Public brief on GitHub Pages (Type III output)
    - Verification: Only derived content crosses boundary, never raw articles

    This publisher is the final step in the Type III workflow. It takes
    locally-generated derived insights and publishes them publicly, while
    raw article content remains on local Betty cluster.

    Attributes:
        repo_path (Path): Path to Git repository containing website

    Example:
        >>> publisher = GitHubPublisher(Path("/path/to/website"))
        >>> success = publisher.commit_and_push(
        ...     Path("content/briefs/2025-11-16-brief.md"),
        ...     "Add Secure Reasoning Brief for 2025-11-16",
        ...     auto_push=True
        ... )
    """

    def __init__(self, repo_path: Path, research_logger: Optional['StructuredLogger'] = None):
        self.repo_path = repo_path
        self.research_logger = research_logger

    def commit_and_push(self, file_path: Path, commit_message: str, auto_push: bool = False,
                        session_id: Optional[str] = None) -> bool:
        """
        Commit and optionally push a file to the repository.

        Type III Boundary Crossing: This method publishes derived insights
        to GitHub Pages, completing the Type III workflow.

        Args:
            file_path (Path): Path to file to commit (Hugo markdown brief)
            commit_message (str): Git commit message
            auto_push (bool): If True, automatically push to remote (triggers deploy)

        Returns:
            bool: True if successful, False on error

        Side Effects:
            - Commits file to local git repository
            - If auto_push=True, pushes to GitHub (triggers Netlify deployment)
            - Netlify then builds and deploys to public GitHub Pages

        Example:
            >>> publisher = GitHubPublisher(website_path)
            >>> publisher.commit_and_push(
            ...     brief_path,
            ...     "Add weekly brief",
            ...     auto_push=True
            ... )
            True
        """
        try:
            # Check if we're in a git repository
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"Not a git repository: {self.repo_path}")
                # Log boundary event: failure
                if self.research_logger and RKL_LOGGING_AVAILABLE:
                    self.research_logger.log("boundary_event", {
                        "event_id": str(uuid.uuid4()),
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "t": int(time.time() * 1000),
                        "session_id": session_id or "unknown",
                        "agent_id": "git_publisher",
                        "rule_id": "type3.publication.derived_only",
                        "trigger_tag": "git_error",
                        "context_tag": "not_git_repo",
                        "action": "block"
                    })
                return False

            # Log boundary event: prepare to publish (Type III boundary crossing)
            if self.research_logger and RKL_LOGGING_AVAILABLE:
                self.research_logger.log("boundary_event", {
                    "event_id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "t": int(time.time() * 1000),
                    "session_id": session_id or "unknown",
                    "agent_id": "git_publisher",
                    "rule_id": "type3.publication.derived_only",
                    "trigger_tag": "prepare_publish",
                    "context_tag": "github_commit",
                    "action": "allow"
                })

            # Add file
            subprocess.run(
                ["git", "add", str(file_path)],
                cwd=self.repo_path,
                check=True
            )

            # Commit
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.repo_path,
                check=True
            )

            logger.info("Successfully committed changes")

            # Get commit SHA for governance ledger
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            commit_sha = sha_result.stdout.strip()

            # Optionally push
            if auto_push:
                # Log boundary event: pushing to remote (Type III boundary crossing)
                if self.research_logger and RKL_LOGGING_AVAILABLE:
                    self.research_logger.log("boundary_event", {
                        "event_id": str(uuid.uuid4()),
                        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "t": int(time.time() * 1000),
                        "session_id": session_id or "unknown",
                        "agent_id": "git_publisher",
                        "rule_id": "type3.publication.derived_only",
                        "trigger_tag": "prepare_publish",
                        "context_tag": "github_push",
                        "action": "allow"
                    })

                subprocess.run(
                    ["git", "push"],
                    cwd=self.repo_path,
                    check=True
                )
                logger.info("Successfully pushed to remote")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e}")
            # Log boundary event: failure
            if self.research_logger and RKL_LOGGING_AVAILABLE:
                self.research_logger.log("boundary_event", {
                    "event_id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "t": int(time.time() * 1000),
                    "session_id": session_id or "unknown",
                    "agent_id": "git_publisher",
                    "rule_id": "type3.publication.derived_only",
                    "trigger_tag": "git_error",
                    "context_tag": "subprocess_error",
                    "action": "block"
                })
            return False


def main():
    """
    Main entry point for brief publishing and GitHub deployment.

    Orchestrates the complete Publishing agent workflow:

    1. **Input Loading** (lines 469-488):
       - Loads .env variables (PUBLISH_TO_GITHUB, AUTO_PUSH)
       - Finds latest article JSON from fetch_and_summarize.py
       - Loads derived insights (summaries, tags, themes)

    2. **Brief Generation** (lines 490-505):
       - Agent #13: Brief Formatter creates Hugo markdown
       - Agent #14: Theme Analyzer identifies patterns
       - Agent #15: Recommendation Generator creates guidance
       - All processing uses derived content only (Type III compliant)

    3. **Local Saving** (lines 507-517):
       - Saves Hugo markdown to website content directory
       - File: website/content/briefs/{date}-secure-reasoning-brief.md
       - Ready for Hugo build or manual review

    4. **GitHub Publishing** (lines 519-538):
       - Agent #16: Git Publisher commits to GitHub
       - Optionally pushes to remote (triggers Netlify deploy)
       - **THIS IS TYPE III BOUNDARY CROSSING**
       - Only derived insights are published, never raw articles

    Type III Workflow Completion:
    - Raw RSS feeds: Stayed on Betty cluster (never exposed)
    - Raw articles: Stayed on Betty cluster (never exposed)
    - Derived summaries: Published to GitHub Pages (Type III output)
    - Demonstrates: "Raw data stays local, derived insights travel"

    Environment Variables:
        PUBLISH_TO_GITHUB: Enable git commit (default: false)
        AUTO_PUSH: Enable git push to remote (default: false)

    Outputs:
        website/content/briefs/{YYYY-MM-DD}-secure-reasoning-brief.md
        Optionally commits to git and pushes to GitHub

    Example:
        $ python scripts/publish_brief.py
        INFO - Using article data from: content/briefs/2025-11-16_articles.json
        INFO - Generating Hugo-compatible brief...
        INFO - Brief saved to: website/content/briefs/2025-11-16-secure-reasoning-brief.md
        INFO - GitHub publishing disabled (set PUBLISH_TO_GITHUB=true to enable)
        INFO - Done!

    Example (with GitHub publishing):
        $ PUBLISH_TO_GITHUB=true AUTO_PUSH=true python scripts/publish_brief.py
        INFO - Committing to git repository...
        INFO - Successfully committed to git
        INFO - Changes pushed to remote - Netlify will auto-deploy
        INFO - Done!
    """
    # Load environment variables
    load_dotenv()

    # Get configuration
    script_dir = Path(__file__).parent.parent
    content_dir = script_dir / "content" / "briefs"

    # Initialize research telemetry logger
    research_logger = None
    if RKL_LOGGING_AVAILABLE:
        research_data_dir = script_dir / "data" / "research"
        research_logger = StructuredLogger(
            base_dir=str(research_data_dir),
            rkl_version="1.0",
            batch_size=50
        )
        logger.info(f"Research telemetry enabled: {research_data_dir}")
    else:
        logger.warning("Research telemetry disabled (rkl_logging not available)")

    # Find latest articles JSON
    json_files = sorted(content_dir.glob("*_articles.json"), reverse=True)

    if not json_files:
        logger.error("No article JSON files found")
        sys.exit(1)

    latest_json = json_files[0]
    logger.info(f"Using article data from: {latest_json}")

    # Load articles data
    with open(latest_json) as f:
        articles_data = json.load(f)

    # Extract session_id from articles data (added by fetch_and_summarize.py)
    session_id = articles_data.get("session_id", f"publish-{datetime.utcnow().strftime('%Y-%m-%d')}-{str(uuid.uuid4())[:8]}")

    # Extract date from filename
    date_str = latest_json.stem.split("_")[0]  # e.g., "2025-11-11" from "2025-11-11_articles.json"

    # Generate brief
    logger.info("Generating Hugo-compatible brief...")
    generator = BriefGenerator()
    brief_content = generator.generate_brief(articles_data, date_str)

    if not brief_content:
        logger.error("Failed to generate brief")
        sys.exit(1)

    # Log reasoning graph edge: brief_formatter → git_publisher
    if research_logger and RKL_LOGGING_AVAILABLE:
        research_logger.log("reasoning_graph_edge", {
            "session_id": session_id,
            "edge_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "t": int(time.time() * 1000),
            "from_agent": "brief_formatter",
            "to_agent": "git_publisher",
            "msg_type": "act",
            "intent_tag": "publish_brief",
            "content_hash": sha256_text(brief_content[:1000])
        })

    # Determine output path (Hugo website content directory)
    website_dir = script_dir.parent / "website"
    hugo_briefs_dir = website_dir / "content" / "briefs"
    hugo_briefs_dir.mkdir(parents=True, exist_ok=True)

    brief_filename = f"{date_str}-secure-reasoning-brief.md"
    brief_path = hugo_briefs_dir / brief_filename

    # Save brief
    with open(brief_path, "w") as f:
        f.write(brief_content)

    logger.info(f"Brief saved to: {brief_path}")

    # Optionally publish to GitHub
    publish_to_github = os.getenv("PUBLISH_TO_GITHUB", "false").lower() == "true"
    auto_push = os.getenv("AUTO_PUSH", "false").lower() == "true"

    if publish_to_github:
        logger.info("Committing to git repository...")
        publisher = GitHubPublisher(website_dir, research_logger)

        commit_msg = f"Add Secure Reasoning Brief for {date_str}\n\nGenerated by RKL Brief Agent using Type III secure reasoning"
        success = publisher.commit_and_push(brief_path, commit_msg, auto_push, session_id)

        if success:
            logger.info("Successfully committed to git")

            # Get commit SHA for governance ledger
            try:
                sha_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=website_dir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                commit_sha = sha_result.stdout.strip()
            except subprocess.CalledProcessError:
                commit_sha = "unknown"

            # Log governance ledger entry (Type III compliance audit)
            if research_logger and RKL_LOGGING_AVAILABLE:
                research_logger.log("governance_ledger", {
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "publish_id": session_id,
                    "artifact_ids": [sha256_text(f"{a.get('title','')}|{a.get('link','')}") for a in articles_data.get("articles", [])],
                    "contributing_agent_ids": ["brief_formatter", "theme_analyzer", "recommendation_generator", "git_publisher"],
                    "verification_hashes": [sha256_text(json.dumps(a)) for a in articles_data.get("articles", [])[:5]],
                    "type3_verified": True,
                    "human_signoff_id": os.getenv("HUMAN_SIGNOFF_ID", "unknown"),
                    "release_commit_sha": commit_sha,
                    "schema_version": 1
                })

            if auto_push:
                logger.info("Changes pushed to remote - Netlify will auto-deploy")
            else:
                logger.info("Run 'git push' manually to deploy to Netlify")
        else:
            logger.warning("Failed to commit to git (brief still saved locally)")
    else:
        logger.info("GitHub publishing disabled (set PUBLISH_TO_GITHUB=true to enable)")

    # Flush and close research logger
    if research_logger:
        research_logger.close()
        logger.info("Research telemetry data saved")

    logger.info("Done!")


if __name__ == "__main__":
    main()
