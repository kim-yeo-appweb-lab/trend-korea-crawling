from bs4 import BeautifulSoup

from src.shared.text_cleaner import clean_text, extract_text_from_html


class TestCleanText:
    """clean_text 함수 테스트"""

    def test_remove_consecutive_spaces(self):
        """연속 공백을 단일 공백으로 치환"""
        assert clean_text("hello   world") == "hello world"
        assert clean_text("여러   개의   공백") == "여러 개의 공백"

    def test_remove_empty_lines(self):
        """빈 줄 제거"""
        text = "첫째 줄\n\n\n둘째 줄\n\n셋째 줄"
        assert clean_text(text) == "첫째 줄\n둘째 줄\n셋째 줄"

    def test_strip_whitespace(self):
        """앞뒤 공백 제거"""
        assert clean_text("  앞뒤 공백  ") == "앞뒤 공백"
        assert clean_text("\n\n본문\n\n") == "본문"

    def test_tabs_replaced(self):
        """탭 문자를 공백으로 치환"""
        assert clean_text("탭\t\t문자") == "탭 문자"

    def test_empty_string(self):
        """빈 문자열 입력"""
        assert clean_text("") == ""
        assert clean_text("   ") == ""


class TestExtractTextFromHtml:
    """extract_text_from_html 함수 테스트"""

    def test_extract_text_from_tag(self):
        """BeautifulSoup Tag에서 텍스트 추출"""
        html = "<div><p>첫 번째 문단</p><p>두 번째 문단</p></div>"
        soup = BeautifulSoup(html, "lxml")
        div = soup.find("div")

        result = extract_text_from_html(div)

        assert "첫 번째 문단" in result
        assert "두 번째 문단" in result

    def test_nested_tags(self):
        """중첩 태그에서 텍스트만 추출"""
        html = "<div><span><strong>강조</strong> 텍스트</span></div>"
        soup = BeautifulSoup(html, "lxml")
        div = soup.find("div")

        result = extract_text_from_html(div)

        assert "강조" in result
        assert "텍스트" in result
