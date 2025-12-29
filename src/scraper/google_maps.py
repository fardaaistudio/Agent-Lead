"""Google Maps scraper using Playwright.

This is intentionally resilient but may need selector tweaks depending on
Google Maps UI changes. It collects a list of place names, addresses and links.
"""
import time
from typing import List

from .playwright_driver import PlaywrightDriver


def search_google_maps(query: str, location: str = "", headless: bool = True, max_results: int = 50) -> List[dict]:
    qp = f"{query} near {location}" if location else query
    driver = PlaywrightDriver(headless=headless)
    page = driver.new_page()
    url = f"https://www.google.com/maps/search/{qp.replace(' ', '+')}"
    page.goto(url, timeout=60000)
    # small wait for dynamic content
    time.sleep(2)

    results = []
    try:
        # Attempt to find article-role cards first (typical place cards)
        cards = page.query_selector_all('div[role="article"]')
        if not cards:
            # Fallback: collect links that point to /maps/place/
            cards = page.query_selector_all('a[href*="/maps/place/"]')

        seen = set()
        for c in cards[:max_results]:
            try:
                # Try extracting a name and address
                name = ""
                addr = ""
                link = ""
                try:
                    h3 = c.query_selector('h3')
                    if h3:
                        name = h3.inner_text().strip()
                except Exception:
                    pass

                if not name:
                    # fallback to first line of inner_text
                    try:
                        name = c.inner_text().split('\n')[0].strip()
                    except Exception:
                        name = ""

                try:
                    a = c.query_selector('a[href*="/maps/place/"]')
                    if a:
                        link = a.get_attribute('href') or ""
                except Exception:
                    # anchor may be the element itself
                    try:
                        link = c.get_attribute('href') or ""
                    except Exception:
                        link = ""

                try:
                    text = c.inner_text().strip()
                    parts = text.split('\n')
                    if len(parts) > 1:
                        addr = parts[1].strip()
                except Exception:
                    addr = ""

                key = (name.lower(), addr.lower())
                if not name:
                    continue
                if key in seen:
                    continue
                seen.add(key)
                results.append({
                    'name': name,
                    'address': addr,
                    'source': 'google_maps',
                    'link': link,
                })
            except Exception:
                continue
    finally:
        driver.close()

    return results
