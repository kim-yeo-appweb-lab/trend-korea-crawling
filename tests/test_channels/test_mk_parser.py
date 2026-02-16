from pathlib import Path

import pytest

from src.core.models import SearchResult

# 파서 모듈이 아직 완성되지 않았을 수 있음
mk_parser = pytest.importorskip("src.channels.mk.parser")

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def mk_search_html():
    return (FIXTURES_DIR / "mk_search.html").read_text(encoding="utf-8")


@pytest.fixture
def mk_article_html():
    return (FIXTURES_DIR / "mk_article.html").read_text(encoding="utf-8")


@pytest.fixture
def mk_search_result():
    return SearchResult(
        title="AI 기술 발전과 경제 성장",
        url="https://www.mk.co.kr/economy/2024/01/15/test-article-1",
    )


class TestMkParseSearchResults:
    """매일경제 검색 결과 파싱 테스트"""

    def test_parse_search_results(self, mk_search_html):
        """검색 결과 HTML에서 SearchResult 리스트 추출"""
        results = mk_parser.parse_search_results(mk_search_html)

        # 빈 링크 기사는 제외되어 2건만 파싱
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_result_fields(self, mk_search_html):
        """파싱된 SearchResult의 제목과 URL 검증"""
        results = mk_parser.parse_search_results(mk_search_html)

        assert results[0].title == "AI 기술 발전과 경제 성장"
        # 상대 경로가 절대 URL로 변환되어야 함
        assert "mk.co.kr" in results[0].url

    def test_empty_html(self):
        """빈 HTML에서는 빈 리스트 반환"""
        results = mk_parser.parse_search_results("<html><body></body></html>")
        assert results == []


class TestMkParseArticle:
    """매일경제 기사 상세 파싱 테스트"""

    def test_parse_article(self, mk_article_html, mk_search_result):
        """기사 HTML에서 Article 생성"""
        article = mk_parser.parse_article(mk_article_html, mk_search_result, "AI")

        assert article.title == "AI 기술 발전과 경제 성장"
        assert article.channel == "mk"
        assert article.keyword == "AI"
        assert "인공지능" in article.content
        assert article.url == mk_search_result.url

    def test_parse_article_date(self, mk_article_html, mk_search_result):
        """기사 발행일 파싱 검증"""
        article = mk_parser.parse_article(mk_article_html, mk_search_result, "AI")

        assert article.published_at is not None
        assert article.published_at.year == 2024
        assert article.published_at.month == 1
        assert article.published_at.day == 15

    def test_parse_article_missing_content(self, mk_search_result):
        """본문이 없는 HTML에서 ParseError 발생"""
        from src.core.exceptions import ParseError

        html = "<html><body><div>본문 없음</div></body></html>"

        with pytest.raises(ParseError):
            mk_parser.parse_article(html, mk_search_result, "AI")
