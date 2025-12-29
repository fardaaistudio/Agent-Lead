"""SnappFood scraper with a Google site-search fallback.

SnappFood's site structure can change; this implementation performs a
`site:snappfood.ir` Google search and collects candidate pages. It is a
practical fallback that avoids brittle internal API scraping.
"""
import time
from typing import List

from .playwright_driver import PlaywrightDriver


def search_snappfood(query: str, location: str = "", headless: bool = True, max_results: int = 50) -> List[dict]:
    qp = f"site:snappfood.ir {query} {location if location else ''}"
    driver = PlaywrightDriver(headless=headless)
    page = driver.new_page()
    url = f"https://www.google.com/search?q={qp.replace(' ', '+')}"
    page.goto(url, timeout=60000)
    time.sleep(2)

    results = []
    try:
        links = page.query_selector_all('a')
        seen = set()
        for a in links:
            try:
                href = a.get_attribute('href') or ''
                if 'snappfood.ir' in href and 'url?q=' in href:
                    actual = href.split('url?q=')[1].split('&sa=U')[0]
                    name = a.inner_text().strip() or actual.split('/')[-1]
                    key = (name.lower(), actual)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append({
                        'name': name,
                        'address': '',
                        'source': 'snappfood',
                        'link': actual,
                    })
                    if len(results) >= max_results:
                        break
            except Exception:
                continue
    finally:
        driver.close()

    return results
