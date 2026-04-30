from __future__ import annotations

from common import absolute_url, build_search_url, compact_text, get_soup, keywords_for_bucket, load_profile, parser, print_result, save_jobs


SOURCE = "Indeed"
BASE_URL = "https://ch.indeed.com"
SEARCH_TEMPLATE = "https://ch.indeed.com/jobs?q={query}&l={location}"


def fetch(bucket: str = "all", limit: int = 80) -> list[dict]:
    profile = load_profile()
    jobs: list[dict] = []
    seen_urls: set[str] = set()

    for keyword in keywords_for_bucket(profile, bucket):
        if len(jobs) >= limit:
            break
        soup = get_soup(build_search_url(SEARCH_TEMPLATE, keyword))
        if soup is None:
            continue

        cards = soup.select("div.job_seen_beacon, div[data-jk], td.resultContent")
        for card in cards:
            link = card.select_one("a[href*='/rc/clk'], a[href*='/viewjob'], a[data-jk]")
            if not link:
                continue
            job_url = absolute_url(BASE_URL, link.get("href"))
            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)
            title_node = card.select_one("h2, a span[title], [id^='jobTitle']")
            company_node = card.select_one("[data-testid='company-name'], .companyName")
            location_node = card.select_one("[data-testid='text-location'], .companyLocation")
            jobs.append(
                {
                    "title": compact_text(title_node.get_text(" ")) if title_node else compact_text(link.get_text(" ")),
                    "company": compact_text(company_node.get_text(" ")) if company_node else "",
                    "location": compact_text(location_node.get_text(" ")) if location_node else "Basel",
                    "url": job_url,
                    "description": compact_text(card.get_text(" ")),
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
