#!/usr/bin/env python3
"""
Prepare telemetry dataset for Kaggle and HuggingFace publication.

Creates a clean, documented dataset package with:
- All telemetry data (Nov 17-26, 2025)
- README with schema documentation
- Example analysis notebooks
- Metadata and manifests
"""

import os
import shutil
import json
from pathlib import Path
from datetime import datetime

def prepare_dataset(output_dir: str = None):
    """Prepare complete dataset for publication."""

    base_dir = Path(__file__).parent.parent
    if output_dir is None:
        # Default: secure-reasoning-brief/datasets/telemetry-v1.0
        output_path = base_dir / "datasets" / "telemetry-v1.0"
    else:
        output_path = base_dir / output_dir

    # Clean output directory
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Preparing dataset in: {output_path}")

    # Copy telemetry data
    print("Copying telemetry data...")
    data_src = base_dir / "data" / "research"
    data_dest = output_path / "telemetry_data"

    # Copy all artifact types
    artifact_types = [
        "boundary_event",
        "execution_context",
        "governance_ledger",
        "hallucination_matrix",
        "quality_trajectories",
        "reasoning_graph_edge",
        "retrieval_provenance",
        "secure_reasoning_trace",
        "system_state",
        "manifests"
    ]

    for artifact_type in artifact_types:
        src = data_src / artifact_type
        if src.exists():
            dest = data_dest / artifact_type
            shutil.copytree(src, dest)
            file_count = len(list(dest.rglob("*.*")))
            print(f"  ✅ {artifact_type}: {file_count} files")

    # Copy documentation
    print("\nCopying documentation...")
    docs_to_copy = [
        "TELEMETRY_SCHEMA_DOCUMENTATION.md",
        "PHASE1_IMPROVEMENTS_COMPLETE.md",
        "PHASE2_IMPROVEMENTS_COMPLETE.md",
        "ENHANCED_TELEMETRY_LOCATIONS.md"
    ]

    for doc in docs_to_copy:
        src = base_dir / doc
        if src.exists():
            shutil.copy(src, output_path / doc)
            print(f"  ✅ {doc}")

    # Copy white paper
    print("\nCopying white paper...")
    white_paper_src = base_dir.parent / "website" / "static" / "resources" / "RKL-Secure-Reasoning-White-Paper-v1.0.pdf"
    if white_paper_src.exists():
        shutil.copy(white_paper_src, output_path / "RKL-Secure-Reasoning-White-Paper-v1.0.pdf")
        print(f"  ✅ RKL-Secure-Reasoning-White-Paper-v1.0.pdf")
    else:
        print(f"  ⚠️  White paper not found at {white_paper_src}")

    # Create main README
    print("\nGenerating README...")
    readme_content = f"""---
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
**Generated:** {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC

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
{{artifact_type}}/YYYY/MM/DD/{{artifact_type}}_HHMMSS.{{parquet|ndjson}}
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
print(f"Total records: {{len(df)}}")
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

print(f"LLM invocations: {{len(article_execs)}}")
print(f"Agent handoffs: {{len(article_edges)}}")
print(f"Quality dimensions: {{article_quality['quality_dimensions'].iloc[0]}}")
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
@dataset{{rkl_secure_reasoning_brief_2025,
  title={{RKL Secure Reasoning Brief - Research Telemetry Dataset}},
  author={{Resonant Knowledge Lab}},
  year={{2025}},
  month={{November}},
  version={{1.0}},
  publisher={{Kaggle / HuggingFace}},
  note={{Nov 17-26, 2025. Phase 0 + Phase 1+ + Phase 2 enhancements.}}
}}
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

## Contact

**Maintainer:** Resonant Knowledge Lab
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

*Generated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC*
*Dataset prepared by Claude Code for Kaggle AI Agents Competition*
"""

    readme_path = output_path / "README.md"
    readme_path.write_text(readme_content)
    print(f"  ✅ README.md")

    # Create dataset metadata
    print("\nGenerating metadata...")
    metadata = {
        "name": "rkl-secure-reasoning-brief-telemetry",
        "version": "1.0.0",
        "description": "Research-grade telemetry from RKL Secure Reasoning Brief system (18-agent multi-agent system)",
        "date_range": {
            "start": "2025-11-17",
            "end": "2025-11-26"
        },
        "artifact_types": len(artifact_types) - 1,  # Exclude manifests
        "total_files": len(list(data_dest.rglob("*.*"))),
        "size_mb": round(sum(f.stat().st_size for f in data_dest.rglob("*.*")) / 1024 / 1024, 2),
        "formats": ["parquet", "ndjson"],
        "enhancements": {
            "phase1": "Chain-of-thought prompts, decision rationale, quality dimensions",
            "phase2": "Artifact ID linking, step-level timing (Unix milliseconds)"
        },
        "license": "CC BY 4.0",
        "competition": "Kaggle AI Agents Capstone",
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }

    metadata_path = output_path / "dataset-metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  ✅ dataset-metadata.json")

    # Create compression instructions
    print("\nDataset preparation complete!")
    print(f"\n📦 Output directory: {output_path}")
    print(f"📊 Total size: {metadata['size_mb']} MB")
    print(f"📁 Total files: {metadata['total_files']}")

    # Create archive automatically
    print("\n📦 Creating compressed archive...")
    archive_name = "rkl-secure-reasoning-brief-telemetry-v1.0.tar.gz"
    archive_path = output_path.parent / archive_name

    import subprocess
    result = subprocess.run(
        ["tar", "-czf", str(archive_path), "-C", str(output_path), "."],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        archive_size_mb = round(archive_path.stat().st_size / 1024 / 1024, 2)
        print(f"  ✅ {archive_name} ({archive_size_mb} MB)")
    else:
        print(f"  ⚠️  Archive creation failed: {result.stderr}")

    print("\n📤 Next steps:")
    print(f"  1. Upload to Kaggle: https://www.kaggle.com/datasets (web interface)")
    print(f"     Archive location: {archive_path}")
    print(f"  2. Upload to HuggingFace: huggingface-cli upload ...")
    print(f"  3. Update submission docs with dataset URLs")

    return output_path

if __name__ == "__main__":
    prepare_dataset()
