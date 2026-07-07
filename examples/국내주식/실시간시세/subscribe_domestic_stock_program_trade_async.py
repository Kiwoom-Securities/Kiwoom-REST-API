# ---
# api_id: 0w
# api_name: 종목프로그램매매
# category: 국내주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 실시간시세 > 종목프로그램매매(0w)
# ---

import asyncio
import logging
from typing import Any, Literal

import pandas as pd

from kiwoom import get_ws_client
from kiwoom.realtime.decoders import decode_values

# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.

API_ID = "0w"
API_URL = "/api/dostk/websocket"


def build_realtime_reg_packet(
    *,
    items: list[str],
    types: list[str],
    group_no: str = "1",
    refresh: str = "1",
) -> dict[str, Any]:
    """키움 실시간 항목 등록(REG) 패킷을 생성합니다."""
    if not types:
        raise ValueError("types is required.")
    return {
        "trnm": "REG",
        "grp_no": group_no,
        "refresh": refresh,
        "data": [
            {
                "item": items,
                "type": types,
            }
        ],
    }

async def subscribe_domestic_stock_program_trade_async(
    items: list[str],
    types: list[str] | None = None,
    group_no: str = "1",
    refresh: str = "1",
    output: Literal["dataframe", "json"] = "dataframe",
    max_messages: int = 10,
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """
    종목프로그램매매[0w] 실시간 데이터를 수신합니다.

    공통 WebSocket 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        items: 실시간 등록 종목 또는 요소 목록.
        types: 실시간 항목 타입 목록. 생략하면 이 예제의 API_ID를 사용합니다.
        group_no: 그룹번호.
        refresh: 기존 등록 유지 여부. "1"은 기존 등록을 유지합니다.
        output: "dataframe" 또는 "json".
        max_messages: 수집할 최대 실시간 메시지 수.

    Returns:
        실시간 수신 데이터를 반환합니다.

    Example:
        >>> result = await subscribe_domestic_stock_program_trade_async(
        ...     items=['005930'],
        ...     types=['0w'],
        ... )
        >>> for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        ...     print(k, v.head() if isinstance(v, pd.DataFrame) else v)
    """
    if max_messages < 1:
        raise ValueError("max_messages must be greater than 0")
    if not items:
        raise ValueError("items is required.")

    body = build_realtime_reg_packet(
        items=items,
        types=types or [API_ID],
        group_no=group_no,
        refresh=refresh,
    )

    client = get_ws_client()
    rows: list[dict[str, Any]] = []
    system_rows: list[dict[str, Any]] = []
    try:
        await client.subscribe(api_url=API_URL, body=body)

        async for message in client.iter_messages():
            if not isinstance(message, dict):
                continue
            trnm = str(message.get("trnm", "")).upper()
            if trnm in {"REG", "SYSTEM"}:
                system_rows.append(message)
                print(f"[{trnm}]", message, flush=True)
                return_code = message.get("return_code")
                if trnm == "SYSTEM" or return_code not in (None, 0, "0"):
                    if output == "json":
                        return {"system": system_rows, "data": rows} if rows else system_rows
                    result: dict[str, pd.DataFrame] = {"system": pd.DataFrame(system_rows)}
                    if rows:
                        result["data"] = pd.DataFrame(rows)
                    return result
                continue
            if trnm != "REAL":
                system_rows.append(message)
                print(f"[{trnm or 'MESSAGE'}]", message, flush=True)
                continue
            for entry in message.get("data", []):
                if not isinstance(entry, dict):
                    continue
                values = decode_values(str(entry.get("type", "")), entry.get("values", {}))
                rows.append({"item": entry.get("item", ""), "type": entry.get("type", ""), **values})
                if len(rows) >= max_messages:
                    if output == "json":
                        return {"system": system_rows, "data": rows} if system_rows else rows
                    result: dict[str, pd.DataFrame] = {"data": pd.DataFrame(rows)}
                    if system_rows:
                        result["system"] = pd.DataFrame(system_rows)
                    return result
    finally:
        await client.close()

    if output == "json":
        return {"system": system_rows, "data": rows} if system_rows else rows
    result: dict[str, pd.DataFrame] = {"data": pd.DataFrame(rows)}
    if system_rows:
        result["system"] = pd.DataFrame(system_rows)
    return result


async def main() -> None:
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # API 호출
    result = await subscribe_domestic_stock_program_trade_async(
        items=['005930'],
        types=['0w'],
    )
    # 결과 출력
    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        print(k, v.head() if isinstance(v, pd.DataFrame) else v)


if __name__ == "__main__":
    asyncio.run(main())
