import asyncio
import logging

from config.settings import CrawlerSettings
from src.core.models import CrawlResult
from src.pipeline.channel_registry import (
    create_crawler,
    get_available_channels,
    has_dynamic_channel,
)
from src.shared.browser_client import BrowserClient
from src.shared.http_client import HttpClient

logger = logging.getLogger(__name__)


class CrawlOrchestrator:
    """모든 채널-키워드 조합을 병렬로 실행하는 오케스트레이터"""

    def __init__(self, settings: CrawlerSettings) -> None:
        self._settings = settings

    async def run(
        self,
        keywords: list[str],
        channels: list[str] | None = None,
    ) -> list[CrawlResult]:
        """지정된 채널과 키워드 조합으로 크롤링을 병렬 실행한다."""
        target_channels = channels or get_available_channels()
        needs_browser = has_dynamic_channel(target_channels)

        logger.info(
            "크롤링 시작: 채널=%s, 키워드=%s",
            target_channels,
            keywords,
        )

        async with HttpClient(self._settings.user_agent, self._settings.request_timeout) as http_client:
            browser_client: BrowserClient | None = None
            try:
                if needs_browser:
                    browser_client = BrowserClient(headless=self._settings.browser.headless)
                    await browser_client.__aenter__()

                # 채널-키워드 조합별 크롤링 태스크 생성
                tasks: list[asyncio.Task[CrawlResult]] = []
                for channel in target_channels:
                    for keyword in keywords:
                        crawler = await create_crawler(
                            channel, self._settings, http_client, browser_client
                        )
                        tasks.append(asyncio.create_task(crawler.crawl(keyword)))

                raw_results = await asyncio.gather(*tasks, return_exceptions=True)

                # 예외를 에러 결과로 변환
                crawl_results: list[CrawlResult] = []
                task_index = 0
                for channel in target_channels:
                    for keyword in keywords:
                        result = raw_results[task_index]
                        if isinstance(result, BaseException):
                            logger.error(
                                "[%s] '%s' 크롤링 실패: %s",
                                channel,
                                keyword,
                                result,
                            )
                            crawl_results.append(
                                CrawlResult(
                                    channel=channel,
                                    keyword=keyword,
                                    errors=[str(result)],
                                )
                            )
                        else:
                            crawl_results.append(result)
                        task_index += 1

                logger.info(
                    "크롤링 완료: 총 %d건 결과",
                    len(crawl_results),
                )
                return crawl_results
            finally:
                if browser_client:
                    await browser_client.__aexit__(None, None, None)
