# 한겨레 HTML 파싱 모듈

import logging
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.channels.hani.config import (
    ARTICLE_CONTENT_SELECTOR,
    ARTICLE_DATE_SELECTOR,
    ARTICLE_LINK_PATTERN,
    BASE_URL,
)
from src.core.exceptions import ParseError
from src.core.models import Article, SearchResult
from src.shared.text_cleaner import extract_text_from_html

logger = logging.getLogger(__name__)


def parse_search_results(html: str) -> list[SearchResult]:
    """검색 결과 HTML에서 기사 목록을 추출한다"""
    soup = BeautifulSoup(html, "lxml")
    results: list[SearchResult] = []
    seen_urls: set[str] = set()

    # href에 '/arti/'가 포함된 모든 a 태그 추출
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if ARTICLE_LINK_PATTERN not in href:
            continue

        # 절대 URL 보장
        url = urljoin(BASE_URL, href) if not href.startswith("http") else href

        # 중복 제거
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = a_tag.get_text(strip=True)
        if not title:
            continue

        results.append(SearchResult(title=title, url=url))

    return results


def _parse_date(soup: BeautifulSoup) -> datetime | None:
    """기사 날짜를 파싱한다. 실패 시 None 반환"""
    date_el = soup.select_one(ARTICLE_DATE_SELECTOR)
    if not date_el:
        return None

    date_text = date_el.get_text(strip=True)

    date_formats = [
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d %H:%M",
        "%Y-%m-%d",
        "%Y.%m.%d",
        "%Y-%m-%dT%H:%M:%S",
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_text, fmt)
        except ValueError:
            continue

    logger.debug("날짜 파싱 실패: %s", date_text)
    return None


def parse_article(html: str, search_result: SearchResult, keyword: str) -> Article:
    """기사 상세 HTML에서 Article 객체를 생성한다"""
    soup = BeautifulSoup(html, "lxml")

    # 본문 추출
    content_el = soup.select_one(ARTICLE_CONTENT_SELECTOR)
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
        channel="hani",
        keyword=keyword,
    )
