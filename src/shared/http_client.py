import httpx


class HttpClient:
    """httpx 기반 HTTP 클라이언트"""

    def __init__(self, user_agent: str, timeout: int = 30) -> None:
        self._user_agent = user_agent
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            headers={"User-Agent": self._user_agent},
            timeout=httpx.Timeout(self._timeout),
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *exc) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get(self, url: str) -> str:
        """URL에서 HTML을 가져온다"""
        if not self._client:
            raise RuntimeError("HttpClient는 async context manager로 사용해야 합니다")
        response = await self._client.get(url)
        response.raise_for_status()
        return response.text
