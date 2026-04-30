# Basel Job Tracker

A local Streamlit + SQLite job tracker for Basel, Switzerland. The app is only for reviewing jobs and tracking application status. Jobs are added when you ask Codex, Claude, or another agent to research live postings and populate SQLite based on `profile.yaml`.

## Install

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy profile.example.yaml profile.yaml
```

Edit `profile.yaml` with the job seeker's real location, languages, work permit, experience, target roles, search keywords, and avoid keywords. `profile.yaml` is ignored by git so personal details stay local.

## Run The App

```bash
streamlit run app.py
```

The app has pages for:

- Dashboard: summary counts, status/bucket snapshots, and top review cards.
- Jobs: filters, search, source links, and quick status updates.
- Job Detail: full description, suitability reason, source link, and status update.

## Normal Workflow

Tell the agent something like:

> Find new realistic jobs around Basel for the profile and populate the database.

The agent should:

1. Read `profile.yaml`.
2. Search live job postings on the web.
3. Verify each posting is real and relevant.
4. Create concise records with title, company, location, source, link, and short description.
5. Import them with:

```bash
python scripts/import_agent_jobs.py --file data/agent_found_jobs.json
```

To replace fake demo rows during a real import:

```bash
python scripts/import_agent_jobs.py --file data/agent_found_jobs.json --remove-demo
```

Then use Streamlit to review jobs and update each job's status.

## Demo Data

To clear the current database and load a few fake demo cards for testing the UI:

```bash
python scripts/seed_demo_jobs.py
```

These rows are clearly marked as demo data and use `example.com` links. They are only for checking the interface.

## How Agent Import Works

1. `profile.yaml` defines location preferences, languages, experience, search keywords, avoid keywords, and preferred roles.
2. The agent performs live research and writes verified jobs to JSON.
3. `scripts/import_agent_jobs.py` validates required fields.
4. `classifier.py` assigns a bucket.
5. `scoring.py` gives a 0-100 suitability score and reason.
6. `db.py` deduplicates by URL and title/company/source hash before inserting into SQLite.

The project must not invent job data. If a job cannot be verified with a real posting link, it should not be inserted.

## How Codex Or Claude Should Populate Jobs

See `AGENTS.md`. In short:

- Use web research when asked to populate jobs.
- Prefer official job-board or employer pages.
- Add a concise description that is quick to read in Streamlit.
- Do not overwrite human status choices when importing jobs.
- Import verified jobs with `scripts/import_agent_jobs.py`.
- Report inserted and duplicate counts.

## Edit The Profile

Start from `profile.example.yaml`, then edit `profile.yaml` to change:

- Location radius and acceptable nearby locations.
- Languages and permit notes.
- Experience areas.
- Target buckets.
- Search keywords per bucket.
- Avoid keywords.
- Preferred roles.

`profile.example.yaml` is intentionally generic. Each user should replace it with their own details before asking an agent to populate jobs.
