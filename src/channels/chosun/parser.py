# 조선일보 HTML 파싱 모듈

import json
import logging
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.channels.chosun.config import (
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
from src.shared.text_cleaner import clean_text, extract_text_from_html

logger = logging.getLogger(__name__)


def _extract_next_data(html: str) -> dict | None:
    """__NEXT_DATA__ script 태그에서 JSON 데이터 추출"""
    soup = BeautifulSoup(html, "lxml")
    script = soup.select_one("script#__NEXT_DATA__")
    if script and script.string:
        try:
            return json.loads(script.string)
        except json.JSONDecodeError:
            return None
    return None


def _parse_search_results_from_next_data(data: dict) -> list[SearchResult]:
    """__NEXT_DATA__ JSON에서 검색 결과 추출"""
    results: list[SearchResult] = []

    try:
        page_props = data.get("props", {}).get("pageProps", {})
        # 검색 결과 데이터 경로 탐색
        items = (
            page_props.get("searchResult", {}).get("items", [])
            or page_props.get("data", {}).get("items", [])
            or page_props.get("articles", [])
        )

        for item in items:
            title = item.get("title", "").strip()
            url = item.get("url", "") or item.get("link", "")
            snippet = item.get("description", "") or item.get("snippet", "")

            if not title or not url:
                continue

            # 상대 경로인 경우 절대 경로로 변환
            if url.startswith("/"):
                url = urljoin(BASE_URL, url)

            results.append(
                SearchResult(
                    title=clean_text(title),
                    url=url,
                    snippet=clean_text(snippet),
                )
            )
    except (KeyError, TypeError, AttributeError) as e:
        logger.debug("__NEXT_DATA__ 검색 결과 파싱 실패: %s", e)

    return results


def _parse_search_results_from_html(soup: BeautifulSoup) -> list[SearchResult]:
    """CSS 선택자 기반 검색 결과 파싱 (폴백)"""
    results: list[SearchResult] = []
    seen_urls: set[str] = set()
    articles = soup.select(ARTICLE_LIST_SELECTOR)

    for article in articles:
        link = article.select_one(ARTICLE_LINK_SELECTOR)
        title_el = article.select_one(ARTICLE_TITLE_SELECTOR)

        if not link or not title_el:
            continue

        href = link.get("href", "")
        if not href:
            continue

        url = urljoin(BASE_URL, str(href))

        # URL 중복 제거
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = clean_text(title_el.get_text())

        if not title:
            continue

        results.append(SearchResult(title=title, url=url))

    return results


def parse_search_results(html: str) -> list[SearchResult]:
    """검색 결과 HTML에서 기사 목록 추출

    __NEXT_DATA__ JSON 추출을 먼저 시도하고, 실패 시 CSS 선택자로 폴백합니다.
    """
    # __NEXT_DATA__ 우선 시도
    next_data = _extract_next_data(html)
    if next_data:
        results = _parse_search_results_from_next_data(next_data)
        if results:
            logger.debug("__NEXT_DATA__에서 검색 결과 %d건 추출", len(results))
            return results

    # CSS 선택자 폴백
    soup = BeautifulSoup(html, "lxml")
    results = _parse_search_results_from_html(soup)
    logger.debug("CSS 선택자에서 검색 결과 %d건 추출", len(results))
    return results


def _parse_date(date_str: str) -> datetime | None:
    """날짜 문자열을 datetime으로 변환"""
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y.%m.%d %H:%M:%S",
        "%Y.%m.%d %H:%M",
        "%Y.%m.%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def _extract_date_from_next_data(data: dict) -> datetime | None:
    """__NEXT_DATA__에서 발행일 추출"""
    try:
        page_props = data.get("props", {}).get("pageProps", {})
        # 다양한 경로에서 날짜 필드 탐색
        article_data = page_props.get("article", {}) or page_props.get("data", {})
        date_str = (
            article_data.get("publishedAt", "")
            or article_data.get("published_at", "")
            or article_data.get("datePublished", "")
            or article_data.get("inputDate", "")
        )
        if date_str:
            return _parse_date(date_str)
    except (KeyError, TypeError, AttributeError):
        pass
    return None


def _extract_content_from_next_data(data: dict) -> str:
    """__NEXT_DATA__에서 기사 본문 추출"""
    try:
        page_props = data.get("props", {}).get("pageProps", {})
        article_data = page_props.get("article", {}) or page_props.get("data", {})
        # 본문 필드 탐색
        content = (
            article_data.get("content", "")
            or article_data.get("body", "")
            or article_data.get("text", "")
        )

        if content:
            # HTML 태그가 포함된 경우 텍스트만 추출
            if "<" in content and ">" in content:
                soup = BeautifulSoup(content, "lxml")
                return clean_text(soup.get_text(separator="\n"))
            return clean_text(content)
    except (KeyError, TypeError, AttributeError):
        pass
    return ""


def parse_article(html: str, search_result: SearchResult, keyword: str) -> Article:
    """기사 상세 HTML에서 Article 생성

    __NEXT_DATA__ JSON에서 본문 추출을 우선 시도하고,
    실패 시 CSS 선택자(section.article-body)로 폴백합니다.
    """
    content = ""
    published_at: datetime | None = None

    # __NEXT_DATA__ 우선 시도
    next_data = _extract_next_data(html)
    if next_data:
        content = _extract_content_from_next_data(next_data)
        published_at = _extract_date_from_next_data(next_data)

    # 본문이 없으면 CSS 선택자로 폴백
    if not content:
        soup = BeautifulSoup(html, "lxml")
        body_el = soup.select_one(ARTICLE_CONTENT_SELECTOR)
        if body_el:
            content = extract_text_from_html(body_el)

        # 날짜도 CSS에서 추출 시도
        if not published_at:
            date_el = soup.select_one(ARTICLE_DATE_SELECTOR)
            if date_el:
                # meta 태그의 content 또는 datetime 속성 우선
                date_str = (
                    date_el.get("content", "")
                    or date_el.get("datetime", "")
                    or date_el.get_text()
                )
                published_at = _parse_date(str(date_str))

    if not content:
        raise ParseError(f"기사 본문을 추출할 수 없습니다: {search_result.url}")

    return Article(
        title=search_result.title,
        url=search_result.url,
        content=content,
        published_at=published_at,
        channel=CHANNEL_NAME,
        keyword=keyword,
    )
