from datetime import datetime

from src.core.models import Article, CrawlResult, SearchResult


class TestArticle:
    """Article 모델 테스트"""

    def test_article_creation(self):
        """모든 필드를 지정하여 Article 생성"""
        now = datetime.now()
        article = Article(
            title="테스트 제목",
            url="https://example.com/1",
            content="테스트 본문 내용",
            published_at=now,
            channel="mk",
            keyword="AI",
            metadata={"source": "test"},
        )

        assert article.title == "테스트 제목"
        assert article.url == "https://example.com/1"
        assert article.content == "테스트 본문 내용"
        assert article.published_at == now
        assert article.channel == "mk"
        assert article.keyword == "AI"
        assert article.metadata == {"source": "test"}

    def test_crawled_at_auto_set(self):
        """crawled_at 필드가 자동으로 현재 시각으로 설정되는지 검증"""
        before = datetime.now()
        article = Article(
            title="제목",
            url="https://example.com/2",
            content="본문",
            channel="mk",
            keyword="테스트",
        )
        after = datetime.now()

        assert before <= article.crawled_at <= after

    def test_metadata_default_empty_dict(self):
        """metadata 기본값이 빈 dict인지 검증"""
        article = Article(
            title="제목",
            url="https://example.com/3",
            content="본문",
            channel="mk",
            keyword="테스트",
        )

        assert article.metadata == {}

    def test_published_at_default_none(self):
        """published_at 기본값이 None인지 검증"""
        article = Article(
            title="제목",
            url="https://example.com/4",
            content="본문",
            channel="mk",
            keyword="테스트",
        )

        assert article.published_at is None

    def test_model_dump_json_serialization(self):
        """model_dump(mode='json')으로 JSON 직렬화 가능한지 검증"""
        article = Article(
            title="직렬화 테스트",
            url="https://example.com/5",
            content="본문 내용",
            published_at=datetime(2024, 1, 15, 9, 30, 0),
            channel="mk",
            keyword="AI",
        )
        data = article.model_dump(mode="json")

        assert isinstance(data, dict)
        assert data["title"] == "직렬화 테스트"
        assert data["channel"] == "mk"
        # datetime이 문자열로 직렬화되었는지 확인
        assert isinstance(data["crawled_at"], str)
        assert isinstance(data["published_at"], str)


class TestSearchResult:
    """SearchResult 모델 테스트"""

    def test_search_result_creation(self):
        """SearchResult 생성 및 필드 검증"""
        sr = SearchResult(
            title="검색 결과 제목",
            url="https://example.com/search/1",
            snippet="검색 결과 요약",
        )

        assert sr.title == "검색 결과 제목"
        assert sr.url == "https://example.com/search/1"
        assert sr.snippet == "검색 결과 요약"

    def test_snippet_default_empty(self):
        """snippet 기본값이 빈 문자열인지 검증"""
        sr = SearchResult(title="제목", url="https://example.com/search/2")

        assert sr.snippet == ""


class TestCrawlResult:
    """CrawlResult 모델 테스트"""

    def test_crawl_result_creation(self):
        """CrawlResult 생성 및 기본값 검증"""
        result = CrawlResult(channel="mk", keyword="AI")

        assert result.channel == "mk"
        assert result.keyword == "AI"
        assert result.articles == []
        assert result.errors == []

    def test_crawl_result_add_articles(self):
        """CrawlResult에 articles 추가"""
        result = CrawlResult(channel="mk", keyword="AI")
        article = Article(
            title="테스트",
            url="https://example.com/1",
            content="본문",
            channel="mk",
            keyword="AI",
        )
        result.articles.append(article)

        assert len(result.articles) == 1
        assert result.articles[0].title == "테스트"

    def test_crawl_result_add_errors(self):
        """CrawlResult에 errors 추가"""
        result = CrawlResult(channel="mk", keyword="AI")
        result.errors.append("페이지 1 실패")

        assert len(result.errors) == 1
        assert result.errors[0] == "페이지 1 실패"
