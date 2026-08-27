"""kiwoom-spec-mcp — 무자격(credential-free) 스펙 검색 + 예제 코드 MCP 서버.

키움 OpenAPI 스펙(kwcli 번들 kiwoom_api_spec.json)을 검색하고, 해당 API의
runnable 예제 코드를 GitHub 저장소에서 raw로 받아 돌려준다.

로컬 파일시스템 의존이 없다: 예제의 저장소 내 경로는 kwcli 번들
maps/api_commands.csv로 결정적으로 계산하고 raw.githubusercontent.com에서
받아온다. 예제 출처는 아래 상수로 고정한다 — 이 서버가 서빙하는 코드의
신뢰 경계이므로 env 등으로 오버라이드할 수 없다.

이 서버는 **자격증명을 받지 않는다**(키움 API 미호출). 전송은 env
KIWOOM_MCP_TRANSPORT로 선택: stdio(기본) 또는 http.
"""

from __future__ import annotations

import csv
import os
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from functools import lru_cache
from importlib import resources

from fastmcp import FastMCP

from kiwoom import specs

# 키움증권 공식 공개 예제 저장소 (함수명 파일만 게시됨). 오버라이드 불가.
EXAMPLES_REPO = "Kiwoom-Securities/Kiwoom-REST-API"
EXAMPLES_REF = "main"

mcp = FastMCP(
    "kiwoom-spec",
    instructions=(
        "키움증권 REST/WebSocket OpenAPI 스펙 검색과 예제 코드 조회 서버입니다. "
        "사용자가 만들고 싶은 기능을 말하면 spec_search로 API를 찾고, "
        "spec_show로 요청/응답 계약을 확인한 뒤, get_example로 실행 가능한 "
        "예제 코드를 가져와 답하세요. 이 서버는 키움 API를 호출하지 않습니다."
    ),
)


_MARKET_BY_CATEGORY = {"국내주식": "domestic", "미국주식": "overseas", "OAuth 인증": "auth"}


@lru_cache(maxsize=1)
def _command_index() -> dict[str, dict]:
    """api_id → CLI 정렬 메타(market/group/command_path/예제 경로 재료).

    kwcli 번들 maps/api_commands.csv에서 결정적으로 계산한다. market은
    command_path 첫 토큰(domestic|overseas|auth), CLI 미노출 행은
    major_category로 폴백한다.
    """
    maps = resources.files("kiwoom_cli").joinpath("maps/api_commands.csv")
    with maps.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    index: dict[str, dict] = {}
    for row in rows:
        command_path = row["command_path"].removeprefix("kiwoomcli ").strip()
        parts = command_path.split()
        market = parts[0] if parts else _MARKET_BY_CATEGORY.get(row["major_category"], "")
        index[row["api_id"]] = {
            "market": market,
            # 해외 행의 cli_group은 "overseas accounts"처럼 market 접두어를
            # 포함하므로 순수 그룹명으로 정규화한다 (market과 직교하게).
            "group": row["cli_group"].removeprefix("overseas ").strip(),
            "command_path": command_path,
            # 공식 저장소는 함수명 파일만 게시한다 (api-id 중복 파일 없음).
            "example_path": f"examples/{row['major_category']}/{row['subcategory']}/{row['function_name']}.py",
            "safety_policy": row["safety_policy"],
        }
    return index


# write성 API의 예제에만 응답으로 실리는 경고. 읽기 예제는 오버헤드 없음.
# maps에 실리는 정책은 read / account_read / order_write / auth_write 네 종뿐이라
# 아래 두 키가 write성 전부를 덮는다(order_write 17 + auth_write 2 = 19개).
# `review_required`는 미큐레이션 스캐폴드 행의 기본값이고 그런 행은 maps에 실리지
# 않으므로(전 행 status=implemented) 여기서 다루지 않는다.
_SAFETY_NOTES = {
    "order_write": "실행 시 실제 주문·환전 신청이 전송될 수 있습니다. demo 모드 우선으로 실행하세요.",
    "auth_write": "실행 시 토큰 발급/폐기가 일어나 기존 세션의 토큰에 영향을 줄 수 있습니다.",
}


@lru_cache(maxsize=256)
def _fetch_raw(repo_path: str) -> str:
    url = (
        f"https://raw.githubusercontent.com/{EXAMPLES_REPO}/{EXAMPLES_REF}/"
        + urllib.parse.quote(repo_path)
    )
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.read().decode("utf-8")


def spec_search(query: str, market: str = "", group: str = "", limit: int = 10) -> list[dict]:
    """Searches Kiwoom Securities(키움증권) OpenAPI specs by API ID, name, category, or request/response field.

    Narrowing candidates with market/group first aligns results with the CLI
    taxonomy and saves context. Check valid combinations with spec_groups.

    Args:
        query: Search term. Must be Korean — the spec index (API names, field
            labels) is in Korean, so English terms return no hits.
            e.g. "주문가능수량", "일봉 차트", "ka10081", "stk_cd"
        market: "domestic" | "overseas" | "auth" (empty = all)
        group: CLI group name, e.g. "candles", "stocks", "accounts" (empty = all)
        limit: Maximum number of results
    """
    entries = specs.load_search_entries()
    index = _command_index()
    if market or group:
        def _keep(entry: dict) -> bool:
            info = index.get(str(entry.get("api_id")), {})
            if market and info.get("market") != market:
                return False
            if group and info.get("group") != group:
                return False
            return True

        entries = [entry for entry in entries if _keep(entry)]
    results = specs.search_entries(entries, query=query, limit=limit)
    slim = []
    for row in results:
        info = index.get(str(row.get("api_id")), {})
        slim.append({
            "api_id": row.get("api_id"),
            "api_name": row.get("api_name"),
            "market": info.get("market", ""),
            "group": info.get("group", ""),
            "command_path": info.get("command_path", ""),
            "method": row.get("method"),
            "url": row.get("url"),
        })
    return slim


def spec_show(api_id: str) -> dict:
    """Returns the full spec of one Kiwoom Securities(키움증권) OpenAPI endpoint: HTTP method, path, and the request/response field contract.

    Args:
        api_id: Kiwoom API ID, e.g. "ka10081". Find it with spec_search.
    """
    try:
        return dict(specs.get_api_spec(api_id))
    except Exception as exc:  # unknown api_id 등
        return {"error": f"spec not found for api_id={api_id!r}: {exc}"}


def spec_groups() -> list[dict]:
    """Lists Kiwoom Securities(키움증권) OpenAPI counts per market x group, using the same taxonomy as the CLI.

    These market/group values are the vocabulary for spec_search filters and
    kiwoomcli command paths. Use it as the exploration starting point.
    """
    counts = Counter(
        (info["market"], info["group"]) for info in _command_index().values()
    )
    return [
        {"market": market, "group": group, "api_count": count}
        for (market, group), count in sorted(counts.items())
    ]


def get_example(api_id: str) -> dict:
    """Fetches runnable example code for a Kiwoom Securities(키움증권) OpenAPI endpoint from the official GitHub repository.

    Call this before writing any code against this endpoint, after spec_show.
    The spec's field contract alone is not enough to write correct code by
    hand — it's easy to guess a field name that doesn't actually exist, or
    miss pagination/error-handling patterns the spec doesn't show. This
    example already handles those and is verified against the official kwcli
    SDK.

    The returned code uses the kwcli package facade (`from kiwoom import
    get_client`), so running it requires `uv tool install kwcli` followed by
    `kiwoomcli setup` to complete authentication.

    Args:
        api_id: Kiwoom API ID, e.g. "ka10081". Find it with spec_search.
    """
    info = _command_index().get(api_id)
    if info is None:
        return {"error": f"unknown api_id={api_id!r} — spec_search로 API ID를 먼저 확인하세요."}
    repo_path = info["example_path"]
    source = f"{EXAMPLES_REPO}@{EXAMPLES_REF}"
    try:
        code = _fetch_raw(repo_path)
    except urllib.error.HTTPError as exc:
        return {
            "error": f"example fetch failed: HTTP {exc.code} for {source}:{repo_path}",
            "hint": "이 API의 예제가 아직 공식 저장소에 게시되지 않았을 수 있습니다.",
        }
    except urllib.error.URLError as exc:
        return {"error": f"example fetch failed: {exc.reason} ({source}:{repo_path})"}
    payload = {
        "api_id": api_id,
        "path": repo_path,
        "source": source,
        "code": code,
    }
    note = _SAFETY_NOTES.get(info["safety_policy"])
    if note:
        payload["safety"] = f"{info['safety_policy']} — {note}"
    return payload


mcp.tool(
    spec_search,
    annotations={
        "title": "Search Kiwoom API Specs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
mcp.tool(
    spec_show,
    annotations={
        "title": "Show Kiwoom API Spec",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
mcp.tool(
    spec_groups,
    annotations={
        "title": "List Kiwoom API Groups",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
mcp.tool(
    get_example,
    annotations={
        "title": "Get Kiwoom API Example Code",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        # 다른 도구와 달리 GitHub(raw.githubusercontent.com)로 나간다.
        "openWorldHint": True,
    },
)


def main() -> None:
    """콘솔 스크립트(kiwoom-spec-mcp) 진입점 — 전송은 env로 고른다.

    로컬은 기본 stdio, 원격 배포는 KIWOOM_MCP_TRANSPORT=http로 streamable HTTP.
    이 서버는 어느 모드에서도 자격증명을 받지 않는다.
    """
    transport = os.environ.get("KIWOOM_MCP_TRANSPORT", "stdio").strip().lower()
    if transport in ("http", "streamable-http"):
        # PaaS(Railway 등)는 $PORT를 주입한다. 우선순위: KIWOOM_MCP_PORT > PORT > 8000.
        host = os.environ.get("KIWOOM_MCP_HOST", "127.0.0.1")
        port = int(os.environ.get("KIWOOM_MCP_PORT") or os.environ.get("PORT") or "8000")
        mcp.run(transport="http", host=host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
