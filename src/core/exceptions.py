class CrawlerError(Exception):
    """크롤러 기본 예외"""


class FetchError(CrawlerError):
    """페이지 가져오기 실패"""


class ParseError(CrawlerError):
    """HTML 파싱 실패"""
