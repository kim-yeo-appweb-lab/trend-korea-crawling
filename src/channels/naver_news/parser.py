from datetime import datetime

from bs4 import BeautifulSoup, Tag

from src.channels.naver_news import config
from src.core.exceptions import ParseError
from src.core.models import Article, SearchResult
from src.shared.text_cleaner import clean_text, extract_text_from_html


def _find_news_container(element: Tag, depth: int = 4) -> Tag | None:
    """네이버 뉴스 링크의 상위 뉴스 아이템 컨테이너를 찾는다."""
    parent = element.parent
    for _ in range(depth):
        if parent is None or parent.name == "body":
            return None
        parent = parent.parent
    return parent


def _find_title_in_container(container: Tag) -> tuple[str, str] | None:
    """컨테이너 내에서 뉴스 제목과 원본 URL을 추출한다."""
    for a_tag in container.select("a[href]"):
        href = str(a_tag.get("href", ""))
        text = a_tag.get_text(strip=True)
        # 외부 뉴스 사이트 링크 + 충분한 길이의 텍스트 = 제목
        if (
            href.startswith("http")
            and "naver.com" not in href
            and "search.naver" not in href
            and len(text) > 10
        ):
            return clean_text(text), href
    return None


def parse_search_results(html: str) -> list[SearchResult]:
    """네이버 뉴스 검색 결과 목록 파싱

    n.news.naver.com 링크를 기준으로 상위 컨테이너를 역탐색하여
    뉴스 제목과 네이버 뉴스 URL을 매핑한다.
    """
    soup = BeautifulSoup(html, "lxml")
    naver_links = soup.select(config.NAVER_NEWS_LINK_SELECTOR)
    results: list[SearchResult] = []
    seen_urls: set[str] = set()

    for link in naver_links:
        naver_url = str(link.get("href", ""))
        if not naver_url or naver_url in seen_urls:
            continue

        container = _find_news_container(link, config.NEWS_CONTAINER_DEPTH)
        if container is None:
            continue

        title_info = _find_title_in_container(container)
        if title_info is None:
            continue

        title, _ = title_info
        seen_urls.add(naver_url)
        results.append(SearchResult(title=title, url=naver_url))

    return results


def _parse_date(soup: BeautifulSoup) -> datetime | None:
    """기사 발행일 파싱"""
    try:
        date_el = soup.select_one(config.ARTICLE_DATE_SELECTOR)
        if not date_el:
            return None

        data_date = date_el.get("data-date-time")
        if data_date:
            return datetime.fromisoformat(str(data_date))

        date_text = clean_text(date_el.get_text())
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y.%m.%d. %H:%M"):
            try:
                return datetime.strptime(date_text, fmt)
            except ValueError:
                continue

        return None
    except Exception:
        return None


def parse_article(html: str, search_result: SearchResult, keyword: str) -> Article:
    """네이버 뉴스 기사 상세 파싱"""
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
