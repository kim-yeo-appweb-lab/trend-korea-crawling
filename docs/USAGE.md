# 사용법

## 설치

### 요구 사항

- Python 3.11 이상
- pip 또는 uv 패키지 매니저

### 패키지 설치

```bash
# 프로젝트 설치 (editable 모드)
pip install -e .

# 개발 의존성 포함 설치
pip install -e ".[dev]"

# Playwright 브라우저 설치 (Chromium)
playwright install chromium
```

> Playwright 브라우저 설치는 Dynamic 렌더링 채널(mk, chosun) 사용 시 필수이다.

---

## 환경 설정

프로젝트 루트에 `.env` 파일을 생성하여 기본 설정을 오버라이드할 수 있다.

| 환경 변수 | 설명 | 기본값 |
|---|---|---|
| `CRAWLER_MAX_PAGES` | 채널당 최대 검색 페이지 수 | `3` |
| `CRAWLER_REQUEST_DELAY` | 요청 간 대기 시간 (초) | `1.0` |
| `CRAWLER_REQUEST_TIMEOUT` | HTTP 요청 타임아웃 (초) | `30` |
| `CRAWLER_USER_AGENT` | 요청에 사용할 User-Agent 문자열 | Chrome 120 UA |
| `CRAWLER_OUTPUT_DIR` | 결과 파일 저장 디렉토리 | `./output` |
| `BROWSER_HEADLESS` | 브라우저 헤드리스 모드 여부 | `True` |

설정 우선순위: **CLI 인자 > 환경 변수(.env) > 기본값**

`.env` 파일 예시:

```env
CRAWLER_MAX_PAGES=5
CRAWLER_REQUEST_DELAY=1.5
CRAWLER_REQUEST_TIMEOUT=30
CRAWLER_OUTPUT_DIR=./output
BROWSER_HEADLESS=True
```

---

## CLI 옵션

```bash
python main.py [옵션]
```

| 옵션 | 축약 | 필수 | 설명 | 기본값 |
|---|---|---|---|---|
| `--keywords` | `-k` | O | 검색 키워드 (복수 지정 가능) | - |
| `--channels` | `-c` | X | 크롤링 대상 채널 | 활성 채널 전체 |
| `--max-pages` | - | X | 최대 검색 페이지 수 | 환경 변수 또는 3 |
| `--output-dir` | - | X | 결과 저장 디렉토리 | 환경 변수 또는 `./output` |

### `-k, --keywords`

검색할 키워드를 하나 이상 지정한다. 각 키워드는 모든 활성 채널에 대해 독립적으로 검색된다.

```bash
python main.py -k "인공지능"
python main.py -k "인공지능" "반도체"
```

### `-c, --channels`

크롤링할 채널을 지정한다. 생략하면 활성화된 전체 채널을 대상으로 크롤링한다. 사용 가능한 채널 목록은 `channel_registry`에 등록된 채널에 의해 결정된다.

```bash
python main.py -k "인공지능" -c mk chosun
python main.py -k "인공지능" -c naver_news
```

### `--max-pages`

채널별로 검색할 최대 페이지 수를 지정한다. CLI 인자가 환경 변수 설정보다 우선한다.

```bash
python main.py -k "인공지능" --max-pages 10
```

### `--output-dir`

결과 JSON 파일을 저장할 디렉토리를 지정한다. 디렉토리가 없으면 자동 생성된다.

```bash
python main.py -k "인공지능" --output-dir ./results
```

---

## 사용 예시

### 단일 키워드, 전체 채널

```bash
python main.py -k "부동산"
```

### 복수 키워드, 특정 채널

```bash
python main.py -k "AI" "챗봇" -c mk maeililbo
```

### 페이지 수 제한, 출력 디렉토리 변경

```bash
python main.py -k "경제위기" --max-pages 5 --output-dir ./data/crawled
```

### 네이버 뉴스만 크롤링

```bash
python main.py -k "트렌드 코리아" -c naver_news --max-pages 10
```

---

## 출력 JSON 구조

결과 파일은 `{output_dir}/crawl_{YYYYMMDD_HHMMSS}.json` 형식으로 저장된다.

### 최상위 구조

```json
{
  "crawled_at": "2026-02-16T14:30:00.123456",
  "total_channels": 3,
  "total_articles": 42,
  "results": [...]
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `crawled_at` | `string` (ISO 8601) | 크롤링 실행 시각 |
| `total_channels` | `int` | 크롤링한 채널 수 (중복 제거) |
| `total_articles` | `int` | 수집된 총 기사 수 |
| `results` | `array` | 채널-키워드별 크롤링 결과 목록 |

### `results` 배열 항목 (CrawlResult)

```json
{
  "channel": "mk",
  "keyword": "인공지능",
  "articles": [...],
  "errors": ["에러 메시지"]
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `channel` | `string` | 채널 식별자 |
| `keyword` | `string` | 검색 키워드 |
| `articles` | `array` | 수집된 기사 목록 |
| `errors` | `array<string>` | 크롤링 중 발생한 에러 메시지 |

### `articles` 배열 항목 (Article)

```json
{
  "title": "기사 제목",
  "url": "https://example.com/article/123",
  "content": "기사 본문 텍스트...",
  "published_at": "2026-02-15T09:00:00",
  "channel": "mk",
  "keyword": "인공지능",
  "crawled_at": "2026-02-16T14:30:00.123456",
  "metadata": {}
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `title` | `string` | 기사 제목 |
| `url` | `string` | 기사 원문 URL |
| `content` | `string` | 기사 본문 텍스트 |
| `published_at` | `string \| null` | 기사 발행일 (ISO 8601), 파싱 실패 시 `null` |
| `channel` | `string` | 수집 채널 |
| `keyword` | `string` | 검색에 사용된 키워드 |
| `crawled_at` | `string` | 기사 수집 시각 (ISO 8601) |
| `metadata` | `object` | 채널별 추가 메타데이터 (기본: 빈 객체) |

---

## 로깅

크롤링 실행 시 표준 출력(stdout)으로 로그가 출력된다.

로그 형식:

```
[2026-02-16 14:30:00] [INFO] [src.pipeline.orchestrator] 크롤링 시작...
```

로그 레벨은 기본 `INFO`이며, `config/logging.py`의 `setup_logging()` 함수에서 변경할 수 있다.

크롤링 완료 시 결과 요약이 출력된다:

```
크롤링 완료! 기사 42건, 에러 3건
결과 파일: output/crawl_20260216_143000.json
```
