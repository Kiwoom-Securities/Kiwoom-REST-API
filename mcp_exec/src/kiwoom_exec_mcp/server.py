"""kiwoom-exec-mcp — kiwoomcli를 래핑해 실제 키움 OpenAPI를 호출하는 MCP 서버.

- read/account_read 명령만 kiwoom_query로 노출한다 (safety_policy를
  kwcli 번들 maps/api_commands.csv에서 읽어 강제).
- 서버 설정은 전부 `KIWOOM_MCP_*` env → `config.Settings` (한 곳에서 읽는다):
  전송(stdio|http)·주문 도구 게이트·동시성·토큰 TTL·rate limit·진단 도구.
- 자격증명 소스는 요청 컨텍스트로 자동 결정된다(`tenant.TenantCredentials`):
  * HTTP 요청 헤더(X-Kiwoom-App-Key/-App-Secret/-Mode)가 있으면 그 값으로 실행
    (멀티테넌트). 서버는 키 없이 기동한다.
  * 헤더가 없으면(stdio 등) 프로세스 env(APP_KEY/APP_SECRET/KIWOOM_MODE 또는
    KIWOOM_PROFILE)로 폴백 — 로컬 단일 테넌트.
  시크릿은 헤더로만 받는다. URL query는 읽지 않는다(로그 유출 방지). 키를 인자로
  받는 도구는 만들지 않는다.
- HTTP 경로의 접근 토큰은 디스크에 쓰지 않는다. 서버가 자격증명별로 한 번 발급해 메모리에
  `Settings.token_ttl`만큼 들고(`tokens.TokenCache`) subprocess에 env로 건네며, subprocess는
  KIWOOM_TOKEN_STORE=memory로 그 토큰을 자기 메모리에서만 쓴다(`runner`).
"""

from __future__ import annotations

import csv
from functools import partial
from importlib import resources

import anyio
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

from kiwoom.core.errors import KiwoomError

from .config import Settings, load_settings
from .runner import KiwoomCliError, mask_secrets, options_to_args, require_token_contract, run_cli, run_json
from .tenant import CREDENTIAL_HEADERS, TenantCredentials
from .tokens import TokenCache

READ_POLICIES = {"read", "account_read"}
ORDER_POLICIES = {"order_write"}

SETTINGS: Settings = load_settings()

mcp = FastMCP(
    "kiwoom-exec",
    instructions=(
        "키움증권 OpenAPI 실행 서버입니다. kiwoom_help로 명령 옵션을 확인하고 "
        "kiwoom_query로 조회를 실행하세요. command_path는 kiwoom-spec 서버의 "
        "spec_search 결과나 kiwoom_commands 목록에서 얻습니다. 주문 도구는 "
        "운영자가 KIWOOM_MCP_ALLOW_ORDERS=1을 설정한 경우에만 존재합니다. "
        "kiwoom_help는 요청 옵션만 보여줍니다 — 응답 필드를 다루는 코드를 짜기 전에 "
        "kiwoom-spec 서버가 있으면 spec_show/get_example을, 없으면 kiwoom_query를 "
        "먼저 실행해 실제 응답 필드를 확인하세요."
    ),
)


def _load_command_index() -> dict[str, dict]:
    maps = resources.files("kiwoom_cli").joinpath("maps/api_commands.csv")
    with maps.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {row["command_path"].removeprefix("kiwoomcli ").strip(): row for row in rows}


_COMMANDS = _load_command_index()


def _lookup(command_path: str) -> dict | None:
    return _COMMANDS.get(command_path.removeprefix("kiwoomcli ").strip())


def _guard(command_path: str, allowed_policies: set[str]) -> list[str] | dict:
    """command_path를 검증하고 실행할 kiwoomcli argv를 돌려준다.

    검증 실패(미지 명령 / 미구현 / 정책 불일치) 시에는 MCP 도구가 그대로 반환할
    error dict를 돌려주고, 성공 시에는 kiwoomcli 접두어를 뗀 argv 리스트를 돌려준다.
    """
    row = _lookup(command_path)
    if row is None:
        return {"error": f"unknown command_path: {command_path!r}. kiwoom_commands로 목록을 확인하세요."}
    if row["status"] != "implemented":
        return {"error": f"{command_path!r} is not implemented (status={row['status']})."}
    if row["safety_policy"] not in allowed_policies:
        return {
            "error": (
                f"{command_path!r} has safety_policy={row['safety_policy']!r}; "
                f"this tool only accepts {sorted(allowed_policies)}."
            )
        }
    return row["command_path"].removeprefix("kiwoomcli ").split()


def _resolve_credentials() -> TenantCredentials | None:
    """요청 HTTP 헤더에서 자격증명을 읽는다. HTTP 요청이 없으면(stdio) None → 프로세스 env."""
    return TenantCredentials.from_headers(get_http_headers())  # HTTP 요청이 없으면 {} (예외 없음)


# query/help가 공유하는 subprocess 동시 실행 리미터. 요청마다 kiwoomcli(+pandas) 프로세스가
# 뜨는데 동시에 너무 많이 뜨면 합산 RSS가 컨테이너 한도를 넘겨 OOM이 난다. 초과 호출은 거부가
# 아니라 슬롯이 날 때까지 대기(백프레셔)하므로, 버스트에도 크래시 없이 완만히 느려진다.
_CLI_LIMITER = anyio.CapacityLimiter(SETTINGS.max_concurrency)

# 헤더 자격증명별 접근 토큰의 서버 메모리 캐시(디스크 없음, TTL 상한). tokens.py 참고.
_TOKENS = TokenCache(SETTINGS.token_ttl)


async def _execute(parts: list[str], options: dict | None, *, confirm: bool = False) -> object:
    """검증된 argv로 kiwoomcli를 실행하고 파싱된 JSON(또는 error dict)을 돌려준다.

    자격증명은 요청 컨텍스트에서 해석하고, 블로킹 subprocess는 스레드로 오프로드한다.
    confirm=True면 실주문 전송(--confirm)을 덧붙인다.
    """
    args = [*parts, *options_to_args(options)]
    if confirm:
        args.append("--confirm")
    credentials = _resolve_credentials()
    if credentials is not None:
        # 헤더 자격증명이면 서버가 들고 있는(또는 지금 발급한) 토큰을 얹는다.
        # stdio(None)는 그대로 — subprocess가 사용자 홈 캐시로 인증한다.
        try:
            credentials = await _TOKENS.attach(credentials)
        except (KiwoomError, ValueError, OSError) as exc:
            # 발급 실패(키 오류·유량·네트워크·잘못된 mode). 메시지에 키/시크릿이 실리지 않게 스크럽.
            return {"error": f"token issue failed: {mask_secrets(str(exc), credentials.secret_values())}"}
    try:
        result = await anyio.to_thread.run_sync(
            partial(run_json, args, credentials=credentials),
            limiter=_CLI_LIMITER,
        )
    except KiwoomCliError as exc:
        result = {"error": str(exc), "exit_code": exc.exit_code}
    return result


async def _guarded_query(command_path: str, options: dict | None, allowed_policies: set[str]) -> object:
    """정책을 검증한 뒤 조회를 실행한다(검증 실패 시 error dict를 그대로 반환)."""
    guarded = _guard(command_path, allowed_policies)
    if isinstance(guarded, dict):
        return guarded
    return await _execute(guarded, options)


def kiwoom_commands(market: str = "", group: str = "") -> list[dict]:
    """Lists executable Kiwoom Securities(키움증권) OpenAPI commands with command_path, API name, and safety_policy.

    Narrow with market/group — the full list is 330+ rows.

    Args:
        market: "domestic" | "overseas" | "auth" (empty = all)
        group: CLI group name, e.g. "candles", "stocks", "accounts" (empty = all)
    """
    out = []
    for path, row in sorted(_COMMANDS.items()):
        if row["status"] != "implemented":
            continue
        path_market = path.split()[0] if path else ""
        # 해외 행의 cli_group은 "overseas accounts"처럼 market 접두어를
        # 포함하므로 순수 그룹명으로 정규화한다.
        path_group = row["cli_group"].removeprefix("overseas ").strip()
        if market and path_market != market:
            continue
        if group and path_group != group:
            continue
        out.append({
            "command_path": path,
            "api_id": row["api_id"],
            "api_name": row["api_name"],
            "market": path_market,
            "group": path_group,
            "safety_policy": row["safety_policy"],
        })
    return out


async def kiwoom_help(command_path: str) -> str:
    """Returns the option contract (--help output) of one Kiwoom Securities(키움증권) command, for confirming option names before kiwoom_query.

    Args:
        command_path: e.g. "domestic stocks info" (the "kiwoomcli" prefix may be omitted)
    """
    row = _lookup(command_path)
    if row is None:
        return f"unknown command_path: {command_path!r}"
    parts = row["command_path"].removeprefix("kiwoomcli ").split()
    creds = _resolve_credentials()
    try:
        return await anyio.to_thread.run_sync(
            partial(run_cli, [*parts, "--help"], credentials=creds, timeout=30),
            limiter=_CLI_LIMITER,
        )
    except KiwoomCliError as exc:
        return str(exc)


async def kiwoom_query(command_path: str, options: dict | None = None) -> object:
    """Executes a read-only Kiwoom Securities(키움증권) OpenAPI command (read/account_read) and returns the JSON result.

    Order (write) commands cannot be run with this tool. Account numbers in
    responses are masked automatically by CLI policy.

    Args:
        command_path: e.g. "domestic stocks info" (the "kiwoomcli" prefix may be omitted)
        options: Option dict, e.g. {"code": "005930"} -> --code 005930
    """
    return await _guarded_query(command_path, options, READ_POLICIES)


mcp.tool(
    kiwoom_commands,
    annotations={
        "title": "List Kiwoom Commands",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,  # 번들 CSV만 읽는다
    },
)
mcp.tool(
    kiwoom_help,
    annotations={
        "title": "Show Kiwoom Command Options",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,  # 로컬 --help subprocess, 네트워크 없음
    },
)
mcp.tool(
    kiwoom_query,
    annotations={
        "title": "Run Kiwoom Query",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,  # 키움 OpenAPI 실호출
    },
)


if SETTINGS.allow_orders:

    async def kiwoom_order_preview(command_path: str, options: dict | None = None) -> object:
        """Returns a non-transmitted preview of a Kiwoom Securities(키움증권) order.

        Runs without --confirm, so no order is ever submitted under any condition.

        Args:
            command_path: e.g. "domestic orders buy" (the "kiwoomcli" prefix may be omitted)
            options: Option dict, e.g. {"code": "005930", "qty": 1}
        """
        return await _guarded_query(command_path, options, ORDER_POLICIES)

    async def kiwoom_order_submit(
        command_path: str, options: dict | None = None, confirm: bool = False
    ) -> object:
        """Submits a real order to Kiwoom Securities(키움증권). Transmits with --confirm only when confirm=true is set explicitly.

        Without confirm nothing is sent and guidance is returned instead (for a
        non-transmitted preview use kiwoom_order_preview). Overseas order writes
        stay blocked by the CLI even with --confirm while coverage is preview-only.

        NOTE: confirm can be set by the caller (an AI included). Human approval
        relies on the client's tool-execution approval or a future plugin hook.

        Args:
            command_path: e.g. "domestic orders buy" (the "kiwoomcli" prefix may be omitted)
            options: Option dict, e.g. {"code": "005930", "qty": 1}
            confirm: Must be true to actually transmit the order
        """
        if not confirm:
            return {"error": "confirm=true 없이는 전송하지 않습니다. 미리보기는 kiwoom_order_preview를 쓰세요."}
        guarded = _guard(command_path, ORDER_POLICIES)
        if isinstance(guarded, dict):
            return guarded
        return await _execute(guarded, options, confirm=True)

    mcp.tool(
        kiwoom_order_preview,
        annotations={
            "title": "Preview Kiwoom Order",
            # --confirm을 붙이지 않아 주문이 접수되지 않는다 → 읽기 전용.
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    mcp.tool(
        kiwoom_order_submit,
        annotations={
            "title": "Submit Kiwoom Order",
            "readOnlyHint": False,
            # 이 도구 하나가 command_path로 매수·매도·정정·취소를 모두 다룬다 →
            # 워스트케이스(취소/매도) 기준으로 파괴적이라고 선언한다.
            "destructiveHint": True,
            "idempotentHint": False,  # 반복 호출하면 주문이 중복 접수된다
            "openWorldHint": True,
        },
    )


if SETTINGS.debug_headers:

    def kiwoom_debug_headers() -> dict:
        """도착한 요청 헤더의 이름·길이와 서버가 해석한 mode를 반환합니다(진단용).

        헤더 **값은 반환하지 않습니다** — 이름과 문자 길이만 돌려줍니다.
        플랫폼이 자격증명 헤더를 실제로 전달하는지 확인할 때만 임시로 켭니다.
        """
        headers = get_http_headers()
        creds = _resolve_credentials()
        return {
            "received_header_names": sorted(headers),
            "credential_headers": {
                name: (len(headers[name].strip()) if name in headers else None)
                for name in CREDENTIAL_HEADERS
            },
            "resolved_mode": creds.mode if creds else None,
            "credentials_resolved": creds is not None,
        }

    mcp.tool(
        kiwoom_debug_headers,
        annotations={
            "title": "Debug Received Headers",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )


def _build_middleware():
    """직접호출 rate limit을 opt-in 구성 — IP 축과 AppKey 지문 축을 겹쳐서 (`Settings.ratelimit*`).

    각 값이 0/미설정이면 그 축만 무제한이고, 둘 다 0이면 미들웨어를 붙이지 않는다.
    두 축이 다 필요하다: AppKey 축이 없으면 아무 값이나 헤더에 실어 제한을 빠져나가고,
    IP 축이 없으면 헤더 값을 매번 바꿔(지문 회전) AppKey 축까지 빠져나간다. 자격증명
    유효성은 subprocess에서 판정되므로 어느 쪽이든 스폰 비용은 이미 발생한다.
    """
    if not SETTINGS.ratelimit_enabled:
        return None
    from starlette.middleware import Middleware

    from .ratelimit import RateLimitMiddleware

    return [
        Middleware(
            RateLimitMiddleware,
            max_requests=SETTINGS.ratelimit,
            window_seconds=SETTINGS.ratelimit_window,
            max_requests_appkey=SETTINGS.ratelimit_appkey,
        )
    ]


def main() -> None:
    """콘솔 스크립트(kiwoom-exec-mcp) 진입점 — 전송은 `Settings.transport`로 고른다.

    로컬은 기본 stdio(단일 테넌트, 프로세스 env 자격증명), 원격 배포는
    KIWOOM_MCP_TRANSPORT=http로 streamable HTTP(멀티테넌트, 요청 헤더 자격증명).
    """
    if SETTINGS.http:
        require_token_contract()  # 멀티테넌트 경로는 계약 없는 kwcli로 띄우지 않는다(fail fast)
        mcp.run(transport="http", host=SETTINGS.host, port=SETTINGS.port, middleware=_build_middleware())
    else:
        mcp.run()


if __name__ == "__main__":
    main()
