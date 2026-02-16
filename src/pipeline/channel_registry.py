import importlib

from config.settings import CrawlerSettings
from src.core.base_crawler import BaseCrawler
from src.core.fetch_strategy import DynamicFetchStrategy, StaticFetchStrategy
from src.shared.browser_client import BrowserClient
from src.shared.http_client import HttpClient

# 채널 이름 → (모듈 경로, 크롤러 클래스명, fetch 전략 타입) 매핑
# 전략 타입: "static" (httpx) 또는 "dynamic" (playwright)
CHANNEL_MAP: dict[str, tuple[str, str, str]] = {
    "mk": ("src.channels.mk.crawler", "MkCrawler", "dynamic"),
    "maeililbo": ("src.channels.maeililbo.crawler", "MaeililboCrawler", "static"),
    "chosun": ("src.channels.chosun.crawler", "ChosunCrawler", "dynamic"),
    "hani": ("src.channels.hani.crawler", "HaniCrawler", "dynamic"),
    "naver_news": ("src.channels.naver_news.crawler", "NaverNewsCrawler", "static"),
}


def get_available_channels() -> list[str]:
    """등록된 채널 이름 목록 반환"""
    return list(CHANNEL_MAP.keys())


def has_dynamic_channel(channels: list[str]) -> bool:
    """주어진 채널 중 dynamic 전략이 필요한 채널이 있는지 확인"""
    return any(CHANNEL_MAP[ch][2] == "dynamic" for ch in channels if ch in CHANNEL_MAP)


async def create_crawler(
    channel_name: str,
    settings: CrawlerSettings,
    http_client: HttpClient,
    browser_client: BrowserClient | None = None,
) -> BaseCrawler:
    """채널 이름으로 크롤러 인스턴스를 동적으로 생성한다.

    importlib를 사용해 동적 import하여 순환 참조를 방지한다.
    """
    if channel_name not in CHANNEL_MAP:
        raise ValueError(f"알 수 없는 채널: '{channel_name}'")

    module_path, class_name, strategy_type = CHANNEL_MAP[channel_name]
    module = importlib.import_module(module_path)
    crawler_cls = getattr(module, class_name)

    if strategy_type == "static":
        strategy = StaticFetchStrategy(http_client)
    else:
        if browser_client is None:
            raise ValueError(f"'{channel_name}' 채널은 브라우저 클라이언트가 필요합니다")
        strategy = DynamicFetchStrategy(browser_client)

    return crawler_cls(strategy, settings)
