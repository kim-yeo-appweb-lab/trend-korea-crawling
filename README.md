# Trend Korea Crawling

트렌드 코리아 프로젝트의 한국 뉴스 크롤링 파이프라인.

5개 한국 뉴스 소스에서 키워드 기반으로 뉴스 기사를 수집하고, 구조화된 JSON 형태로 저장한다. async 기반의 standalone Python 프로젝트로 SPA/SSR/Static HTML 페이지를 모두 처리할 수 있다.

## 채널 현황

| 채널 | 소스 | 상태 | 수집 방식 |
| --- | --- | --- | --- |
| `mk` | 매일경제 | 정상 | Dynamic (Playwright) |
| `maeililbo` | 매일일보 | 정상 | Static (httpx) |
| `chosun` | 조선일보 | 정상 | Dynamic (Playwright) |
| `hani` | 한겨레 | 비활성 (검색 구조 변경) | Dynamic (Playwright) |
| `naver_news` | 네이버뉴스 | 정상 | Static (httpx) |

## 기술 스택

- **HTTP 클라이언트**: httpx (async, HTTP/2 지원)
- **HTML 파싱**: beautifulsoup4 + lxml
- **동적 렌더링**: Playwright (Chromium)
- **데이터 모델**: Pydantic v2
- **설정 관리**: pydantic-settings (.env 파일 지원)
- **테스트**: pytest + pytest-asyncio
- **린팅**: Ruff
- **Python**: 3.11+

## 빠른 시작

### 의존성 설치

```bash
pip install -e .
pip install -e ".[dev]"
playwright install chromium
```

### 환경 변수 설정

`pydantic-settings`를 사용하며, 환경 변수 접두사로 설정을 오버라이드할 수 있다.

```bash
# 크롤러 설정 (CRAWLER_ 접두사)
CRAWLER_MAX_PAGES=3
CRAWLER_REQUEST_DELAY=1.0
CRAWLER_REQUEST_TIMEOUT=30
CRAWLER_OUTPUT_DIR=./output

# 브라우저 설정 (BROWSER_ 접두사)
BROWSER_HEADLESS=true
```

### 실행

```bash
# 단일 키워드 크롤링 (모든 활성 채널)
python main.py -k "부동산"

# 복수 키워드 + 특정 채널
python main.py -k "부동산" "금리" -c mk naver_news

# 최대 페이지 수 지정
python main.py -k "AI" --max-pages 5

# 출력 디렉토리 지정
python main.py -k "AI" --max-pages 5 --output-dir ./results
```

### CLI 옵션

| 옵션 | 설명 | 기본값 |
| --- | --- | --- |
| `-k`, `--keywords` | 검색 키워드 (필수, 복수 가능) | - |
| `-c`, `--channels` | 크롤링할 채널 선택 | 전체 채널 |
| `--max-pages` | 채널당 최대 페이지 수 | 3 |
| `--output-dir` | 결과 JSON 출력 디렉토리 | `./output` |

## 프로젝트 구조

```
trend-korea-crawling/
├── pyproject.toml           # 프로젝트 메타데이터 및 의존성
├── main.py                  # CLI 진입점
├── config/
│   ├── settings.py          # CrawlerSettings, BrowserSettings (pydantic-settings)
│   └── logging.py           # 로깅 설정
├── src/
│   ├── core/                # 핵심 추상화
│   │   ├── models.py        # Article, SearchResult, CrawlResult
│   │   ├── base_crawler.py  # BaseCrawler 추상 클래스
│   │   ├── fetch_strategy.py # StaticFetchStrategy, DynamicFetchStrategy
│   │   ├── exceptions.py    # 커스텀 예외
│   │   └── retry.py         # 재시도 데코레이터
│   ├── channels/            # 채널별 크롤링 모듈
│   │   ├── mk/              # 매일경제
│   │   ├── maeililbo/       # 매일일보
│   │   ├── chosun/          # 조선일보
│   │   ├── hani/            # 한겨레
│   │   └── naver_news/      # 네이버뉴스
│   ├── pipeline/            # 파이프라인 오케스트레이션
│   │   ├── orchestrator.py  # CrawlOrchestrator (크롤링 실행 관리)
│   │   ├── channel_registry.py # 채널 등록 및 동적 크롤러 생성
│   │   └── result_writer.py # 결과 JSON 파일 저장
│   └── shared/              # 공유 유틸리티
│       ├── http_client.py   # httpx 기반 async HTTP 클라이언트
│       ├── browser_client.py # Playwright 기반 브라우저 클라이언트
│       └── text_cleaner.py  # HTML/텍스트 정제
├── output/                  # 크롤링 결과 JSON 출력
└── tests/                   # 테스트
    ├── conftest.py
    ├── fixtures/            # HTML 테스트 픽스처
    ├── test_core/           # 핵심 모듈 테스트
    └── test_channels/       # 채널 파서 테스트
```

## 아키텍처 개요

프로젝트는 Strategy 패턴과 Template Method 패턴을 기반으로 설계되었다.

- **FetchStrategy**: 페이지를 가져오는 방법을 추상화한다. `StaticFetchStrategy`(httpx)와 `DynamicFetchStrategy`(Playwright)로 SPA/SSR/Static HTML을 분리 대응한다.
- **BaseCrawler**: 검색 -> 기사 수집 흐름을 정의하는 Template Method 패턴. 각 채널은 이를 상속해 파싱 로직만 구현한다.
- **CrawlOrchestrator**: 키워드와 채널 조합을 받아 비동기 크롤링을 관리한다.
- **ChannelRegistry**: 채널 이름으로 크롤러를 동적으로 생성하는 Factory 역할을 한다.

## 테스트

```bash
# 전체 테스트 실행
pytest

# 특정 테스트 파일
pytest tests/test_channels/test_mk_parser.py

# 린팅
ruff check .
```

## 문서

상세 문서는 `docs/` 디렉토리를 참고한다.

- [아키텍처 및 설계 패턴](docs/ARCHITECTURE.md)
- [상세 사용법](docs/USAGE.md)
- [채널별 크롤링 전략](docs/CHANNELS.md)
- [개발 가이드](docs/DEVELOPMENT.md)
