#!/usr/bin/env python3
"""
Upload RKL Secure Reasoning Brief telemetry dataset to HuggingFace.

This script uploads the prepared dataset to the RKL organization account
on HuggingFace for research community access.
"""

from huggingface_hub import HfApi, create_repo
from pathlib import Path
import json

def upload_dataset():
    """Upload dataset to HuggingFace."""

    # Paths
    base_dir = Path(__file__).parent.parent
    dataset_dir = base_dir / "datasets" / "telemetry-v1.0"
    metadata_file = dataset_dir / "dataset-metadata.json"

    # Load metadata
    with open(metadata_file) as f:
        metadata = json.load(f)

    # HuggingFace configuration
    repo_id = "rkl-org/rkl-secure-reasoning-brief-telemetry"

    print(f"Uploading dataset to HuggingFace: {repo_id}")
    print(f"Source directory: {dataset_dir}")

    # Initialize API
    api = HfApi()

    # Create repository (if it doesn't exist)
    try:
        print("\nCreating repository...")
        create_repo(
            repo_id=repo_id,
            repo_type="dataset",
            private=True,  # Start as private
            exist_ok=True
        )
        print(f"  ✅ Repository created/verified: https://huggingface.co/datasets/{repo_id}")
    except Exception as e:
        print(f"  ⚠️  Repository creation: {e}")

    # Upload folder
    print("\nUploading files...")
    try:
        api.upload_folder(
            folder_path=str(dataset_dir),
            repo_id=repo_id,
            repo_type="dataset",
            commit_message="Upload RKL Secure Reasoning Brief telemetry v1.0 (Nov 17-26, 2025)"
        )
        print(f"  ✅ Dataset uploaded successfully!")
    except Exception as e:
        print(f"  ❌ Upload failed: {e}")
        return False

    # Update README card
    print("\nDataset card updated from README.md")

    print(f"\n✅ Complete! View at: https://huggingface.co/datasets/{repo_id}")
    print(f"\nNext steps:")
    print(f"  1. Go to https://huggingface.co/datasets/{repo_id}/settings")
    print(f"  2. Add tags: {', '.join(metadata['keywords'])}")
    print(f"  3. Set license: CC-BY-4.0")
    print(f"  4. Make public when ready")

    return True

if __name__ == "__main__":
    upload_dataset()
