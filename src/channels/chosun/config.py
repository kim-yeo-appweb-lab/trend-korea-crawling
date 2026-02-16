# 조선일보 크롤러 설정

CHANNEL_NAME = "chosun"
BASE_URL = "https://www.chosun.com"
SEARCH_URL_TEMPLATE = (
    "https://www.chosun.com/nsearch/?query={keyword}&page={page}&siteid=www&sort=1"
)

# 검색 결과 페이지 선택자 (search-feed 내부만 선택)
ARTICLE_LIST_SELECTOR = "div.search-feed div.story-card"
ARTICLE_LINK_SELECTOR = "a.story-card__headline, a[href*='/article/']"
ARTICLE_TITLE_SELECTOR = "a.story-card__headline, div.story-card__headline"

# 기사 상세 페이지 선택자
ARTICLE_CONTENT_SELECTOR = "section.article-body"
ARTICLE_DATE_SELECTOR = "meta[property='article:published_time'], time"

# Next.js 데이터 선택자
NEXT_DATA_SELECTOR = "script#__NEXT_DATA__"

# Playwright 대기 선택자 (검색 결과 영역 로드 대기)
SEARCH_WAIT_SELECTOR = "div.search-feed div.story-card"
DETAIL_WAIT_SELECTOR = "section.article-body"
