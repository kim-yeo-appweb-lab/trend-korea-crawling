from pathlib import Path

import pytest

from src.core.models import SearchResult

# 파서 모듈이 아직 완성되지 않았을 수 있음
maeililbo_parser = pytest.importorskip("src.channels.maeililbo.parser")

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def maeililbo_search_html():
    return (FIXTURES_DIR / "maeililbo_search.html").read_text(encoding="utf-8")


@pytest.fixture
def maeililbo_article_html():
    return (FIXTURES_DIR / "maeililbo_article.html").read_text(encoding="utf-8")


@pytest.fixture
def maeililbo_search_result():
    return SearchResult(
        title="지방 자치 활성화 방안 논의",
        url="https://www.m-i.kr/news/articleView.html?idxno=100001",
    )


class TestMaeililboParseSearchResults:
    """매일일보 검색 결과 파싱 테스트"""

    def test_parse_search_results(self, maeililbo_search_html):
        """검색 결과 HTML에서 SearchResult 리스트 추출"""
        results = maeililbo_parser.parse_search_results(maeililbo_search_html)

        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_result_fields(self, maeililbo_search_html):
        """파싱된 SearchResult의 제목과 URL 검증"""
        results = maeililbo_parser.parse_search_results(maeililbo_search_html)

        assert results[0].title == "지방 자치 활성화 방안 논의"
        assert "articleView" in results[0].url

    def test_empty_html(self):
        """빈 HTML에서는 빈 리스트 반환"""
        results = maeililbo_parser.parse_search_results("<html><body></body></html>")
        assert results == []


class TestMaeililboParseArticle:
    """매일일보 기사 상세 파싱 테스트"""

    def test_parse_article(self, maeililbo_article_html, maeililbo_search_result):
        """기사 HTML에서 Article 생성"""
        article = maeililbo_parser.parse_article(
            maeililbo_article_html, maeililbo_search_result, "자치"
        )

        assert article.title == "지방 자치 활성화 방안 논의"
        assert article.channel == "maeililbo"
        assert article.keyword == "자치"
        assert "지방 자치" in article.content

    def test_parse_article_date(self, maeililbo_article_html, maeililbo_search_result):
        """기사 발행일 파싱 검증"""
        article = maeililbo_parser.parse_article(
            maeililbo_article_html, maeililbo_search_result, "자치"
        )

        assert article.published_at is not None
        assert article.published_at.year == 2024

    def test_parse_article_missing_content(self, maeililbo_search_result):
        """본문이 없는 HTML에서 ParseError 발생"""
        from src.core.exceptions import ParseError

        html = "<html><body><div>본문 없음</div></body></html>"

        with pytest.raises(ParseError):
            maeililbo_parser.parse_article(html, maeililbo_search_result, "자치")
