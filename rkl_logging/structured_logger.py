"""
Core StructuredLogger implementation.

Lightweight structured logger with:
- Batched writes to Parquet or NDJSON
- Date/artifact partitioning
- Automatic manifest generation
- Schema validation
- Sampling support
"""

import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from collections import defaultdict
import threading
import atexit

# Try to import Parquet support
try:
    import pandas as pd
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False


class StructuredLogger:
    """
    Structured logger for RKL agentic system.

    Features:
    - Batched writes (configurable batch size)
    - Parquet (preferred) or NDJSON (fallback)
    - Date/artifact partitioning
    - Schema validation (optional)
    - Sampling support
    - Automatic manifest generation

    Example:
        logger = StructuredLogger(
            base_dir="./data/research",
            rkl_version="1.0",
            batch_size=100
        )

        logger.log("execution_context", {
            "session_id": "s1",
            "agent_id": "summarizer",
            ...
        })

        logger.close()  # Flush remaining records
    """

    def __init__(
        self,
        base_dir: str,
        rkl_version: str = "1.0",
        type3_enforcement: bool = True,
        batch_size: int = 100,
        sampling: Optional[Dict[str, float]] = None,
        auto_manifest: bool = True,
        validate_schema: bool = True
    ):
        """
        Initialize StructuredLogger.

        Args:
            base_dir: Base directory for data storage
            rkl_version: RKL system version
            type3_enforcement: Enable Type III boundary tracking
            batch_size: Records to buffer before writing
            sampling: Sampling rates per artifact (default: 1.0 for all)
            auto_manifest: Auto-generate daily manifests
            validate_schema: Enable schema validation
        """
        self.base_dir = Path(base_dir)
        self.rkl_version = rkl_version
        self.type3_enforcement = type3_enforcement
        self.batch_size = batch_size
        self.sampling = sampling or {}
        self.auto_manifest = auto_manifest
        self.validate_schema = validate_schema

        # Buffers for batching
        self._buffers: Dict[str, List[Dict]] = defaultdict(list)
        self._lock = threading.Lock()

        # Track statistics for manifest
        self._stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"rows": 0, "writes": 0}
        )

        # Create base directory
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Register cleanup
        atexit.register(self.close)

    def log(
        self,
        artifact_type: str,
        record: Dict[str, Any],
        force_write: bool = False
    ) -> None:
        """
        Log a structured record.

        Args:
            artifact_type: Type of artifact (e.g., "execution_context")
            record: Record dictionary
            force_write: Skip batching, write immediately

        Example:
            logger.log("execution_context", {
                "session_id": "s1",
                "agent_id": "summarizer",
                "model_id": "llama3.2:8b",
                ...
            })
        """
        # Apply sampling
        if not self._should_sample(artifact_type):
            return

        # Add RKL metadata
        enriched_record = self._enrich_record(record)

        # Validate schema (optional)
        if self.validate_schema:
            self._validate_record(artifact_type, enriched_record)

        with self._lock:
            self._buffers[artifact_type].append(enriched_record)
            self._stats[artifact_type]["rows"] += 1

            # Write batch if full or forced
            if force_write or len(self._buffers[artifact_type]) >= self.batch_size:
                self._write_batch(artifact_type)

    def _should_sample(self, artifact_type: str) -> bool:
        """Check if record should be sampled based on sampling rate."""
        rate = self.sampling.get(artifact_type, 1.0)  # Default 100%

        if rate >= 1.0:
            return True
        if rate <= 0.0:
            return False

        import random
        return random.random() < rate

    def _enrich_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Add RKL-specific metadata to record."""
        enriched = record.copy()

        # Add RKL context if not present
        if "rkl_version" not in enriched:
            enriched["rkl_version"] = self.rkl_version

        if "timestamp" not in enriched:
            enriched["timestamp"] = datetime.utcnow().isoformat() + "Z"

        if self.type3_enforcement and "type3_compliant" not in enriched:
            enriched["type3_compliant"] = True  # Assume compliant unless stated

        return enriched

    def _validate_record(self, artifact_type: str, record: Dict[str, Any]) -> None:
        """Validate record against schema."""
        from .schemas import validate_record

        valid, errors = validate_record(artifact_type, record)
        if not valid:
            print(f"WARNING: Schema validation failed for {artifact_type}: {errors}")
            # Don't block logging, just warn

    def _write_batch(self, artifact_type: str) -> None:
        """Write buffered records to disk."""
        if not self._buffers[artifact_type]:
            return

        records = self._buffers[artifact_type]
        self._buffers[artifact_type] = []  # Clear buffer

        # Determine output path with date partitioning
        today = datetime.utcnow().strftime("%Y-%m-%d")
        year, month, day = today.split("-")

        output_dir = self.base_dir / artifact_type / year / month / day
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write to Parquet or NDJSON
        timestamp = datetime.utcnow().strftime("%H%M%S")

        if PARQUET_AVAILABLE:
            output_file = output_dir / f"{artifact_type}_{timestamp}.parquet"
            self._write_parquet(output_file, records)
        else:
            output_file = output_dir / f"{artifact_type}_{timestamp}.ndjson"
            self._write_ndjson(output_file, records)

        self._stats[artifact_type]["writes"] += 1

    def _write_parquet(self, file_path: Path, records: List[Dict]) -> None:
        """Write records to Parquet file."""
        df = pd.DataFrame(records)
        try:
            df.to_parquet(file_path, index=False, engine="pyarrow")
        except ImportError:
            # Fallback to default engine if pyarrow not available
            df.to_parquet(file_path, index=False)

    def _write_ndjson(self, file_path: Path, records: List[Dict]) -> None:
        """Write records to NDJSON file."""
        with open(file_path, "w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

    def flush(self, artifact_type: Optional[str] = None) -> None:
        """
        Flush buffered records to disk.

        Args:
            artifact_type: Specific artifact to flush, or None for all
        """
        with self._lock:
            if artifact_type:
                self._write_batch(artifact_type)
            else:
                for atype in list(self._buffers.keys()):
                    self._write_batch(atype)

    def close(self) -> None:
        """
        Close logger and flush all remaining records.

        Also generates manifest if auto_manifest is True.
        """
        self.flush()

        if self.auto_manifest:
            self._generate_manifest()

    def _generate_manifest(self) -> None:
        """
        Generate daily manifest with statistics.

        CRITICAL: Merges with existing manifest instead of overwriting.
        This allows multiple processes per day to accumulate stats correctly.
        """
        today = datetime.utcnow().strftime("%Y-%m-%d")
        manifest_dir = self.base_dir / "manifests"
        manifest_dir.mkdir(parents=True, exist_ok=True)

        manifest_path = manifest_dir / f"{today}.json"

        # Load existing manifest if present (merge instead of overwrite)
        existing = {
            "date": today,
            "rkl_version": self.rkl_version,
            "artifacts": {}
        }

        if manifest_path.exists():
            try:
                with open(manifest_path, "r") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                # If manifest is corrupted, start fresh but log warning
                import logging
                logging.warning(f"Could not load existing manifest {manifest_path}, starting fresh")

        # Merge: add this process's stats to existing counts
        for artifact, stats in self._stats.items():
            if artifact not in existing["artifacts"]:
                existing["artifacts"][artifact] = {
                    "rows": 0,
                    "writes": 0,
                    "schema_version": "v1.0"
                }

            # Accumulate counts from this process
            prev = existing["artifacts"][artifact]
            prev["rows"] = int(prev.get("rows", 0)) + int(stats["rows"])
            prev["writes"] = int(prev.get("writes", 0)) + int(stats["writes"])
            prev["schema_version"] = "v1.0"

        # Update timestamp
        existing["generated_at"] = datetime.utcnow().isoformat() + "Z"
        existing["rkl_version"] = self.rkl_version

        # Atomic write: tmp file + rename (prevents corruption from interrupted writes)
        tmp_path = manifest_path.with_suffix(".json.tmp")
        with open(tmp_path, "w") as f:
            f.write(json.dumps(existing, indent=2))

        # Atomic rename (OS-level atomic operation)
        import os
        os.replace(tmp_path, manifest_path)

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get logging statistics."""
        return dict(self._stats)


# Convenience function
def sha256_text(text: str) -> str:
    """Generate SHA-256 hash of text for privacy-preserving content fingerprinting."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
