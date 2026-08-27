"""exec 서버가 읽는 환경변수 전부 — 이름·기본값·파싱 규칙의 단일 출처.

서버 동작을 바꾸는 `KIWOOM_MCP_*`는 여기서만 읽는다(server/tokens/runner는 `Settings`를 본다).
README·.env.example의 표는 이 파일과 맞춰 둔다. 자격증명(`APP_KEY` 등)과 kwcli 계약
(`KIWOOM_TOKEN_STORE`, `KIWOOM_ACCESS_TOKEN*`)은 서버 설정이 아니라 subprocess env라서
`runner.py`가 다룬다.

파싱 규칙:
- 게이트(`ALLOW_ORDERS`, `DEBUG_HEADERS`)는 값이 **정확히 `1`** 일 때만 켜진다. `true`/`yes`는 off.
- 정수 값은 비어 있으면 기본값, 숫자가 아니면 **기동 시 ValueError**로 멈춘다 — rate limit이나
  TTL의 오타가 조용히 "무제한/기본값"으로 떨어지는 것보다 안 뜨는 편이 안전하다.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass

ENV_TRANSPORT = "KIWOOM_MCP_TRANSPORT"
ENV_HOST = "KIWOOM_MCP_HOST"
ENV_PORT = "KIWOOM_MCP_PORT"
ENV_ALLOW_ORDERS = "KIWOOM_MCP_ALLOW_ORDERS"
ENV_DEBUG_HEADERS = "KIWOOM_MCP_DEBUG_HEADERS"
ENV_MAX_CONCURRENCY = "KIWOOM_MCP_MAX_CONCURRENCY"
ENV_TOKEN_TTL = "KIWOOM_MCP_TOKEN_TTL"
ENV_RATELIMIT = "KIWOOM_MCP_RATELIMIT"
ENV_RATELIMIT_APPKEY = "KIWOOM_MCP_RATELIMIT_APPKEY"
ENV_RATELIMIT_WINDOW = "KIWOOM_MCP_RATELIMIT_WINDOW"

DEFAULT_TRANSPORT = "stdio"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_MAX_CONCURRENCY = 8
DEFAULT_TOKEN_TTL = 900
DEFAULT_RATELIMIT_WINDOW = 60


@dataclass(frozen=True)
class Settings:
    transport: str  # "stdio" | "http"
    host: str
    port: int
    allow_orders: bool  # 주문 도구 등록 여부
    debug_headers: bool  # 진단 도구 등록 여부
    max_concurrency: int  # 동시 kiwoomcli subprocess 상한 (>=1)
    token_ttl: int  # 헤더 자격증명별 토큰의 서버 메모리 보관 상한(초). 0=요청마다 발급
    ratelimit: int  # IP당 윈도우 상한. 0=off
    ratelimit_appkey: int  # AppKey 지문당 윈도우 상한. 0=off
    ratelimit_window: int  # 두 축이 공유하는 윈도우(초)

    @property
    def http(self) -> bool:
        return self.transport in ("http", "streamable-http")

    @property
    def ratelimit_enabled(self) -> bool:
        return self.ratelimit > 0 or self.ratelimit_appkey > 0


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    env = os.environ if environ is None else environ
    return Settings(
        transport=(env.get(ENV_TRANSPORT) or DEFAULT_TRANSPORT).strip().lower(),
        host=env.get(ENV_HOST) or DEFAULT_HOST,
        # PaaS(Railway 등)는 $PORT를 주입한다. 우선순위: KIWOOM_MCP_PORT > PORT > 기본값.
        port=_int(env.get(ENV_PORT) or env.get("PORT"), DEFAULT_PORT, name=f"{ENV_PORT}/PORT"),
        allow_orders=env.get(ENV_ALLOW_ORDERS) == "1",
        debug_headers=env.get(ENV_DEBUG_HEADERS) == "1",
        max_concurrency=max(1, _int(env.get(ENV_MAX_CONCURRENCY), DEFAULT_MAX_CONCURRENCY, name=ENV_MAX_CONCURRENCY)),
        token_ttl=max(0, _int(env.get(ENV_TOKEN_TTL), DEFAULT_TOKEN_TTL, name=ENV_TOKEN_TTL)),
        ratelimit=max(0, _int(env.get(ENV_RATELIMIT), 0, name=ENV_RATELIMIT)),
        ratelimit_appkey=max(0, _int(env.get(ENV_RATELIMIT_APPKEY), 0, name=ENV_RATELIMIT_APPKEY)),
        ratelimit_window=max(1, _int(env.get(ENV_RATELIMIT_WINDOW), DEFAULT_RATELIMIT_WINDOW, name=ENV_RATELIMIT_WINDOW)),
    )


def _int(raw: str | None, default: int, *, name: str) -> int:
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
