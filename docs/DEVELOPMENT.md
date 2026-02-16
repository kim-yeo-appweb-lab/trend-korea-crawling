# 개발 가이드

이 문서는 trend-korea-crawling 프로젝트의 개발 환경 설정, 새 채널 추가 방법, 테스트 작성법, 코드 스타일 규칙을 다룹니다.

---

## 목차

1. [개발 환경 설정](#개발-환경-설정)
2. [새 채널 추가 방법](#새-채널-추가-방법)
3. [테스트](#테스트)
4. [코드 스타일](#코드-스타일)
5. [디버깅 팁](#디버깅-팁)

---

## 개발 환경 설정

### 요구 사항

- Python 3.12 이상
- pip (최신 버전 권장)

### 설치

```bash
# 저장소 클론
git clone <repository-url>
cd trend-korea-crawling

# 개발 의존성을 포함하여 설치 (editable 모드)
pip install -e ".[dev]"

# playwright 브라우저 설치 (동적 크롤링 채널에 필요)
playwright install chromium
```

`pip install -e ".[dev]"`는 프로젝트를 editable 모드로 설치하면서 `dev` 그룹의 의존성(`pytest`, `pytest-asyncio`, `ruff`)도 함께 설치합니다.

### 핵심 의존성 요약

| 패키지 | 용도 |
|---|---|
| `httpx[http2]` | 정적 페이지 HTTP 요청 (HTTP/2 지원) |
| `beautifulsoup4` + `lxml` | HTML 파싱 |
| `playwright` | 동적 페이지 렌더링 (JavaScript 실행 필요 시) |
| `pydantic` / `pydantic-settings` | 데이터 모델 및 설정 관리 |
| `pytest` + `pytest-asyncio` | 테스트 프레임워크 |
| `ruff` | 린팅 및 포매팅 |

---

## 새 채널 추가 방법

이 프로젝트는 Template Method 패턴을 사용합니다. `BaseCrawler`가 크롤링 흐름을 정의하고, 각 채널은 검색 URL 생성, 목록 파싱, 기사 파싱만 구현하면 됩니다.

아래 가이드는 **매일일보(maeililbo)**를 참고 템플릿으로 사용합니다.

### 단계 1: 채널 디렉토리 생성

```
src/channels/{channel_name}/
    __init__.py
    config.py
    parser.py
    crawler.py
```

예시 (채널 이름이 `mypress`라고 가정):

```bash
mkdir -p src/channels/mypress
touch src/channels/mypress/__init__.py
touch src/channels/mypress/config.py
touch src/channels/mypress/parser.py
touch src/channels/mypress/crawler.py
```

### 단계 2: config.py 작성

채널 고유 상수(이름, URL, CSS 셀렉터)를 정의합니다.

```python
# src/channels/mypress/config.py

CHANNEL_NAME = "mypress"
BASE_URL = "https://www.mypress.co.kr"
SEARCH_URL_TEMPLATE = "https://www.mypress.co.kr/search?q={keyword}&page={page}"

# 검색 결과 목록 셀렉터
ARTICLE_LIST_SELECTOR = "div.search-result-item"
ARTICLE_LINK_SELECTOR = "a.article-link"
ARTICLE_TITLE_SELECTOR = "h3.article-title"

# 기사 상세 페이지 셀렉터
ARTICLE_CONTENT_SELECTOR = "div.article-body"
ARTICLE_DATE_SELECTOR = "span.publish-date"
```

셀렉터는 대상 사이트의 HTML 구조를 분석하여 작성합니다. 브라우저 개발자 도구(F12)에서 요소를 확인한 뒤 CSS 셀렉터를 결정합니다.

### 단계 3: parser.py 작성

두 가지 핵심 함수를 구현합니다:

- `parse_search_results(html)` -- 검색 결과 HTML에서 `SearchResult` 리스트 추출
- `parse_article(html, search_result, keyword)` -- 기사 상세 HTML에서 `Article` 모델 생성

```python
# src/channels/mypress/parser.py

import logging
from datetime import datetime

from bs4 import BeautifulSoup

from src.channels.mypress.config import (
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

        url = href if href.startswith("http") else f"{BASE_URL}{href}"

        title_tag = item.select_one(ARTICLE_TITLE_SELECTOR)
        title = title_tag.get_text(strip=True) if title_tag else ""

        if not title:
            continue

        results.append(SearchResult(title=title, url=url))

    return results


def _parse_date(soup: BeautifulSoup) -> datetime | None:
    """기사 상세 페이지에서 발행일을 파싱한다."""
    date_el = soup.select_one(ARTICLE_DATE_SELECTOR)
    if not date_el:
        return None

    text = date_el.get_text(strip=True)
    # 사이트의 날짜 형식에 맞게 파싱 로직 작성
    for fmt in ("%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    return None


def parse_article(html: str, search_result: SearchResult, keyword: str) -> Article:
    """기사 상세 HTML에서 Article 모델을 생성한다."""
    soup = BeautifulSoup(html, "lxml")

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
        channel=CHANNEL_NAME,
        keyword=keyword,
    )
```

주요 포인트:

- `parse_search_results`는 빈 HTML이나 셀렉터에 매칭되지 않는 HTML에 대해 빈 리스트를 반환해야 합니다 (예외를 발생시키지 않음).
- `parse_article`은 본문을 찾을 수 없을 때 `ParseError`를 발생시킵니다. `BaseCrawler.crawl()`이 이 예외를 잡아 에러 목록에 기록합니다.
- `_parse_date` 헬퍼는 실패 시 `None`을 반환합니다. 날짜 파싱 실패가 전체 크롤링을 중단시키지 않도록 설계되어 있습니다.

### 단계 4: crawler.py 작성

`BaseCrawler`를 상속하여 추상 메서드를 구현합니다.

```python
# src/channels/mypress/crawler.py

from urllib.parse import quote

from config.settings import CrawlerSettings
from src.channels.mypress.config import CHANNEL_NAME, SEARCH_URL_TEMPLATE
from src.channels.mypress.parser import parse_article, parse_search_results
from src.core.base_crawler import BaseCrawler
from src.core.fetch_strategy import FetchStrategy
from src.core.models import Article, CrawlResult, SearchResult


class MyPressCrawler(BaseCrawler):
    """MyPress 크롤러"""

    def __init__(self, fetch_strategy: FetchStrategy, settings: CrawlerSettings) -> None:
        super().__init__(fetch_strategy, settings)
        self._current_keyword: str = ""

    @property
    def channel_name(self) -> str:
        return CHANNEL_NAME

    def build_search_url(self, keyword: str, page: int) -> str:
        return SEARCH_URL_TEMPLATE.format(keyword=quote(keyword), page=page)

    def parse_article_list(self, html: str) -> list[SearchResult]:
        return parse_search_results(html)

    def parse_article_detail(self, html: str, search_result: SearchResult) -> Article:
        return parse_article(html, search_result, keyword=self._current_keyword)

    async def crawl(self, keyword: str, max_pages: int | None = None) -> CrawlResult:
        self._current_keyword = keyword
        return await super().crawl(keyword, max_pages)
```

`BaseCrawler`가 요구하는 4가지 추상 멤버:

| 추상 멤버 | 타입 | 설명 |
|---|---|---|
| `channel_name` | `property` | 채널 식별자 문자열 |
| `build_search_url(keyword, page)` | `method` | 검색 페이지 URL 생성 |
| `parse_article_list(html)` | `method` | 검색 결과 HTML -> `list[SearchResult]` |
| `parse_article_detail(html, search_result)` | `method` | 기사 HTML -> `Article` |

### 단계 5: \_\_init\_\_.py에 exports 추가

```python
# src/channels/mypress/__init__.py

from src.channels.mypress.crawler import MyPressCrawler

__all__ = ["MyPressCrawler"]
```

### 단계 6: channel_registry.py에 채널 등록

`src/pipeline/channel_registry.py`의 `CHANNEL_MAP`에 새 채널을 추가합니다.

```python
CHANNEL_MAP: dict[str, tuple[str, str, str]] = {
    # 기존 채널들 ...
    "maeililbo": ("src.channels.maeililbo.crawler", "MaeililboCrawler", "static"),
    # 새 채널 추가
    "mypress": ("src.channels.mypress.crawler", "MyPressCrawler", "static"),
}
```

세 번째 값은 fetch 전략 타입입니다:

| 전략 | 값 | 사용 조건 |
|---|---|---|
| 정적 (httpx) | `"static"` | 서버 사이드 렌더링 페이지, JavaScript 실행이 필요 없는 경우 |
| 동적 (playwright) | `"dynamic"` | SPA, JavaScript로 콘텐츠를 로드하는 페이지 |

대상 사이트에서 JavaScript를 비활성화한 후에도 콘텐츠가 정상 노출되면 `"static"`, 그렇지 않으면 `"dynamic"`을 선택합니다.

### 단계 7: 테스트 작성

테스트는 [테스트](#테스트) 섹션에서 자세히 설명합니다. 최소한 파서에 대한 단위 테스트를 작성해야 합니다.

---

## 테스트

### 테스트 실행

```bash
# 전체 테스트 실행
pytest tests/

# 특정 채널만 테스트
pytest tests/test_channels/test_mypress_parser.py

# 특정 테스트 클래스만 실행
pytest tests/test_channels/test_mypress_parser.py::TestMyPressParseSearchResults

# 특정 테스트 함수만 실행
pytest tests/test_channels/test_mypress_parser.py::TestMyPressParseArticle::test_parse_article

# 상세 출력
pytest tests/ -v
```

`pyproject.toml`에 `asyncio_mode = "auto"`가 설정되어 있으므로 `async def` 테스트 함수에 별도의 `@pytest.mark.asyncio` 데코레이터가 필요 없습니다.

### HTML fixture 기반 단위 테스트

이 프로젝트의 파서 테스트는 **실제 HTML 스냅샷을 fixture 파일로 저장**하고 이를 기반으로 파싱 로직을 검증합니다. 네트워크 요청 없이 순수 파싱 로직만 테스트할 수 있어 빠르고 안정적입니다.

#### fixture 파일 구조

```
tests/
    fixtures/
        mypress_search.html     # 검색 결과 페이지 HTML 스냅샷
        mypress_article.html    # 기사 상세 페이지 HTML 스냅샷
    test_channels/
        test_mypress_parser.py
    conftest.py                 # 공통 fixture
```

#### fixture 파일 작성법

1. 브라우저에서 대상 페이지에 접속합니다.
2. 개발자 도구(F12) > Elements 탭에서 `<html>` 요소를 우클릭 > "Copy" > "Copy outerHTML"을 선택합니다.
3. 복사한 HTML을 `tests/fixtures/{channel_name}_search.html` 또는 `{channel_name}_article.html`로 저장합니다.
4. 민감 정보(광고 스크립트, 개인정보 등)가 포함된 부분은 제거합니다.
5. 파서가 사용하는 셀렉터에 매칭되는 요소가 포함되어 있는지 확인합니다.

fixture 파일에는 전체 페이지 HTML을 저장하되, 파서 테스트에 필요한 핵심 요소가 반드시 포함되어야 합니다.

#### conftest.py 공통 fixture

`tests/conftest.py`에는 전체 테스트에서 공통으로 사용하는 fixture가 정의되어 있습니다:

```python
# tests/conftest.py

import pytest

from config.settings import CrawlerSettings
from src.core.models import SearchResult


@pytest.fixture
def settings():
    """테스트용 크롤러 설정"""
    return CrawlerSettings(
        max_pages=1,
        request_delay=0.0,
        request_timeout=5,
        output_dir="./test_output",
    )


@pytest.fixture
def sample_search_result():
    """테스트용 검색 결과"""
    return SearchResult(
        title="테스트 기사 제목",
        url="https://example.com/article/123",
        snippet="테스트 기사 요약",
    )
```

#### 테스트 파일 작성 예시

매일일보 파서 테스트(`tests/test_channels/test_maeililbo_parser.py`)를 참고하여 새 채널의 테스트를 작성합니다:

```python
# tests/test_channels/test_mypress_parser.py

from pathlib import Path

import pytest

from src.core.models import SearchResult

mypress_parser = pytest.importorskip("src.channels.mypress.parser")

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def mypress_search_html():
    return (FIXTURES_DIR / "mypress_search.html").read_text(encoding="utf-8")


@pytest.fixture
def mypress_article_html():
    return (FIXTURES_DIR / "mypress_article.html").read_text(encoding="utf-8")


@pytest.fixture
def mypress_search_result():
    return SearchResult(
        title="테스트 기사 제목",
        url="https://www.mypress.co.kr/article/12345",
    )


class TestMyPressParseSearchResults:
    """검색 결과 파싱 테스트"""

    def test_parse_search_results(self, mypress_search_html):
        """검색 결과 HTML에서 SearchResult 리스트 추출"""
        results = mypress_parser.parse_search_results(mypress_search_html)

        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_result_fields(self, mypress_search_html):
        """파싱된 SearchResult의 제목과 URL 검증"""
        results = mypress_parser.parse_search_results(mypress_search_html)

        assert results[0].title  # 빈 문자열이 아닌지 확인
        assert results[0].url.startswith("http")

    def test_empty_html(self):
        """빈 HTML에서는 빈 리스트 반환"""
        results = mypress_parser.parse_search_results("<html><body></body></html>")
        assert results == []


class TestMyPressParseArticle:
    """기사 상세 파싱 테스트"""

    def test_parse_article(self, mypress_article_html, mypress_search_result):
        """기사 HTML에서 Article 생성"""
        article = mypress_parser.parse_article(
            mypress_article_html, mypress_search_result, "테스트키워드"
        )

        assert article.title == "테스트 기사 제목"
        assert article.channel == "mypress"
        assert article.keyword == "테스트키워드"
        assert len(article.content) > 0

    def test_parse_article_date(self, mypress_article_html, mypress_search_result):
        """기사 발행일 파싱 검증"""
        article = mypress_parser.parse_article(
            mypress_article_html, mypress_search_result, "테스트키워드"
        )

        assert article.published_at is not None

    def test_parse_article_missing_content(self, mypress_search_result):
        """본문이 없는 HTML에서 ParseError 발생"""
        from src.core.exceptions import ParseError

        html = "<html><body><div>본문 없음</div></body></html>"

        with pytest.raises(ParseError):
            mypress_parser.parse_article(html, mypress_search_result, "테스트키워드")
```

테스트 작성 시 확인해야 할 핵심 케이스:

| 테스트 대상 | 검증 내용 |
|---|---|
| `parse_search_results` | 정상 HTML에서 올바른 개수의 `SearchResult` 추출 |
| `parse_search_results` | 각 결과의 `title`과 `url` 필드 검증 |
| `parse_search_results` | 빈 HTML 입력 시 빈 리스트 반환 |
| `parse_article` | 정상 HTML에서 `Article` 모델 생성 |
| `parse_article` | `channel`, `keyword` 필드가 올바르게 설정되는지 확인 |
| `parse_article` | 발행일(`published_at`) 파싱 검증 |
| `parse_article` | 본문 없는 HTML에서 `ParseError` 발생 |

---

## 코드 스타일

### ruff 린팅 및 포매팅

이 프로젝트는 `ruff`를 린터 겸 포매터로 사용합니다. 설정은 `pyproject.toml`에 정의되어 있습니다:

```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
```

활성화된 규칙:

| 코드 | 설명 |
|---|---|
| `E` | pycodestyle 에러 (들여쓰기, 공백 등) |
| `F` | pyflakes (미사용 import, 정의되지 않은 변수 등) |
| `I` | isort (import 정렬) |
| `N` | pep8-naming (네이밍 컨벤션) |
| `W` | pycodestyle 경고 |

```bash
# 린팅 검사
ruff check .

# 자동 수정 가능한 문제 수정
ruff check --fix .

# 포매팅 검사
ruff format --check .

# 포매팅 적용
ruff format .
```

### import 순서

`ruff`의 `I` 규칙(isort)에 의해 import 순서가 자동 정렬됩니다. 기본 순서:

```python
# 1. 표준 라이브러리
import logging
from datetime import datetime

# 2. 서드파티 패키지
from bs4 import BeautifulSoup

# 3. 프로젝트 내부 모듈
from src.channels.mypress.config import CHANNEL_NAME
from src.core.exceptions import ParseError
from src.core.models import Article, SearchResult
```

### 타입 힌트

- 함수 매개변수와 반환 타입에 타입 힌트를 사용합니다.
- Python 3.11+ 문법을 사용합니다 (`list[str]`, `dict[str, int]`, `str | None`).
- `typing` 모듈의 `List`, `Dict`, `Optional` 대신 내장 타입을 사용합니다.

```python
# 올바른 예
def parse_search_results(html: str) -> list[SearchResult]: ...
def _parse_date(soup: BeautifulSoup) -> datetime | None: ...

# 피해야 할 예
from typing import List, Optional
def parse_search_results(html: str) -> List[SearchResult]: ...
def _parse_date(soup: BeautifulSoup) -> Optional[datetime]: ...
```

---

## 디버깅 팁

### 로그 레벨 조정

크롤링 과정을 상세히 확인하려면 로그 레벨을 `DEBUG`로 설정합니다:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

또는 특정 모듈만 디버그 로그를 확인할 수 있습니다:

```python
import logging

logging.getLogger("src.channels.mypress").setLevel(logging.DEBUG)
```

### 단일 채널 테스트 실행

개발 중인 채널만 빠르게 테스트하려면:

```bash
# 파서 단위 테스트만 실행
pytest tests/test_channels/test_mypress_parser.py -v

# 특정 테스트만 실행
pytest tests/test_channels/test_mypress_parser.py::TestMyPressParseSearchResults::test_parse_search_results -v
```

### playwright 헤드풀 모드

동적 크롤링 채널을 디버깅할 때, 실제 브라우저 창을 띄워서 동작을 확인할 수 있습니다. `config/settings.py`의 `BrowserSettings`에서 `headless` 옵션을 제어합니다:

```python
class BrowserSettings(BaseSettings):
    model_config = {"env_prefix": "BROWSER_"}
    headless: bool = True
```

환경 변수로 설정을 변경합니다:

```bash
# 브라우저 창을 띄워서 크롤링 (디버깅 시)
BROWSER_HEADLESS=false python -m src.main --channels mypress --keyword "테스트"

# 기본값 (headless 모드, 브라우저 창 없음)
BROWSER_HEADLESS=true python -m src.main --channels mypress --keyword "테스트"
```

헤드풀 모드에서는 브라우저가 페이지를 로드하고 JavaScript를 실행하는 과정을 직접 눈으로 확인할 수 있어, 셀렉터 오류나 페이지 로딩 타이밍 문제를 진단하는 데 유용합니다.

### 파서 개발 시 빠른 반복

새 채널의 파서를 개발할 때 권장하는 워크플로우:

1. 브라우저에서 대상 사이트의 검색 결과 페이지와 기사 상세 페이지를 열고, HTML을 `tests/fixtures/`에 저장합니다.
2. 테스트를 먼저 작성합니다 (TDD).
3. `pytest --watch` 또는 터미널에서 반복 실행하며 파서를 완성합니다.

```bash
# 파서 테스트를 반복 실행하며 개발
pytest tests/test_channels/test_mypress_parser.py -v --tb=short
```

`--tb=short` 옵션은 실패 시 트레이스백을 간결하게 보여줍니다.
