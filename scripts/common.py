from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus, urljoin

import requests
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from classifier import classify_job
from db import insert_jobs
from scoring import score_job


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9,de-CH;q=0.8,de;q=0.7",
}

INVALID_TITLES = {
    "english",
    "deutsch",
    "francais",
    "français",
    "italiano",
    "find a job",
    "find jobs",
    "job search",
    "job alert",
    "login",
    "sign in",
    "menu",
}


@dataclass
class FetchResult:
    source: str
    found: int
    inserted: int
    duplicates: int
    errors: int = 0
    message: str = ""


def load_profile(path: Path | str = ROOT / "profile.yaml") -> dict:
    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(
            "Missing profile.yaml. Copy profile.example.yaml to profile.yaml and fill in the job seeker's details."
        )
    with profile_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def keywords_for_bucket(profile: dict, bucket: str | None = None) -> list[str]:
    search_keywords = profile.get("search_keywords", {})
    if not bucket or bucket == "all":
        keywords: list[str] = []
        for values in search_keywords.values():
            keywords.extend(values)
        return keywords

    normalized = bucket.lower().replace("/", "_").replace(" ", "_").replace("-", "_")
    return search_keywords.get(normalized, [])


def is_relevant_location(location: str, description: str, profile: dict) -> bool:
    text = f"{location} {description}".lower()
    accepted = profile.get("location", {}).get("acceptable_locations", [])
    if any(place.lower() in text for place in accepted):
        return True
    return any(term in text for term in ["remote", "hybrid", "home office", "homeoffice"])


def enrich_and_filter(raw_jobs: list[dict], profile: dict, source: str) -> list[dict]:
    enriched: list[dict] = []
    for raw in raw_jobs:
        title = (raw.get("title") or "").strip()
        if not is_valid_title(title):
            continue
        location = raw.get("location") or ""
        description = raw.get("description") or ""
        if not is_relevant_location(location, description, profile):
            continue
        job = {
            "title": title,
            "company": raw.get("company") or "",
            "location": location,
            "source": source,
            "url": raw.get("url") or "",
            "description": description,
        }
        job["bucket"] = classify_job(job["title"], job["description"])
        score, reason, language = score_job(job, profile)
        job["suitability_score"] = score
        job["suitability_reason"] = reason
        job["language_requirement"] = language
        enriched.append(job)
    return enriched


def save_jobs(raw_jobs: list[dict], profile: dict, source: str) -> FetchResult:
    jobs = enrich_and_filter(raw_jobs, profile, source)
    stats = insert_jobs(jobs)
    return FetchResult(
        source=source,
        found=len(jobs),
        inserted=stats["inserted"],
        duplicates=stats["duplicates"],
        errors=stats["errors"],
    )


def get_soup(url: str, timeout: int = 20) -> BeautifulSoup | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        if response.status_code in {401, 403, 429}:
            print(f"Blocked or rate-limited: {url} returned HTTP {response.status_code}")
            return None
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Could not fetch {url}: {exc}")
        return None
    return BeautifulSoup(response.text, "html.parser")


def build_search_url(template: str, keyword: str, location: str = "Basel") -> str:
    return template.format(query=quote_plus(keyword), location=quote_plus(location))


def absolute_url(base_url: str, href: str | None) -> str:
    return urljoin(base_url, href or "")


def compact_text(value: str) -> str:
    return " ".join((value or "").split())


def is_valid_title(title: str) -> bool:
    normalized = compact_text(title).lower()
    if len(normalized) < 4 or normalized in INVALID_TITLES:
        return False
    if normalized.startswith(("find ", "search ", "show ")):
        return False
    return True


def parser() -> argparse.ArgumentParser:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--bucket", default="all")
    arg_parser.add_argument("--limit", type=int, default=80)
    return arg_parser


def print_result(result: FetchResult) -> None:
    print(
        f"{result.source}: found={result.found}, inserted={result.inserted}, "
        f"duplicates={result.duplicates}, errors={result.errors}"
    )
    if result.message:
        print(result.message)
