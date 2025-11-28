#!/usr/bin/env python3
"""
Example usage of rkl_logging package.

Demonstrates:
- Basic logging
- All Phase 0 artifacts
- Privacy helpers
- Validation
"""

from rkl_logging import (
    StructuredLogger,
    sha256_text,
    sha256_dict,
    sanitize_for_research,
    anonymize_for_public
)


def example_basic_logging():
    """Basic logging example"""
    print("=" * 60)
    print("Example 1: Basic Logging")
    print("=" * 60)

    logger = StructuredLogger(
        base_dir="./example_data",
        rkl_version="1.0",
        batch_size=10
    )

    # Log some execution contexts
    for i in range(5):
        logger.log("execution_context", {
            "session_id": "example-session-1",
            "turn_id": i,
            "agent_id": "summarizer",
            "model_id": "llama3.2:8b",
            "temp": 0.3,
            "top_p": 0.95,
            "ctx_tokens_used": 2000 + i * 10,
            "gen_tokens": 150 + i * 5,
            "tool_lat_ms": 1200 + i * 50,
            "cache_hit": i % 2 == 0,
            "prompt_id_hash": sha256_text(f"prompt version {i}")
        })

    logger.close()
    print("✓ Logged 5 execution contexts")
    print(f"✓ Check output in: ./example_data/execution_context/")
    print()


def example_all_phase0_artifacts():
    """Example logging all Phase 0 artifacts"""
    print("=" * 60)
    print("Example 2: All Phase 0 Artifacts")
    print("=" * 60)

    logger = StructuredLogger(
        base_dir="./example_data",
        rkl_version="1.0"
    )

    session_id = "example-session-2"

    # 1. Execution Context
    logger.log("execution_context", {
        "session_id": session_id,
        "turn_id": 1,
        "agent_id": "summarizer",
        "model_id": "llama3.2:8b",
        "model_rev": "8B-q4",
        "quant": "q4",
        "temp": 0.3,
        "top_p": 0.95,
        "ctx_tokens_used": 2048,
        "gen_tokens": 150,
        "tool_lat_ms": 1234,
        "cache_hit": False,
        "prompt_id_hash": sha256_text("summarization prompt v1"),
        "pipeline_phase": "processing",
        "care_metadata": {
            "collective_benefit": True,
            "authority_to_control": "local",
            "responsibility": "audit-001",
            "ethics": "consent_verified"
        }
    })
    print("✓ Logged execution_context")

    # 2. Agent Graph
    logger.log("agent_graph", {
        "edge_id": "edge-001",
        "session_id": session_id,
        "from_agent": "summarizer",
        "to_agent": "qa_reviewer",
        "msg_type": "summary_for_review",
        "intent_tag": "quality_check",
        "content_hash": sha256_text("summary content"),
        "parent_edge_id": None,
        "role_tags": ["processing", "quality_assurance"],
        "latency_ms": 45,
        "retry_count": 0
    })
    print("✓ Logged agent_graph")

    # 3. Boundary Events
    logger.log("boundary_events", {
        "event_id": "boundary-001",
        "agent_id": "summarizer",
        "rule_id": "processing_boundary",
        "trigger_tag": "local_inference_check",
        "context_tag": "ollama_verification",
        "action": "passed",
        "reviewer": "governance_auditor",
        "severity": "info"
    })
    print("✓ Logged boundary_events")

    # 4. Governance Ledger
    logger.log("governance_ledger", {
        "publish_id": "pub-001",
        "artifact_ids": ["brief-2025-11-11"],
        "contributing_agent_ids": ["summarizer", "qa_reviewer", "brief_composer"],
        "verification_hashes": [
            sha256_text("input data"),
            sha256_text("output data")
        ],
        "human_signoff_id": "reviewer-mike",
        "quality_score": 8.5,
        "type3_verified": True,
        "care_compliance_verified": True
    })
    print("✓ Logged governance_ledger")

    logger.close()
    print()
    print("✓ All Phase 0 artifacts logged")
    print()


def example_privacy_helpers():
    """Example using privacy helpers"""
    print("=" * 60)
    print("Example 3: Privacy Helpers")
    print("=" * 60)

    # Original record with sensitive data
    original_record = {
        "session_id": "session-123",
        "agent_id": "summarizer",
        "model_id": "llama3.2:8b",
        "temp": 0.3,
        "gen_tokens": 150,
        "prompt_text": "This is the actual prompt text that should be hashed",
        "input_text": "This is sensitive input data",
        "output_text": "This is the generated output"
    }

    print("Original record (INTERNAL):")
    print(f"  Keys: {list(original_record.keys())}")
    print()

    # Sanitize for research
    research_record = sanitize_for_research(original_record)
    print("Sanitized for RESEARCH:")
    print(f"  Keys: {list(research_record.keys())}")
    print(f"  Sensitive fields hashed: prompt_text_hash, input_text_hash, output_text_hash")
    print()

    # Anonymize for public
    public_record = anonymize_for_public(original_record)
    print("Anonymized for PUBLIC:")
    print(f"  Keys: {list(public_record.keys())}")
    print(f"  Only structural fields kept")
    print()


def example_with_sampling():
    """Example with sampling configuration"""
    print("=" * 60)
    print("Example 4: Sampling Configuration")
    print("=" * 60)

    logger = StructuredLogger(
        base_dir="./example_data",
        rkl_version="1.0",
        sampling={
            "execution_context": 1.0,    # 100% - always log
            "agent_graph": 0.5,           # 50% - log half
            "boundary_events": 1.0,       # 100%
            "expensive_traces": 0.05      # 5% - rarely log
        }
    )

    # Log many records - some will be sampled
    for i in range(20):
        logger.log("agent_graph", {
            "edge_id": f"edge-{i:03d}",
            "session_id": "sampling-test",
            "from_agent": "agent_a",
            "to_agent": "agent_b",
            "msg_type": "test",
            "content_hash": sha256_text(f"message {i}")
        })

    logger.close()

    print("✓ Logged 20 agent_graph records with 50% sampling")
    print("✓ ~10 records should be in output (probabilistic)")
    print()


def example_validation():
    """Example showing schema validation"""
    print("=" * 60)
    print("Example 5: Schema Validation")
    print("=" * 60)

    logger = StructuredLogger(
        base_dir="./example_data",
        rkl_version="1.0",
        validate_schema=True  # Enable validation
    )

    # Valid record
    print("Logging valid record...")
    logger.log("execution_context", {
        "session_id": "valid-session",
        "turn_id": 1,
        "agent_id": "test_agent",
        "model_id": "llama3.2:1b",
        "timestamp": "2025-11-11T09:00:00Z"
    })
    print("✓ Valid record accepted")
    print()

    # Invalid record (missing required fields)
    print("Logging invalid record (missing required fields)...")
    logger.log("execution_context", {
        "session_id": "invalid-session",
        # Missing: turn_id, agent_id, model_id
    })
    print("⚠ Invalid record logged with warning (non-blocking)")
    print()

    logger.close()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "RKL Logging Package Examples" + " " * 19 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        example_basic_logging()
        example_all_phase0_artifacts()
        example_privacy_helpers()
        example_with_sampling()
        example_validation()

        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print()
        print("Output location: ./example_data/")
        print()
        print("To inspect the data:")
        print("  import pandas as pd")
        print("  df = pd.read_parquet('example_data/execution_context/')")
        print("  print(df.head())")
        print()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
