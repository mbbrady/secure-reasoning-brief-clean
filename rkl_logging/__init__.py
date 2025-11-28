"""
RKL Logging - Structured telemetry for secure reasoning agentic systems

A lightweight, async structured logger designed for the RKL Secure Reasoning
Agentic System. Captures structural telemetry without raw text, enabling
research-grade datasets while preserving privacy.

Design Principles:
- Structural telemetry by default (no raw text in public artifacts)
- Async, batched writes to disk (Parquet if available, else NDJSON)
- Date/Artifact partitioning with automatic manifests
- SHA-256 cross-referencing without exposing content
- Type III compliance tracking built-in
- CARE principles metadata on every record

Quick Start:
    from rkl_logging import StructuredLogger, sha256_text

    logger = StructuredLogger(base_dir="./data/research")
    logger.log("execution_context", {
        "session_id": "s1",
        "agent_id": "summarizer",
        "model_id": "llama3.2:8b",
        "temp": 0.3,
        "gen_tokens": 150,
        "prompt_id_hash": sha256_text("prompt v1")
    })
    logger.close()

Version: 1.0
License: Apache 2.0
"""

__version__ = "1.0.0"
__author__ = "Resonant Knowledge Lab"

from .structured_logger import StructuredLogger
from .utils.hashing import sha256_text, sha256_dict, sha256_file
from .schemas import SCHEMAS, validate_record
from .utils.privacy import sanitize_for_research, anonymize_for_public

__all__ = [
    "StructuredLogger",
    "sha256_text",
    "sha256_dict",
    "sha256_file",
    "SCHEMAS",
    "validate_record",
    "sanitize_for_research",
    "anonymize_for_public"
]
