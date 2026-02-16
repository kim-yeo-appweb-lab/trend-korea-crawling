# 아키텍처

한국 뉴스 크롤링 파이프라인의 전체 아키텍처를 설명한다.

## 1. 아키텍처 개요

### 시스템 데이터 흐름

전체 파이프라인은 아래 단계를 순차적으로 거쳐 동작한다.

```
[CLI 키워드 입력]
       |
       v
[CrawlOrchestrator]
       |
       |-- 채널별 asyncio.Task 생성
       |
       v
[ChannelRegistry] -- 채널명으로 Crawler 인스턴스 동적 생성
       |
       v
[BaseCrawler.crawl()]  (Template Method)
       |
       |  1. build_search_url(keyword, page)
       |  2. FetchStrategy.fetch(url)          -- 전략에 따라 httpx 또는 playwright
       |  3. parse_article_list(html)           -- 검색 결과 목록 파싱
       |  4. FetchStrategy.fetch(article_url)   -- 기사 상세 페이지 요청
       |  5. parse_article_detail(html)         -- 기사 본문 파싱
       |
       v
[CrawlResult]  (채널별 수집 결과)
       |
       v
[asyncio.gather]  -- 모든 채널-키워드 조합 병렬 수집
       |
       v
[ResultWriter]  -- JSON 파일 출력
```

### 모듈 의존성 구조

```
main.py
  +-- config/settings.py        (CrawlerSettings)
  +-- config/logging.py         (setup_logging)
  +-- src/pipeline/
  |     +-- orchestrator.py     (CrawlOrchestrator)
  |     +-- channel_registry.py (CHANNEL_MAP, create_crawler)
  |     +-- result_writer.py    (ResultWriter)
  +-- src/core/
  |     +-- base_crawler.py     (BaseCrawler ABC)
  |     +-- fetch_strategy.py   (FetchStrategy ABC)
  |     +-- models.py           (Article, SearchResult, CrawlResult)
  |     +-- exceptions.py       (CrawlerError, FetchError, ParseError)
  |     +-- retry.py            (지수 백오프 데코레이터)
  +-- src/shared/
  |     +-- http_client.py      (HttpClient - httpx)
  |     +-- browser_client.py   (BrowserClient - playwright)
  |     +-- text_cleaner.py     (clean_text, extract_text_from_html)
  +-- src/channels/
        +-- naver_news/         (StaticFetchStrategy 사용)
        +-- maeililbo/          (StaticFetchStrategy 사용)
        +-- mk/                 (DynamicFetchStrategy 사용)
        +-- chosun/             (DynamicFetchStrategy 사용)
        +-- hani/               (DynamicFetchStrategy 사용)
```

## 2. 디자인 패턴

### Template Method -- BaseCrawler

`BaseCrawler`는 크롤링의 전체 흐름을 `crawl()` 메서드에서 고정하고, 각 단계의 구체적인 구현은 하위 클래스에 위임한다.

```python
class BaseCrawler(ABC):
    async def crawl(self, keyword: str, max_pages: int | None = None) -> CrawlResult:
        """전체 크롤링 흐름 실행"""
        pages = max_pages or self._settings.max_pages
        result = CrawlResult(channel=self.channel_name, keyword=keyword)

        for page in range(1, pages + 1):
            url = self.build_search_url(keyword, page)           # 추상 메서드
            html = await self._fetch_strategy.fetch(url)          # 전략 위임
            search_results = self.parse_article_list(html)        # 추상 메서드

            for sr in search_results:
                detail_html = await self._fetch_strategy.fetch(sr.url)
                article = self.parse_article_detail(detail_html, sr)  # 추상 메서드
                result.articles.append(article)

        return result
```

하위 클래스가 반드시 구현해야 하는 추상 메서드:

| 메서드 | 역할 |
|--------|------|
| `channel_name` (property) | 채널 식별 이름 반환 |
| `build_search_url(keyword, page)` | 채널별 검색 URL 생성 |
| `parse_article_list(html)` | 검색 결과 HTML에서 `SearchResult` 목록 추출 |
| `parse_article_detail(html, search_result)` | 기사 상세 HTML에서 `Article` 객체 생성 |

### Strategy -- FetchStrategy

페이지를 가져오는 방식을 전략 객체로 분리하여, 크롤러가 정적/동적 렌더링에 무관하게 동일한 인터페이스를 사용할 수 있도록 한다.

```python
class FetchStrategy(ABC):
    @abstractmethod
    async def fetch(self, url: str, wait_selector: str | None = None) -> str:
        """URL에서 HTML을 가져온다"""
```

두 가지 구체 전략이 존재한다:

| 전략 | 클라이언트 | 사용 시점 |
|------|-----------|-----------|
| `StaticFetchStrategy` | `HttpClient` (httpx) | 서버 사이드 렌더링(SSR) 페이지. 빠르고 가볍다. |
| `DynamicFetchStrategy` | `BrowserClient` (playwright) | 클라이언트 사이드 렌더링(CSR) 페이지. JS 실행이 필요한 경우. |

채널별 전략 배정은 `ChannelRegistry`의 `CHANNEL_MAP`에서 관리한다.

### Factory Registry -- ChannelRegistry

채널명 문자열로부터 크롤러 인스턴스를 동적으로 생성하는 팩토리 레지스트리 패턴이다.

```python
CHANNEL_MAP: dict[str, tuple[str, str, str]] = {
    "mk":         ("src.channels.mk.crawler",         "MkCrawler",         "dynamic"),
    "maeililbo":  ("src.channels.maeililbo.crawler",   "MaeililboCrawler",  "static"),
    "chosun":     ("src.channels.chosun.crawler",      "ChosunCrawler",     "dynamic"),
    "hani":       ("src.channels.hani.crawler",        "HaniCrawler",       "dynamic"),
    "naver_news": ("src.channels.naver_news.crawler",  "NaverNewsCrawler",  "static"),
}
```

각 항목은 `(모듈 경로, 크롤러 클래스명, fetch 전략 타입)` 튜플이다.
`create_crawler()` 함수가 `importlib.import_module()`을 사용해 모듈을 동적으로 로드하고, 전략 타입에 따라 적절한 `FetchStrategy`를 주입하여 크롤러 인스턴스를 반환한다.

동적 import를 사용하는 이유:
- 순환 참조 방지
- 필요한 채널만 로드하여 초기화 비용 절감
- 새 채널 추가 시 `CHANNEL_MAP`에 항목만 추가하면 됨

## 3. 핵심 모듈 설명

### core/ -- 추상화 계층

크롤러의 근간이 되는 인터페이스와 공통 로직을 정의한다.

| 파일 | 역할 |
|------|------|
| `base_crawler.py` | `BaseCrawler` ABC. Template Method로 크롤링 흐름을 고정 |
| `fetch_strategy.py` | `FetchStrategy` ABC와 `StaticFetchStrategy`, `DynamicFetchStrategy` 구현 |
| `models.py` | Pydantic 데이터 모델 (`Article`, `SearchResult`, `CrawlResult`) |
| `exceptions.py` | 예외 계층 (`CrawlerError` > `FetchError`, `ParseError`) |
| `retry.py` | 지수 백오프 재시도 데코레이터 |

### channels/ -- 채널별 구현

각 뉴스 채널 디렉토리는 아래 구조를 따른다:

```
src/channels/<channel_name>/
  +-- __init__.py
  +-- config.py      (CHANNEL_NAME, SEARCH_URL_TEMPLATE 등 상수)
  +-- crawler.py     (BaseCrawler 하위 클래스)
  +-- parser.py      (BeautifulSoup 기반 HTML 파싱 함수)
```

크롤러 클래스는 `BaseCrawler`를 상속하고, 채널 고유의 URL 생성과 HTML 파싱만 구현한다. 파싱 로직은 `parser.py`로 분리하여 단위 테스트가 용이하도록 한다.

현재 등록된 채널:

| 채널명 | 크롤러 | Fetch 전략 |
|--------|--------|-----------|
| `naver_news` | `NaverNewsCrawler` | Static (httpx) |
| `maeililbo` | `MaeililboCrawler` | Static (httpx) |
| `mk` | `MkCrawler` | Dynamic (playwright) |
| `chosun` | `ChosunCrawler` | Dynamic (playwright) |
| `hani` | `HaniCrawler` | Dynamic (playwright) |

### pipeline/ -- 오케스트레이션

| 파일 | 역할 |
|------|------|
| `orchestrator.py` | `CrawlOrchestrator`. 모든 채널-키워드 조합을 병렬 실행 |
| `channel_registry.py` | `CHANNEL_MAP` 관리, `create_crawler()` 팩토리 함수 |
| `result_writer.py` | `ResultWriter`. 크롤링 결과를 JSON 파일로 직렬화 |

### shared/ -- 공유 유틸리티

| 파일 | 역할 |
|------|------|
| `http_client.py` | `HttpClient`. httpx 기반 async HTTP 클라이언트 (async context manager) |
| `browser_client.py` | `BrowserClient`. playwright 기반 헤드리스 브라우저 클라이언트 (async context manager) |
| `text_cleaner.py` | `clean_text()`, `extract_text_from_html()`. HTML 텍스트 정제 유틸리티 |

## 4. 데이터 모델

모든 모델은 Pydantic `BaseModel`을 사용하여 타입 검증과 직렬화를 자동으로 처리한다.

### SearchResult

검색 결과 페이지에서 파싱한 개별 항목이다. 상세 페이지 요청의 입력으로 사용된다.

| 필드 | 타입 | 설명 |
|------|------|------|
| `title` | `str` | 기사 제목 |
| `url` | `str` | 기사 상세 페이지 URL |
| `snippet` | `str` | 검색 결과 미리보기 (기본값: 빈 문자열) |

### Article

수집이 완료된 하나의 뉴스 기사 데이터이다.

| 필드 | 타입 | 설명 |
|------|------|------|
| `title` | `str` | 기사 제목 |
| `url` | `str` | 기사 URL |
| `content` | `str` | 기사 본문 |
| `published_at` | `datetime \| None` | 기사 발행일 |
| `channel` | `str` | 채널명 |
| `keyword` | `str` | 검색 키워드 |
| `crawled_at` | `datetime` | 수집 시각 (자동 생성) |
| `metadata` | `dict` | 채널별 추가 메타데이터 |

### CrawlResult

하나의 채널-키워드 조합에 대한 크롤링 결과를 담는다.

| 필드 | 타입 | 설명 |
|------|------|------|
| `channel` | `str` | 채널명 |
| `keyword` | `str` | 검색 키워드 |
| `articles` | `list[Article]` | 수집된 기사 목록 |
| `errors` | `list[str]` | 수집 중 발생한 에러 메시지 목록 |

## 5. 병렬 처리

`CrawlOrchestrator.run()`은 모든 채널-키워드 조합을 `asyncio.gather()`로 병렬 실행한다.

```python
# 채널-키워드 조합별 크롤링 태스크 생성
tasks: list[asyncio.Task[CrawlResult]] = []
for channel in target_channels:
    for keyword in keywords:
        crawler = await create_crawler(channel, self._settings, http_client, browser_client)
        tasks.append(asyncio.create_task(crawler.crawl(keyword)))

raw_results = await asyncio.gather(*tasks, return_exceptions=True)
```

핵심 설계:
- 채널 3개, 키워드 2개인 경우 총 6개의 비동기 태스크가 동시에 실행된다.
- `return_exceptions=True`를 사용하여 개별 태스크 실패가 전체 파이프라인을 중단시키지 않는다.
- `HttpClient`와 `BrowserClient`는 오케스트레이터 레벨에서 한 번만 생성하고 모든 크롤러가 공유한다.
- 동적 채널이 하나라도 포함된 경우에만 `BrowserClient`를 초기화한다 (`has_dynamic_channel()` 검사).

### 리소스 수명 관리

```
CrawlOrchestrator.run()
  +-- async with HttpClient(...)       -- 전체 실행 동안 유지
  |     +-- BrowserClient.__aenter__() -- 동적 채널이 있을 때만 생성
  |     |     +-- asyncio.gather(...)  -- 모든 태스크 병렬 실행
  |     +-- BrowserClient.__aexit__()  -- finally 블록에서 정리
  +-- HttpClient.__aexit__()           -- async with 종료 시 정리
```

## 6. 에러 처리

### 예외 계층

```
CrawlerError (기본 예외)
  +-- FetchError   (페이지 가져오기 실패)
  +-- ParseError   (HTML 파싱 실패)
```

모든 크롤러 관련 예외는 `CrawlerError`를 상속하므로, 상위 레벨에서 일괄 처리할 수 있다.

### Fail-Soft 전략

`BaseCrawler.crawl()`은 개별 기사 수집 실패 시 에러를 기록하고 나머지 수집을 계속한다.

```python
for sr in search_results:
    try:
        detail_html = await self._fetch_strategy.fetch(sr.url)
        article = self.parse_article_detail(detail_html, sr)
        result.articles.append(article)
    except CrawlerError as e:
        error_msg = f"기사 수집 실패 ({sr.url}): {e}"
        logger.warning(error_msg)
        result.errors.append(error_msg)
```

동일한 패턴이 검색 페이지 레벨에서도 적용된다. 특정 페이지 요청이 실패하면 해당 페이지를 건너뛰고 다음 페이지로 진행한다.

`CrawlOrchestrator` 레벨에서도 `asyncio.gather(return_exceptions=True)`로 개별 채널 크롤링 실패를 격리한다. 실패한 태스크는 에러 메시지만 담긴 `CrawlResult`로 변환된다.

### 지수 백오프 재시도

`src/core/retry.py`의 `@retry` 데코레이터를 사용하면 일시적인 네트워크 오류에 대해 자동 재시도를 수행한다.

```python
@retry(max_retries=3, base_delay=1.0, backoff_factor=2.0, retry_on=(FetchError,))
async def some_fetch_operation():
    ...
```

재시도 간격은 지수적으로 증가한다:
- 1차 재시도: 1.0초 후
- 2차 재시도: 2.0초 후
- 3차 재시도: 4.0초 후

모든 재시도가 실패하면 마지막 예외를 그대로 발생시킨다.

### 요청 간 지연

`BaseCrawler.crawl()`은 각 요청 사이에 `settings.request_delay`(기본 1초) 만큼 대기하여 대상 서버에 과도한 부하를 주지 않도록 한다.

```python
for sr in search_results:
    await asyncio.sleep(self._settings.request_delay)
    # ... 기사 수집
```
