# 한겨레 크롤러

from urllib.parse import quote

from config.settings import CrawlerSettings
from src.channels.hani.config import CHANNEL_NAME, SEARCH_URL_TEMPLATE
from src.channels.hani.parser import parse_article, parse_search_results
from src.core.base_crawler import BaseCrawler
from src.core.fetch_strategy import FetchStrategy
from src.core.models import Article, CrawlResult, SearchResult


class HaniCrawler(BaseCrawler):
    """한겨레 뉴스 크롤러 (DynamicFetchStrategy 사용 - 검색 페이지 JS 렌더링)"""

    def __init__(self, fetch_strategy: FetchStrategy, settings: CrawlerSettings) -> None:
        super().__init__(fetch_strategy, settings)
        self._current_keyword: str = ""

    @property
    def channel_name(self) -> str:
        return CHANNEL_NAME

    def build_search_url(self, keyword: str, page: int) -> str:
        return SEARCH_URL_TEMPLATE.format(keyword=quote(keyword), page=page)

    def parse_article_list(self, html: str) -> list[SearchResult]:
        return parse_search_results(html)

    def parse_article_detail(self, html: str, search_result: SearchResult) -> Article:
        return parse_article(html, search_result, self._current_keyword)

    async def crawl(self, keyword: str, max_pages: int | None = None) -> CrawlResult:
        self._current_keyword = keyword
        return await super().crawl(keyword, max_pages)
