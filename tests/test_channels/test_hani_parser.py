from pathlib import Path

import pytest

from src.core.models import SearchResult

# 파서 모듈이 아직 완성되지 않았을 수 있음
hani_parser = pytest.importorskip("src.channels.hani.parser")

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def hani_search_html():
    return (FIXTURES_DIR / "hani_search.html").read_text(encoding="utf-8")


@pytest.fixture
def hani_article_html():
    return (FIXTURES_DIR / "hani_article.html").read_text(encoding="utf-8")


@pytest.fixture
def hani_search_result():
    return SearchResult(
        title="사회 불평등 해소 방안 논의",
        url="https://www.hani.co.kr/arti/society/2024/01/15/1234567.html",
    )


class TestHaniParseSearchResults:
    """한겨레 검색 결과 파싱 테스트"""

    def test_parse_search_results(self, hani_search_html):
        """검색 결과 HTML에서 /arti/ 패턴이 포함된 링크만 추출"""
        results = hani_parser.parse_search_results(hani_search_html)

        # /arti/ 패턴이 있는 링크만 추출 (3번째는 /other/이므로 제외)
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_result_fields(self, hani_search_html):
        """파싱된 SearchResult의 제목과 URL 검증"""
        results = hani_parser.parse_search_results(hani_search_html)

        assert results[0].title == "사회 불평등 해소 방안 논의"
        assert "/arti/" in results[0].url

    def test_duplicate_urls_removed(self):
        """중복 URL이 제거되는지 검증"""
        html = """
        <html><body>
        <a href="https://www.hani.co.kr/arti/test/1">제목1</a>
        <a href="https://www.hani.co.kr/arti/test/1">제목1 중복</a>
        <a href="https://www.hani.co.kr/arti/test/2">제목2</a>
        </body></html>
        """
        results = hani_parser.parse_search_results(html)
        assert len(results) == 2

    def test_empty_html(self):
        """빈 HTML에서는 빈 리스트 반환"""
        results = hani_parser.parse_search_results("<html><body></body></html>")
        assert results == []


class TestHaniParseArticle:
    """한겨레 기사 상세 파싱 테스트"""

    def test_parse_article(self, hani_article_html, hani_search_result):
        """기사 HTML에서 Article 생성"""
        article = hani_parser.parse_article(hani_article_html, hani_search_result, "불평등")

        assert article.title == "사회 불평등 해소 방안 논의"
        assert article.channel == "hani"
        assert article.keyword == "불평등"
        assert "불평등" in article.content

    def test_parse_article_date(self, hani_article_html, hani_search_result):
        """기사 발행일 파싱 검증"""
        article = hani_parser.parse_article(hani_article_html, hani_search_result, "불평등")

        assert article.published_at is not None
        assert article.published_at.year == 2024
        assert article.published_at.month == 1
        assert article.published_at.day == 15

    def test_parse_article_missing_content(self, hani_search_result):
        """본문이 없는 HTML에서 ParseError 발생"""
        from src.core.exceptions import ParseError

        html = "<html><body><div>본문 없음</div></body></html>"

        with pytest.raises(ParseError):
            hani_parser.parse_article(html, hani_search_result, "불평등")
