#!/usr/bin/env python3
"""
Export telemetry parquet files to a zipped bundle suitable for HuggingFace/Kaggle upload.

Usage:
    python scripts/export_telemetry.py --output /tmp/telemetry_export.zip

Notes:
    - Exports data/research/* parquet/NDJSON files plus a manifest.json.
    - Does NOT upload; just prepares an archive for manual push.
    - Optional filters: --since YYYY-MM-DD to include files on/after that date.
"""

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "research"


def collect_files(since: str | None):
    files = []
    if since:
        since_dt = datetime.strptime(since, "%Y-%m-%d").date()
    else:
        since_dt = None

    for path in DATA_DIR.rglob("*"):
        if path.is_file():
            if since_dt:
                try:
                    # Expect path like .../YYYY/MM/DD/...
                    parts = path.parts
                    year, month, day = int(parts[-4]), int(parts[-3]), int(parts[-2])
                    file_date = datetime(year, month, day).date()
                    if file_date < since_dt:
                        continue
                except Exception:
                    pass
            files.append(path)
    return files


def main():
    parser = argparse.ArgumentParser(description="Export telemetry bundle.")
    parser.add_argument("--output", "-o", required=True, help="Output zip path")
    parser.add_argument("--since", help="Earliest date to include (YYYY-MM-DD)")
    args = parser.parse_args()

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    files = collect_files(args.since)
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "since": args.since or "all",
        "file_count": len(files),
        "base_dir": str(DATA_DIR)
    }

    tmp_dir = out_path.parent / (out_path.stem + "_export_tmp")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        rel = f.relative_to(DATA_DIR)
        dest = tmp_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)

    manifest_path = tmp_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    shutil.make_archive(str(out_path.with_suffix("")), "zip", tmp_dir)
    shutil.rmtree(tmp_dir)
    print(f"Exported {len(files)} files to {out_path}")


if __name__ == "__main__":
    main()
