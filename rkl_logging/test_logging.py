#!/usr/bin/env python3
"""
Unit tests for rkl_logging package.

Tests:
- Schema validation and drift detection
- Logging interface consistency
- Privacy helpers
- Hashing utilities
- Parquet/NDJSON fallback
"""

import json
import tempfile
import shutil
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now we can import as a package
from rkl_logging.structured_logger import StructuredLogger
from rkl_logging.utils.hashing import sha256_text, sha256_dict
from rkl_logging.schemas import SCHEMAS, validate_record
from rkl_logging.utils.privacy import sanitize_for_research, anonymize_for_public


def test_schema_registry():
    """Test that all Phase 0 schemas are registered."""
    required_schemas = [
        "execution_context",
        "agent_graph",
        "boundary_events",
        "governance_ledger"
    ]

    for schema_name in required_schemas:
        assert schema_name in SCHEMAS, f"Missing schema: {schema_name}"
        schema = SCHEMAS[schema_name]

        # Check schema structure
        assert "version" in schema
        assert "artifact_type" in schema
        assert "required_fields" in schema
        assert "field_types" in schema

        print(f"✓ Schema '{schema_name}' v{schema['version']} registered")


def test_schema_validation():
    """Test schema validation catches errors."""
    # Valid record
    valid_record = {
        "session_id": "test-session",
        "turn_id": 1,
        "agent_id": "test_agent",
        "model_id": "llama3.2:1b",
        "timestamp": "2025-11-11T09:00:00Z"
    }

    is_valid, errors = validate_record("execution_context", valid_record)
    assert is_valid, f"Valid record rejected: {errors}"
    print("✓ Valid record accepted")

    # Invalid record (missing required fields)
    invalid_record = {
        "session_id": "test-session",
        # Missing: turn_id, agent_id, model_id
    }

    is_valid, errors = validate_record("execution_context", invalid_record)
    assert not is_valid, "Invalid record accepted"
    assert len(errors) > 0
    print(f"✓ Invalid record rejected: {errors[0]}")


def test_hashing_utilities():
    """Test SHA-256 hashing helpers."""
    text = "This is sensitive content"

    # Test sha256_text
    hash1 = sha256_text(text)
    hash2 = sha256_text(text)

    assert hash1 == hash2, "Hashing not deterministic"
    assert hash1.startswith("sha256:"), "Hash missing prefix"
    assert len(hash1) == 71, f"Hash wrong length: {len(hash1)}"  # sha256: + 64 hex chars
    print(f"✓ sha256_text: {hash1[:20]}...")

    # Test sha256_dict
    data = {"key1": "value1", "key2": "value2"}
    dict_hash1 = sha256_dict(data)
    dict_hash2 = sha256_dict(data)

    assert dict_hash1 == dict_hash2, "Dict hashing not deterministic"
    assert dict_hash1.startswith("sha256:")
    print(f"✓ sha256_dict: {dict_hash1[:20]}...")


def test_privacy_helpers():
    """Test sanitization and anonymization."""
    original = {
        "session_id": "s123",
        "agent_id": "summarizer",
        "model_id": "llama3.2:8b",
        "temp": 0.3,
        "gen_tokens": 150,
        "prompt_text": "This is sensitive",
        "input_text": "Also sensitive",
        "output_text": "Generated text"
    }

    # Test sanitize_for_research
    research = sanitize_for_research(original)

    assert "session_id" in research
    assert "agent_id" in research
    assert "temp" in research
    assert "prompt_text" not in research  # Replaced with hash
    assert "prompt_text_hash" in research
    assert research["prompt_text_hash"].startswith("sha256:")
    print("✓ sanitize_for_research: sensitive fields hashed")

    # Test anonymize_for_public
    public = anonymize_for_public(original)

    assert "session_id" in public
    assert "agent_id" in public
    assert "temp" in public
    assert "prompt_text" not in public
    assert "input_text" not in public
    assert "prompt_text_hash" not in public  # Hashes also removed
    print("✓ anonymize_for_public: only structural fields kept")


def test_basic_logging():
    """Test basic logging functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = StructuredLogger(
            base_dir=tmpdir,
            rkl_version="1.0.test",
            batch_size=2,  # Small batch for testing
            validate_schema=True
        )

        # Log some records
        for i in range(3):
            logger.log("execution_context", {
                "session_id": "test-session",
                "turn_id": i,
                "agent_id": "test_agent",
                "model_id": "llama3.2:1b",
                "temp": 0.3,
                "gen_tokens": 100 + i
            })

        logger.close()

        # Check output directory structure
        base_path = Path(tmpdir)
        assert (base_path / "execution_context").exists(), "No execution_context directory"

        # Check date partitioning
        from datetime import datetime
        today = datetime.utcnow()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")

        date_path = base_path / "execution_context" / year / month / day
        assert date_path.exists(), f"Date partitioning failed: {date_path}"

        # Check files were written
        files = list(date_path.glob("*.parquet")) + list(date_path.glob("*.ndjson"))
        assert len(files) > 0, "No output files created"

        print(f"✓ Basic logging: {len(files)} file(s) written to {date_path}")


def test_sampling():
    """Test sampling behavior."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = StructuredLogger(
            base_dir=tmpdir,
            sampling={
                "execution_context": 0.0,  # 0% - never log
                "agent_graph": 1.0         # 100% - always log
            },
            batch_size=10
        )

        # Log records that should be dropped
        for i in range(5):
            logger.log("execution_context", {
                "session_id": "test",
                "turn_id": i,
                "agent_id": "test",
                "model_id": "test"
            })

        # Log records that should be kept
        for i in range(5):
            logger.log("agent_graph", {
                "edge_id": f"e{i}",
                "session_id": "test",
                "from_agent": "a",
                "to_agent": "b",
                "msg_type": "test",
                "content_hash": sha256_text(f"msg{i}")
            })

        logger.close()

        base_path = Path(tmpdir)

        # execution_context should NOT exist (0% sampling)
        exec_ctx_path = base_path / "execution_context"
        assert not exec_ctx_path.exists() or len(list(exec_ctx_path.rglob("*"))) == 0, \
            "execution_context should be empty (0% sampling)"

        # agent_graph should exist (100% sampling)
        agent_graph_path = base_path / "agent_graph"
        assert agent_graph_path.exists(), "agent_graph should exist (100% sampling)"

        print("✓ Sampling: 0% drops all, 100% keeps all")


def test_manifest_generation():
    """Test that manifests track statistics correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = StructuredLogger(
            base_dir=tmpdir,
            rkl_version="1.0.test",
            batch_size=5
        )

        # Log records
        for i in range(12):
            logger.log("execution_context", {
                "session_id": "test",
                "turn_id": i,
                "agent_id": "test",
                "model_id": "test"
            })

        logger.close()

        # Check stats
        stats = logger._stats["execution_context"]
        assert stats["rows"] == 12, f"Wrong row count: {stats['rows']}"
        assert stats["writes"] >= 2, f"Expected at least 2 writes (batch_size=5): {stats['writes']}"

        print(f"✓ Manifest: {stats['rows']} rows, {stats['writes']} writes")


def test_schema_drift_detection():
    """Test that schema changes are detected."""
    # Get current schema
    schema = SCHEMAS["execution_context"]
    current_required = set(schema["required_fields"])

    # Expected required fields (from design)
    expected_required = {
        "session_id",
        "turn_id",
        "agent_id",
        "model_id",
        "timestamp"
    }

    # Check no drift
    assert current_required == expected_required, \
        f"Schema drift detected!\n  Current: {current_required}\n  Expected: {expected_required}"

    print("✓ Schema drift: execution_context schema is stable")

    # Check all Phase 0 schemas have version fields
    for artifact_type, schema in SCHEMAS.items():
        assert "version" in schema, f"{artifact_type} missing version field"
        assert schema["version"].startswith("v"), f"{artifact_type} version should start with 'v'"
        print(f"  - {artifact_type}: {schema['version']}")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RKL Logging Package Tests")
    print("=" * 60)
    print()

    tests = [
        ("Schema Registry", test_schema_registry),
        ("Schema Validation", test_schema_validation),
        ("Hashing Utilities", test_hashing_utilities),
        ("Privacy Helpers", test_privacy_helpers),
        ("Basic Logging", test_basic_logging),
        ("Sampling", test_sampling),
        ("Manifest Generation", test_manifest_generation),
        ("Schema Drift Detection", test_schema_drift_detection)
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"Test: {name}")
        print("-" * 60)
        try:
            test_func()
            print(f"✓ PASSED\n")
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}\n")
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
