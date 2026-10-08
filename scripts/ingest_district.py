#!/usr/bin/env python
"""
Surakshit Basti — District Data Ingestion CLI
Usage:
    python scripts/ingest_district.py --district wayanad
    python scripts/ingest_district.py --district wayanad --dry-run
"""
import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.ingestion.pipeline import run_district_ingestion_pipeline


def main():
    parser = argparse.ArgumentParser(description="Ingest open geospatial & rainfall datasets for a pilot district.")
    parser.add_argument("--district", type=str, default="wayanad", help="Pilot District ID (default: wayanad)")
    parser.add_argument("--dry-run", action="store_true", help="Perform reachability/manifest checks without downloading large files.")
    args = parser.parse_args()

    results = run_district_ingestion_pipeline(district_id=args.district, dry_run=args.dry_run)
    print(f"\nIngestion pipeline completed for district '{args.district}'. Datasets processed: {list(results.keys())}")


if __name__ == "__main__":
    main()
