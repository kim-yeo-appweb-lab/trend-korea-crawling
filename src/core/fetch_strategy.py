import logging
from abc import ABC, abstractmethod

from src.core.exceptions import FetchError
from src.shared.browser_client import BrowserClient
from src.shared.http_client import HttpClient

logger = logging.getLogger(__name__)


class FetchStrategy(ABC):
    """페이지 가져오기 전략 인터페이스"""

    @abstractmethod
    async def fetch(self, url: str, wait_selector: str | None = None) -> str:
        """URL에서 HTML을 가져온다"""


class StaticFetchStrategy(FetchStrategy):
    """httpx 기반 정적 페이지 가져오기"""

    def __init__(self, http_client: HttpClient) -> None:
        self._client = http_client

    async def fetch(self, url: str, wait_selector: str | None = None) -> str:
        try:
            return await self._client.get(url)
        except Exception as e:
            raise FetchError(f"정적 페이지 가져오기 실패: {url}") from e


class DynamicFetchStrategy(FetchStrategy):
    """playwright 기반 동적 페이지 가져오기"""

    def __init__(self, browser_client: BrowserClient) -> None:
        self._client = browser_client

    async def fetch(self, url: str, wait_selector: str | None = None) -> str:
        try:
            return await self._client.get(url, wait_selector=wait_selector)
        except Exception as e:
            raise FetchError(f"동적 페이지 가져오기 실패: {url}") from e
