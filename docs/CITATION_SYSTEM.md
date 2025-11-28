# Citation System - Type III Compliance

**Date:** 2025-11-21
**Purpose:** Document how citations are generated while maintaining Type III compliance (raw data never exposed)

---

## Overview

The weekly blog generation system automatically generates IEEE-style citations for all papers mentioned in the blog post. This document explains how citations are created while ensuring raw content never leaves the local system.

---

## Citation Format

**IEEE-style** (standard in data science/ML communities):

```
[N] Title, Source, Date. [Online]. Available: URL
```

**Example:**
```
[2] PathMind: A Retrieve-Prioritize-Reason Framework for Knowledge Graph Reasoning
    with Large Language Models, ArXiv AI, 2025-11-20.
    [Online]. Available: https://arxiv.org/abs/2511.14256
```

---

## Data Flow for Citations

### 1. Gemini Writes Blog (with citations)

**Input to Gemini:**
```python
article_text = f"""
[{idx}] {article.get('title', 'Untitled')}
Source: {article.get('source', 'Unknown')}
Link: {article.get('link', 'N/A')}
Summary (by Ollama): {tech_summary}  # ← Ollama-generated, NOT raw content
Tags: {', '.join(article.get('tags', []))}
Significance: {gemini_analysis.get('significance', 'N/A')}
Relevance: {gemini_analysis.get('relevance_score', 0):.2f}
Key Insight: {gemini_analysis.get('key_insight', 'N/A')[:200]}...
"""
```

**What Gemini receives:**
- ✅ Article title (public metadata)
- ✅ Link, source, date (public metadata)
- ✅ Ollama technical summary (derived insight, ~300 chars)
- ✅ Tags (extracted by Ollama from abstracts)
- ✅ Gemini's own prior analysis (significance, relevance, key insight)
- ❌ **NOT** raw_content_excerpt (stays local)

**Gemini output:**
```markdown
## Top Papers of the Week

* **PathMind [2]**: This paper tackles the "black box" reasoning
  challenge in LLMs by using knowledge graphs...
```

### 2. Citation Extraction

**Pattern matching:**
```python
# Handles both [N] and [N, M, P] formats
cited_numbers = set()
for match in re.finditer(r'\[([0-9, ]+)\]', blog_content):
    nums_str = match.group(1)
    for num_str in nums_str.split(','):
        if num_str.strip().isdigit():
            cited_numbers.add(int(num_str))
```

**Extracted citations:** `{2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 20, 23}`

### 3. Reference Generation

**For each cited number:**
```python
article = all_articles[num - 1]
title = article.get('title', 'Untitled')      # Public metadata
link = article.get('link', '')                 # Public metadata
date = article.get('date', 'n.d.')            # Public metadata
source = article.get('source', 'Unknown')      # Public metadata

# IEEE-style citation
citation = f"[{num}] {title}, *{source}*, {date}. [Online]. Available: {link}"
```

**What gets used:**
- ✅ Title, link, date, source (all public metadata)
- ❌ **NOT** raw_content_excerpt
- ❌ **NOT** technical_summary or lay_explanation

**Citations use ONLY public metadata that was already available from RSS feed!**

---

## Type III Compliance Verification

### Question: Do citations expose raw content?

**Answer: NO** ✅

| Field | Used in Citations? | Source | Privacy Level |
|-------|-------------------|--------|---------------|
| `title` | ✅ Yes | RSS feed (public) | Public |
| `link` | ✅ Yes | RSS feed (public) | Public |
| `date` | ✅ Yes | RSS feed (public) | Public |
| `source` | ✅ Yes | RSS feed (public) | Public |
| `raw_content_excerpt` | ❌ **NO** | Article content (local) | Local only |
| `technical_summary` | ❌ **NO** | Ollama (local) | Derived insight |
| `lay_explanation` | ❌ **NO** | Ollama (local) | Derived insight |

### Verification in Code

**generate_weekly_blog.py lines 231-252:**

```python
# Generate references section with IEEE-style citations
# NOTE: Citations use only metadata (title, link, date, source)
# They do NOT include raw_content_excerpt - only public metadata
if cited_numbers:
    references = "\n\n---\n\n## References\n\n"
    for num in sorted(cited_numbers):
        article = all_articles[num - 1]
        title = article.get('title', 'Untitled')
        link = article.get('link', '')
        date = article.get('date', 'n.d.')
        source = article.get('source', 'Unknown')

        # IEEE-style citation format
        citation = f"[{num}] {title}, *{source}*, {date}. [Online]. Available: {link}"
```

**Key observation:** Only `title`, `link`, `date`, `source` are accessed - all public metadata from original RSS feed.

---

## Example References Section

From [2025-11-20_WEEKLY_BLOG.md](../content/briefs/2025-11-20_WEEKLY_BLOG.md):

```markdown
---

## References

[2] PathMind: A Retrieve-Prioritize-Reason Framework for Knowledge Graph Reasoning
    with Large Language Models, *ArXiv AI*, 2025-11-20.
    [Online]. Available: https://arxiv.org/abs/2511.14256

[3] Operationalizing Pluralistic Values in Large Language Model Alignment Reveals
    Trade-offs in Safety, Inclusivity, and Model Behavior, *ArXiv AI*, 2025-11-20.
    [Online]. Available: https://arxiv.org/abs/2511.14476

[5] DeepDefense: Layer-Wise Gradient-Feature Alignment for Building Robust Neural
    Networks, *ArXiv AI*, 2025-11-20.
    [Online]. Available: https://arxiv.org/abs/2511.13749

... [15 total references]
```

---

## Complete Data Provenance Chain

### Blog Content Flow

```
1. RSS Feed (Public Internet)
   ↓
   title, link, date, source (public metadata)

2. Article Content Scraping
   ↓
   raw_content_excerpt (8000 chars) → Stored locally, NEVER transmitted

3. Ollama Processing (LOCAL - 192.168.1.11)
   ↓
   technical_summary, lay_explanation, tags → Derived insights

4. Gemini Analysis (CLOUD API)
   ← Receives: title, link, Ollama summaries (NOT raw content)
   → Produces: relevance_score, key_insight, significance

5. Gemini Blog Writing (CLOUD API)
   ← Receives: title, link, Ollama summaries, prior analysis (NOT raw)
   → Produces: Weekly blog with [N] citations

6. Citation Generation (LOCAL)
   ← Uses: title, link, date, source (public metadata only)
   → Produces: IEEE-style references
```

**Verification:** At no point does raw content leave local system!

---

## Why This Matters for Competition

### 1. Academic Rigor

Using IEEE-style citations demonstrates professional academic standards in automated content generation.

### 2. Traceability

Every claim in the blog can be traced back to its original source via clickable URLs.

### 3. Type III Compliance

Citations prove that we can provide full provenance while maintaining data privacy:
- Raw content never transmitted (stays local)
- Only public metadata appears in citations
- Derived insights (summaries) are clearly attributed to Ollama

### 4. Reproducibility

Readers can:
1. Click citation links to read original papers
2. Verify blog claims against sources
3. Trust that summaries are based on actual research

---

## Future Enhancements

### Post-Competition: Author Extraction

For academic papers, could extract authors from ArXiv API:

```python
# Future enhancement
authors = article.get('authors', [])  # From ArXiv metadata API
author_str = ', '.join(authors[:3])   # First 3 authors
if len(authors) > 3:
    author_str += ', et al.'

# Enhanced IEEE citation
citation = f"[{num}] {author_str}, \"{title},\" *{source}*, {date}.
           [Online]. Available: {link}"
```

**Example:**
```
[2] J. Smith, A. Johnson, and B. Williams, "PathMind: A Retrieve-Prioritize-Reason
    Framework for Knowledge Graph Reasoning with Large Language Models,"
    ArXiv AI, 2025-11-20. [Online]. Available: https://arxiv.org/abs/2511.14256
```

---

## Summary

**Citation System:**
- ✅ Automatically generates IEEE-style citations
- ✅ Uses only public metadata (title, link, date, source)
- ✅ Never includes raw content or private data
- ✅ Maintains full Type III compliance
- ✅ Provides academic rigor and traceability
- ✅ Enables reproducibility and verification

**Key Principle:**
> "Citations reference public metadata from the original source, not the private raw content we processed locally."

This allows us to provide full academic attribution while demonstrating secure reasoning principles in practice.

---

## See Also

- [TELEMETRY_VERIFICATION.md](../TELEMETRY_VERIFICATION.md) - Complete Type III compliance verification
- [RAW_DATA_HANDLING.md](../RAW_DATA_HANDLING.md) - Raw data handling patterns
- [type3-compliance-flow.md](diagrams/type3-compliance-flow.md) - Visual data flow
