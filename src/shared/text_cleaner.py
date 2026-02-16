import re

from bs4 import Tag


def clean_text(text: str) -> str:
    """연속 공백 제거, strip, 빈 줄 정리"""
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text.strip()


def extract_text_from_html(element: Tag) -> str:
    """BeautifulSoup element에서 텍스트만 추출"""
    return clean_text(element.get_text(separator="\n"))
