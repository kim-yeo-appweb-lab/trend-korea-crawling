from pathlib import Path

import pytest

from src.core.models import SearchResult

# 파서 모듈이 아직 완성되지 않았을 수 있음
naver_parser = pytest.importorskip("src.channels.naver_news.parser")

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def naver_search_html():
    return (FIXTURES_DIR / "naver_search.html").read_text(encoding="utf-8")


@pytest.fixture
def naver_article_html():
    return (FIXTURES_DIR / "naver_article.html").read_text(encoding="utf-8")


@pytest.fixture
def naver_search_result():
    return SearchResult(
        title="AI 산업 전망 보고서",
        url="https://n.news.naver.com/article/001/0001234567",
    )


class TestNaverParseSearchResults:
    """네이버 뉴스 검색 결과 파싱 테스트"""

    def test_parse_search_results(self, naver_search_html):
        """검색 결과 HTML에서 네이버 뉴스 링크가 있는 항목만 추출"""
        results = naver_parser.parse_search_results(naver_search_html)

        # 3번째 항목은 n.news.naver.com 링크가 없으므로 2건만 추출
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_result_naver_link(self, naver_search_html):
        """네이버 뉴스 링크(n.news.naver.com)가 URL로 사용되는지 검증"""
        results = naver_parser.parse_search_results(naver_search_html)

        assert "n.news.naver.com" in results[0].url
        assert "n.news.naver.com" in results[1].url

    def test_search_result_titles(self, naver_search_html):
        """파싱된 제목 검증"""
        results = naver_parser.parse_search_results(naver_search_html)

        assert results[0].title == "AI 산업 전망 보고서"
        assert results[1].title == "스타트업 투자 동향"

    def test_empty_html(self):
        """빈 HTML에서는 빈 리스트 반환"""
        results = naver_parser.parse_search_results("<html><body></body></html>")
        assert results == []


class TestNaverParseArticle:
    """네이버 뉴스 기사 상세 파싱 테스트"""

    def test_parse_article(self, naver_article_html, naver_search_result):
        """기사 HTML에서 Article 생성"""
        article = naver_parser.parse_article(naver_article_html, naver_search_result, "AI")

        assert article.title == "AI 산업 전망 보고서"
        assert article.channel == "naver_news"
        assert article.keyword == "AI"
        assert "인공지능" in article.content

    def test_parse_article_date(self, naver_article_html, naver_search_result):
        """data-date-time 속성에서 발행일 파싱 검증"""
        article = naver_parser.parse_article(naver_article_html, naver_search_result, "AI")

        assert article.published_at is not None
        assert article.published_at.year == 2024
        assert article.published_at.month == 1
        assert article.published_at.day == 15

    def test_parse_article_missing_content(self, naver_search_result):
        """본문이 없는 HTML에서 ParseError 발생"""
        from src.core.exceptions import ParseError

        html = "<html><body><div>본문 없음</div></body></html>"

        with pytest.raises(ParseError):
            naver_parser.parse_article(html, naver_search_result, "AI")
