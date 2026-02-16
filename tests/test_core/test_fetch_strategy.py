from unittest.mock import AsyncMock

import pytest

from src.core.exceptions import FetchError
from src.core.fetch_strategy import DynamicFetchStrategy, StaticFetchStrategy


class TestStaticFetchStrategy:
    """StaticFetchStrategy 테스트"""

    async def test_fetch_success(self):
        """mock HttpClient로 fetch 성공"""
        mock_client = AsyncMock()
        mock_client.get.return_value = "<html><body>정적 콘텐츠</body></html>"

        strategy = StaticFetchStrategy(http_client=mock_client)
        result = await strategy.fetch("https://example.com")

        assert result == "<html><body>정적 콘텐츠</body></html>"
        mock_client.get.assert_called_once_with("https://example.com")

    async def test_fetch_failure_raises_fetch_error(self):
        """HttpClient 실패 시 FetchError 발생"""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("네트워크 오류")

        strategy = StaticFetchStrategy(http_client=mock_client)

        with pytest.raises(FetchError, match="정적 페이지 가져오기 실패"):
            await strategy.fetch("https://example.com/fail")


class TestDynamicFetchStrategy:
    """DynamicFetchStrategy 테스트"""

    async def test_fetch_success(self):
        """mock BrowserClient로 fetch 성공"""
        mock_client = AsyncMock()
        mock_client.get.return_value = "<html><body>동적 콘텐츠</body></html>"

        strategy = DynamicFetchStrategy(browser_client=mock_client)
        result = await strategy.fetch("https://example.com")

        assert result == "<html><body>동적 콘텐츠</body></html>"
        mock_client.get.assert_called_once_with("https://example.com", wait_selector=None)

    async def test_fetch_with_wait_selector(self):
        """wait_selector가 BrowserClient에 전달되는지 확인"""
        mock_client = AsyncMock()
        mock_client.get.return_value = "<html><body>렌더링 완료</body></html>"

        strategy = DynamicFetchStrategy(browser_client=mock_client)
        await strategy.fetch("https://example.com", wait_selector="div.content")

        mock_client.get.assert_called_once_with(
            "https://example.com", wait_selector="div.content"
        )

    async def test_fetch_failure_raises_fetch_error(self):
        """BrowserClient 실패 시 FetchError 발생"""
        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("브라우저 오류")

        strategy = DynamicFetchStrategy(browser_client=mock_client)

        with pytest.raises(FetchError, match="동적 페이지 가져오기 실패"):
            await strategy.fetch("https://example.com/fail")
