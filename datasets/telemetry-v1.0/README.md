---
license: cc-by-4.0
task_categories:
- other
tags:
- multi-agent-systems
- ai-safety
- telemetry
- secure-reasoning
- agent-coordination
- llm-performance
- research-data
- kaggle-competition
size_categories:
- 1K<n<10K
---

# RKL Secure Reasoning Brief - Research Telemetry Dataset

> **⚠️ Development Transparency:** This project was developed with extensive AI coding assistance (Claude Code, ChatGPT) under tight time constraints for the Kaggle AI Agents Capstone. The developer designed the architecture, telemetry schema, and system integration decisions; AI tools scaffolded most of the implementation code. This is an honest exploratory prototype built to learn what telemetry is valuable to collect. Full disclosure in the "Development & AI Assistance" section below.

**Version:** 1.0
**Date Range:** November 17-26, 2025
**Generated:** 2025-11-24 19:46:15 UTC

---

## Overview

This dataset contains research-grade telemetry from the **Resonant Knowledge Lab (RKL) Secure Reasoning Brief** system - an 18-agent multi-agent system demonstrating **Type III Secure Reasoning** principles.

> **Note:** Type III Secure Reasoning is defined in the included white paper ([RKL-Secure-Reasoning-White-Paper-v1.0.pdf](RKL-Secure-Reasoning-White-Paper-v1.0.pdf)). It represents a framework where raw sensitive data is processed locally, while derived insights and structural telemetry are shareable for research purposes.

**Key Features:**
- ✅ **9 telemetry artifact types** tracking agent behavior, decisions, and quality
- ✅ **Phase 1+ enhancements**: Chain-of-thought prompts, decision rationale, 4D quality dimensions
- ✅ **Phase 2 enhancements**: Artifact ID linking, step-level timing (Unix ms precision)
- ✅ **~433 files, 6.9MB** of research data from Nov 17-26, 2025
- ✅ **Mixed format**: Parquet (baseline) + NDJSON (enhanced)

**Research Value:**
- Multi-agent coordination analysis
- LLM performance profiling
- Quality assessment studies
- Type III secure reasoning verification
- Agent decision transparency research

---

## Included Documentation

This dataset includes:

1. **Telemetry Data** (`telemetry_data/`) - 9 artifact types, 441 files, Nov 17-26, 2025
2. **White Paper** (`RKL-Secure-Reasoning-White-Paper-v1.0.pdf`) - Theoretical foundation for Type III Secure Reasoning
3. **Schema Documentation** (`TELEMETRY_SCHEMA_DOCUMENTATION.md`) - Complete field-by-field reference
4. **Implementation Reports**:
   - `PHASE1_IMPROVEMENTS_COMPLETE.md` - Chain-of-thought, decision rationale, quality dimensions
   - `PHASE2_IMPROVEMENTS_COMPLETE.md` - Artifact ID linking and step-level timing
   - `ENHANCED_TELEMETRY_LOCATIONS.md` - Code locations for all telemetry

**Recommended Reading Order:**
1. This README (overview)
2. White Paper (theoretical framework)
3. Schema Documentation (data reference)
4. Phase reports (implementation details)

---

## Dataset Structure

```
telemetry_data/
├── boundary_event/          # Type III compliance events
├── execution_context/       # LLM invocations (prompts, responses, timing)
├── governance_ledger/       # Governance decisions
├── hallucination_matrix/    # Gemini QA quality checks
├── quality_trajectories/    # Quality scoring with 4D dimensions
├── reasoning_graph_edge/    # Agent handoffs with decision rationale
├── retrieval_provenance/    # Source citations and retrieval metadata
├── secure_reasoning_trace/  # Step-by-step reasoning traces
├── system_state/            # Pipeline status and resource usage
└── manifests/               # Daily row count tracking
```

Each artifact type is organized by date:
```
{artifact_type}/YYYY/MM/DD/{artifact_type}_HHMMSS.{parquet|ndjson}
```

---

## Data Formats

### Baseline Period (Nov 17-22)
- **Format:** Apache Parquet
- **Features:** Basic telemetry without enhancements
- **Files:** `*_HHMMSS.parquet`

### Phase 1+ Period (Nov 23)
- **Format:** NDJSON
- **Features:** Chain-of-thought, decision rationale, quality dimensions
- **Files:** `*_HHMMSS.ndjson`

### Phase 2 Period (Nov 24+)
- **Format:** NDJSON
- **Features:** Phase 1+ PLUS artifact_id linking and step-level timing
- **Files:** `*_HHMMSS.ndjson`

---

## Getting Started

### Reading Parquet Files (Python)
```python
import pandas as pd

# Read a single file
df = pd.read_parquet('telemetry_data/execution_context/2025/11/21/execution_context_140036.parquet')
print(df.head())

# Read all files for a day
df = pd.read_parquet('telemetry_data/execution_context/2025/11/21/')
print(f"Total records: {len(df)}")
```

### Reading NDJSON Files (Python)
```python
import json
import pandas as pd

# Read line-by-line
with open('telemetry_data/execution_context/2025/11/24/execution_context_192841.ndjson') as f:
    for line in f:
        record = json.loads(line)
        print(record['agent_id'], record.get('artifact_id', 'N/A'))

# Read into DataFrame
df = pd.read_json('telemetry_data/execution_context/2025/11/24/execution_context_192841.ndjson',
                  lines=True)
print(df[['agent_id', 'model_id', 'tool_lat_ms', 'artifact_id']].head())
```

### Reading with DuckDB
```python
import duckdb

# Query Parquet files directly
con = duckdb.connect()
result = con.execute('''
    SELECT agent_id, model_id, AVG(tool_lat_ms) as avg_latency
    FROM 'telemetry_data/execution_context/**/*.parquet'
    GROUP BY agent_id, model_id
    ORDER BY avg_latency DESC
''').fetchdf()
print(result)
```

---

## Key Research Questions

### With artifact_id linking (Phase 2):
1. **End-to-End Tracing**: How long does it take to process an article from discovery to publication?
2. **Quality Attribution**: Which agents contribute most to high-quality outputs?
3. **Cross-Table Analysis**: Are prompt patterns correlated with quality dimensions?

### With step-level timing (Phase 2):
1. **Performance Profiling**: Which agent is the bottleneck?
2. **Optimization Targets**: What's the 95th percentile duration for each step?
3. **Agent Comparison**: How does llama3.2:3b compare to llama3.1:8b on speed?

### With decision rationale (Phase 1+):
1. **Multi-Agent Coordination**: What decision logic triggers agent handoffs?
2. **Reasoning Transparency**: Can we audit agent decision chains?
3. **Quality Predictors**: Do decision patterns predict output quality?

---

## Schema Documentation

See [`TELEMETRY_SCHEMA_DOCUMENTATION.md`](TELEMETRY_SCHEMA_DOCUMENTATION.md) for:
- Complete field-by-field documentation
- Data types and constraints
- Research value explanation
- Phase 1/1+/2 feature mapping

---

## Example Analyses

### 1. Agent Performance Comparison
```python
import pandas as pd

# Load execution context
df = pd.read_json('telemetry_data/execution_context/**/*.ndjson', lines=True)

# Compare agent latency
summary = df.groupby('agent_id')['tool_lat_ms'].describe()
print(summary)
```

### 2. End-to-End Article Tracing (Phase 2)
```python
# Pick an artifact_id
artifact_id = "e72f7710ae3a872980bd6bc04b7e76b0820f8afe32b074f9cc53531387d8..."

# Find all LLM invocations
exec_df = pd.read_json('telemetry_data/execution_context/**/*.ndjson', lines=True)
article_execs = exec_df[exec_df['artifact_id'] == artifact_id]

# Find all agent handoffs
edge_df = pd.read_json('telemetry_data/reasoning_graph_edge/**/*.ndjson', lines=True)
article_edges = edge_df[edge_df['artifact_id'] == artifact_id]

# Find quality score
quality_df = pd.read_json('telemetry_data/quality_trajectories/**/*.ndjson', lines=True)
article_quality = quality_df[quality_df['artifact_id'] == artifact_id]

print(f"LLM invocations: {len(article_execs)}")
print(f"Agent handoffs: {len(article_edges)}")
print(f"Quality dimensions: {article_quality['quality_dimensions'].iloc[0]}")
```

### 3. Step Timing Analysis (Phase 2)
```python
# Load secure_reasoning_trace
df = pd.read_json('telemetry_data/secure_reasoning_trace/**/*.ndjson', lines=True)

# Explode steps
steps_df = df.explode('steps').reset_index()
steps_df = pd.json_normalize(steps_df['steps'])

# Analyze duration by agent
print(steps_df.groupby('agent_id')['duration_ms'].describe())
```

---

## Data Governance

### Type III Secure Reasoning

> **See the included white paper** ([RKL-Secure-Reasoning-White-Paper-v1.0.pdf](RKL-Secure-Reasoning-White-Paper-v1.0.pdf)) for the complete definition and framework of Type III Secure Reasoning.

This dataset demonstrates **Type III Secure Reasoning** in practice:
- ✅ **Raw data processed locally** (Ollama llama3.2:3b on homelab)
- ✅ **Derived insights shareable** (summaries, quality scores)
- ✅ **Boundary events logged** (every local→external transition)
- ✅ **No raw article content** in public dataset (only excerpts/hashes)

### CARE Principles
All telemetry follows [CARE Principles for Indigenous Data Governance](https://www.gida-global.org/care):
- **Collective Benefit**: Research value for AI safety community
- **Authority to Control**: Local data sovereignty maintained
- **Responsibility**: Transparent decision logging
- **Ethics**: Privacy-preserving design (hashes, not raw text)

---

## Citation

If you use this dataset in your research, please cite:

```bibtex
@dataset{rkl_secure_reasoning_brief_2025,
  title={RKL Secure Reasoning Brief - Research Telemetry Dataset},
  author={Resonant Knowledge Lab},
  year={2025},
  month={November},
  version={1.0},
  publisher={Kaggle / HuggingFace},
  note={Nov 17-26, 2025. Phase 0 + Phase 1+ + Phase 2 enhancements.}
}
```

---

## Competition Context

This dataset was created for the **Kaggle AI Agents Capstone Competition** ("Agents for Good" track).

**Project:** Secure Reasoning Research Brief
**Track:** Agents for Good
**Submission Date:** November 30, 2025
**Team:** Resonant Knowledge Lab

---

## License

**Data License:** CC BY 4.0 (Attribution)
**Code License:** Apache 2.0

You are free to:
- ✅ Share and redistribute
- ✅ Adapt and build upon
- ✅ Use commercially

Under these terms:
- 📝 Provide attribution
- 📝 Indicate if changes were made
- 📝 Link to license

---

## Development & AI Assistance

**Transparency Statement**: This project was developed with extensive AI assistance (Claude Code, ChatGPT) under tight time constraints for the Kaggle AI Agents Capstone. The developer focused on:
- Architecture design and Type III boundary concepts
- Telemetry schema design and what data to capture
- System integration and pipeline orchestration
- Research question formulation

AI tools scaffolded much of the code and documentation. This is an honest, exploratory prototype built to learn which telemetry is valuable to collect. Deeper code understanding and comprehensive QA are ongoing work beyond the capstone deadline.

**What the Developer Can Explain**:
- High-level architecture and data flow
- Why each telemetry artifact exists
- Type III Secure Reasoning framework
- Integration decisions and tradeoffs

**What's Still Being Learned**:
- Detailed implementation of all helper functions
- Optimal schema refinements
- Advanced analysis techniques for the collected data

This transparency is intentional: the goal is learning through building, not presenting a production-ready system.

---

## Contact

**Maintainer:** Resonant Knowledge Lab (Michael B. Brady)
**Competition:** Kaggle AI Agents Capstone
**Issues:** [GitHub Issues](https://github.com/mbbrady/rkl-consolidated/issues)

---

## Changelog

### Version 1.0 (November 24, 2025)
- Initial release
- Data from Nov 17-26, 2025
- Baseline (Parquet) + Phase 1+ + Phase 2 (NDJSON)
- 9 telemetry artifact types
- Full schema documentation

---

*Generated: 2025-11-24 19:46:15 UTC*
*Dataset prepared by Claude Code for Kaggle AI Agents Competition*
