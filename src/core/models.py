from datetime import datetime

from pydantic import BaseModel, Field


class Article(BaseModel):
    """뉴스 기사 모델"""

    title: str
    url: str
    content: str
    published_at: datetime | None = None
    channel: str
    keyword: str
    crawled_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)


class SearchResult(BaseModel):
    """검색 결과 항목"""

    title: str
    url: str
    snippet: str = ""


class CrawlResult(BaseModel):
    """크롤링 결과"""

    channel: str
    keyword: str
    articles: list[Article] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
