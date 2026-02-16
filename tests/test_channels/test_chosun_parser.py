from pathlib import Path

import pytest

from src.core.models import SearchResult

# 파서 모듈이 아직 완성되지 않았을 수 있음
chosun_parser = pytest.importorskip("src.channels.chosun.parser")

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def chosun_search_html():
    return (FIXTURES_DIR / "chosun_search.html").read_text(encoding="utf-8")


@pytest.fixture
def chosun_article_html():
    return (FIXTURES_DIR / "chosun_article.html").read_text(encoding="utf-8")


@pytest.fixture
def chosun_search_result():
    return SearchResult(
        title="한미 정상회담 주요 의제 분석",
        url="https://www.chosun.com/politics/2024/01/15/test-chosun-1",
    )


class TestChosunParseSearchResults:
    """조선일보 검색 결과 파싱 테스트"""

    def test_parse_search_results(self, chosun_search_html):
        """검색 결과 HTML에서 SearchResult 리스트 추출 (__NEXT_DATA__ 또는 CSS 폴백)"""
        results = chosun_parser.parse_search_results(chosun_search_html)

        assert len(results) >= 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_result_titles(self, chosun_search_html):
        """파싱된 SearchResult의 제목 검증"""
        results = chosun_parser.parse_search_results(chosun_search_html)
        titles = [r.title for r in results]

        assert any("정상회담" in t for t in titles)

    def test_empty_html(self):
        """빈 HTML에서는 빈 리스트 반환"""
        results = chosun_parser.parse_search_results("<html><body></body></html>")
        assert results == []


class TestChosunParseArticle:
    """조선일보 기사 상세 파싱 테스트"""

    def test_parse_article_from_next_data(self, chosun_article_html, chosun_search_result):
        """__NEXT_DATA__에서 기사 본문 추출"""
        article = chosun_parser.parse_article(
            chosun_article_html, chosun_search_result, "정상회담"
        )

        assert article.title == "한미 정상회담 주요 의제 분석"
        assert article.channel == "chosun"
        assert article.keyword == "정상회담"
        assert "정상" in article.content or "논의" in article.content

    def test_parse_article_date(self, chosun_article_html, chosun_search_result):
        """기사 발행일 파싱 검증"""
        article = chosun_parser.parse_article(
            chosun_article_html, chosun_search_result, "정상회담"
        )

        assert article.published_at is not None
        assert article.published_at.year == 2024

    def test_parse_article_css_fallback(self, chosun_search_result):
        """__NEXT_DATA__가 없을 때 CSS 선택자로 폴백"""
        html = """
        <html><body>
        <section class="article-body">
            <p>CSS 폴백으로 추출한 본문 내용입니다.</p>
        </section>
        </body></html>
        """
        article = chosun_parser.parse_article(html, chosun_search_result, "정상회담")

        assert "폴백" in article.content

    def test_parse_article_missing_content(self, chosun_search_result):
        """본문이 없는 HTML에서 ParseError 발생"""
        from src.core.exceptions import ParseError

        html = "<html><body><div>본문 없음</div></body></html>"

        with pytest.raises(ParseError):
            chosun_parser.parse_article(html, chosun_search_result, "정상회담")
