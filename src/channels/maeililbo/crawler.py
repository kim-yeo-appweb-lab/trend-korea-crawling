from urllib.parse import quote

from config.settings import CrawlerSettings
from src.channels.maeililbo.config import CHANNEL_NAME, SEARCH_URL_TEMPLATE
from src.channels.maeililbo.parser import parse_article, parse_search_results
from src.core.base_crawler import BaseCrawler
from src.core.fetch_strategy import FetchStrategy
from src.core.models import Article, CrawlResult, SearchResult


class MaeililboCrawler(BaseCrawler):
    """매일일보 크롤러 (StaticFetchStrategy 사용)"""

    def __init__(self, fetch_strategy: FetchStrategy, settings: CrawlerSettings) -> None:
        super().__init__(fetch_strategy, settings)
        self._current_keyword: str = ""

    @property
    def channel_name(self) -> str:
        return CHANNEL_NAME

    def build_search_url(self, keyword: str, page: int) -> str:
        """URL 인코딩된 검색 URL을 생성한다."""
        return SEARCH_URL_TEMPLATE.format(keyword=quote(keyword), page=page)

    def parse_article_list(self, html: str) -> list[SearchResult]:
        return parse_search_results(html)

    def parse_article_detail(self, html: str, search_result: SearchResult) -> Article:
        return parse_article(html, search_result, keyword=self._current_keyword)

    async def crawl(self, keyword: str, max_pages: int | None = None) -> CrawlResult:
        """키워드를 인스턴스에 저장한 후 크롤링을 실행한다."""
        self._current_keyword = keyword
        return await super().crawl(keyword, max_pages)
