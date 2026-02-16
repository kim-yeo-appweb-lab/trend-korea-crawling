from playwright.async_api import Browser, Playwright, async_playwright


class BrowserClient:
    """playwright 기반 브라우저 클라이언트"""

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        return self

    async def __aexit__(self, *exc) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None

    async def get(self, url: str, wait_selector: str | None = None, timeout: int = 30000) -> str:
        """URL에서 HTML을 가져온다 (동적 렌더링 포함)"""
        if not self._browser:
            raise RuntimeError("BrowserClient는 async context manager로 사용해야 합니다")

        page = await self._browser.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            if wait_selector:
                await page.wait_for_selector(wait_selector, timeout=timeout)
            else:
                await page.wait_for_timeout(2000)
            return await page.content()
        finally:
            await page.close()
