# 한겨레 채널 설정 상수

CHANNEL_NAME = "hani"
BASE_URL = "https://www.hani.co.kr"
SEARCH_BASE_URL = "https://search.hani.co.kr"
SEARCH_URL_TEMPLATE = (
    "https://search.hani.co.kr/?"
    "command=query&keyword={keyword}&media=news&sort=d&pageseq={page}"
)

# 검색 결과는 JS 렌더링 → DynamicFetchStrategy 필요
SEARCH_WAIT_SELECTOR = "div.search-inner"
ARTICLE_LINK_PATTERN = "/arti/"

# 기사 상세 페이지 CSS 선택자
ARTICLE_CONTENT_SELECTOR = "div.article-text, div.text"
ARTICLE_DATE_SELECTOR = "span.date-time, p.date-time, span.date_info"
