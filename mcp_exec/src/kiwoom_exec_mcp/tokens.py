"""요청 헤더 자격증명별 접근 토큰을 **서버 프로세스 메모리에만** 짧게 보관한다.

왜: HTTP 멀티테넌트 경로는 토큰을 디스크에 두지 않는다(MCP/docs/design.md §6). 그렇다고 요청마다
subprocess가 `/oauth2/token`을 부르면 키움 `au10001` 유량 제한(초당 ~2회, 2026-08-18 demo
실측)에 걸려 같은 키로 조회를 3~5개만 연달아/동시에 보내도 절반이 `1700`으로 거절된다.
그래서 서버가 키별로 **한 번** 발급해 메모리에 들고, subprocess에는 env
(`KIWOOM_ACCESS_TOKEN` / `_EXPIRES_AT`)로 건네 발급 호출을 없앤다.

- 보관 기간은 `Settings.token_ttl`(`KIWOOM_MCP_TOKEN_TTL`, 기본 900s)로 **절대** 상한을 둔다(sliding 아님).
  키움 토큰 자체는 ~24h 유효하지만, 서버 RAM에 사용자 토큰이 머무는 시간을 짧게 묶어
  프로세스 침해 시 노출 범위를 제한하고, 다른 곳에서 `auth revoke`된 토큰이 stale로 남는
  시간도 TTL로 묶는다(그 사이 요청은 subprocess가 스스로 재발급해 성공한다).
- 키움은 유효 토큰이 있으면 같은 토큰을 돌려주므로 TTL마다의 재발급은 사실상 "현재 토큰
  조회"이고 다른 클라이언트의 토큰을 끊지 않는다.
- 같은 키의 동시 첫 요청은 지문별 lock으로 **단일 발급**(single-flight)한다 — cold start
  버스트가 `au10001` 유량에 걸리지 않게.
- 키/시크릿은 발급 순간에만 `StaticSecretProvider`에 담겨 쓰이고 보관하지 않는다. 캐시
  키는 `sha256(appkey:secret)`(원문 비가역), 값은 토큰·만료뿐. 디스크에 쓰지 않는다.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import partial

import anyio
from kiwoom.core.auth import KiwoomAuth
from kiwoom.core.token_store import MemoryTokenStore

from .tenant import TenantCredentials

_MAX_ENTRIES = 10000
# 키움 만료(expires_dt)에 이만큼 못 미치면 재발급한다 — 만료 직전 토큰을 subprocess에
# 넘겨 그쪽에서 다시 발급하게 만들지 않는다.
_EXPIRY_MARGIN = timedelta(minutes=10)


@dataclass(frozen=True)
class IssuedToken:
    access_token: str
    expires_at: datetime  # 키움이 준 만료(UTC)
    cached_until: float  # monotonic — 서버 보관 상한


class TokenCache:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, IssuedToken] = {}
        self._locks: dict[str, anyio.Lock] = {}
        self._locks_guard = anyio.Lock()

    async def attach(self, credentials: TenantCredentials) -> TenantCredentials:
        """자격증명에 유효 토큰을 얹어 돌려준다(캐시 hit이면 발급 호출 없음)."""
        issued = await self._get(credentials)
        return credentials.with_token(issued.access_token, issued.expires_at)

    async def _get(self, credentials: TenantCredentials) -> IssuedToken:
        key = _fingerprint(credentials)
        hit = self._fresh(key)
        if hit is not None:
            return hit
        lock = await self._lock_for(key)
        async with lock:
            hit = self._fresh(key)  # lock 대기 중 다른 요청이 발급했을 수 있다
            if hit is not None:
                return hit
            access_token, expires_at = await anyio.to_thread.run_sync(partial(_issue, credentials))
            issued = IssuedToken(
                access_token=access_token,
                expires_at=expires_at,
                cached_until=time.monotonic() + self.ttl_seconds,
            )
            if self.ttl_seconds > 0:
                self._store(key, issued)
            return issued

    def _fresh(self, key: str) -> IssuedToken | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.cached_until or datetime.now(UTC) >= entry.expires_at - _EXPIRY_MARGIN:
            self._entries.pop(key, None)
            return None
        return entry

    def _store(self, key: str, issued: IssuedToken) -> None:
        if len(self._entries) >= _MAX_ENTRIES:
            self._evict_expired()
        if len(self._entries) >= _MAX_ENTRIES:
            # 여전히 가득이면 가장 먼저 만료될 항목을 비운다 — 캐시는 성능용이라 잃어도 재발급으로 복구.
            oldest = min(self._entries, key=lambda k: self._entries[k].cached_until)
            self._entries.pop(oldest, None)
        self._entries[key] = issued

    def _evict_expired(self) -> None:
        now = time.monotonic()
        self._entries = {k: v for k, v in self._entries.items() if v.cached_until > now}

    async def _lock_for(self, key: str) -> anyio.Lock:
        async with self._locks_guard:
            lock = self._locks.get(key)
            if lock is None:
                if len(self._locks) >= _MAX_ENTRIES:
                    self._locks.clear()
                lock = self._locks[key] = anyio.Lock()
            return lock


def _fingerprint(credentials: TenantCredentials) -> str:
    raw = f"{credentials.mode}:{credentials.appkey}:{credentials.secretkey}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _issue(credentials: TenantCredentials) -> tuple[str, datetime]:
    """블로킹 발급 — 스레드에서 실행된다. 자격증명은 이 호출 안에서만 객체에 담긴다.

    (access_token, 키움 만료 UTC)를 돌려준다.
    """
    # 계약(kwcli>=1.1.0)에 속한 심볼이라 여기서만 import — stdio 전용 환경(구버전 kwcli)에서도
    # 서버 모듈은 로드되어야 한다. HTTP 경로는 runner.require_token_contract가 먼저 확인한다.
    from kiwoom.core.secrets import StaticSecretProvider

    auth = KiwoomAuth(
        credentials.mode,  # type: ignore[arg-type]
        StaticSecretProvider(credentials.appkey, credentials.secretkey, source="header"),
        MemoryTokenStore(),
    )
    access_token = auth.refresh_access_token()
    record = auth.token_store.load(auth.mode)
    if record is None:  # refresh_access_token은 저장까지 하므로 도달 불가; 방어적 확인
        raise RuntimeError("token issued but not stored")
    return access_token, record.expires_at
