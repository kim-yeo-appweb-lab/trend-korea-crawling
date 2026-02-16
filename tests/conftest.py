import pytest

from config.settings import CrawlerSettings
from src.core.models import SearchResult


@pytest.fixture
def settings():
    """테스트용 크롤러 설정"""
    return CrawlerSettings(
        max_pages=1,
        request_delay=0.0,
        request_timeout=5,
        output_dir="./test_output",
    )


@pytest.fixture
def sample_search_result():
    """테스트용 검색 결과"""
    return SearchResult(
        title="테스트 기사 제목",
        url="https://example.com/article/123",
        snippet="테스트 기사 요약",
    )
