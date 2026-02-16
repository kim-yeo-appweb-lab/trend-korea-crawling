import json
import logging
from datetime import datetime
from pathlib import Path

from src.core.models import CrawlResult

logger = logging.getLogger(__name__)


class ResultWriter:
    """크롤링 결과를 JSON 파일로 저장"""

    def __init__(self, output_dir: str = "./output") -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def write(self, results: list[CrawlResult]) -> Path:
        """결과를 JSON 파일로 저장하고 파일 경로를 반환한다."""
        total_articles = sum(len(r.articles) for r in results)

        output = {
            "crawled_at": datetime.now().isoformat(),
            "total_channels": len({r.channel for r in results}),
            "total_articles": total_articles,
            "results": [r.model_dump(mode="json") for r in results],
        }

        filename = f"crawl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self._output_dir / filename
        filepath.write_text(
            json.dumps(output, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        logger.info("결과 저장 완료: %s (기사 %d건)", filepath, total_articles)
        return filepath
