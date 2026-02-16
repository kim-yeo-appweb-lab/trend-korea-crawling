# 채널별 크롤링 전략

각 뉴스 채널의 크롤링 설정과 전략을 정리한 문서이다.

---

## mk (매일경제)

| 항목 | 값 |
|---|---|
| 채널 이름 | `mk` |
| 기본 URL | `https://www.mk.co.kr` |
| 검색 URL 패턴 | `https://www.mk.co.kr/search?word={keyword}&page={page}` |
| 렌더링 방식 | **Dynamic** (Playwright) |
| 상태 | 정상 |

### 렌더링 방식 선택 이유

매일경제 검색 결과 페이지는 JavaScript로 동적 렌더링되므로 `DynamicFetchStrategy`를 사용한다. Playwright가 `li.news_node` 요소가 로드될 때까지 대기한 후 HTML을 파싱한다.

### CSS 선택자

| 구분 | 선택자 | 설명 |
|---|---|---|
| 기사 목록 | `li.news_node` | 검색 결과 각 항목 컨테이너 |
| 기사 링크 | `a[href*='/news/']` | 기사 상세 페이지 링크 |
| 기사 제목 | `a[href*='/news/']` | 링크 텍스트에서 제목 추출 |
| 기사 본문 | `div.news_cnt_detail_wrap` | 기사 상세 본문 영역 |
| 발행일 | `time` | 기사 발행 시각 |
| 검색 대기 | `li.news_node` | 검색 페이지 로드 대기 |
| 상세 대기 | `div.news_cnt_detail_wrap` | 상세 페이지 로드 대기 |

### 특이사항

- 일부 특수 형태 기사(포토뉴스, 영상 기사 등)는 `div.news_cnt_detail_wrap` 선택자로 본문을 추출하지 못할 수 있다.
- 페이지네이션은 `page` 쿼리 파라미터로 처리한다.

---

## maeililbo (매일일보)

| 항목 | 값 |
|---|---|
| 채널 이름 | `maeililbo` |
| 기본 URL | `https://www.m-i.kr` |
| 검색 URL 패턴 | `https://www.m-i.kr/news/articleList.html?sc_word={keyword}&page={page}` |
| 렌더링 방식 | **Static** (httpx + BeautifulSoup) |
| 상태 | 정상 |

### 렌더링 방식 선택 이유

매일일보는 서버 사이드 렌더링으로 검색 결과와 기사 본문을 모두 제공한다. JavaScript 없이 HTML 파싱만으로 충분하므로 `StaticFetchStrategy`를 사용한다.

### CSS 선택자

| 구분 | 선택자 | 설명 |
|---|---|---|
| 기사 목록 | `li.clearfix` | 검색 결과 각 항목 컨테이너 |
| 기사 링크 | `div.auto-titles a[href*='articleView']` | 기사 상세 페이지 링크 |
| 기사 제목 | `div.auto-titles a` | 기사 제목 텍스트 |
| 기사 본문 | `div#article-view-content-div` | 기사 상세 본문 영역 |
| 발행일 | `ul.infomation li`, `ul.auto-infomation li`, `i` | 기사 발행일 (복수 폴백 선택자) |

### 특이사항

- 전체 채널 중 가장 안정적으로 동작한다.
- 발행일 선택자가 복수(폴백 방식)로 구성되어 있어 페이지 구조 변경에 유연하다.

---

## chosun (조선일보)

| 항목 | 값 |
|---|---|
| 채널 이름 | `chosun` |
| 기본 URL | `https://www.chosun.com` |
| 검색 URL 패턴 | `https://www.chosun.com/nsearch/?query={keyword}&page={page}&siteid=www&sort=1` |
| 렌더링 방식 | **Dynamic** (Playwright) |
| 상태 | 정상 |

### 렌더링 방식 선택 이유

조선일보는 Next.js 기반으로 구축되어 검색 결과가 JavaScript로 렌더링된다. `DynamicFetchStrategy`를 사용하며, `div.search-feed` 내부의 검색 결과만 선택하여 광고 등 불필요한 요소를 제외한다.

### CSS 선택자

| 구분 | 선택자 | 설명 |
|---|---|---|
| 기사 목록 | `div.search-feed div.story-card` | search-feed 내부의 기사 카드 |
| 기사 링크 | `a.story-card__headline`, `a[href*='/article/']` | 기사 상세 링크 (폴백) |
| 기사 제목 | `a.story-card__headline`, `div.story-card__headline` | 기사 제목 (폴백) |
| 기사 본문 | `section.article-body` | 기사 상세 본문 영역 |
| 발행일 | `meta[property='article:published_time']`, `time` | 발행일 메타 태그 우선 |
| `__NEXT_DATA__` | `script#__NEXT_DATA__` | Next.js 서버 데이터 |
| 검색 대기 | `div.search-feed div.story-card` | 검색 페이지 로드 대기 |
| 상세 대기 | `section.article-body` | 상세 페이지 로드 대기 |

### 특이사항

- **`__NEXT_DATA__` JSON 우선 추출**: 기사 상세 페이지에서 `script#__NEXT_DATA__` 태그의 JSON 데이터를 먼저 파싱한다. 이 방식이 DOM 파싱보다 정확하고 안정적이다. JSON 파싱 실패 시 CSS 선택자로 폴백한다.
- 검색 결과에서 `div.search-feed` 내부만 선택하여 사이드바 추천 기사 등을 제외한다.
- 검색 URL의 `sort=1` 파라미터로 최신순 정렬을 적용한다.

---

## hani (한겨레)

| 항목 | 값 |
|---|---|
| 채널 이름 | `hani` |
| 기본 URL | `https://www.hani.co.kr` |
| 검색 URL 패턴 | `https://search.hani.co.kr/?command=query&keyword={keyword}&media=news&sort=d&pageseq={page}` |
| 렌더링 방식 | **Dynamic** (Playwright) |
| 상태 | **비활성** |

### 렌더링 방식 선택 이유

한겨레 검색 페이지는 JavaScript 기반으로 렌더링되어 `DynamicFetchStrategy`가 필요하다. 그러나 현재 검색 페이지 구조 변경으로 인해 키워드 전달이 정상적으로 동작하지 않는다.

### CSS 선택자

| 구분 | 선택자 | 설명 |
|---|---|---|
| 검색 대기 | `div.search-inner` | 검색 결과 영역 로드 대기 |
| 기사 링크 패턴 | `/arti/` 포함 URL | 기사 상세 링크 필터 |
| 기사 본문 | `div.article-text`, `div.text` | 기사 본문 (폴백) |
| 발행일 | `span.date-time`, `p.date-time`, `span.date_info` | 발행일 (폴백) |

### 특이사항

- **현재 비활성 상태이다.** 검색 페이지가 전면 JS 기반으로 변경되면서 URL 쿼리 파라미터를 통한 키워드 전달이 정상 동작하지 않는다.
- 검색 도메인(`search.hani.co.kr`)이 본 사이트(`www.hani.co.kr`)와 분리되어 있다.
- 기사 링크는 CSS 선택자 대신 URL 패턴(`/arti/`)으로 필터링한다.

---

## naver_news (네이버 뉴스)

| 항목 | 값 |
|---|---|
| 채널 이름 | `naver_news` |
| 기본 URL | `https://news.naver.com` |
| 검색 URL 패턴 | `https://search.naver.com/search.naver?where=news&query={keyword}&start={start}&sort=1` |
| 렌더링 방식 | **Static** (httpx + BeautifulSoup) |
| 상태 | 정상 |

### 렌더링 방식 선택 이유

네이버 뉴스 검색 결과는 서버 사이드 렌더링으로 제공되어 `StaticFetchStrategy`로 충분하다. 기사 상세 페이지도 `n.news.naver.com` 도메인에서 정적 HTML로 제공된다.

### CSS 선택자

| 구분 | 선택자 | 설명 |
|---|---|---|
| 네이버 뉴스 링크 | `a[href*='n.news.naver.com']` | 네이버 뉴스 호스팅 기사 링크 |
| 기사 본문 | `article#dic_area` | 기사 본문 영역 |
| 발행일 | `span.media_end_head_info_datestamp_time` | 기사 발행 시각 |

### 특이사항

- **역방향 탐색 방식**: 검색 결과 HTML에서 `n.news.naver.com` 링크를 먼저 찾고, 해당 링크의 상위 요소를 `NEWS_CONTAINER_DEPTH`(4단계)만큼 거슬러 올라가 기사 컨테이너를 특정한다. 네이버 검색 결과 페이지의 SDS 컴포넌트 구조가 자주 변경되기 때문에 이 방식을 사용한다.
- 페이지네이션은 `start` 파라미터로 처리한다 (`page`가 아닌 오프셋 기반).
- 검색 URL의 `sort=1`로 최신순 정렬을 적용한다.
- 2026년 기준 네이버 검색 결과가 SDS 컴포넌트 구조로 변경되어, 고정된 클래스명 대신 링크 URL 패턴 기반 탐색을 채택했다.

---

## 채널 상태 요약

| 채널 | 렌더링 방식 | 상태 | 비고 |
|---|---|---|---|
| mk | Dynamic | 정상 | 일부 특수 기사 본문 추출 실패 가능 |
| maeililbo | Static | 정상 | 가장 안정적 |
| chosun | Dynamic | 정상 | `__NEXT_DATA__` JSON 우선 추출 |
| hani | Dynamic | 비활성 | 검색 페이지 JS 변경으로 키워드 전달 불가 |
| naver_news | Static | 정상 | `n.news.naver.com` 링크 역방향 탐색 |
