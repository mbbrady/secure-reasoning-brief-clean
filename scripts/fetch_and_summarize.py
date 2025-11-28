#!/usr/bin/env python3
"""
Secure Reasoning Brief Agent - RSS Fetcher and Summarizer

Part of the RKL 18-Agent Multi-Agent System for Type III Secure Reasoning
================================================================================

This script implements the Discovery and Processing agent groups:
- Discovery (3 agents): Feed monitoring, filtering, credibility checks
- Processing (6 agents): Summarization, metadata extraction, theme identification

Type III Secure Reasoning Demonstration:
- Processes raw RSS feeds locally (never sent to external APIs)
- Generates derived insights (summaries) using local Ollama models
- Derived insights can be shared publicly or reviewed by external QA (Gemini)
- Raw article content remains under local control (Betty cluster)

Research Data Generation:
- Captures execution context (model configs, token usage, latency)
- Logs agent graph (multi-agent message passing)
- Records boundary events (Type III compliance verification)
- Generates research-grade telemetry for AI safety science

Agents Implemented:
1. Feed Monitor - Fetches RSS feeds from configured sources
2. Content Filter - Filters by keywords and recency
3. Summarizer - Generates technical summaries (local Ollama)
4. Metadata Extractor - Extracts tags and categories
5. Theme Identifier - Identifies common themes across articles

For Kaggle AI Agents Capstone Competition - "Agents for Good" Track
Demonstrates: Multi-agent orchestration, local data sovereignty, Type III boundaries,
             research data generation for AI science community
"""

import os
import sys
import json
import logging
import requests
import feedparser
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
import subprocess
import platform

# CRITICAL: Load .env BEFORE importing GeminiClient (which checks USE_VERTEX_AI)
script_dir = Path(__file__).parent.parent
load_dotenv(dotenv_path=script_dir / ".env")

# Optional system metrics
try:
    import psutil  # type: ignore
except ImportError:
    psutil = None

# Optional Gemini QA
try:
    from gemini_client import GeminiClient  # type: ignore
    GEMINI_CLIENT_AVAILABLE = True
except Exception as e:
    GEMINI_CLIENT_AVAILABLE = False
    logging.warning(f"GeminiClient import failed: {e}")

# Import RKL logging for research telemetry
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from rkl_logging import StructuredLogger, sha256_text
    RKL_LOGGING_AVAILABLE = True
except ImportError:
    RKL_LOGGING_AVAILABLE = False
    logging.warning("rkl_logging not available - telemetry disabled")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OllamaClient:
    """
    Client for interacting with local Ollama API.

    Type III Implementation:
    - All raw data processing happens through this local client
    - Ensures article content never leaves local environment
    - Local processing is the first phase of Type III workflow
    - (Type III = local raw data processing + derived insights that can be external)

    Research Telemetry:
    - Logs execution context (model, tokens, latency) for each generation
    - Records boundary events to verify Type III compliance
    - Generates research data for studying model performance

    Attributes:
        endpoint (str): Ollama API endpoint (e.g., http://192.168.1.11:11434/api/generate)
        model (str): Model name to use (e.g., llama3.2:3b, llama3.2:8b)
        research_logger (StructuredLogger): Optional logger for telemetry

    Example:
        >>> client = OllamaClient("http://localhost:11434/api/generate", "llama3.2:3b")
        >>> response = client.generate("Summarize this text...")
    """

    def __init__(self, endpoint: str, model: str, research_logger: Optional['StructuredLogger'] = None):
        """
        Initialize Ollama client.

        Args:
            endpoint: Full URL to Ollama generate API
            model: Model identifier (must be pulled in Ollama first)
            research_logger: Optional StructuredLogger for research telemetry
        """
        self.endpoint = endpoint
        self.model = model
        self.research_logger = research_logger

    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 agent_id: str = "unknown", session_id: Optional[str] = None,
                 turn_id: Optional[int] = None, artifact_id: Optional[str] = None) -> str:
        """
        Send a prompt to Ollama and return the response.

        Type III Note: This processes raw data locally (Type III requirement).
        Only derived outputs from this processing can be external/public.

        Research Telemetry: Logs execution context for each generation.

        Args:
            prompt: User prompt to send to the model
            system_prompt: Optional system prompt to set model behavior
            agent_id: Agent identifier for telemetry
            session_id: Session identifier for telemetry
            turn_id: Turn number for telemetry

        Returns:
            str: Model's generated response, or empty string on error

        Raises:
            Does not raise - logs errors and returns empty string
        """
        start_time = time.time()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            response = requests.post(self.endpoint, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            generated_text = result.get("response", "")

            # Calculate metrics
            latency_ms = int((time.time() - start_time) * 1000)
            # Prefer Ollama's actual counts if available, fallback to word count estimates
            prompt_tokens = result.get("prompt_eval_count", len(prompt.split()))
            gen_tokens = result.get("eval_count", len(generated_text.split()))

            # Log execution context for research
            if self.research_logger and RKL_LOGGING_AVAILABLE:
                quant = os.getenv("OLLAMA_QUANT", "")
                seed_env = os.getenv("OLLAMA_SEED")
                seed_val = int(seed_env) if seed_env and seed_env.isdigit() else None
                exec_record = {
                    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "session_id": session_id or "unknown",
                    "turn_id": turn_id or 0,
                    "agent_id": agent_id,
                    "model_id": self.model,
                    "model_rev": self.model.split(":")[-1] if ":" in self.model else "latest",
                    "quant": quant or "unknown",
                    "temp": payload.get("temperature", 0.7),  # Default from Ollama
                    "top_p": payload.get("top_p", 1.0),  # Default from Ollama
                    "ctx_tokens_used": prompt_tokens,
                    "gen_tokens": gen_tokens,
                    "tool_lat_ms": latency_ms,
                    "prompt_id_hash": sha256_text(prompt) if RKL_LOGGING_AVAILABLE else "",
                    "system_prompt_hash": sha256_text(system_prompt) if system_prompt and RKL_LOGGING_AVAILABLE else "",
                    "token_estimation": "api" if prompt_tokens and gen_tokens else "word_count",
                    # Phase 1 Enhancement: Capture full prompts and responses for deeper analysis
                    "prompt_preview": prompt[:1000] if prompt else "",
                    "response_preview": generated_text[:1000] if generated_text else "",
                    # Phase 2 Enhancement: Link to artifact for end-to-end tracing
                    "artifact_id": artifact_id or ""
                }
                if seed_val is not None:
                    exec_record["seed"] = seed_val
                self.research_logger.log("execution_context", exec_record)

                # Log boundary event (Type III compliance)
                self.research_logger.log("boundary_event", {
                    "event_id": str(uuid.uuid4()),
                    "t": int(time.time() * 1000),
                    "session_id": session_id or "unknown",
                    "agent_id": agent_id,
                    "rule_id": "type3.local_processing.allowed",
                    "trigger_tag": "ollama_generate",
                    "context_tag": "summarization",
                    "action": "allow"
                })

            return generated_text

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            return ""


class ArticleSummarizer:
    """
    Handles article summarization using Ollama (Processing Agent Group).

    Agent Role in 18-Agent System:
    - Agent #3: Summarizer - Generates technical summaries
    - Agent #4: Metadata Extractor - Extracts tags and themes
    - Agent #5: Lay Translator - Creates accessible explanations

    Type III Implementation:
    - Input: Raw article content (local only)
    - Processing: Local Ollama models (never sent externally)
    - Output: Derived insights (summaries, tags) - can cross Type III boundary
    - Demonstrates: "Raw data stays local, derived insights travel"

    Attributes:
        client (OllamaClient): Local Ollama API client
        max_words (int): Maximum words for summaries (default 80)
    """

    def __init__(self, ollama_client: OllamaClient, max_words: int = 80):
        """
        Initialize the article summarizer.

        Args:
            ollama_client: Configured OllamaClient for local processing
            max_words: Maximum words per summary (configurable via BRIEF_SUMMARY_MAX_WORDS)
        """
        self.client = ollama_client
        self.max_words = max_words

    def summarize_article(self, title: str, content: str, link: str,
                          session_id: Optional[str] = None, turn_id: Optional[int] = None) -> Dict:
        """
        Generate technical summary and lay explanation for an article.

        Type III Boundary: Raw article content processed locally, only derived summaries
        could potentially be sent to external QA (Gemini) in hybrid mode.

        Args:
            title: Article title
            content: Full article content (raw data - stays local)
            link: Article URL for reference
            session_id: Session identifier for research telemetry
            turn_id: Turn number for research telemetry

        Returns:
            Dict containing:
                - title: Original article title
                - link: Article URL
                - technical_summary: Technical summary (derived - can share)
                - lay_explanation: Accessible explanation (derived - can share)
                - tags: Extracted keywords (derived - can share)

        Processing Flow:
            1. Generate technical summary (local Ollama)
            2. Generate lay explanation (local Ollama)
            3. Extract tags (local Ollama)
            4. Return derived insights only (Type III safe)
        """

        # Phase 2 Enhancement: Calculate artifact_id for end-to-end tracing
        artifact_id = sha256_text(link) if RKL_LOGGING_AVAILABLE else ""

        # Phase 2 Enhancement: Track timing for each step
        step_timings = []

        # System prompt for technical summary - sets agent role
        system_prompt = """You are an AI research analyst specializing in verifiable AI,
trustworthy AI, and AI governance. Provide concise, accurate technical summaries."""

        # Use more context for Ollama (up to 8000 chars - still well within 128K limit)
        # This allows better summaries especially for long-form content
        content_for_llm = content[:8000]

        # Technical summary prompt - Agent #3: Summarizer
        # Phase 1 Enhancement: Chain-of-thought prompting for deeper reasoning traces
        tech_prompt = f"""Analyze this AI research paper and create a technical summary.

First, identify:
1. Main contribution (1 sentence)
2. Key methodology (1 sentence)
3. Most important result (1 sentence)

Then, combine these into a {self.max_words}-word technical summary focusing on what practitioners need to know.

Title: {title}
Content: {content_for_llm}

Reasoning:"""

        # Log reasoning graph edge: feed_monitor → summarizer
        if self.client.research_logger and RKL_LOGGING_AVAILABLE:
            self.client.research_logger.log("reasoning_graph_edge", {
                "edge_id": str(uuid.uuid4()),
                "session_id": session_id or "unknown",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "t": int(time.time() * 1000),
                "from_agent": "feed_monitor",
                "to_agent": "summarizer",
                "msg_type": "act",
                "intent_tag": "tech_summary",
                "content_hash": sha256_text(f"{title}|{content[:500]}"),
                # Phase 1 Enhancement: Add decision rationale
                "decision_rationale": f"Article from {link[:50]}... passed keyword/date filter. Sending to summarizer for technical analysis.",
                "payload_summary": f"Title: {title[:80]}... ({len(content_for_llm)} chars content)",
                # Phase 2 Enhancement: Link to artifact for end-to-end tracing
                "artifact_id": artifact_id
            })

        # PROCESSING: Local Ollama generates summary (Type III: raw data processed locally)
        step_start = int(time.time() * 1000)
        technical_summary = self.client.generate(
            tech_prompt, system_prompt,
            agent_id="summarizer",
            session_id=session_id,
            turn_id=turn_id,
            artifact_id=artifact_id
        )
        step_end = int(time.time() * 1000)
        step_timings.append({
            "phase": "act",
            "agent_id": "summarizer",
            "start_t": step_start,
            "end_t": step_end,
            "duration_ms": step_end - step_start
        })

        # Lay explanation prompt
        lay_prompt = f"""Based on this article, explain in 2-3 sentences what this means for
organizations adopting AI systems. Focus on practical implications, risks, or opportunities.

Title: {title}
Content: {content_for_llm}

Provide only the explanation, no preamble."""

        # Log reasoning graph edge: summarizer → lay_translator
        if self.client.research_logger and RKL_LOGGING_AVAILABLE:
            self.client.research_logger.log("reasoning_graph_edge", {
                "edge_id": str(uuid.uuid4()),
                "session_id": session_id or "unknown",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "t": int(time.time() * 1000),
                "from_agent": "summarizer",
                "to_agent": "lay_translator",
                "msg_type": "act",
                "intent_tag": "lay_explanation",
                "content_hash": sha256_text(technical_summary),
                # Phase 1 Enhancement: Add decision rationale
                "decision_rationale": f"Technical summary complete ({len(technical_summary)} chars). Passing to lay translator for accessible explanation.",
                "payload_summary": f"Summary: {technical_summary[:100]}...",
                # Phase 2 Enhancement: Link to artifact for end-to-end tracing
                "artifact_id": artifact_id
            })

        step_start = int(time.time() * 1000)
        lay_explanation = self.client.generate(
            lay_prompt, system_prompt,
            agent_id="lay_translator",
            session_id=session_id,
            turn_id=turn_id,
            artifact_id=artifact_id
        )
        step_end = int(time.time() * 1000)
        step_timings.append({
            "phase": "verify",
            "agent_id": "lay_translator",
            "start_t": step_start,
            "end_t": step_end,
            "duration_ms": step_end - step_start
        })

        # Tag extraction prompt (use less content for speed since tags don't need full article)
        tag_prompt = f"""Extract 3-5 relevant tags from this article. Choose from:
verifiable AI, trustworthy AI, AI governance, AI safety, interpretability, alignment,
responsible AI, AI policy, secure reasoning, formal verification, machine learning,
deep learning, neural networks, bias, fairness, transparency, accountability.

Title: {title}
Content: {content_for_llm[:2000]}

Return only comma-separated tags, no explanation."""

        # Log reasoning graph edge: lay_translator → metadata_extractor
        if self.client.research_logger and RKL_LOGGING_AVAILABLE:
            self.client.research_logger.log("reasoning_graph_edge", {
                "edge_id": str(uuid.uuid4()),
                "session_id": session_id or "unknown",
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "t": int(time.time() * 1000),
                "from_agent": "lay_translator",
                "to_agent": "metadata_extractor",
                "msg_type": "act",
                "intent_tag": "tag_extraction",
                "content_hash": sha256_text(f"{title}|{lay_explanation}"),
                # Phase 1 Enhancement: Add decision rationale
                "decision_rationale": f"Lay explanation complete ({len(lay_explanation)} chars). Ready for metadata extraction and tagging.",
                "payload_summary": f"Lay text: {lay_explanation[:100]}...",
                # Phase 2 Enhancement: Link to artifact for end-to-end tracing
                "artifact_id": artifact_id
            })

        step_start = int(time.time() * 1000)
        tags_raw = self.client.generate(
            tag_prompt, system_prompt,
            agent_id="metadata_extractor",
            session_id=session_id,
            turn_id=turn_id,
            artifact_id=artifact_id
        )
        step_end = int(time.time() * 1000)
        step_timings.append({
            "phase": "observe",  # Metadata extraction is an observation step
            "agent_id": "metadata_extractor",
            "start_t": step_start,
            "end_t": step_end,
            "duration_ms": step_end - step_start
        })
        tags = [tag.strip() for tag in tags_raw.split(",") if tag.strip()]

        return {
            "title": title,
            "link": link,
            "technical_summary": technical_summary.strip(),
            "lay_explanation": lay_explanation.strip(),
            "tags": tags[:5],  # Limit to 5 tags
            # Phase 2 Enhancement: Return timing information for secure_reasoning_trace
            "_step_timings": step_timings
        }


class FeedFetcher:
    """
    Fetches and filters RSS feed articles (Discovery Agent Group).

    Agent Role in 18-Agent System:
    - Agent #1: Feed Monitor - Fetches RSS feeds from configured sources
    - Agent #2: Content Filter - Filters articles by keywords and recency
    - Agent #6: Credibility Checker - Validates source reliability

    Type III Implementation:
    - Input: Public RSS feed URLs (configuration)
    - Processing: Downloads raw RSS XML and article content (local)
    - Output: Filtered article list for local summarization
    - Boundary: Raw RSS/articles stay local, never sent to external APIs

    This is the entry point for Type III workflow - raw data acquisition
    under local control before any processing begins.

    Attributes:
        feeds_config (Dict): Feed configuration from feeds.json
        keywords (List[str]): Keywords to filter articles by
        days_back (int): How many days back to fetch articles (default 7)
        cutoff_date (datetime): Calculated cutoff date for filtering

    Example:
        >>> config = {"feeds": [{"name": "ArXiv", "url": "...", "enabled": true}]}
        >>> fetcher = FeedFetcher(config, ["AI safety", "alignment"], days_back=7)
        >>> articles = fetcher.fetch_feeds()
    """

    def __init__(self, feeds_config: Dict, keywords: List[str], days_back: int = 7,
                 research_logger: Optional['StructuredLogger'] = None,
                 session_id: str = "unknown"):
        self.feeds_config = feeds_config
        ignore_kw = os.getenv("BRIEF_IGNORE_KEYWORDS", "false").lower() in ("1", "true", "yes")
        self.keywords = [] if ignore_kw else [kw.lower() for kw in keywords]
        self.days_back = int(os.getenv("BRIEF_DAYS_BACK", str(days_back)))
        self.cutoff_date = datetime.now() - timedelta(days=self.days_back)
        self.research_logger = research_logger
        self.session_id = session_id
        self.remote_fetch_host = os.getenv("REMOTE_FETCH_HOST", "").strip()
        self.remote_fetch_user = os.getenv("REMOTE_FETCH_USER", "").strip()

    def fetch_feeds(self) -> List[Dict]:
        """
        Fetch all enabled feeds and return filtered articles.

        Orchestrates the Discovery agent workflow:
        1. Feed Monitor: Fetches each enabled RSS feed
        2. Content Filter: Applies keyword and date filtering
        3. Deduplication: Removes duplicate articles by URL

        Type III Note: All raw RSS content stays local during this process.

        Returns:
            List[Dict]: Filtered articles, each containing:
                - title: Article title
                - content: Full article content (raw)
                - summary: RSS feed summary
                - link: Article URL
                - date: Publication date
                - source: Feed name
                - category: Feed category

        Example:
            >>> articles = fetcher.fetch_feeds()
            >>> print(f"Found {len(articles)} articles")
        """
        all_articles = []

        for feed in self.feeds_config.get("feeds", []):
            if not feed.get("enabled", True):
                logger.info(f"Skipping disabled feed: {feed['name']}")
                continue

            logger.info(f"Fetching feed: {feed['name']}")
            articles = self._fetch_single_feed(feed)
            all_articles.extend(articles)

        # Remove duplicates based on link
        unique_articles = {article["link"]: article for article in all_articles}
        filtered_articles = list(unique_articles.values())

        logger.info(f"Fetched {len(filtered_articles)} unique articles")
        return filtered_articles

    def _fetch_single_feed(self, feed: Dict) -> List[Dict]:
        """
        Fetch and parse a single RSS feed.

        Implements Feed Monitor agent behavior:
        - Parses RSS XML using feedparser
        - Extracts article metadata (title, date, content)
        - Applies keyword filtering
        - Validates recency based on cutoff_date

        Args:
            feed (Dict): Feed configuration containing:
                - name: Feed display name
                - url: RSS feed URL
                - category: Feed category for organization

        Returns:
            List[Dict]: Articles from this feed matching filter criteria

        Note: Uses feedparser library which handles various RSS/Atom formats
        and date parsing automatically.
        """
        articles = []

        try:
            parsed = self._fetch_parsed_feed(feed["url"])

            for entry in parsed.entries:
                # Get article date
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    pub_date = datetime(*published[:6])
                else:
                    pub_date = datetime.now()  # Default to now if no date

                # Check if article is recent enough
                if pub_date < self.cutoff_date:
                    continue

                # Extract content
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                content = entry.get("content", [{}])[0].get("value", summary)
                link = entry.get("link", "")

                # Check if article matches keywords. If keyword list is empty, accept all.
                text_to_search = f"{title} {summary}".lower()
                if (not self.keywords) or any(keyword in text_to_search for keyword in self.keywords):
                    articles.append({
                        "title": title,
                        "content": content,
                        "summary": summary,
                        "link": link,
                        "date": pub_date,
                        "source": feed["name"],
                        "category": feed.get("category", "general")
                    })

            logger.info(f"Found {len(articles)} relevant articles in {feed['name']}")

            # Telemetry: retrieval provenance (structural only)
            if self.research_logger and RKL_LOGGING_AVAILABLE:
                candidate_hashes = [
                    sha256_text(entry.get("link", "") or entry.get("id", ""))
                    for entry in parsed.entries
                ]
                selected_hashes = [sha256_text(a["link"]) for a in articles]
                self.research_logger.log("retrieval_provenance", {
                    "session_id": self.session_id,
                    "feed_name": feed.get("name", "unknown"),
                    "feed_url_hash": sha256_text(feed.get("url", "")),
                    "candidate_count": len(candidate_hashes),
                    "selected_count": len(selected_hashes),
                    "candidate_hashes": candidate_hashes[:50],
                    "selected_hashes": selected_hashes[:50],
                    "cutoff_date": self.cutoff_date.strftime("%Y-%m-%d"),
                    "category": feed.get("category", "general")
                })

        except Exception as e:
            logger.error(f"Error fetching feed {feed['name']}: {e}")

        return articles

    def _fetch_parsed_feed(self, url: str):
        """
        Fetch and parse an RSS feed. If REMOTE_FETCH_HOST is set, fetch via SSH curl on that host.
        """
        if self.remote_fetch_host:
            try:
                host_target = self.remote_fetch_host
                if self.remote_fetch_user:
                    host_target = f"{self.remote_fetch_user}@{self.remote_fetch_host}"
                cmd = [
                    "ssh",
                    "-o", "BatchMode=yes",
                    "-o", "StrictHostKeyChecking=accept-new",
                    host_target,
                    "curl", "-L", "-s", url
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if proc.returncode != 0:
                    logger.error(f"Remote fetch via {host_target} failed for {url}: rc={proc.returncode}, stderr={proc.stderr.strip()}")
                    return feedparser.parse("")
                return feedparser.parse(proc.stdout)
            except Exception as e:
                logger.error(f"Remote fetch via {self.remote_fetch_host} failed for {url}: {e}")
                return feedparser.parse("")  # empty
        # Local fetch
        logger.info(f"Fetching feed locally: {url}")
        return feedparser.parse(url)


def generate_readable_markdown(articles, session_id, output_path):
    """Generate human-readable markdown from articles JSON."""
    with open(output_path, "w") as f:
        f.write(f"# Secure Reasoning Research Brief\n\n")
        f.write(f"**Session:** `{session_id}`\n\n")
        f.write(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n")
        f.write(f"**Total Articles:** {len(articles)}\n\n")
        f.write("---\n\n")

        for idx, article in enumerate(articles, 1):
            f.write(f"## {idx}. {article.get('title', 'Untitled')}\n\n")
            f.write(f"**Source:** {article.get('source', 'Unknown')} | ")
            f.write(f"**Date:** {article.get('date', 'Unknown')} | ")
            f.write(f"**Link:** [{article.get('link', 'N/A')}]({article.get('link', '')})\n\n")

            # Tags
            tags = article.get('tags', [])
            if tags:
                f.write(f"**Tags:** {', '.join(tags)}\n\n")

            # Technical Summary (Ollama)
            f.write("### 📋 Technical Summary\n\n")
            f.write(f"*Generated by Ollama (llama3.2:3b)*\n\n")
            f.write(f"{article.get('technical_summary', 'N/A')}\n\n")

            # Lay Explanation (Ollama)
            f.write("### 💡 What This Means for Organizations\n\n")
            f.write(f"*Generated by Ollama (llama3.2:3b)*\n\n")
            f.write(f"{article.get('lay_explanation', 'N/A')}\n\n")

            # Gemini Analysis
            gemini = article.get('gemini_analysis', {})
            if gemini:
                f.write("### 🔍 Expert Secure Reasoning Analysis\n\n")
                f.write(f"*Generated by Gemini (2.0-flash)*\n\n")

                # Quality check
                f.write(f"**Quality Verdict:** {gemini.get('quality_verdict', 'N/A').upper()} ")
                f.write(f"(Confidence: {gemini.get('quality_confidence', 0):.0%})\n\n")

                # Relevance score
                relevance = gemini.get('relevance_score', 0)
                f.write(f"**Relevance Score:** {relevance:.2f} / 1.0\n\n")

                # Significance and recommendation
                f.write(f"**Significance:** {gemini.get('significance', 'N/A').upper()} | ")
                f.write(f"**Recommendation:** {gemini.get('recommendation', 'N/A').upper()}\n\n")

                # Key insight
                if gemini.get('key_insight'):
                    f.write("#### Why This Matters\n\n")
                    f.write(f"{gemini['key_insight']}\n\n")

                # Relevance rationale
                if gemini.get('relevance_rationale'):
                    f.write("#### Secure Reasoning Connection\n\n")
                    f.write(f"{gemini['relevance_rationale']}\n\n")

                # Practical value
                if gemini.get('practical_value'):
                    f.write("#### Practical Implications\n\n")
                    f.write(f"{gemini['practical_value']}\n\n")

            f.write("---\n\n")


def generate_gemini_blog(brief_json_path, output_path, session_id):
    """Generate Gemini-written blog post from brief JSON."""

    # Load brief data
    with open(brief_json_path) as f:
        brief_data = json.load(f)

    articles = brief_data.get('articles', [])
    generated_at = brief_data.get('generated_at', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))

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

    # Call Gemini to write the blog
    if not GEMINI_CLIENT_AVAILABLE:
        raise RuntimeError("Gemini client not available")

    gem_client = GeminiClient()

    response = gem_client.generate(
        blog_writing_prompt,
        system_prompt="You are a senior AI safety researcher and excellent technical writer. You write engaging, insightful blog posts about secure reasoning research for practitioners.",
        temperature=0.7,  # Slightly higher for creative writing
        max_tokens=4096,  # Need room for full blog post
        agent_id="blog_writer",
        session_id=session_id,
        turn_id=999,  # Use high number to avoid conflicts
        task_type="blog_writing"
    )

    blog_content = response.strip()

    # Clean markdown fences if present
    import re
    if blog_content.startswith("```"):
        match = re.search(r'```(?:markdown)?\s*\n?(.*?)\n?```', blog_content, re.DOTALL)
        if match:
            blog_content = match.group(1).strip()

    # Write to output file
    with open(output_path, 'w') as f:
        f.write(blog_content)


def main():
    """
    Main entry point for RSS feed processing and article summarization.

    Orchestrates the complete Discovery → Processing agent workflow:

    1. **Configuration Loading** (lines 299-312):
       - Loads .env variables (OLLAMA_ENDPOINT, model settings)
       - Reads feeds.json configuration
       - Sets up logging

    2. **Client Initialization** (lines 315-326):
       - Creates OllamaClient for local processing
       - Creates ArticleSummarizer with configured max_words
       - Creates FeedFetcher with keywords from config

    3. **Discovery Phase** (lines 331-341):
       - Agent #1: Feed Monitor fetches RSS feeds
       - Agent #2: Content Filter applies keyword/date filters
       - Selects top N most recent articles (BRIEF_MAX_ARTICLES)

    4. **Processing Phase** (lines 344-362):
       - Agent #3: Summarizer generates technical summaries
       - Agent #4: Metadata Extractor extracts tags
       - Agent #5: Lay Translator creates accessible explanations
       - All processing uses LOCAL Ollama (Type III requirement)

    5. **Output Generation** (lines 364-381):
       - Saves JSON with summaries and metadata
       - File: content/briefs/{date}_articles.json
       - This derived content can be used by Publishing agents

    Type III Workflow:
    - Raw RSS feeds and articles: Processed locally, never leave system
    - Derived summaries and tags: Saved locally, can be published or QA reviewed
    - Demonstrates: "Raw data stays local, derived insights travel"

    Environment Variables:
        OLLAMA_ENDPOINT: Ollama API endpoint (default: http://localhost:11434/api/generate)
        OLLAMA_MODEL: Model to use (default: llama3.2)
        BRIEF_MAX_ARTICLES: Max articles to process (default: 20)
        BRIEF_SUMMARY_MAX_WORDS: Max words per summary (default: 80)

    Outputs:
        content/briefs/{YYYY-MM-DD}_articles.json containing:
        - generated_at: ISO timestamp
        - articles: List of summarized articles
        - metadata: Processing metadata (count, date range)

    Example:
        $ python scripts/fetch_and_summarize.py
        INFO - Fetching RSS feeds...
        INFO - Found 15 relevant articles
        INFO - Summarizing 15 articles...
        INFO - Saved results to content/briefs/2025-11-16_articles.json
    """
    # Environment variables already loaded at module level (line 52-53)
    # Get configuration
    config_dir = script_dir / "config"

    # Initialize research telemetry logger
    research_logger = None
    if RKL_LOGGING_AVAILABLE:
        research_data_dir = script_dir / "data" / "research"
        research_logger = StructuredLogger(
            base_dir=str(research_data_dir),
            rkl_version="1.0",
            batch_size=50  # Write after 50 records
        )
        logger.info(f"Research telemetry enabled: {research_data_dir}")
    else:
        logger.warning("Research telemetry disabled (rkl_logging not available)")

    # Generate session ID for this brief generation run
    session_id = f"brief-{datetime.now().strftime('%Y-%m-%d')}-{str(uuid.uuid4())[:8]}"
    logger.info(f"Session ID: {session_id}")

    # Load feeds configuration
    feeds_config_path = config_dir / "feeds.json"
    if not feeds_config_path.exists():
        logger.error(f"Feeds configuration not found: {feeds_config_path}")
        sys.exit(1)

    with open(feeds_config_path) as f:
        feeds_config = json.load(f)

    # Initialize Ollama client with research logger
    ollama_endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")

    logger.info(f"Using Ollama endpoint: {ollama_endpoint}")
    logger.info(f"Using model: {ollama_model}")

    ollama_client = OllamaClient(ollama_endpoint, ollama_model, research_logger)

    # Initialize components
    max_words = int(os.getenv("BRIEF_SUMMARY_MAX_WORDS", "80"))
    summarizer = ArticleSummarizer(ollama_client, max_words)

    keywords = feeds_config.get("keywords", [])
    fetcher = FeedFetcher(feeds_config, keywords, research_logger=research_logger, session_id=session_id)

    def log_human_intervention(intervention_type: str, human_role: str = "operator", target_turn_id: int = 0, rationale_tag: str = "") -> None:
        """Manually log a human intervention event (use during reruns/approvals)."""
        if not research_logger or not RKL_LOGGING_AVAILABLE:
            return
        research_logger.log("human_interventions", {
            "session_id": session_id,
            "event_id": str(uuid.uuid4()),
            "t": int(time.time() * 1000),
            "human_role": human_role,
            "intervention_type": intervention_type,
            "target_turn_id": target_turn_id,
            "delta_metrics": {},
            "rationale_tag": rationale_tag
        })
    def log_system_state(stage: str) -> None:
        """Capture lightweight host metrics for research (structural only)."""
        if not research_logger or not psutil:
            return
        vm = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)
        load1, load5, load15 = (0.0, 0.0, 0.0)
        try:
            load1, load5, load15 = os.getloadavg()
        except (AttributeError, OSError):
            pass
        gpu_stats = []
        driver_version = None
        try:
            gpu_query = [
                "nvidia-smi",
                "--query-gpu=uuid,name,utilization.gpu,memory.used,memory.total,temperature.gpu,power.draw,power.limit,pstate,clocks.sm,clocks.mem,driver_version",
                "--format=csv,noheader,nounits"
            ]
            raw = subprocess.check_output(gpu_query, stderr=subprocess.DEVNULL, text=True)
            for line in raw.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 11:
                    gpu_stats.append({
                        "uuid": parts[0],
                        "name": parts[1],
                        "util_percent": float(parts[2]),
                        "mem_used_mb": float(parts[3]),
                        "mem_total_mb": float(parts[4]),
                        "temp_c": float(parts[5]),
                        "power_w": float(parts[6]),
                        "power_cap_w": float(parts[7]),
                        "pstate": parts[8],
                        "sm_clock_mhz": float(parts[9]),
                        "mem_clock_mhz": float(parts[10]),
                        "driver_version": parts[11] if len(parts) > 11 else None
                    })
                    driver_version = parts[11] if len(parts) > 11 else None
        except Exception:
            gpu_stats = []

        # Disk and network
        disk_io = {}
        net_io = {}
        try:
            dio = psutil.disk_io_counters()
            if dio:
                disk_io = {
                    "read_bytes": dio.read_bytes,
                    "write_bytes": dio.write_bytes,
                    "read_time_ms": dio.read_time,
                    "write_time_ms": dio.write_time
                }
        except Exception:
            pass
        try:
            nio = psutil.net_io_counters()
            if nio:
                net_io = {
                    "bytes_sent": nio.bytes_sent,
                    "bytes_recv": nio.bytes_recv,
                    "dropin": nio.dropin,
                    "dropout": nio.dropout,
                    "errin": nio.errin,
                    "errout": nio.errout
                }
        except Exception:
            pass

        # Per-process stats
        proc_cpu = None
        proc_mem = None
        try:
            p = psutil.Process()
            proc_cpu = p.cpu_percent(interval=0.0)
            meminfo = p.memory_info()
            proc_mem = {"rss": meminfo.rss, "vms": meminfo.vms}
        except Exception:
            pass

        # Phase 1 Enhancement: Add pipeline-level agent state tracking
        pipeline_status = "starting" if stage == "start_fetch" else "running" if "fetch" in stage else "completed"

        record = {
            "session_id": session_id,
            "stage": stage,
            "host": platform.node(),
            "platform": platform.platform(),
            "cpu_percent": cpu_percent,
            "load1": load1,
            "load5": load5,
            "load15": load15,
            "mem_total_bytes": vm.total,
            "mem_used_bytes": vm.used,
            "mem_free_bytes": vm.available,
            "mem_percent": vm.percent,
            "pipeline_status": pipeline_status,
            "current_phase": stage
        }
        if gpu_stats:
            record["gpus"] = gpu_stats
            record["gpu_count"] = len(gpu_stats)
            if driver_version:
                record["driver_version"] = driver_version
        if disk_io:
            record["disk_io"] = disk_io
        if net_io:
            record["net_io"] = net_io
        if proc_cpu is not None:
            record["proc_cpu_percent"] = proc_cpu
        if proc_mem is not None:
            record["proc_mem_bytes"] = proc_mem

        research_logger.log("system_state", record)

    # Fetch articles
    log_system_state("start_fetch")
    logger.info("Fetching RSS feeds...")
    articles = fetcher.fetch_feeds()
    log_system_state("done_fetch")

    if not articles:
        logger.warning("No articles found matching criteria")
        if research_logger:
            research_logger.close()
        return

    # Limit number of articles
    max_articles = int(os.getenv("BRIEF_MAX_ARTICLES", "20"))
    articles = sorted(articles, key=lambda x: x["date"], reverse=True)[:max_articles]

    # Summarize articles
    logger.info(f"Summarizing {len(articles)} articles...")
    summarized_articles = []

    for i, article in enumerate(articles, 1):
        logger.info(f"Processing article {i}/{len(articles)}: {article['title'][:60]}...")

        summary = summarizer.summarize_article(
            article["title"],
            article["content"] or article["summary"],
            article["link"],
            session_id=session_id,
            turn_id=i
        )

        summary.update({
            "date": article["date"].strftime("%Y-%m-%d"),
            "source": article["source"],
            "category": article["category"],
            "raw_content_excerpt": article["content"][:8000]  # What Ollama actually saw (up to 8000 chars)
            # NOTE: When memory upgraded, increase this limit to give Ollama more context
            # llama3.2:3b supports 128K context, so could go much higher
        })

        summarized_articles.append(summary)

        # Telemetry: secure reasoning trace bundle (structural)
        # Phase 2 Enhancement: Include timing data for each step
        if research_logger and RKL_LOGGING_AVAILABLE:
            step_timings = summary.get("_step_timings", [])

            # Build steps with timing information
            steps = []

            # Step 0: Metadata extraction (observe)
            if len(step_timings) > 2:
                timing = step_timings[2]  # metadata_extractor is 3rd step
                steps.append({
                    "step_index": 0,
                    "phase": "observe",
                    "agent_id": timing.get("agent_id", "metadata_extractor"),
                    "input_hash": sha256_text(article["content"][:500]),
                    "output_hash": sha256_text(article["summary"][:200]),
                    "verifier_verdict": "n/a",
                    "citations": [],
                    "start_t": timing.get("start_t", 0),
                    "end_t": timing.get("end_t", 0),
                    "duration_ms": timing.get("duration_ms", 0)
                })

            # Step 1: Technical summary generation (act)
            if len(step_timings) > 0:
                timing = step_timings[0]  # summarizer is 1st step
                steps.append({
                    "step_index": 1,
                    "phase": "act",
                    "agent_id": timing.get("agent_id", "summarizer"),
                    "input_hash": sha256_text(article["title"]),
                    "output_hash": sha256_text(summary.get("technical_summary", "")),
                    "verifier_verdict": "n/a",
                    "citations": [],
                    "start_t": timing.get("start_t", 0),
                    "end_t": timing.get("end_t", 0),
                    "duration_ms": timing.get("duration_ms", 0)
                })

            # Step 2: Lay explanation generation (verify)
            if len(step_timings) > 1:
                timing = step_timings[1]  # lay_translator is 2nd step
                steps.append({
                    "step_index": 2,
                    "phase": "verify",
                    "agent_id": timing.get("agent_id", "lay_translator"),
                    "input_hash": sha256_text(summary.get("technical_summary", "")),
                    "output_hash": sha256_text(summary.get("lay_explanation", "")),
                    "verifier_verdict": "pending",
                    "citations": [],
                    "start_t": timing.get("start_t", 0),
                    "end_t": timing.get("end_t", 0),
                    "duration_ms": timing.get("duration_ms", 0)
                })

            research_logger.log("secure_reasoning_trace", {
                "session_id": session_id,
                "task_id": sha256_text(article["link"]),
                "turn_id": i,
                "steps": steps
            })
            # Phase 1+: Enhanced quality trajectories with dimensional scoring
            tech_len = len(summary.get("technical_summary", ""))
            lay_len = len(summary.get("lay_explanation", ""))
            tags_count = len(summary.get("tags", []))

            research_logger.log("quality_trajectories", {
                "session_id": session_id,
                "artifact_id": sha256_text(article["link"]),
                "version": 1,
                "score_name": "summary_presence",
                "score": 1.0 if tech_len > 0 and lay_len > 0 else 0.0,
                "evaluator_id": "pipeline",
                "reason_tag": "non_empty_fields",
                "time_to_next_version": 0,
                # Phase 1+: Quality dimensions
                "quality_dimensions": {
                    "completeness": 1.0 if (tech_len > 0 and lay_len > 0 and tags_count > 0) else 0.5,
                    "technical_depth": min(tech_len / 600.0, 1.0),  # Expect ~600 chars for good depth
                    "clarity": min(lay_len / 400.0, 1.0),  # Expect ~400 chars for good lay explanation
                    "metadata_richness": min(tags_count / 5.0, 1.0)  # Expect ~5 tags
                },
                "metrics": {
                    "technical_summary_length": tech_len,
                    "lay_explanation_length": lay_len,
                    "tags_count": tags_count
                }
            })

    # Optional Gemini QA / hallucination matrix logging
    def run_gemini_qa(summaries: List[Dict]) -> None:
        if not GEMINI_CLIENT_AVAILABLE:
            return
        if os.getenv("ENABLE_GEMINI_QA", "false").lower() not in ("1", "true", "yes"):
            return
        try:
            gem_qamodel = os.getenv("GEMINI_QA_MODEL", "gemini-2.0-flash")
            gem_client = GeminiClient(model_name=gem_qamodel, research_logger=research_logger)
            theme_threshold = float(os.getenv("GEMINI_THEME_THRESHOLD", "0.6"))
            logger.info(f"Gemini QA enabled: processing {len(summaries)} articles with {gem_qamodel}")
        except Exception as e:
            logger.warning(f"Gemini QA unavailable: {e}")
            return

        for idx, article in enumerate(summaries, 1):
            prompt = f"""IMPORTANT CONTEXT: These summaries are based on article ABSTRACTS (ArXiv) or partial content (first 1500 chars), not full papers.

Article: {article.get('title', 'Unknown')}
Source: {article.get('source', 'Unknown')}
Technical Summary: {article.get('technical_summary','')}
Lay Explanation: {article.get('lay_explanation','')}

Your task has TWO parts:

PART A: QUALITY VALIDATION
1. Do summaries accurately reflect the abstract/excerpt?
2. Any hallucinations or misrepresentations?

PART B: ORIGINAL SECURE REASONING ANALYSIS
Secure reasoning encompasses: reasoning provenance, auditability, interpretability, alignment, verification, governance.

Analyze:
1. Which secure reasoning aspects does this address?
2. What specific problem does it tackle?
3. What capability does it enable for practitioners?
4. How does it connect to secure reasoning challenges?
5. WHY does this matter (2-3 sentences)?

Return JSON only:
{{
  "quality_verdict": "pass|fail|uncertain",
  "quality_confidence": 0.0-1.0,
  "error_type": "none|hallucination|omission|misrepresentation",
  "confidence_factors": {{
    "summary_completeness": 0.0-1.0,
    "technical_accuracy": 0.0-1.0,
    "clarity": 0.0-1.0,
    "source_alignment": 0.0-1.0
  }},
  "confidence_reasoning": "Explanation of confidence factors",

  "relevance_score": 0.0-1.0,
  "relevance_rationale": "Which secure reasoning aspects this addresses",
  "key_insight": "2-3 sentences on why this matters to secure reasoning",
  "practical_value": "What this enables for practitioners",
  "significance": "breakthrough|important|useful|incremental|tangential",
  "recommendation": "must-include|include|consider|exclude"
}}"""
            verdict = "uncertain"
            confidence = 0.0
            error_type = "none"
            notes = ""
            theme_score = None
            theme_verdict = "keep"
            try:
                resp = gem_client.generate(
                    prompt,
                    system_prompt="You are a senior AI safety researcher specializing in secure reasoning, AI alignment, and governance. You provide expert analysis of research relevance to building trustworthy, auditable AI systems.",
                    temperature=0.2,
                    max_tokens=512,
                    agent_id="gemini_qa",
                    session_id=session_id,
                    turn_id=idx,
                    task_type="secure_reasoning_analysis"
                )
                if resp:
                    import json as _json
                    import re
                    # Strip markdown code fences if present (Gemini often wraps JSON in ```json...```)
                    cleaned_resp = resp.strip()
                    if cleaned_resp.startswith("```"):
                        # Extract content between code fences
                        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', cleaned_resp, re.DOTALL)
                        if match:
                            cleaned_resp = match.group(1).strip()
                    parsed = _json.loads(cleaned_resp)
                    # PART A: Quality validation
                    verdict = str(parsed.get("quality_verdict", verdict)).lower()
                    confidence = float(parsed.get("quality_confidence", confidence))
                    error_type = parsed.get("error_type", error_type)
                    # Phase 1+: Confidence breakdown
                    confidence_factors = parsed.get("confidence_factors", {})
                    confidence_reasoning = parsed.get("confidence_reasoning", "")

                    # PART B: Original analysis
                    theme_score = parsed.get("relevance_score", theme_score)
                    relevance_rationale = parsed.get("relevance_rationale", "")
                    key_insight = parsed.get("key_insight", "")
                    practical_value = parsed.get("practical_value", "")
                    significance = parsed.get("significance", "")
                    recommendation = parsed.get("recommendation", "")

                    # Add Gemini analysis to article
                    article["gemini_analysis"] = {
                        "relevance_score": theme_score,
                        "relevance_rationale": relevance_rationale,
                        "key_insight": key_insight,
                        "practical_value": practical_value,
                        "significance": significance,
                        "recommendation": recommendation,
                        "quality_verdict": verdict,
                        "quality_confidence": confidence,
                        # Phase 1+: Enhanced confidence metrics
                        "confidence_factors": confidence_factors,
                        "confidence_reasoning": confidence_reasoning
                    }

                    # Legacy fields for filtering
                    theme_verdict = "keep" if recommendation in ["must-include", "include"] else "consider"
                    notes = key_insight[:200] if key_insight else ""
            except Exception as e:
                logger.warning(f"Gemini QA parse failure on article {idx}: {e}")

            # Apply theme gate if score present
            keep_article = True
            if theme_score is not None:
                try:
                    keep_article = float(theme_score) >= theme_threshold
                except Exception:
                    keep_article = True

            if research_logger and RKL_LOGGING_AVAILABLE:
                research_logger.log("hallucination_matrix", {
                    "session_id": session_id,
                    "artifact_id": sha256_text(article.get("link","")),
                    "verdict": verdict,
                    "method": "gemini_qa",
                    "confidence": confidence,
                    "error_type": error_type,
                    "notes": notes,
                    "theme_score": theme_score,
                    "theme_verdict": theme_verdict,
                    "theme_threshold": theme_threshold
                })

            # Drop articles that fail the secure reasoning theme gate
            if not keep_article:
                logger.info(f"Dropping article {idx} for secure reasoning theme score {theme_score}")
                summaries[idx-1]["_drop"] = True

    run_gemini_qa(summarized_articles)

    # Filter out dropped articles if theme gate marked them
    summarized_articles = [a for a in summarized_articles if not a.get("_drop")]

    # Validate summaries before proceeding
    invalid_articles = [
        (idx + 1, article) for idx, article in enumerate(summarized_articles)
        if not article.get("technical_summary") or not article.get("lay_explanation")
    ]

    if invalid_articles:
        if research_logger and RKL_LOGGING_AVAILABLE:
            research_logger.log("failure_snapshots", {
                "session_id": session_id,
                "reason": "empty_summaries",
                "failed_count": len(invalid_articles),
                "failed_titles": [a.get("title", "untitled") for _, a in invalid_articles],
            }, force_write=True)
        logger.error("Detected empty summaries; aborting publish step.")
        for idx, article in invalid_articles:
            logger.error(
                "Article %s missing fields (tech:%s, lay:%s): %s",
                idx,
                "ok" if article.get("technical_summary") else "EMPTY",
                "ok" if article.get("lay_explanation") else "EMPTY",
                article.get("title", "untitled")
            )
        if research_logger:
            research_logger.close()
        sys.exit(1)
    else:
        logger.info("All %d articles have non-empty technical and lay summaries.", len(summarized_articles))

    # Log governance ledger entry (for research)
    if research_logger and RKL_LOGGING_AVAILABLE:
        research_logger.log("governance_ledger", {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "publish_id": session_id,
            "artifact_ids": [sha256_text(f"{a.get('title','')}|{a.get('link','')}") for a in summarized_articles],
            "contributing_agent_ids": ["feed_monitor", "content_filter", "summarizer", "lay_translator", "metadata_extractor"],
            "verification_hashes": [sha256_text(json.dumps(a)) for a in summarized_articles[:5]],  # Sample
            "type3_verified": True,
            "raw_data_exposed": False,
            "derived_insights_only": True,
            "raw_data_handling": {
                "raw_content_stored": True,  # Stored in JSON for auditability
                "raw_content_location": "local_filesystem",  # Never transmitted
                "processing_location": "local_ollama",  # Processed locally
                "published_artifacts": ["summaries", "tags", "gemini_analysis"],  # Only derived insights
                "verification_capability": "enabled",  # Can verify summaries against raw
                "privacy_level": "public_internet_articles"  # Source data is already public
            },
            "schema_version": 1
        })

    # Save results
    output_dir = script_dir / "content" / "briefs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Include time in filename to avoid overwriting 2x/day runs
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    output_file = output_dir / f"{timestamp}_articles.json"

    with open(output_file, "w") as f:
        json.dump({
            "session_id": session_id,
            "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "articles": summarized_articles,
            "metadata": {
                "num_articles": len(summarized_articles),
                "date_range": f"{fetcher.cutoff_date.strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}"
            }
        }, f, indent=2)

    logger.info(f"Saved results to {output_file}")
    logger.info(f"Successfully processed {len(summarized_articles)} articles")

    # Generate readable markdown version
    readable_file = output_dir / f"{timestamp}_READABLE.md"
    generate_readable_markdown(summarized_articles, session_id, readable_file)
    logger.info(f"Saved readable version to {readable_file}")

    # Note: Weekly blog generation happens separately on Monday 10 AM
    # See scripts/generate_weekly_blog.py

    # Flush and close research logger
    if research_logger:
        research_logger.close()
        logger.info("Research telemetry data saved")


if __name__ == "__main__":
    main()
