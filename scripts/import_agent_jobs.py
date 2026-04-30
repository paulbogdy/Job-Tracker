from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from classifier import classify_job
from db import DB_PATH, init_db, insert_jobs
from scoring import score_job


REQUIRED_FIELDS = {"title", "company", "url"}


def load_profile() -> dict[str, Any]:
    profile_path = ROOT / "profile.yaml"
    if not profile_path.exists():
        raise FileNotFoundError(
            "Missing profile.yaml. Copy profile.example.yaml to profile.yaml and fill in the job seeker's details."
        )
    with profile_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_jobs(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict):
        payload = payload.get("jobs", [])
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of jobs or an object with a 'jobs' list.")
    return payload


def remove_demo_jobs() -> int:
    init_db(DB_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("DELETE FROM jobs WHERE source = 'Demo data'")
        return cursor.rowcount


def validate_job(job: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if not str(job.get(field) or "").strip()]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
    url = str(job.get("url") or "")
    if not url.startswith(("http://", "https://")):
        raise ValueError("Job url must be an http(s) link to a real posting.")


def summarize_description(job: dict[str, Any]) -> str:
    description = " ".join(str(job.get("description") or "").split())
    if len(description) <= 700:
        return description
    return description[:697].rsplit(" ", 1)[0] + "..."


def prepare_job(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    validate_job(job)
    prepared = {
        "title": str(job.get("title") or "").strip(),
        "company": str(job.get("company") or "").strip(),
        "location": str(job.get("location") or "Basel").strip(),
        "source": str(job.get("source") or "Agent research").strip(),
        "url": str(job.get("url") or "").strip(),
        "description": summarize_description(job),
    }
    prepared["bucket"] = job.get("bucket") or classify_job(prepared["title"], prepared["description"])
    score, reason, language = score_job(prepared, profile)
    prepared["suitability_score"] = job.get("suitability_score", score)
    prepared["suitability_reason"] = job.get("suitability_reason") or reason
    prepared["language_requirement"] = job.get("language_requirement") or language
    return prepared


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import verified jobs found by an agent into the local SQLite database."
    )
    parser.add_argument("--file", required=True, type=Path, help="Path to a JSON file containing verified jobs.")
    parser.add_argument("--remove-demo", action="store_true", help="Remove fake demo jobs before importing real jobs.")
    args = parser.parse_args()

    profile = load_profile()
    removed_demo = remove_demo_jobs() if args.remove_demo else 0
    raw_jobs = load_jobs(args.file)
    prepared_jobs: list[dict[str, Any]] = []
    errors = 0
    for index, job in enumerate(raw_jobs, start=1):
        try:
            prepared_jobs.append(prepare_job(job, profile))
        except Exception as exc:
            errors += 1
            print(f"Skipped job #{index}: {exc}")

    stats = insert_jobs(prepared_jobs)
    print(
        "Agent import complete: "
        f"found={len(raw_jobs)}, prepared={len(prepared_jobs)}, inserted={stats['inserted']}, "
        f"duplicates={stats['duplicates']}, errors={stats['errors'] + errors}, removed_demo={removed_demo}"
    )


if __name__ == "__main__":
    main()
