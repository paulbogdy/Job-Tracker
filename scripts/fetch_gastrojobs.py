from __future__ import annotations

from common import absolute_url, build_search_url, compact_text, get_soup, keywords_for_bucket, load_profile, parser, print_result, save_jobs


SOURCE = "Gastrojobs"
BASE_URL = "https://www.gastrojobs.ch"
SEARCH_TEMPLATE = "https://www.gastrojobs.ch/en/jobs/?query={query}&location={location}"


def fetch(bucket: str = "hospitality", limit: int = 80) -> list[dict]:
    profile = load_profile()
    jobs: list[dict] = []
    seen_urls: set[str] = set()
    keywords = keywords_for_bucket(profile, bucket) or keywords_for_bucket(profile, "hospitality")

    for keyword in keywords:
        if len(jobs) >= limit:
            break
        soup = get_soup(build_search_url(SEARCH_TEMPLATE, keyword))
        if soup is None:
            continue
        cards = soup.select("article, div[class*='job'], li[class*='job']")
        for card in cards:
            link = card.select_one("a[href*='/job/'], a[href*='/jobs/'], a[href]")
            if not link:
                continue
            job_url = absolute_url(BASE_URL, link.get("href"))
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)
            text = compact_text(card.get_text(" "))
            jobs.append(
                {
                    "title": compact_text(link.get_text(" ")) or text[:120],
                    "company": "",
                    "location": "Basel",
                    "url": job_url,
                    "description": text,
                }
            )
            if len(jobs) >= limit:
                break
    return jobs


def main() -> None:
    args = parser().parse_args()
    profile = load_profile()
    result = save_jobs(fetch(args.bucket, args.limit), profile, SOURCE)
    print_result(result)


if __name__ == "__main__":
    main()
