from __future__ import annotations

from classifier import infer_language_requirement


POSITIVE_TERMS = {
    "Basel location": ["basel", "basel-stadt", "basel-landschaft", "allschwil", "muttenz", "riehen"],
    "English acceptable": ["english", "englisch"],
    "Hospitality/hotel fit": [
        "hotel",
        "hospitality",
        "housekeeping",
        "waiter",
        "waitress",
        "server",
        "service staff",
        "cleaning",
        "restaurant",
        "bar",
        "gastronomie",
    ],
    "Junior or entry-level": ["junior", "entry level", "entry-level", "assistant", "aushilfe", "praktikum"],
    "Data tools match": ["power bi", "sql", "excel", "data analyst", "reporting"],
    "Remote or hybrid": ["remote", "hybrid", "home office", "homeoffice"],
}

NEGATIVE_TERMS = {
    "Fluent German required": [
        "fluent german",
        "native german",
        "deutsch fliessend",
        "fliessend deutsch",
        "muttersprache deutsch",
        "stilsicheres deutsch",
    ],
    "Swiss German required": ["swiss german", "schweizerdeutsch"],
    "Senior role": ["senior", "lead ", "head of", "director", "manager"],
    "Licensed/certified profession": [
        "nurse",
        "pflegefach",
        "doctor",
        "physician",
        "eidg. fachausweis",
        "certified accountant",
    ],
    "Far from Basel": ["zurich", "zürich", "geneva", "genève", "bern", "lausanne", "lugano"],
}


def score_job(job: dict, profile: dict | None = None) -> tuple[int, str, str]:
    text = " ".join(
        [
            str(job.get("title") or ""),
            str(job.get("company") or ""),
            str(job.get("location") or ""),
            str(job.get("description") or ""),
        ]
    ).lower()

    score = 50
    reasons: list[str] = []

    for reason, terms in POSITIVE_TERMS.items():
        if any(term in text for term in terms):
            if reason == "Basel location":
                score += 18
            elif reason == "English acceptable":
                score += 12
            elif reason == "Hospitality/hotel fit":
                score += 12
            elif reason == "Junior or entry-level":
                score += 8
            elif reason == "Data tools match":
                score += 10
            else:
                score += 5
            reasons.append(reason)

    for reason, terms in NEGATIVE_TERMS.items():
        if any(term in text for term in terms):
            if reason in {"Fluent German required", "Swiss German required"}:
                score -= 30
            elif reason == "Far from Basel":
                score -= 18
            else:
                score -= 15
            reasons.append(reason)

    avoid_keywords = (profile or {}).get("avoid_keywords", [])
    matched_avoid = [keyword for keyword in avoid_keywords if keyword.lower() in text]
    if matched_avoid:
        score -= 10
        reasons.append(f"Avoid keywords: {', '.join(matched_avoid[:3])}")

    score = max(0, min(100, score))
    language_requirement = infer_language_requirement(text)
    if not reasons:
        reasons.append("Limited information available; review manually")
    return score, "; ".join(reasons), language_requirement
