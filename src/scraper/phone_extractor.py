import re
import time
from typing import Optional
from playwright.sync_api import TimeoutError as PlaywrightTimeout

from .playwright_driver import PlaywrightDriver


PHONE_RE = re.compile(r"(\+?\d[\d\-\s\(\)\.]{6,}\d)")


def _clean_phone(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[\.\s]+", " ", s)
    return s


def _find_tel_anchor(page) -> Optional[str]:
    try:
        anchors = page.query_selector_all('a[href^="tel:"]')
        for a in anchors:
            href = a.get_attribute('href') or ''
            if href.startswith('tel:'):
                return href.split('tel:')[1]
    except Exception:
        return None
    return None


def _try_click_show_phone(page):
    # Some sites hide phone behind a button/link — try common patterns
    selectors = [
        'button[aria-label*="phone" i]',
        'button[aria-label*="Show phone" i]',
        'button[aria-label*="Copy phone" i]',
        'button[jsaction*="phone"]',
        'button[aria-haspopup="true"]',
    ]
    for sel in selectors:
        try:
            btn = page.query_selector(sel)
            if btn:
                try:
                    btn.click()
                    time.sleep(0.5)
                    return True
                except Exception:
                    continue
        except Exception:
            continue
    return False


def fetch_phone_from_page(url: str, headless: bool = True, timeout: float = 8.0) -> Optional[str]:
    """Best-effort phone extractor.

    Strategy:
    - Open page, look for `tel:` anchors.
    - Try clicking common "show phone" buttons to reveal hidden numbers.
    - Fallback to regex search in visible text.

    Each call creates and closes its own Playwright driver (safe for parallel calls).
    """
    driver = PlaywrightDriver(headless=headless)
    page = driver.new_page()
    try:
        try:
            page.goto(url, timeout=int(timeout * 1000))
        except PlaywrightTimeout:
            # page load timed out — continue, maybe content partially loaded
            pass

        # small wait for dynamic content
        time.sleep(1.0)

        # 1) tel: anchors
        try:
            tel = _find_tel_anchor(page)
            if tel:
                return _clean_phone(tel)
        except Exception:
            pass

        # 2) try clicking reveal buttons
        try:
            _try_click_show_phone(page)
        except Exception:
            pass

        # 3) search for phone-like patterns in visible text
        try:
            body = ''
            try:
                body = page.inner_text('body')
            except Exception:
                try:
                    body = page.content()
                except Exception:
                    body = ''
            if body:
                matches = PHONE_RE.findall(body)
                if matches:
                    # prefer those with + or parentheses
                    for m in matches:
                        if '+' in m or '(' in m:
                            return _clean_phone(m)
                    return _clean_phone(matches[0])
        except Exception:
            pass

        return None
    finally:
        try:
            driver.close()
        except Exception:
            pass
