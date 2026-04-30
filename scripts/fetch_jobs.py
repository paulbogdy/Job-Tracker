from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from scripts.common import load_profile, print_result, save_jobs


FETCHERS = {
    "jobs.ch": "scripts.fetch_jobs_ch",
    "indeed": "scripts.fetch_indeed",
    "hotelcareer": "scripts.fetch_hotelcareer",
    "jobscout24": "scripts.fetch_jobscout24",
    "gastrojobs": "scripts.fetch_gastrojobs",
}

BUCKET_ALIASES = {
    "all": "all",
    "hospitality": "hospitality",
    "data/marketing": "data_marketing",
    "data_marketing": "data_marketing",
    "hotels/housekeeping": "hotels_housekeeping",
    "hotels_housekeeping": "hotels_housekeeping",
}


def run_fetcher(module_name: str, bucket: str, limit: int):
    module = importlib.import_module(module_name)
    raw_jobs = module.fetch(bucket=bucket, limit=limit)
    return module.SOURCE, raw_jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch Basel jobs into SQLite.")
    parser.add_argument("--source", choices=["all", *FETCHERS.keys()], default="all")
    parser.add_argument("--bucket", default="all")
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()

    profile = load_profile()
    bucket = BUCKET_ALIASES.get(args.bucket.lower(), args.bucket)
    selected = FETCHERS if args.source == "all" else {args.source: FETCHERS[args.source]}

    for _, module_name in selected.items():
        try:
            source, raw_jobs = run_fetcher(module_name, bucket, args.limit)
            result = save_jobs(raw_jobs, profile, source)
            print_result(result)
        except Exception as exc:
            print(f"{module_name}: failed gracefully: {exc}")


if __name__ == "__main__":
    main()
