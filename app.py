from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from db import DB_PATH, STATUSES, fetch_jobs_df, get_job, init_db, update_job


st.set_page_config(page_title="Basel Job Tracker", page_icon="briefcase", layout="wide")


CARD_CSS = """
<style>
.job-meta {
    color: var(--text-color);
    opacity: 0.72;
    font-size: 0.92rem;
    margin-bottom: 0.35rem;
}
.job-description {
    color: var(--text-color);
    line-height: 1.45;
}
.score-pill {
    display: inline-block;
    border: 1px solid rgba(128, 128, 128, 0.35);
    border-radius: 999px;
    padding: 0.15rem 0.55rem;
    font-size: 0.82rem;
    color: var(--text-color);
    background: rgba(128, 128, 128, 0.10);
    margin-right: 0.25rem;
}
.summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.75rem;
    margin: 0.75rem 0 1.25rem;
}
.summary-item {
    background: rgba(128, 128, 128, 0.08);
    border: 1px solid rgba(128, 128, 128, 0.25);
    border-radius: 8px;
    padding: 0.85rem 1rem;
}
.summary-label {
    color: var(--text-color);
    opacity: 0.68;
    font-size: 0.82rem;
}
.summary-value {
    color: var(--text-color);
    font-size: 1.55rem;
    font-weight: 700;
}
.compact-line {
    color: var(--text-color);
    margin-bottom: 0.35rem;
}
</style>
"""


def refresh_jobs() -> pd.DataFrame:
    init_db()
    return fetch_jobs_df()


def save_status(job_id: int, status: str, job: dict) -> None:
    updates = {"status": status}
    if status == "Applied" and not job.get("date_applied"):
        updates["date_applied"] = date.today().isoformat()
    update_job(job_id, updates)


def status_index(status: str | None) -> int:
    return STATUSES.index(status) if status in STATUSES else 0


def render_summary(total: int, new_today: int, active: int, high_fit: int) -> None:
    st.markdown(
        f"""
        <div class="summary-grid">
            <div class="summary-item">
                <div class="summary-label">Total</div>
                <div class="summary-value">{total}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">New today</div>
                <div class="summary-value">{new_today}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">Active</div>
                <div class="summary-value">{active}</div>
            </div>
            <div class="summary-item">
                <div class="summary-label">High fit</div>
                <div class="summary-value">{high_fit}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    filters = st.columns([1, 1, 1, 1])
    bucket = filters[0].selectbox("Bucket", ["All", *sorted(df["bucket"].fillna("Other").unique())])
    status = filters[1].selectbox("Status", ["All", *STATUSES])
    source = filters[2].selectbox("Source", ["All", *sorted(df["source"].fillna("").unique())])
    min_score = filters[3].slider("Minimum score", 0, 100, 0)
    search = st.text_input("Search title, company, description")

    filtered = df[df["suitability_score"] >= min_score].copy()
    if bucket != "All":
        filtered = filtered[filtered["bucket"].fillna("Other") == bucket]
    if status != "All":
        filtered = filtered[filtered["status"] == status]
    if source != "All":
        filtered = filtered[filtered["source"] == source]
    if search:
        haystack = (
            filtered["title"].fillna("")
            + " "
            + filtered["company"].fillna("")
            + " "
            + filtered["description"].fillna("")
        ).str.lower()
        filtered = filtered[haystack.str.contains(search.lower(), na=False)]
    return filtered


def render_job_card(row: pd.Series, key_prefix: str) -> None:
    job_id = int(row["id"])
    job = get_job(job_id) or row.to_dict()
    title = job.get("title") or "Untitled job"
    company = job.get("company") or "Unknown company"
    location = job.get("location") or "Unknown location"
    bucket = job.get("bucket") or "Other"
    source = job.get("source") or "Unknown source"
    score = int(job.get("suitability_score") or 0)
    status = job.get("status") or "New"
    description = job.get("description") or "No description was saved for this posting."

    with st.container(border=True):
        top_left, top_right = st.columns([4, 1])
        with top_left:
            st.subheader(title)
            st.markdown(
                f"<div class='job-meta'>{company} - {location} - {source}</div>",
                unsafe_allow_html=True,
            )
        with top_right:
            st.markdown(
                f"<div class='summary-label'>Fit</div><div class='summary-value'>{score}</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<span class='score-pill'>{bucket}</span><span class='score-pill'>{status}</span>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<p class='job-description'>{description}</p>", unsafe_allow_html=True)

        if job.get("suitability_reason"):
            st.caption(job["suitability_reason"])

        actions = st.columns([1, 1, 2])
        with actions[0]:
            if job.get("url"):
                st.link_button("Apply / View", job["url"], use_container_width=True)
        with actions[1]:
            new_status = st.selectbox(
                "Status",
                STATUSES,
                index=status_index(status),
                key=f"{key_prefix}_status_{job_id}",
                label_visibility="collapsed",
            )
        with actions[2]:
            if st.button("Save status", key=f"{key_prefix}_save_{job_id}", use_container_width=True):
                save_status(job_id, new_status, job)
                st.success("Status updated.")
                st.rerun()


def render_cards(df: pd.DataFrame, key_prefix: str, limit: int | None = None) -> None:
    rows = df.head(limit) if limit else df
    for _, row in rows.iterrows():
        render_job_card(row, key_prefix)


def dashboard(df: pd.DataFrame) -> None:
    st.title("Job Dashboard")
    today = date.today().isoformat()
    active_statuses = ["Interesting", "Applied", "Follow-up", "Interview"]

    render_summary(
        total=len(df),
        new_today=int((df["date_found"] == today).sum()) if not df.empty else 0,
        active=int(df["status"].isin(active_statuses).sum()) if not df.empty else 0,
        high_fit=int((df["suitability_score"] >= 75).sum()) if not df.empty else 0,
    )

    if df.empty:
        st.info("No jobs yet. Ask Codex or another agent to find Basel jobs and populate the database.")
        return

    chart_df = df.copy()
    chart_df["bucket"] = chart_df["bucket"].fillna("Other")
    status_counts = chart_df["status"].value_counts().to_dict()
    bucket_counts = chart_df["bucket"].value_counts().to_dict()

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Status snapshot")
        for status, count in status_counts.items():
            st.markdown(f"<div class='compact-line'><strong>{status}</strong>: {count}</div>", unsafe_allow_html=True)
    with right:
        st.subheader("Bucket mix")
        for bucket, count in bucket_counts.items():
            st.markdown(f"<div class='compact-line'><strong>{bucket}</strong>: {count}</div>", unsafe_allow_html=True)

    st.subheader("Best next reviews")
    review_queue = chart_df[chart_df["status"].isin(["New", "Interesting"])].sort_values(
        ["suitability_score", "date_found"],
        ascending=[False, False],
    )
    render_cards(review_queue, "dashboard", limit=6)


def jobs_page(df: pd.DataFrame) -> None:
    st.title("Jobs")
    if df.empty:
        st.info("No jobs found yet. Ask the agent to find jobs and add them to SQLite.")
        return

    filtered = apply_filters(df)
    st.caption(f"Showing {len(filtered)} of {len(df)} jobs")
    render_cards(filtered.sort_values(["suitability_score", "date_found"], ascending=[False, False]), "jobs")


def detail_page(df: pd.DataFrame) -> None:
    st.title("Job Detail")
    if df.empty:
        st.info("No jobs available.")
        return

    job_id = st.selectbox(
        "Choose job",
        df["id"].tolist(),
        format_func=lambda value: f"{value} - {df.loc[df['id'] == value, 'title'].iloc[0]}",
    )
    job = get_job(int(job_id))
    if not job:
        st.warning("Job not found.")
        return

    render_job_card(pd.Series(job), "detail")
    st.subheader("Full agent notes")
    st.write("Language requirement")
    st.write(job.get("language_requirement") or "Not specified")


def main() -> None:
    st.markdown(CARD_CSS, unsafe_allow_html=True)
    init_db(DB_PATH)
    df = refresh_jobs()
    page = st.sidebar.radio("Page", ["Dashboard", "Jobs", "Job Detail"])
    st.sidebar.caption(f"Database: {DB_PATH}")
    st.sidebar.caption("Ask the agent to find jobs. Use this app to review and update status.")

    if page == "Dashboard":
        dashboard(df)
    elif page == "Jobs":
        jobs_page(df)
    else:
        detail_page(df)


if __name__ == "__main__":
    main()
