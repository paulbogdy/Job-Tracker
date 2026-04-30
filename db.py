from __future__ import annotations

import hashlib
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "jobs.db"

STATUSES = [
    "New",
    "Interesting",
    "Applied",
    "Follow-up",
    "Interview",
    "Rejected",
    "Not suitable",
]


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    source TEXT NOT NULL,
    url TEXT,
    description TEXT,
    bucket TEXT,
    suitability_score INTEGER DEFAULT 0,
    suitability_reason TEXT,
    language_requirement TEXT,
    status TEXT DEFAULT 'New',
    date_found TEXT NOT NULL,
    date_applied TEXT,
    notes TEXT,
    hash_key TEXT NOT NULL UNIQUE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_url
ON jobs(url)
WHERE url IS NOT NULL AND url != '';

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_bucket ON jobs(bucket);
CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(suitability_score);
"""


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DB_PATH) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)


def make_hash_key(title: str, company: str | None, source: str | None = None) -> str:
    normalized = "|".join(
        [
            (title or "").strip().lower(),
            (company or "").strip().lower(),
            (source or "").strip().lower(),
        ]
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def normalize_job(job: dict[str, Any]) -> dict[str, Any]:
    title = (job.get("title") or "").strip()
    company = (job.get("company") or "").strip()
    source = (job.get("source") or "unknown").strip()
    if not title:
        raise ValueError("Job title is required")

    normalized = {
        "title": title,
        "company": company,
        "location": (job.get("location") or "").strip(),
        "source": source,
        "url": (job.get("url") or "").strip(),
        "description": (job.get("description") or "").strip(),
        "bucket": (job.get("bucket") or "Other").strip(),
        "suitability_score": int(job.get("suitability_score") or 0),
        "suitability_reason": (job.get("suitability_reason") or "").strip(),
        "language_requirement": (job.get("language_requirement") or "").strip(),
        "status": job.get("status") or "New",
        "date_found": job.get("date_found") or date.today().isoformat(),
        "date_applied": job.get("date_applied") or None,
        "notes": job.get("notes") or "",
    }
    normalized["hash_key"] = job.get("hash_key") or make_hash_key(title, company, source)
    return normalized


def insert_job(job: dict[str, Any], db_path: Path | str = DB_PATH) -> tuple[bool, str]:
    init_db(db_path)
    normalized = normalize_job(job)

    columns = ", ".join(normalized.keys())
    placeholders = ", ".join([f":{key}" for key in normalized.keys()])
    query = f"INSERT INTO jobs ({columns}) VALUES ({placeholders})"

    try:
        with get_connection(db_path) as conn:
            conn.execute(query, normalized)
        return True, "inserted"
    except sqlite3.IntegrityError:
        return False, "duplicate"


def insert_jobs(jobs: list[dict[str, Any]], db_path: Path | str = DB_PATH) -> dict[str, int]:
    stats = {"found": len(jobs), "inserted": 0, "duplicates": 0, "errors": 0}
    for job in jobs:
        try:
            inserted, reason = insert_job(job, db_path)
            if inserted:
                stats["inserted"] += 1
            elif reason == "duplicate":
                stats["duplicates"] += 1
        except Exception:
            stats["errors"] += 1
    return stats


def fetch_jobs_df(db_path: Path | str = DB_PATH) -> pd.DataFrame:
    import pandas as pd

    init_db(db_path)
    with get_connection(db_path) as conn:
        return pd.read_sql_query(
            "SELECT * FROM jobs ORDER BY suitability_score DESC, date_found DESC, id DESC",
            conn,
        )


def get_job(job_id: int, db_path: Path | str = DB_PATH) -> dict[str, Any] | None:
    init_db(db_path)
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def update_job(job_id: int, updates: dict[str, Any], db_path: Path | str = DB_PATH) -> None:
    allowed = {"status", "date_applied", "notes"}
    clean = {key: value for key, value in updates.items() if key in allowed}
    if not clean:
        return

    assignments = ", ".join([f"{key} = :{key}" for key in clean])
    clean["id"] = job_id
    with get_connection(db_path) as conn:
        conn.execute(f"UPDATE jobs SET {assignments} WHERE id = :id", clean)


def dedupe_existing_jobs(db_path: Path | str = DB_PATH) -> dict[str, int]:
    init_db(db_path)
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, url, hash_key
            FROM jobs
            ORDER BY date_found ASC, id ASC
            """
        ).fetchall()
        seen_urls: set[str] = set()
        seen_hashes: set[str] = set()
        delete_ids: list[int] = []
        for row in rows:
            url = (row["url"] or "").strip().lower()
            hash_key = row["hash_key"]
            if (url and url in seen_urls) or hash_key in seen_hashes:
                delete_ids.append(row["id"])
            else:
                if url:
                    seen_urls.add(url)
                seen_hashes.add(hash_key)

        if delete_ids:
            conn.executemany("DELETE FROM jobs WHERE id = ?", [(job_id,) for job_id in delete_ids])
    return {"removed": len(delete_ids), "kept": len(rows) - len(delete_ids)}
