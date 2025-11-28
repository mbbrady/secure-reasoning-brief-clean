# Enhanced Telemetry Data - File Locations

**Session:** brief-2025-11-22-33ee12cf
**Date:** November 22, 2025
**Test Run:** Single article (1 paper processed)

---

## Directory Structure

```
data/research/
├── execution_context/2025/11/22/
│   └── execution_context_220424.ndjson ✅ ENHANCED
├── reasoning_graph_edge/2025/11/22/
│   └── reasoning_graph_edge_220424.ndjson ✅ ENHANCED
├── system_state/2025/11/22/
│   └── system_state_220424.ndjson ✅ ENHANCED
├── quality_trajectories/2025/11/22/
│   └── quality_trajectories_220424.ndjson ✅ ENHANCED (next full run)
├── boundary_event/2025/11/22/
│   └── boundary_event_220424.ndjson
├── governance_ledger/2025/11/22/
│   └── governance_ledger_220424.ndjson
├── secure_reasoning_trace/2025/11/22/
│   └── secure_reasoning_trace_220424.ndjson
└── retrieval_provenance/2025/11/22/
    └── retrieval_provenance_220424.ndjson
```

---

## 1. Execution Context (Prompts & Responses)

**File:** `data/research/execution_context/2025/11/22/execution_context_220424.ndjson`

**New Fields:**
- `prompt_preview`: First 1000 characters of prompt
- `response_preview`: First 1000 characters of response

**Example Record:**
```json
{
  "agent_id": "summarizer",
  "model_id": "llama3.2:3b",
  "prompt_preview": "Analyze this AI research paper and create a technical summary.\n\nFirst, identify:\n1. Main contribution (1 sentence)\n2. Key methodology (1 sentence)\n3. Most important result (1 sentence)\n\nThen, combine these into a 80-word technical summary focusing on what practitioners need to know.\n\nTitle: Abstract advice to researchers tackling the difficult core problems...",
  "response_preview": "Here are the requested summaries:\n\n**Main Contribution**\nThe author provides advice to researchers tackling technical AGI alignment problems, focusing on overcoming deference and making progress despite numerous challenges.\n\n**Key Methodology**\nThe author recommends a process of \"graceful deference,\" where researchers start by deferring to others' assumptions..."
}
```

**Impact:** Researchers can now see exact prompts used and how models responded.

---

## 2. Reasoning Graph Edge (Decision Rationale)

**File:** `data/research/reasoning_graph_edge/2025/11/22/reasoning_graph_edge_220424.ndjson`

**New Fields:**
- `decision_rationale`: Explanation of why handoff occurred
- `payload_summary`: Description of data being passed

**Example Records:**

**Edge 1: feed_monitor → summarizer**
```json
{
  "from_agent": "feed_monitor",
  "to_agent": "summarizer",
  "intent_tag": "tech_summary",
  "decision_rationale": "Article from https://www.alignmentforum.org/posts/rZQjk7T6dNqD5... passed keyword/date filter. Sending to summarizer for technical analysis.",
  "payload_summary": "Title: Abstract advice to researchers tackling the difficult core problems of AGI align... (8000 chars content)"
}
```

**Edge 2: summarizer → lay_translator**
```json
{
  "from_agent": "summarizer",
  "to_agent": "lay_translator",
  "intent_tag": "lay_explanation",
  "decision_rationale": "Technical summary complete (1418 chars). Passing to lay translator for accessible explanation.",
  "payload_summary": "Summary: Here are the requested summaries:\n\n**Main Contribution**\nThe author provides advice to researchers t..."
}
```

**Edge 3: lay_translator → metadata_extractor**
```json
{
  "from_agent": "lay_translator",
  "to_agent": "metadata_extractor",
  "intent_tag": "tag_extraction",
  "decision_rationale": "Lay explanation complete (392 chars). Ready for metadata extraction and tagging.",
  "payload_summary": "Lay text: For organizations adopting AI systems, this means considering the potential high risks of sacrificin..."
}
```

**Impact:** Multi-agent coordination is now transparent - shows WHY handoffs happen.

---

## 3. System State (Pipeline Status)

**File:** `data/research/system_state/2025/11/22/system_state_220424.ndjson`

**New Fields:**
- `pipeline_status`: "starting", "running", or "completed"
- `current_phase`: Stage name

**Example Records:**

**Stage 1:**
```json
{
  "session_id": "brief-2025-11-22-33ee12cf",
  "stage": "start_fetch",
  "pipeline_status": "starting",
  "current_phase": "start_fetch",
  "cpu_percent": 1.9,
  "mem_percent": 13.9,
  "host": "homelab",
  "platform": "Linux-6.8.0-49-generic-x86_64-with-glibc2.39"
}
```

**Stage 2:**
```json
{
  "session_id": "brief-2025-11-22-33ee12cf",
  "stage": "done_fetch",
  "pipeline_status": "running",
  "current_phase": "done_fetch",
  "cpu_percent": 0.0,
  "mem_percent": 13.9
}
```

**Impact:** System-level operational monitoring and pipeline progress tracking.

---

## 4. Quality Trajectories (Dimensional Scoring)

**File:** `data/research/quality_trajectories/2025/11/22/quality_trajectories_220424.ndjson`

**New Fields (will appear in next full run):**
- `quality_dimensions`: 4D quality scoring
  - `completeness`: Overall completeness (0.0-1.0)
  - `technical_depth`: Technical detail level (0.0-1.0)
  - `clarity`: Readability and clarity (0.0-1.0)
  - `metadata_richness`: Tag/metadata quality (0.0-1.0)
- `metrics`: Raw measurements
  - `technical_summary_length`: Character count
  - `lay_explanation_length`: Character count
  - `tags_count`: Number of tags

**Expected Format (next run):**
```json
{
  "session_id": "brief-2025-11-22-...",
  "artifact_id": "...",
  "score": 1.0,
  "quality_dimensions": {
    "completeness": 1.0,
    "technical_depth": 0.95,
    "clarity": 0.88,
    "metadata_richness": 0.80
  },
  "metrics": {
    "technical_summary_length": 1418,
    "lay_explanation_length": 392,
    "tags_count": 3
  }
}
```

**Status:** Code is live, will generate with next full pipeline run.

---

## 5. Chain-of-Thought in Output

**File:** `content/briefs/2025-11-22_1704_READABLE.md`

**Enhancement:** Summaries now show explicit reasoning steps before final output.

**Example:**
```markdown
### 📋 Technical Summary

*Generated by Ollama (llama3.2:3b)*

Here are the requested summaries:

**Main Contribution**
The author provides advice to researchers tackling technical AGI alignment
problems, focusing on overcoming deference and making progress despite
numerous challenges.

**Key Methodology**
The author recommends a process of "graceful deference," where researchers
start by deferring to others' assumptions, then gradually question and
investigate their own background conclusions to make progress in technical
AGI alignment research.

**Most Important Result**
Technical AGI alignment problems are considered illegible, meaning they are
less likely to receive funding or support due to the significant challenges
and headwinds involved, but researchers can still contribute by doing other
related work or finding ways to balance those sacrifices.

Here is a 80-word technical summary:

To tackle technical AGI alignment problems, researchers must overcome
deference to others' assumptions. Gracefully deferring initially helps,
then gradually questioning and investigating own background conclusions
enables progress...
```

**Impact:** Reasoning process is now visible, not just final output.

---

## Baseline Data (For Comparison)

**Location:** `data/research/*/2025/11/17-21/`

**Format:** Parquet files (older format, pre-enhancement)

**Example:**
```
data/research/execution_context/2025/11/21/execution_context_140036.parquet
data/research/reasoning_graph_edge/2025/11/21/reasoning_graph_edge_140036.parquet
data/research/system_state/2025/11/21/system_state_140036.parquet
```

**Content:** Basic operational telemetry without enhancements
- No prompt_preview/response_preview
- No decision_rationale/payload_summary
- No pipeline_status/current_phase
- No quality_dimensions

**Value:** Provides baseline for comparison studies.

---

## Next Enhanced Data

**When:** Tonight at 9 PM EST (automated cron run)

**Expected:** Full pipeline with:
- All Phase 1+ enhancements
- Multiple articles processed
- Complete quality_dimensions data
- Gemini QA with confidence_factors (if enabled)

**Files will be:**
```
data/research/execution_context/2025/11/22/execution_context_210000.ndjson
data/research/reasoning_graph_edge/2025/11/22/reasoning_graph_edge_210000.ndjson
data/research/quality_trajectories/2025/11/22/quality_trajectories_210000.ndjson
...
```

---

## How to Read the Data

### Using Python
```python
import json

# Read NDJSON file
with open('data/research/execution_context/2025/11/22/execution_context_220424.ndjson', 'r') as f:
    for line in f:
        record = json.loads(line)
        print(record['agent_id'], record['prompt_preview'][:100])
```

### Using pandas
```python
import pandas as pd

# Read NDJSON into DataFrame
df = pd.read_json('data/research/execution_context/2025/11/22/execution_context_220424.ndjson',
                  lines=True)
print(df[['agent_id', 'prompt_preview', 'response_preview']].head())
```

### Using jq (command line)
```bash
# Show all agent names
jq -r '.agent_id' data/research/execution_context/2025/11/22/execution_context_220424.ndjson

# Show prompt previews
jq -r '.prompt_preview' data/research/execution_context/2025/11/22/execution_context_220424.ndjson
```

---

## Summary

**Enhanced Files Today:**
1. ✅ execution_context_220424.ndjson - Has prompt/response previews
2. ✅ reasoning_graph_edge_220424.ndjson - Has decision rationale
3. ✅ system_state_220424.ndjson - Has pipeline status
4. ⏭️ quality_trajectories_220424.ndjson - Will have quality dimensions (next full run)

**Next Full Run:** Tonight 9 PM EST
**Data Volume:** ~20 articles with complete enhancements
**Mixed Dataset:** Nov 17-22 baseline + Nov 23+ enhanced

---

*Last Updated: November 22, 2025 - 5:45 PM EST*
