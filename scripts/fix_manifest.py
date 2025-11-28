#!/usr/bin/env python3
"""
Manifest Fixer - Retroactively fix manifest by scanning Parquet files

This utility reads actual Parquet files and regenerates the daily manifest
with accurate row counts. Use this to fix manifests that were overwritten
by the last process to close before the merge fix was applied.

Usage:
    python scripts/fix_manifest.py [--date YYYY-MM-DD] [--base-dir PATH]

Options:
    --date YYYY-MM-DD  Date to fix (default: today)
    --base-dir PATH    Research data directory (default: ./data/research)
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("❌ pandas required for Parquet reading")
    print("   Install: pip install pandas pyarrow")
    exit(1)


def scan_artifact_counts(base_dir: Path, date_str: str) -> dict:
    """Scan Parquet files for a given date and count actual rows."""
    artifacts = ["execution_context", "reasoning_graph_edge", "boundary_event", "governance_ledger"]
    counts = {}

    print(f"📂 Scanning Parquet files for {date_str}...")
    print()

    for artifact in artifacts:
        artifact_dir = base_dir / artifact

        if not artifact_dir.exists():
            print(f"   ⚠️  {artifact}: directory not found")
            counts[artifact] = {"rows": 0, "files": 0}
            continue

        # Find all Parquet files for this date
        date_parts = date_str.split("-")  # YYYY-MM-DD
        if len(date_parts) == 3:
            year, month, day = date_parts
            # Check date-partitioned path: artifact/YYYY/MM/DD/*.parquet
            date_path = artifact_dir / year / month / day
            if date_path.exists():
                parquet_files = list(date_path.glob("*.parquet"))
            else:
                # Fallback: search all Parquet files (non-partitioned)
                parquet_files = list(artifact_dir.rglob("*.parquet"))
        else:
            parquet_files = list(artifact_dir.rglob("*.parquet"))

        if not parquet_files:
            print(f"   ⚠️  {artifact}: no Parquet files found")
            counts[artifact] = {"rows": 0, "files": 0}
            continue

        # Count rows across all files
        total_rows = 0
        for pf in parquet_files:
            try:
                df = pd.read_parquet(pf)
                total_rows += len(df)
            except Exception as e:
                print(f"   ⚠️  {artifact}: error reading {pf.name}: {e}")

        counts[artifact] = {"rows": total_rows, "files": len(parquet_files)}
        print(f"   ✅ {artifact}: {total_rows} rows across {len(parquet_files)} file(s)")

    return counts


def fix_manifest(base_dir: Path, date_str: str):
    """Fix manifest for given date by scanning actual Parquet files."""
    print("=" * 60)
    print("Manifest Fixer")
    print("=" * 60)
    print(f"\nDate: {date_str}")
    print(f"Base directory: {base_dir}")
    print()

    # Scan Parquet files
    counts = scan_artifact_counts(base_dir, date_str)

    # Build corrected manifest
    manifest_dir = base_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"{date_str}.json"

    # Load existing manifest (if any) to preserve metadata
    existing = {"rkl_version": "1.0"}
    if manifest_path.exists():
        try:
            with open(manifest_path, "r") as f:
                existing = json.load(f)
            print(f"📋 Loaded existing manifest: {manifest_path.name}")
        except Exception:
            print(f"⚠️  Could not load existing manifest, creating new one")

    # Build corrected manifest
    corrected = {
        "date": date_str,
        "rkl_version": existing.get("rkl_version", "1.0"),
        "artifacts": {},
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "corrected_by": "fix_manifest.py"
    }

    for artifact, data in counts.items():
        corrected["artifacts"][artifact] = {
            "rows": data["rows"],
            "writes": data["files"],  # Approximate: 1 write per file
            "schema_version": "v1.0"
        }

    # Write corrected manifest
    print()
    print(f"💾 Writing corrected manifest to {manifest_path}")

    with open(manifest_path, "w") as f:
        f.write(json.dumps(corrected, indent=2))

    print()
    print("=" * 60)
    print("✅ MANIFEST FIXED")
    print("=" * 60)
    print()
    print("Corrected counts:")
    for artifact, data in counts.items():
        print(f"   - {artifact}: {data['rows']} rows")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Fix manifest by scanning actual Parquet files"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=datetime.utcnow().strftime("%Y-%m-%d"),
        help="Date to fix (YYYY-MM-DD, default: today)"
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("./data/research"),
        help="Research data directory (default: ./data/research)"
    )

    args = parser.parse_args()

    if not args.base_dir.exists():
        print(f"❌ Base directory not found: {args.base_dir}")
        print("   Check that you're running from the project root")
        exit(1)

    fix_manifest(args.base_dir, args.date)


if __name__ == "__main__":
    main()
