# Sample Telemetry Data - November 21, 2025

**Complete Day:** 2 pipeline runs (morning + evening)
**Compressed Size:** 383 KB
**Uncompressed Size:** ~3.9 MB
**Total Files:** 256 parquet files

---

## What's Included

This archive contains **one complete day** of Phase-0 Research Telemetry from November 21, 2025, demonstrating the full operational system.

### Pipeline Runs Captured
- **Morning run (9:01 AM):** 19 papers collected and analyzed
- **Evening run (9:01 PM):** 20 papers collected and analyzed

### Artifact Types (9 types)

| Artifact Type | Files | Size | Description |
|--------------|-------|------|-------------|
| **execution_context** | 35 | 596 KB | Agent execution logs |
| **reasoning_graph_edge** | 40 | 480 KB | Agent interactions |
| **governance_ledger** | 25 | 312 KB | Type III compliance proofs |
| boundary_event | 35 | 420 KB | External API calls |
| system_state | 31 | 624 KB | System checkpoints |
| retrieval_provenance | 31 | 676 KB | Data source tracking |
| quality_trajectories | 25 | 304 KB | Quality metrics over time |
| secure_reasoning_trace | 25 | 376 KB | Secure reasoning verification |
| hallucination_matrix | 9 | 124 KB | Hallucination detection |
| **TOTAL** | **256** | **3.9 MB** | |

**Bold = Core Phase-0 artifact types**

---

## How to Extract and Explore

### Extract Archive
```bash
tar -xzf telemetry_2025-11-21_complete_day.tar.gz
```

This will create directory structure:
```
data/research/
├── boundary_event/2025/11/21/
├── execution_context/2025/11/21/
├── governance_ledger/2025/11/21/
├── hallucination_matrix/2025/11/21/
├── quality_trajectories/2025/11/21/
├── reasoning_graph_edge/2025/11/21/
├── retrieval_provenance/2025/11/21/
├── secure_reasoning_trace/2025/11/21/
└── system_state/2025/11/21/
```

### View Files (Python + pandas)
```python
import pandas as pd
import pyarrow.parquet as pq

# Example: Read a governance ledger file
df = pd.read_parquet('data/research/governance_ledger/2025/11/21/governance_ledger_090045.parquet')
print(df)

# Or with pyarrow directly
table = pq.read_table('data/research/governance_ledger/2025/11/21/governance_ledger_090045.parquet')
print(table.to_pandas())
```

### Verify Type III Compliance
```python
import pandas as pd
from pathlib import Path

# Load all governance ledger files
gov_dir = Path('data/research/governance_ledger/2025/11/21/')
for file in gov_dir.glob('*.parquet'):
    df = pd.read_parquet(file)
    # Check for Type III verification fields
    if 'type3_verified' in df.columns:
        print(f"{file.name}: type3_verified={df['type3_verified'].iloc[0]}")
```

---

## What This Data Proves

### 1. Complete System Operation
This single day captures:
- RSS feed monitoring (3 sources)
- Content filtering and deduplication
- Local Ollama processing (raw content)
- Cloud Gemini analysis (summaries only)
- Output generation (daily briefs)
- Continuous telemetry capture

### 2. Type III Compliance
**Governance ledger** files explicitly document:
- `type3_verified: true`
- `raw_data_exposed: false`
- `cloud_api_receives: summaries_only`
- `processing_location: local_ollama`

**Reasoning graph** shows:
- No direct edges from `raw_content` nodes to `gemini_*` nodes
- All cloud API calls receive preprocessed summaries

### 3. Multi-Agent Coordination
**Execution context** logs show:
- 18 agents executing across 2 pipeline runs
- Clear separation of local vs. cloud processing
- Successful coordination across collection → processing → analysis → output

### 4. Reproducibility
Complete telemetry enables:
- Exact reconstruction of system state at any point
- Verification of all agent decisions
- Debugging and optimization
- Meta-research on agent behavior

---

## Telemetry Statistics

### By Run
| Metric | Morning Run | Evening Run |
|--------|-------------|-------------|
| Papers collected | 19 | 20 |
| Agents executed | 18 | 18 |
| Telemetry files | ~128 | ~128 |
| API calls (Ollama) | 76 | 80 |
| API calls (Gemini) | 19 | 20 |
| Processing time | ~45 min | ~45 min |

### Data Quality
- **No missing artifacts:** All 9 types present in both runs
- **No failed runs:** All agents completed successfully
- **Type III violations:** 0 (verified in governance ledger)
- **Data consistency:** All timestamps align, no gaps

---

## Technical Details

### File Format
- **Format:** Apache Parquet (columnar)
- **Compression:** Snappy (default)
- **Schema:** Phase-0 Research Telemetry specification
- **Compatibility:** pandas, pyarrow, duckdb, spark

### Schema Examples

**execution_context:**
```python
{
  'agent_id': 'gemini_qa_agent',
  'timestamp': '2025-11-21T09:15:32Z',
  'action': 'analyze_paper',
  'input_tokens': 450,
  'output_tokens': 120,
  'model': 'gemini-2.0-flash',
  'duration_ms': 2340
}
```

**governance_ledger:**
```python
{
  'timestamp': '2025-11-21T09:15:45Z',
  'event_type': 'type3_verification',
  'type3_verified': True,
  'raw_data_exposed': False,
  'cloud_api_receives': 'summaries_only',
  'compliance_status': 'pass'
}
```

**reasoning_graph_edge:**
```python
{
  'source_agent': 'summarizer_agent',
  'target_agent': 'gemini_qa_agent',
  'edge_type': 'data_flow',
  'data_type': 'technical_summary',
  'timestamp': '2025-11-21T09:14:20Z'
}
```

---

## Why November 21?

This date was chosen for the sample because:
1. **Complete day:** Both morning and evening runs successful
2. **High volume:** 39 papers processed (good data density)
3. **All artifacts present:** Full 9 artifact types in both runs
4. **No anomalies:** Clean runs with no errors or missing data
5. **Representative:** Typical operational day

---

## Full System Telemetry

This sample represents **~68% of one week** of operation:
- **Sample:** 256 files (Nov 21)
- **Full week:** ~375 files (Nov 18-22)
- **Projection:** ~1,560 files per month

The complete telemetry archive (not included in submission due to size) demonstrates:
- 5+ days of continuous operation
- Multiple weeks of data collection possible
- Scalable to months/years with automated cleanup

---

## Verification Checklist

Use this data to verify competition criteria:

- [x] **Multi-agent system:** 18 agents logged in execution_context
- [x] **Phase-0 telemetry:** 9 artifact types present
- [x] **Type III compliance:** Verified in governance_ledger
- [x] **Real-world operation:** Complete day of production runs
- [x] **Reproducibility:** All agent decisions documented
- [x] **Data quality:** No missing artifacts, no errors

---

## Questions & Analysis

### Common Queries

**Q: How do I verify no raw content was sent to Gemini?**
A: Check governance_ledger files for `raw_data_exposed: false` and reasoning_graph_edge for absence of `raw_content → gemini_*` edges.

**Q: How many API calls were made?**
A: Count boundary_event files filtered by `api_provider: 'gemini'` vs `api_provider: 'ollama'`.

**Q: What was the longest-running agent?**
A: Query execution_context for max `duration_ms` by `agent_id`.

**Q: Were there any hallucinations detected?**
A: Check hallucination_matrix files for non-zero scores.

### Advanced Analysis

For deeper analysis, this telemetry supports:
- Agent performance profiling
- Data lineage tracking
- Compliance auditing
- System optimization
- Meta-research on AI agent behavior

---

## Contact & Documentation

**Full Documentation:** See `TELEMETRY_VERIFICATION.md` in repository root
**Architecture:** See `ARCHITECTURE_DIAGRAM.md` for visual system overview
**Competition Docs:** See `COMPETITION_SUBMISSION.md` for full submission

**Questions?** resonantknowledgelab.org

---

*Sample telemetry for Kaggle 5-Day AI Agents Intensive Capstone Competition*
*Generated from production system: November 21, 2025*
