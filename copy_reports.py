#!/usr/bin/env python3
"""
Copy report JSON files from output/reports to website/data for deployment.

This script copies the latest generated reports to the website directory
so the dashboard can access them as static files.
"""

import shutil
from pathlib import Path


def main():
    """Copy report files to website/data directory."""
    output_dir = Path("output/reports")
    website_data_dir = Path("website/data")
    
    # Create website/data directory if it doesn't exist
    website_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to copy
    files_to_copy = [
        "results.json",
        "statistics.json",
        "insights.json",
        "clusters.json",
        "manual_review.json",
    ]
    
    copied = 0
    for filename in files_to_copy:
        src = output_dir / filename
        dst = website_data_dir / filename
        
        if src.exists():
            shutil.copy2(src, dst)
            print(f"✓ Copied {filename}")
            copied += 1
        else:
            print(f"✗ {filename} not found (run research first)")
    
    print(f"\nCopied {copied}/{len(files_to_copy)} files to website/data/")


if __name__ == "__main__":
    main()