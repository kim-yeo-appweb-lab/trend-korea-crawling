from urllib.parse import quote

from config.settings import CrawlerSettings
from src.channels.naver_news import config
from src.channels.naver_news.parser import parse_article, parse_search_results
from src.core.base_crawler import BaseCrawler
from src.core.fetch_strategy import FetchStrategy
from src.core.models import Article, CrawlResult, SearchResult


class NaverNewsCrawler(BaseCrawler):
    """네이버 뉴스 크롤러 (StaticFetchStrategy 사용)"""

    def __init__(self, fetch_strategy: FetchStrategy, settings: CrawlerSettings) -> None:
        super().__init__(fetch_strategy, settings)
        self._current_keyword: str = ""

    @property
    def channel_name(self) -> str:
        return config.CHANNEL_NAME

    def build_search_url(self, keyword: str, page: int) -> str:
        # 네이버 검색은 start 파라미터 사용: 1, 11, 21, ...
        encoded_keyword = quote(keyword)
        start = (page - 1) * 10 + 1
        return config.SEARCH_URL_TEMPLATE.format(keyword=encoded_keyword, start=start)

    def parse_article_list(self, html: str) -> list[SearchResult]:
        return parse_search_results(html)

    def parse_article_detail(self, html: str, search_result: SearchResult) -> Article:
        return parse_article(html, search_result, keyword=self._current_keyword)

    async def crawl(self, keyword: str, max_pages: int | None = None) -> CrawlResult:
        # 현재 키워드를 인스턴스에 저장하여 parse_article_detail에서 사용
        self._current_keyword = keyword
        return await super().crawl(keyword, max_pages)
