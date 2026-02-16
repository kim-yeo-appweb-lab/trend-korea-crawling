CHANNEL_NAME = "maeililbo"
BASE_URL = "https://www.m-i.kr"
SEARCH_URL_TEMPLATE = "https://www.m-i.kr/news/articleList.html?sc_word={keyword}&page={page}"

# 검색 결과 목록 셀렉터
ARTICLE_LIST_SELECTOR = "li.clearfix"
ARTICLE_LINK_SELECTOR = "div.auto-titles a[href*='articleView']"
ARTICLE_TITLE_SELECTOR = "div.auto-titles a"

# 기사 상세 페이지 셀렉터
ARTICLE_CONTENT_SELECTOR = "div#article-view-content-div"
ARTICLE_DATE_SELECTOR = "ul.infomation li, ul.auto-infomation li, i"
