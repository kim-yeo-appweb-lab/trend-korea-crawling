# 매일경제 채널 설정 상수

CHANNEL_NAME = "mk"
BASE_URL = "https://www.mk.co.kr"
SEARCH_URL_TEMPLATE = "https://www.mk.co.kr/search?word={keyword}&page={page}"

# 검색 결과 페이지 CSS 선택자
ARTICLE_LIST_SELECTOR = "li.news_node"
ARTICLE_LINK_SELECTOR = "a[href*='/news/']"
ARTICLE_TITLE_SELECTOR = "a[href*='/news/']"

# 기사 상세 페이지 CSS 선택자
ARTICLE_CONTENT_SELECTOR = "div.news_cnt_detail_wrap"
ARTICLE_DATE_SELECTOR = "time"

# DynamicFetchStrategy 사용 시 대기 선택자
SEARCH_WAIT_SELECTOR = "li.news_node"
DETAIL_WAIT_SELECTOR = "div.news_cnt_detail_wrap"
