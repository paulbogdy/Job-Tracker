# Agent Guide

This project is designed so Codex, Claude, or another coding agent can populate and maintain the job database through conversation. Streamlit is only a review/status UI over SQLite.

## Main Workflow

When the user says something like "find new jobs", "populate the database", or "look for Basel jobs":

1. Read `profile.yaml`. If it does not exist, tell the user to copy `profile.example.yaml` to `profile.yaml` and fill in their real details.
2. Search the live web for real current postings that match the profile.
3. Prefer official job-board or employer posting pages.
4. Verify every candidate is real and relevant to Basel, nearby Basel, remote, or hybrid.
5. Extract a concise record: title, company, location, source, URL, and a short readable description.
6. Skip jobs that are clearly unsuitable because they require fluent German, Swiss German, senior credentials, or licensed professions unless there is a strong reason to include them.
7. Write verified jobs to a temporary JSON file and run `python scripts/import_agent_jobs.py --file <json-file>`.
8. Report how many jobs were found, inserted, and skipped as duplicates.
9. The human uses Streamlit to review jobs and update status.

The Streamlit app must not be treated as the fetching workflow. It is the tracker and review surface. `profile.yaml`, `data/jobs.db`, and temporary import JSON files are local runtime files and should not be committed.

## Rules For Agents

- Do not invent job postings.
- Do not add made-up example jobs to `data/jobs.db`.
- Use live web research when the user asks to populate jobs.
- Use the original posting URL, not a generic homepage, whenever possible.
- Store a short, human-readable description in `description`; keep it quick to scan.
- Keep deduplication by URL and by title/company/source hash.
- Keep scoring logic in `scoring.py` and bucket logic in `classifier.py`.
- Never overwrite human status choices when importing jobs.
- If automated scraper scripts are used as helper tools, treat them as optional research aids, not as the product workflow.

## Useful Commands

```bash
python scripts/import_agent_jobs.py --file data/agent_found_jobs.json
python scripts/import_agent_jobs.py --file data/agent_found_jobs.json --remove-demo
python scripts/seed_demo_jobs.py
python scripts/dedupe_jobs.py
streamlit run app.py
```

Use `scripts/seed_demo_jobs.py` only when the user explicitly wants fake demo data for testing the UI. Do not mix demo rows with real job-search results.

## JSON Import Format

The agent import script accepts either a list of jobs or an object with a `jobs` list:

```json
{
  "jobs": [
    {
      "title": "Service Staff",
      "company": "Real Company Name",
      "location": "Basel",
      "source": "jobs.ch",
      "url": "https://example.com/real-posting",
      "description": "Short summary of the actual job posting and why it may fit."
    }
  ]
}
```

Required fields are `title`, `company`, and `url`. The importer fills bucket, suitability score, suitability reason, language requirement, status, and date found.

## Optional Fetcher Maintenance Notes

The `scripts/fetch_*.py` files are optional helpers. Job boards change markup often. If a fetcher is useful but starts returning zero jobs:

1. Open the search URL in the script.
2. Inspect the current listing card selectors.
3. Update only that fetcher if possible.
4. Run the fetcher directly and confirm it logs found/inserted/duplicate counts.
5. Do not add fake fallback jobs.
