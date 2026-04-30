from __future__ import annotations


BUCKET_KEYWORDS = {
    "Hospitality": [
        "waiter",
        "waitress",
        "server",
        "service",
        "restaurant",
        "bar",
        "cafe",
        "catering",
        "gastronomie",
        "servicekraft",
        "servicemitarbeiter",
    ],
    "Hotels/Housekeeping": [
        "hotel",
        "housekeeping",
        "housekeeper",
        "room attendant",
        "cleaning",
        "cleaner",
        "reinigung",
        "zimmer",
        "etage",
        "hauswirtschaft",
    ],
    "Admin/Customer Support": [
        "admin",
        "assistant",
        "reception",
        "front desk",
        "customer support",
        "customer service",
        "office",
        "backoffice",
        "rezeption",
    ],
    "Retail/Events": [
        "retail",
        "sales assistant",
        "shop",
        "store",
        "event",
        "messe",
        "verkauf",
        "promoter",
    ],
    "Data/Marketing": [
        "data",
        "analyst",
        "power bi",
        "sql",
        "excel",
        "marketing",
        "social media",
        "content",
        "crm",
    ],
}


def classify_job(title: str, description: str = "") -> str:
    text = f"{title} {description}".lower()
    scores: dict[str, int] = {}
    for bucket, keywords in BUCKET_KEYWORDS.items():
        scores[bucket] = sum(1 for keyword in keywords if keyword in text)
    best_bucket, best_score = max(scores.items(), key=lambda item: item[1])
    return best_bucket if best_score > 0 else "Other"


def infer_language_requirement(text: str) -> str:
    lower = text.lower()
    if "swiss german" in lower or "schweizerdeutsch" in lower:
        return "Swiss German required"
    if any(term in lower for term in ["fluent german", "native german", "deutsch fliessend", "fliessend deutsch"]):
        return "Fluent German required"
    if any(term in lower for term in ["good german", "gute deutsch", "deutschkenntnisse", "german required"]):
        return "German likely required"
    if any(term in lower for term in ["english", "englisch"]):
        return "English mentioned"
    if any(term in lower for term in ["romanian", "rumänisch", "rumaenisch"]):
        return "Romanian mentioned"
    return "Not specified"
