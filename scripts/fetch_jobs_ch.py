from __future__ import annotations

from common import absolute_url, build_search_url, compact_text, get_soup, keywords_for_bucket, load_profile, parser, print_result, save_jobs


SOURCE = "jobs.ch"
BASE_URL = "https://www.jobs.ch"
SEARCH_TEMPLATE = "https://www.jobs.ch/en/vacancies/?term={query}&location={location}"


def fetch(bucket: str = "all", limit: int = 80) -> list[dict]:
    profile = load_profile()
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for keyword in keywords_for_bucket(profile, bucket):
        if len(jobs) >= limit:
            break
        url = build_search_url(SEARCH_TEMPLATE, keyword)
        soup = get_soup(url)
        if soup is None:
            continue

        cards = soup.select("article, div[data-cy*='job'], div[class*='vacancy'], li")
        for card in cards:
            link = card.select_one("a[href*='/en/vacancies/detail/'], a[href*='/vacancies/detail/'], a[href]")
            if not link:
                continue
            job_url = absolute_url(BASE_URL, link.get("href"))
            if job_url in seen_urls or "/vacancies" not in job_url:
                continue
            seen_urls.add(job_url)
            text = compact_text(card.get_text(" "))
            title = compact_text(link.get_text(" ")) or text.split("  ")[0]
            if len(title) < 3:
                continue
            company_node = card.select_one("[class*='company'], [data-cy*='company']")
            location_node = card.select_one("[class*='location'], [data-cy*='location']")
            jobs.append(
                {
                    "title": title,
                    "company": compact_text(company_node.get_text(" ")) if company_node else "",
                    "location": compact_text(location_node.get_text(" ")) if location_node else "Basel",
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
