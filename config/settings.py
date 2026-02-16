from pydantic import Field
from pydantic_settings import BaseSettings


class BrowserSettings(BaseSettings):
    """브라우저 관련 설정"""

    model_config = {"env_prefix": "BROWSER_"}

    headless: bool = True


class CrawlerSettings(BaseSettings):
    """크롤러 설정"""

    model_config = {"env_prefix": "CRAWLER_"}

    max_pages: int = 3
    request_delay: float = 1.0
    request_timeout: int = 30
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    output_dir: str = "./output"
    browser: BrowserSettings = Field(default_factory=BrowserSettings)
