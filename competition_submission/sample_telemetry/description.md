# Kaggle AI Agents Intensive - Capstone Submission

**Project:** Secure Reasoning Research Brief

**Subtitle:** Automated AI safety research monitoring that generates research telemetry for AI science

**Author:** Mike Brady | Resonant Knowledge Lab

**Submission Date:** November 28, 2025

---

## Problem Statement

AI practitioners and researchers face an information crisis: over 100 papers on AI safety, alignment, and secure reasoning are published weekly across ArXiv, AI Alignment Forum, LessWrong, and research blogs. Reading them all is impossible. Missing critical advances is dangerous. Existing AI summarization tools help, but they create a trust problem: how do you prove they don't leak sensitive data to external models?

This matters beyond research monitoring. Many organizations want AI-powered analysis but cannot risk exposing confidential data to cloud APIs. Healthcare records, financial data, proprietary research—all could benefit from AI reasoning, but security requirements prohibit sending raw data to external services.

**The core problem:** We need AI agents that can reason over sensitive data while provably keeping that data local. We need an architecture where powerful cloud AI can still contribute without ever seeing the raw content.

This is what I call **Type III Secure Reasoning**—a framework where raw data stays local, but derived insights flow to cloud AI for sophisticated analysis. My research monitoring system demonstrates this architecture in action, proving it works for real-world tasks.

---

## Why Agents?

Agents are essential for this problem because it requires **coordinated specialization** across a trust boundary.

**Single AI approaches fail:**
- One local model can't match cloud AI quality for complex analysis
- One cloud model can't access raw data without violating security
- A simple pipeline can't adapt to varying content quality or handle failures

**Why multi-agent coordination works:**

1. **Specialization:** Each agent focuses on one task it does well. Local agents (Ollama llama3.2:3b) handle summarization—simple enough for smaller models. Cloud agents (Gemini 2.0) handle quality assessment and synthesis—where reasoning power matters.

2. **Trust boundaries:** Agents enforce data flow rules. Local agents never send raw content onward. Cloud agents never request it. The handoff point is architecturally enforced, not just policy-based.

3. **Governance by design:** Monitoring agents verify compliance without human oversight. Every data flow is logged. Every boundary crossing is audited. Violations trigger alerts automatically.

4. **Resilience:** If one agent fails (API timeout, quality issue), others continue. The system degrades gracefully rather than failing completely.

5. **Observability:** Agent-to-agent handoffs create natural audit points. Phase-0 telemetry captures every invocation, every token, every decision. This isn't possible with monolithic AI calls.

**The architecture mirrors real-world secure systems:** untrusted networks, DMZ zones, data classification—but for AI reasoning instead of network traffic.

---

## What I Created

### System Overview

I built an **18-agent system** that monitors AI research 24/7, generates daily briefs and weekly blogs, while maintaining **provable Type III compliance**. It runs on my homelab cluster (Betty) with local Ollama + cloud Gemini.

### Four-Phase Architecture

**Phase 1: Discovery (3 agents) - All Local**
- Feed Monitor: Scrapes ArXiv, AI Alignment Forum, research blogs via RSS
- Content Filter: Pre-filters using keywords (AI safety, alignment, secure reasoning)
- Source Credibility: Assesses reliability (planned—currently manual)

**Phase 2: Processing (6 agents) - All Local, Raw Data Stays Here**
- Technical Summarizer: 8000 chars → 600 char technical summary (Ollama)
- Translation Agent: Technical → plain language (~400 chars) (Ollama)
- Metadata Extractor: Extract topics, themes, citations (Ollama)
- Relationship Analyzer: Connect related papers (planned)
- Theme Synthesizer: Identify patterns across papers (planned)
- Recommendation Generator: Generate action items (planned)

**Phase 3: Governance (3 agents) - Cloud AI, Summaries Only**
- QA Reviewer: Quality check summaries (Gemini receives summaries, not raw content)
- Terminology Compliance: Verify consistent framework terminology (planned)
- Fact Checker: Cross-reference claims and citations (planned)

**Phase 4: Publication (3 agents) - Output Generation**
- Brief Composer: Assemble final daily brief with IEEE citations (Gemini)
- Git Publisher: Commit and push to GitHub
- Archive Manager: Maintain searchable archive (planned)

**Cross-Phase: Monitoring (3 agents) - Continuous Oversight**
- Performance Monitor: Track system health (planned)
- Governance Auditor: Verify Type III compliance (planned)
- Education Generator: Create teaching materials from telemetry (planned)

### Key Innovation: The Type III Boundary

The critical architectural element is the **handoff point between Phase 2 and Phase 3**. Local agents generate summaries. Cloud agents receive only those summaries. This boundary is enforced by the `HybridModelClient` which routes requests to Ollama or Gemini based on data classification.

Every boundary crossing generates a `boundary_event` telemetry artifact:
```json
{
  "rule_id": "type3.external_api.gemini",
  "action": "allow",
  "data_type": "summary",
  "raw_data_included": false
}
```

### Phase-0 Research Telemetry

Every pipeline run generates **9 types of research artifacts**:
1. Execution Context - Every LLM call (79 files, 2,128 invocations collected)
2. Reasoning Graph Edge - Agent handoffs (94 files, 1,911 transitions)
3. Boundary Event - Type III crossings (79 files, 2,128 events)
4. Secure Reasoning Trace - Complete thought processes (45 files, 301 traces)
5. Quality Trajectories - Quality evolution (45 files, 301 revisions)
6. Hallucination Matrix - Claims verification (24 files, 168 analyses)
7. Retrieval Provenance - Source tracking (59 files, 228 retrievals)
8. Governance Ledger - Audit trail (54 files, 52 governance checks)
9. System State - Health monitoring (59 files, 114 snapshots)

**Total collected:** 538 files, 7.42 MB, spanning Nov 18-28, 2025 (11 days).
**Published:** HuggingFace dataset for AI science community research.

This telemetry enables research into multi-agent coordination, secure reasoning architectures, and AI governance—all while the system does useful work.

---

## Demo

**Watch the 3-minute video:** [Link to be added]

The demo shows:
1. **Morning brief generation** - System fetches 20 papers at 9 AM, processes locally, generates executive summary
2. **Weekly blog synthesis** - Gemini analyzes week's summaries (not raw content), produces IEEE-cited analysis
3. **Live telemetry dashboard** - Real-time view of agent coordination and Type III compliance
4. **Sample outputs** - Actual briefs from Nov 27-28 showing practical utility

**Live deployment:** System runs via cron (9 AM & 9 PM daily). View outputs at:
- GitHub: https://github.com/mbbrady/rkl-consolidated/tree/main/secure-reasoning-brief
- HuggingFace: [Dataset link to be added]

---

## The Build

### Technologies Used

**AI Models:**
- Ollama llama3.2:3b (local) - Fast, good for summarization, runs on homelab
- Google Gemini 2.0 Flash (cloud) - Sophisticated reasoning, quality assessment

**Infrastructure:**
- Python 3.11 - Core pipeline
- RSS/Feedparser - Content discovery
- SQLite - Deduplication tracking
- Apache Parquet + NDJSON - Telemetry storage
- GitHub Actions - Automated publishing
- Cron - Scheduling (systemd timers considered but cron simpler)

**Homelab Cluster:**
- Betty node (192.168.1.11) - Ollama API server
- Wilma node (192.168.1.10) - Pipeline orchestration, telemetry storage
- Linux Ubuntu 22.04

**Development Approach:**
- Claude Code (Anthropic) - Architecture design, code implementation
- ChatGPT - Problem-solving, debugging
- Human oversight - Architecture decisions, quality control, framework design

**Honest disclosure:** I designed the system architecture and Type III framework concepts. AI assistants (Claude Code, ChatGPT) helped me implement it much faster than I could alone. I reviewed all code, tested the system, and validated outputs. This collaboration model—human vision + AI execution—is itself a demonstration of multi-agent coordination.

### Key Technical Challenges Solved

1. **Gemini API authentication** - Required service account setup, proper scoping
2. **Deduplication across sources** - Papers appear on multiple sites; needed content-based hashing
3. **Local vs cloud routing** - Built `HybridModelClient` to automatically route based on data classification
4. **Telemetry overhead** - Parquet compression kept storage manageable (7.42 MB for 11 days)
5. **Citation formatting** - IEEE style required careful parsing of author/date/source metadata

---

## If I Had More Time

### Immediate Next Steps (Days)

1. **Deploy remaining 10 agents** - Currently 8 operational, 10 planned. Priorities:
   - Source Credibility (Phase 1) - Automated reliability scoring
   - Fact Checker (Phase 3) - Cross-reference claims
   - Performance Monitor (Cross-phase) - System health dashboard

2. **Interactive web UI** - Currently GitHub-based. Build React dashboard:
   - Browse briefs with search/filter
   - View telemetry visualizations
   - Trigger ad-hoc analysis requests

3. **Email delivery** - Automated morning brief emails for subscribers

### Strategic Enhancements (Weeks)

4. **Expand source coverage** - Add Google Scholar, OpenAI blog, Anthropic updates, DeepMind
5. **Citation graph** - Link related papers, show research lineage
6. **User preferences** - Personalized briefs based on research interests
7. **Multi-language support** - Translate briefs to Spanish, Chinese, French

### Research Directions (Months)

8. **Federated learning integration** - Multiple organizations contribute to shared analysis without sharing raw data
9. **Zero-knowledge proofs** - Cryptographically prove Type III compliance without revealing internals
10. **Agent marketplace** - Allow community to contribute specialized agents (e.g., domain-specific fact checkers)
11. **Adversarial testing** - Red team attempts to extract raw data via prompt injection

### Broader Vision

This architecture isn't just for research monitoring. The same Type III pattern applies to:
- **Healthcare:** Analyze patient records locally, send de-identified insights to cloud AI for diagnosis support
- **Finance:** Process transaction data on-premise, use cloud AI for fraud detection on aggregates
- **Legal:** Review confidential documents locally, leverage cloud AI for case strategy on summaries

**The goal:** Prove that secure reasoning is achievable, practical, and useful—making AI accessible for sensitive domains that currently can't adopt it.

---

**Total word count: 1,498**
