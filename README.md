# Secure Reasoning Brief: Phase‑0 Research Telemetry

This repository contains a **multi‑agent research brief system** and the **Phase‑0 telemetry dataset** used for my Kaggle AI Agents Capstone submission (Agents for Good track). It shows a Type III secure reasoning pattern: raw text is processed locally with Ollama, derived summaries are sent to Gemini, and every step emits structured telemetry.

> **Note on AI assistance:** I designed the Type III architecture and telemetry schema; Claude Code and ChatGPT helped scaffold and refactor the code. I review changes, run the pipeline on real AI safety feeds, and inspect the outputs.

---

## 📋 Quick Start for Judges

Start here if you’re reviewing the project:

1. **Project description (Kaggle)** – Main write‑up (<1500 words, on the competition page).
2. **Architecture:** [`ARCHITECTURE.md`](ARCHITECTURE.md) – System overview and phases.
3. **Telemetry dataset:** [`datasets/telemetry-v1.0/README.md`](datasets/telemetry-v1.0/README.md) – Full dataset documentation.
4. **Sample day:** [`competition_submission/sample_telemetry/README.md`](competition_submission/sample_telemetry/README.md) – One complete day (Nov 21, 2025).
5. **White paper:** [`rkl_white-paper.pdf`](rkl_white-paper.pdf) – Secure reasoning framework (Type I/II/III).
6. **Demo video:** YouTube link in the Kaggle submission; transcript in [`video/RECORDING_TRANSCRIPT_v2.txt`](video/RECORDING_TRANSCRIPT_v2.txt).

Key operational stats (Nov 17–22, 2025):
- **Pipeline runs:** 17 (6 days)
- **Papers processed:** ~200
- **Telemetry files:** 375 Parquet files
- **Daily cost:** ≈ **$0.08/day** (local‑first + Gemini QA)

---

## 🏗️ What’s in This Repo?

- `scripts/` – Production pipeline:
  - `fetch_and_summarize.py` – Main daily pipeline (RSS → Ollama → Gemini → briefs + telemetry).
  - `generate_weekly_blog.py` – Weekly synthesis using Gemini on summaries only.
  - `export_telemetry.py`, `prepare_dataset.py`, `upload_to_huggingface.py` – Dataset packaging helpers.
- `config/agents/` – Minimal agent configs (summarizer, QA reviewer, etc.).
- `rkl_logging/` – `StructuredLogger` used to write Phase‑0 artifacts (`execution_context`, `reasoning_graph_edge`, `boundary_event`, `governance_ledger`) to Parquet.
- `datasets/telemetry-v1.0/` – Telemetry dataset, schemas, and verification docs.
- `competition_submission/sample_telemetry/` – Compressed “single‑day” example + README.
- `data/sample_briefs/` – A few example daily briefs and readable outputs.
- `docs/` – Supporting docs, including [`docs/TELEMETRY_SUMMARY.md`](docs/TELEMETRY_SUMMARY.md) and [`docs/CITATION_SYSTEM.md`](docs/CITATION_SYSTEM.md).

This copy intentionally omits large raw logs and full historical data; it’s a lean, reproducible subset focused on the competition.

---

## 🚀 Running the Pipeline Locally

### Prerequisites

- Python 3.11
- [Ollama](https://ollama.com/) running with `llama3.2:3b` pulled
- Optional: Google Gemini API key (`GOOGLE_API_KEY`) for QA and weekly synthesis

### Setup

```bash
git clone https://github.com/mbbrady/secure-reasoning-brief-clean.git
cd secure-reasoning-brief-clean

python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment (create a .env file in repo root)
cat > .env << 'EOF'
OLLAMA_ENDPOINT=http://localhost:11434
GOOGLE_API_KEY=your-gemini-key           # optional if you want Gemini
ENABLE_GEMINI_QA=true                    # or false to run Ollama‑only
EOF
```

### Run a Single Daily Pipeline

```bash
python scripts/fetch_and_summarize.py
```

This will:
- Fetch recent AI safety papers from configured RSS feeds.
- Use Ollama to generate technical + lay summaries locally.
- Optionally call Gemini for QA and synthesis (summaries only).
- Write outputs under `content/briefs/` and telemetry under `data/research/` (when enabled).

### Run the Weekly Blog

```bash
python scripts/generate_weekly_blog.py
```

This reads the last 7 days of `*_articles.json` briefs from `content/briefs/`, calls Gemini on the stored summaries only, and writes a weekly blog file as `YYYY-MM-DD_WEEKLY_BLOG.md` into `content/briefs/`.

For automation, see `scripts/setup_cron.sh` as a reference for 2× daily runs and weekly synthesis on your own environment.

---

## 📊 Telemetry & Datasets

During each run, `StructuredLogger` records:
- `execution_context` – model config, tokens, latency per LLM call.
- `reasoning_graph_edge` – agent‑to‑agent handoffs.
- `boundary_event` – Type III boundary crossings (local → cloud).
- `governance_ledger` – audit trail for each published brief.

These artifacts are written as partitioned Parquet files with daily manifests under `datasets/telemetry-v1.0/telemetry_data/`. The dataset is mirrored to Hugging Face and Kaggle (see competition submission for links).

Public dataset links:
- **Hugging Face:** https://huggingface.co/datasets/rkl-org/rkl-secure-reasoning-brief-telemetry
- **Kaggle:** https://www.kaggle.com/datasets/bradyopenmaps/rkl-secure-reasoning-brief-telemetry

---

## 🤝 Development Transparency

This is an **honest exploratory prototype**, not a polished enterprise product. I designed the architecture, Type III boundary, and telemetry schema; AI coding tools helped implement and refactor the code. The repo is intended to be:
- Small enough to clone and run,
- Transparent enough to study,
- And useful as a starting point for further secure reasoning and telemetry research.***
