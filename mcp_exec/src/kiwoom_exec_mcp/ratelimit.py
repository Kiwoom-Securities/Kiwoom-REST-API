"""직접 호출에 대한 인메모리 rate limit 미들웨어 (고정 윈도우).

두 축을 **겹쳐서** 제한한다:

- **IP당** — 자격증명 유무와 **무관하게 모든 요청**. env `KIWOOM_MCP_RATELIMIT`.
- **AppKey 지문당** — 자격증명을 실은 요청에 추가로. env `KIWOOM_MCP_RATELIMIT_APPKEY`.

왜 두 축이 다 필요한가 — 자원 DoS 벡터는 요청 하나가 `kiwoomcli` subprocess 하나를 띄운다는
점이고, 키움 자격증명 검증은 그 subprocess **안에서** 일어난다. 즉 유효하지 않은 키로 온
요청도 이미 스폰 비용을 유발한 뒤다. bearer 인증을 제거하면서 자원남용 대응을 rate limit에
맡겼으므로(MCP/docs/design.md §8) 두 축이 그 약속의 실체다.

- AppKey 축만 있으면: 헤더 값을 매번 바꿔(**지문 회전**) 버킷을 갈아타며 무제한이 된다.
- IP 축만 있으면: 한 IP 뒤의 여러 사용자가 서로의 몫을 잡아먹는다(플랫폼 프록시 뒤에서는
  IP가 전부 같을 수 있다) — 그래서 IP 축은 느슨한 backstop, AppKey 축이 사용자당 정밀 상한.

- 두 축 모두 env opt-in이고, 0/미설정이면 **그 축만** 무제한이다. 둘 다 0이면 서버가
  미들웨어를 붙이지 않는다(`server.py`의 `_build_middleware`).
- 윈도우 길이는 공유한다: `KIWOOM_MCP_RATELIMIT_WINDOW`(초, 기본 60).
- 단일 레플리카용 인메모리 카운터. 멀티 레플리카면 공유 저장소(Redis)로 교체.
- AppKey **원문은 보관하지 않는다** — sha256 지문 앞 16자만 버킷 키로 쓰고, 값은
  저장·로깅하지 않는다.
"""

from __future__ import annotations

import hashlib
import time

CRED_HEADER = b"x-kiwoom-app-key"  # ASGI 헤더 이름은 소문자 bytes
_MAX_TRACKED_BUCKETS = 10000


class FixedWindow:
    """버킷 키(IP 또는 AppKey 지문)별 고정 윈도우 카운터.

    `max_requests<=0`이면 비활성 — 카운트도 하지 않고 항상 통과시킨다.
    """

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, tuple[float, int]] = {}  # bucket -> (window_start, count)

    def over_limit(self, bucket: str) -> bool:
        if self.max_requests <= 0:
            return False
        now = time.monotonic()
        window_start, count = self._hits.get(bucket, (now, 0))
        if now - window_start >= self.window:
            window_start, count = now, 0
        count += 1
        self._hits[bucket] = (window_start, count)
        if len(self._hits) > _MAX_TRACKED_BUCKETS:
            self._prune(now)
        return count > self.max_requests

    def _prune(self, now: float) -> None:
        self._hits = {
            bucket: entry for bucket, entry in self._hits.items() if now - entry[0] < self.window
        }


def _fingerprint(appkey: bytes) -> str:
    """AppKey 지문 — 버킷 키용(원문 비보관, 비가역)."""
    return hashlib.sha256(appkey).hexdigest()[:16]


class RateLimitMiddleware:
    def __init__(
        self,
        app,
        *,
        max_requests: int,
        window_seconds: int,
        max_requests_appkey: int = 0,
    ) -> None:
        self.app = app
        self.window = window_seconds
        self._ip = FixedWindow(max_requests, window_seconds)
        self._appkey = FixedWindow(max_requests_appkey, window_seconds)

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers") or [])
        appkey = (headers.get(CRED_HEADER) or b"").strip()

        # IP 축은 자격증명 유무와 무관하게 센다 — 자격증명 요청을 면제하면 헤더 값을 매번
        # 바꾸는 것만으로 두 축을 모두 빠져나갈 수 있다(지문 회전).
        if self._ip.over_limit(_client_ip(scope, headers)):
            return await _reject(send, self.window, "ip")
        # 자격증명을 실은 요청은 지문 단위로 한 번 더 제한한다. 값의 유효성은 subprocess에서
        # 판정되므로 여기서는 알 수 없고, 알 필요도 없다.
        if appkey and self._appkey.over_limit(_fingerprint(appkey)):
            return await _reject(send, self.window, "app-key")

        return await self.app(scope, receive, send)


def _client_ip(scope, headers: dict) -> str:
    # 프록시(Railway/PlayMCP) 뒤이므로 X-Forwarded-For 첫 IP를 쓴다.
    # 원 클라이언트가 주장하는 값이라 스푸핑 가능 — best-effort 자원 보호용.
    xff = headers.get(b"x-forwarded-for")
    if xff:
        return xff.decode("latin-1").split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else "unknown"


async def _reject(send, retry_after: int, axis: str) -> None:
    body = f'{{"error":"rate limited: {axis} request quota exceeded"}}'.encode("ascii")
    await send({
        "type": "http.response.start",
        "status": 429,
        "headers": [
            (b"content-type", b"application/json"),
            (b"retry-after", str(retry_after).encode("ascii")),
            (b"content-length", str(len(body)).encode("ascii")),
        ],
    })
    await send({"type": "http.response.body", "body": body})
