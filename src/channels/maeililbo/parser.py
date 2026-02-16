import logging
from datetime import datetime

from bs4 import BeautifulSoup

from src.channels.maeililbo.config import (
    ARTICLE_CONTENT_SELECTOR,
    ARTICLE_DATE_SELECTOR,
    ARTICLE_LINK_SELECTOR,
    ARTICLE_LIST_SELECTOR,
    ARTICLE_TITLE_SELECTOR,
    BASE_URL,
    CHANNEL_NAME,
)
from src.core.exceptions import ParseError
from src.core.models import Article, SearchResult
from src.shared.text_cleaner import extract_text_from_html

logger = logging.getLogger(__name__)


def parse_search_results(html: str) -> list[SearchResult]:
    """검색 결과 HTML에서 기사 목록을 파싱한다."""
    soup = BeautifulSoup(html, "lxml")
    items = soup.select(ARTICLE_LIST_SELECTOR)
    results: list[SearchResult] = []

    for item in items:
        link_tag = item.select_one(ARTICLE_LINK_SELECTOR)
        if not link_tag:
            continue

        href = link_tag.get("href", "")
        if not href:
            continue

        # 상대 URL 처리
        url = href if href.startswith("http") else f"{BASE_URL}{href}"

        # 제목 추출
        title_tag = item.select_one(ARTICLE_TITLE_SELECTOR)
        title = title_tag.get_text(strip=True) if title_tag else link_tag.get_text(strip=True)

        if not title:
            continue

        results.append(SearchResult(title=title, url=url))

    return results


def _parse_date(soup: BeautifulSoup) -> datetime | None:
    """기사 상세 페이지에서 발행일을 파싱한다."""
    date_items = soup.select(ARTICLE_DATE_SELECTOR)

    for item in date_items:
        text = item.get_text(strip=True)
        # "승인 2024.01.15 10:30" 같은 형식 처리
        if "승인" in text:
            date_str = text.replace("승인", "").strip()
            for fmt in ("%Y.%m.%d %H:%M", "%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

    return None


def parse_article(html: str, search_result: SearchResult, keyword: str) -> Article:
    """기사 상세 HTML에서 Article 모델을 생성한다."""
    soup = BeautifulSoup(html, "lxml")

    # 본문 추출
    content_el = soup.select_one(ARTICLE_CONTENT_SELECTOR)
    if not content_el:
        raise ParseError(f"본문을 찾을 수 없습니다: {search_result.url}")

    content = extract_text_from_html(content_el)
    if not content:
        raise ParseError(f"본문이 비어있습니다: {search_result.url}")

    # 날짜 파싱
    published_at = _parse_date(soup)

    return Article(
        title=search_result.title,
        url=search_result.url,
        content=content,
        published_at=published_at,
        channel=CHANNEL_NAME,
        keyword=keyword,
    )
