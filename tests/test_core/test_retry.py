import pytest

from src.core.exceptions import FetchError
from src.core.retry import retry


class TestRetry:
    """retry 데코레이터 테스트"""

    async def test_success_without_retry(self):
        """성공 시 재시도 없이 바로 반환"""
        call_count = 0

        @retry(max_retries=3, base_delay=0.0)
        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        result = await succeed()

        assert result == "ok"
        assert call_count == 1

    async def test_success_after_retry(self):
        """실패 후 재시도에서 성공"""
        call_count = 0

        @retry(max_retries=3, base_delay=0.0)
        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise FetchError("일시적 오류")
            return "ok"

        result = await fail_then_succeed()

        assert result == "ok"
        assert call_count == 3

    async def test_max_retries_exceeded(self):
        """최대 재시도 횟수 초과 시 예외 발생"""
        call_count = 0

        @retry(max_retries=2, base_delay=0.0)
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise FetchError("항상 실패")

        with pytest.raises(FetchError, match="항상 실패"):
            await always_fail()

        # 최초 1회 + 재시도 2회 = 총 3회 호출
        assert call_count == 3

    async def test_non_retryable_exception_not_retried(self):
        """retry_on에 지정되지 않은 예외는 재시도하지 않음"""
        call_count = 0

        @retry(max_retries=3, base_delay=0.0, retry_on=(FetchError,))
        async def raise_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("재시도 대상이 아닌 예외")

        with pytest.raises(ValueError, match="재시도 대상이 아닌 예외"):
            await raise_value_error()

        # 재시도 없이 1회만 호출
        assert call_count == 1
