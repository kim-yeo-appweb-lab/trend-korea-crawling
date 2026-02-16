# 네이버 뉴스 채널 설정 상수

CHANNEL_NAME = "naver_news"
BASE_URL = "https://news.naver.com"
SEARCH_URL_TEMPLATE = (
    "https://search.naver.com/search.naver?where=news&query={keyword}&start={start}&sort=1"
)

# 검색 결과 페이지 CSS 선택자
# 2026년 기준 SDS 컴포넌트 구조로 변경됨
NAVER_NEWS_LINK_SELECTOR = "a[href*='n.news.naver.com']"
NEWS_CONTAINER_DEPTH = 4

# 기사 상세 페이지 CSS 선택자 (n.news.naver.com)
ARTICLE_CONTENT_SELECTOR = "article#dic_area"
ARTICLE_DATE_SELECTOR = "span.media_end_head_info_datestamp_time"
