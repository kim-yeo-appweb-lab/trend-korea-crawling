import asyncio
import logging
from abc import ABC, abstractmethod

from config.settings import CrawlerSettings
from src.core.exceptions import CrawlerError
from src.core.fetch_strategy import FetchStrategy
from src.core.models import Article, CrawlResult, SearchResult

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """크롤러 기본 클래스 (Template Method 패턴)"""

    def __init__(self, fetch_strategy: FetchStrategy, settings: CrawlerSettings) -> None:
        self._fetch_strategy = fetch_strategy
        self._settings = settings

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """채널 이름"""

    @abstractmethod
    def build_search_url(self, keyword: str, page: int) -> str:
        """검색 URL 생성"""

    @abstractmethod
    def parse_article_list(self, html: str) -> list[SearchResult]:
        """검색 결과 목록 파싱"""

    @abstractmethod
    def parse_article_detail(self, html: str, search_result: SearchResult) -> Article:
        """기사 상세 페이지 파싱"""

    async def crawl(self, keyword: str, max_pages: int | None = None) -> CrawlResult:
        """전체 크롤링 흐름 실행"""
        pages = max_pages or self._settings.max_pages
        result = CrawlResult(channel=self.channel_name, keyword=keyword)

        for page in range(1, pages + 1):
            url = self.build_search_url(keyword, page)
            logger.info("[%s] 검색 페이지 %d 요청: %s", self.channel_name, page, url)

            try:
                html = await self._fetch_strategy.fetch(url)
                search_results = self.parse_article_list(html)
            except CrawlerError as e:
                error_msg = f"페이지 {page} 검색 실패: {e}"
                logger.warning(error_msg)
                result.errors.append(error_msg)
                continue

            for sr in search_results:
                await asyncio.sleep(self._settings.request_delay)

                try:
                    detail_html = await self._fetch_strategy.fetch(sr.url)
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
