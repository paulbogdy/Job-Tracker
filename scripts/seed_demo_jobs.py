from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import DB_PATH, init_db, insert_jobs


DEMO_JOBS = [
    {
        "title": "Demo: Service Staff",
        "company": "Basel Riverside Cafe",
        "location": "Basel",
        "source": "Demo data",
        "url": "https://example.com/apply/service-staff-basel",
        "description": "Example posting for a cafe service role in Basel. Good fit for waitressing and service experience; English-friendly team is mentioned in this demo record.",
        "bucket": "Hospitality",
        "suitability_score": 86,
        "suitability_reason": "Demo job: Basel location; hospitality/service fit; English acceptable.",
        "language_requirement": "English mentioned",
    },
    {
        "title": "Demo: Housekeeping Assistant",
        "company": "Hotel Central Basel",
        "location": "Basel",
        "source": "Demo data",
        "url": "https://example.com/apply/housekeeping-assistant-basel",
        "description": "Example hotel housekeeping role focused on room preparation, cleaning standards, and guest-area support. Suitable for housekeeping and cleaning experience.",
        "bucket": "Hotels/Housekeeping",
        "suitability_score": 82,
        "suitability_reason": "Demo job: Basel hotel role; housekeeping fit; no fluent German requirement shown.",
        "language_requirement": "Not specified",
    },
    {
        "title": "Demo: Junior Data Assistant",
        "company": "Basel Operations Team",
        "location": "Hybrid - Basel",
        "source": "Demo data",
        "url": "https://example.com/apply/junior-data-assistant-basel",
        "description": "Example junior data support role using Excel, SQL, and Power BI to prepare reports and clean operational data. Hybrid setup around Basel.",
        "bucket": "Data/Marketing",
        "suitability_score": 78,
        "suitability_reason": "Demo job: Basel hybrid; junior role; Power BI, SQL, and Excel match.",
        "language_requirement": "English mentioned",
    },
    {
        "title": "Demo: Retail Assistant",
        "company": "Basel City Shop",
        "location": "Basel",
        "source": "Demo data",
        "url": "https://example.com/apply/retail-assistant-basel",
        "description": "Example retail assistant role helping customers, organizing products, and supporting shop operations. Useful as an entry-level customer-facing option.",
        "bucket": "Retail/Events",
        "suitability_score": 72,
        "suitability_reason": "Demo job: Basel location; customer-facing experience applies; entry-level fit.",
        "language_requirement": "Not specified",
    },
    {
        "title": "Demo: Social Media Assistant",
        "company": "Local Events Basel",
        "location": "Basel",
        "source": "Demo data",
        "url": "https://example.com/apply/social-media-assistant-basel",
        "description": "Example assistant role creating simple posts, updating event listings, and tracking campaign results in Excel. Could fit marketing and social media experience.",
        "bucket": "Data/Marketing",
        "suitability_score": 75,
        "suitability_reason": "Demo job: Basel location; marketing/social media fit; Excel useful.",
        "language_requirement": "English mentioned",
    },
]


def clear_jobs() -> None:
    init_db(DB_PATH)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM jobs")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'jobs'")


def main() -> None:
    clear_jobs()
    stats = insert_jobs(DEMO_JOBS)
    print(
        "Demo database seeded: "
        f"inserted={stats['inserted']}, duplicates={stats['duplicates']}, errors={stats['errors']}"
    )


if __name__ == "__main__":
    main()
