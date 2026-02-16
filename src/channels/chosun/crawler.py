# 조선일보 크롤러

import asyncio
import logging

from config.settings import CrawlerSettings
from src.channels.chosun.config import (
    CHANNEL_NAME,
    DETAIL_WAIT_SELECTOR,
    SEARCH_URL_TEMPLATE,
    SEARCH_WAIT_SELECTOR,
)
from src.channels.chosun.parser import parse_article, parse_search_results
from src.core.base_crawler import BaseCrawler
from src.core.exceptions import CrawlerError
from src.core.fetch_strategy import DynamicFetchStrategy
from src.core.models import Article, CrawlResult, SearchResult

logger = logging.getLogger(__name__)


class ChosunCrawler(BaseCrawler):
    """조선일보 크롤러 (React SPA - DynamicFetchStrategy 필수)"""

    def __init__(
        self, fetch_strategy: DynamicFetchStrategy, settings: CrawlerSettings
    ) -> None:
        super().__init__(fetch_strategy, settings)
        self._current_keyword: str = ""

    @property
    def channel_name(self) -> str:
        return CHANNEL_NAME

    def build_search_url(self, keyword: str, page: int) -> str:
        return SEARCH_URL_TEMPLATE.format(keyword=keyword, page=page)

    def parse_article_list(self, html: str) -> list[SearchResult]:
        return parse_search_results(html)

    def parse_article_detail(self, html: str, search_result: SearchResult) -> Article:
        return parse_article(html, search_result, self._current_keyword)

    async def crawl(self, keyword: str, max_pages: int | None = None) -> CrawlResult:
        """크롤링 실행 (wait_selector를 활용한 동적 렌더링 대기)"""
        self._current_keyword = keyword
        pages = max_pages or self._settings.max_pages
        result = CrawlResult(channel=self.channel_name, keyword=keyword)

        for page in range(1, pages + 1):
            url = self.build_search_url(keyword, page)
            logger.info("[%s] 검색 페이지 %d 요청: %s", self.channel_name, page, url)

            try:
                html = await self._fetch_strategy.fetch(
                    url, wait_selector=SEARCH_WAIT_SELECTOR
                )
                search_results = self.parse_article_list(html)
            except CrawlerError as e:
                error_msg = f"페이지 {page} 검색 실패: {e}"
                logger.warning(error_msg)
                result.errors.append(error_msg)
                continue

            for sr in search_results:
                await asyncio.sleep(self._settings.request_delay)

                try:
                    detail_html = await self._fetch_strategy.fetch(
                        sr.url, wait_selector=DETAIL_WAIT_SELECTOR
                    )
                    article = self.parse_article_detail(detail_html, sr)
                    result.articles.append(article)
                    logger.info("[%s] 기사 수집 완료: %s", self.channel_name, sr.title)
                except CrawlerError as e:
                    error_msg = f"기사 수집 실패 ({sr.url}): {e}"
                    logger.warning(error_msg)
                    result.errors.append(error_msg)

            await asyncio.sleep(self._settings.request_delay)

        logger.info(
            "[%s] 크롤링 완료: 기사 %d건, 에러 %d건",
            self.channel_name,
            len(result.articles),
            len(result.errors),
        )
        return result
