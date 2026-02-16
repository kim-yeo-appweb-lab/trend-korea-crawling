from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.channels.mk import config
from src.core.exceptions import ParseError
from src.core.models import Article, SearchResult
from src.shared.text_cleaner import clean_text, extract_text_from_html


def parse_search_results(html: str) -> list[SearchResult]:
    """매일경제 검색 결과 목록 파싱"""
    soup = BeautifulSoup(html, "lxml")
    items = soup.select(config.ARTICLE_LIST_SELECTOR)
    results: list[SearchResult] = []

    for item in items:
        link_tag = item.select_one(config.ARTICLE_LINK_SELECTOR)
        if not link_tag:
            continue

        href = link_tag.get("href", "")
        if not href:
            continue

        # 상대 경로인 경우 절대 URL로 변환
        url = urljoin(config.BASE_URL, str(href))

        title_tag = item.select_one(config.ARTICLE_TITLE_SELECTOR)
        title = clean_text(title_tag.get_text()) if title_tag else ""

        if not title:
            continue

        results.append(SearchResult(title=title, url=url))

    return results


def _parse_date(soup: BeautifulSoup) -> datetime | None:
    """기사 발행일 파싱 (실패 시 None 반환)"""
    try:
        date_el = soup.select_one(config.ARTICLE_DATE_SELECTOR)
        if not date_el:
            return None

        date_text = clean_text(date_el.get_text())
        # "입력 : 2026.02.16 18:02" 같은 접두사 제거
        if ":" in date_text and not date_text[0].isdigit():
            date_text = date_text.split(":", 1)[-1].strip()
        for fmt in ("%Y.%m.%d %H:%M:%S", "%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def parse_article(html: str, search_result: SearchResult, keyword: str) -> Article:
    """매일경제 기사 상세 파싱"""
    soup = BeautifulSoup(html, "lxml")

    content_el = soup.select_one(config.ARTICLE_CONTENT_SELECTOR)
    if not content_el:
        raise ParseError(f"본문을 찾을 수 없습니다: {search_result.url}")

    content = extract_text_from_html(content_el)
    if not content:
        raise ParseError(f"본문이 비어있습니다: {search_result.url}")

    published_at = _parse_date(soup)

    return Article(
        title=search_result.title,
        url=search_result.url,
        content=content,
        published_at=published_at,
        channel=config.CHANNEL_NAME,
        keyword=keyword,
    )
