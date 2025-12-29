from playwright.sync_api import sync_playwright


class PlaywrightDriver:
    """Simple synchronous Playwright browser manager.

    Use `new_page()` to get a fresh Page. Call `close()` when done.
    """

    def __init__(self, headless: bool = True):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=headless, args=["--no-sandbox"])

    def new_page(self):
        return self.browser.new_page()

    def close(self):
        try:
            self.browser.close()
        finally:
            try:
                self.playwright.stop()
            except Exception:
                pass
