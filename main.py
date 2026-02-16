import argparse
import asyncio
import logging

from config.logging import setup_logging
from config.settings import CrawlerSettings
from src.pipeline.channel_registry import get_available_channels
from src.pipeline.orchestrator import CrawlOrchestrator
from src.pipeline.result_writer import ResultWriter

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """CLI 인자 파싱"""
    parser = argparse.ArgumentParser(description="한국 뉴스 크롤링 파이프라인")
    parser.add_argument(
        "-k",
        "--keywords",
        nargs="+",
        required=True,
        help="검색 키워드",
    )
    parser.add_argument(
        "-c",
        "--channels",
        nargs="+",
        default=None,
        choices=get_available_channels(),
        help="크롤링할 채널 (기본: 전체)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="최대 페이지 수",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="출력 디렉토리",
    )
    return parser.parse_args()


async def main() -> None:
    """메인 진입점"""
    args = parse_args()
    setup_logging()

    settings = CrawlerSettings()

    # CLI 인자로 설정 오버라이드
    overrides: dict = {}
    if args.max_pages is not None:
        overrides["max_pages"] = args.max_pages
    if overrides:
        settings = settings.model_copy(update=overrides)

    orchestrator = CrawlOrchestrator(settings)
    results = await orchestrator.run(args.keywords, args.channels)

    output_dir = args.output_dir or settings.output_dir
    writer = ResultWriter(output_dir)
    filepath = writer.write(results)

    # 결과 요약 출력
    total_articles = sum(len(r.articles) for r in results)
    total_errors = sum(len(r.errors) for r in results)
    print(f"\n크롤링 완료! 기사 {total_articles}건, 에러 {total_errors}건")
    print(f"결과 파일: {filepath}")


if __name__ == "__main__":
    asyncio.run(main())
