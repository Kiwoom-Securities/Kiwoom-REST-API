# 수동 생성 필요: CNSRREQ 실시간은 같은 WebSocket 연결에서 CNSRLST 선행 호출 후 요청해야 안정적으로 응답합니다.
# generator marker: MANUAL_REQUIRED_API_IDS
# ---
# api_id: ka10173
# api_name: 조건검색 요청 실시간
# category: 국내주식
# sub_category: 조건검색
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 조건검색 > 조건검색 요청 실시간(ka10173)
# ---

import asyncio
import logging
import os
from typing import Any, Literal

import pandas as pd

from kiwoom import get_ws_client
from kiwoom.realtime.decoders import decode_values

# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.
# 이 API는 같은 WebSocket 연결에서 CNSRLST를 먼저 호출한 뒤 CNSRREQ를 보내야 합니다.
# 응답은 초기 조회 데이터(CNSRREQ)와 이후 실시간 데이터(REAL)가 분리되어 도착합니다.
# 예제는 실시간 등록 후 CNSRCLR로 해제하고 종료합니다.

API_ID = "ka10173"
API_URL = "/api/dostk/websocket"
LIST_TRNM = "CNSRLST"
CLEAR_TRNM = "CNSRCLR"
CONDITION_LIST_KEY = "조건검색식 목록"
INITIAL_DATA_KEY = "조회데이터"
REALTIME_DATA_KEY = "실시간데이터"
SYSTEM_KEY = "시스템메시지"
SUMMARY_KEY = "요약"

CONDITION_COLUMNS = {
    "seq": "조건검색식 일련번호",
    "name": "조건검색식 명",
}
INITIAL_COLUMNS = {
    "jmcode": "종목코드",
}
REALTIME_COLUMNS = {
    "item": "수신종목코드",
    "type": "실시간 항목",
    "name": "실시간 항목명",
    "841": "일련번호",
    "9001": "종목코드",
    "843": "삽입삭제 구분",
    "20": "체결시간",
    "907": "매도/수 구분",
    "9081": "거래소구분",
}
SUMMARY_COLUMNS = {
    "seq": "조건검색식 일련번호",
    "condition_name": "조건검색식 명",
    "return_code": "응답코드",
    "return_msg": "응답메시지",
    "initial_count": "초기조회건수",
    "realtime_count": "실시간수신건수",
}


def _format_display(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()


async def request_domestic_realtime_condition_search_async(
    trnm: str = "CNSRREQ",
    seq: str | None = None,
    search_type: str = "1",
    stex_tp: str = "K",
    output: Literal["dataframe", "json"] = "dataframe",
    max_messages: int = 1,
    max_wait_seconds: float = 15.0,
) -> dict[str, pd.DataFrame] | dict[str, Any]:
    """
    조건검색 요청 실시간[ka10173] API를 호출합니다.

    조건검색 실시간 요청은 같은 WebSocket 연결에서 조건검색 목록조회(CNSRLST)를 먼저 수행한 뒤
    CNSRREQ(search_type=1)를 보내야 안정적으로 응답합니다. seq를 생략하면 CNSRLST 응답의
    첫 번째 조건검색식 일련번호를 사용합니다.

    Args:
        trnm: CNSRREQ 고정값
        seq: 조건검색식 일련번호. 생략 시 CNSRLST의 첫 번째 seq 사용.
        search_type: 1: 조건검색+실시간조건검색
        stex_tp: K:KRX, N:NXT, A:통합
        output: "dataframe" 또는 "json".
        max_messages: 수집할 최대 REAL 메시지 수.
        max_wait_seconds: REAL 메시지를 기다릴 최대 시간(초).

    Returns:
        조건검색식 목록, 초기 조회 데이터, 실시간 수신 데이터, 해제 응답을 반환합니다.

    Example:
        >>> result = await request_domestic_realtime_condition_search_async()
        >>> for k, v in result.items():
        ...     print(k, v.to_string(index=False) if isinstance(v, pd.DataFrame) else v)
    """
    if max_messages < 0:
        raise ValueError("max_messages must be greater than or equal to 0")
    if max_wait_seconds <= 0:
        raise ValueError("max_wait_seconds must be greater than 0")
    if not trnm:
        raise ValueError("trnm is required.")
    if not search_type:
        raise ValueError("search_type is required.")
    if not stex_tp:
        raise ValueError("stex_tp is required.")

    client = get_ws_client()
    condition_rows: list[dict[str, str]] = []
    selected_condition: dict[str, str] | None = None
    initial_response: dict[str, Any] = {}
    realtime_messages: list[dict[str, Any]] = []
    realtime_rows: list[dict[str, Any]] = []
    system_messages: list[dict[str, Any]] = []
    clear_response: dict[str, Any] = {}

    try:
        await client.connect(api_url=API_URL)
        list_response = await _send_and_receive(client, {"trnm": LIST_TRNM})
        condition_rows = _condition_rows(list_response.get("data"))
        selected_condition = _select_condition(condition_rows, preferred_seq=seq)

        body = {
            "trnm": trnm,
            "seq": selected_condition["seq"],
            "search_type": search_type,
            "stex_tp": stex_tp,
        }
        initial_response = await _send_and_receive(client, body)
        initial_return_code = initial_response.get("return_code")
        if initial_return_code in (None, 0, "0") and max_messages > 0:
            realtime_messages, realtime_rows, system_messages = await _collect_realtime_messages(
                client,
                max_messages=max_messages,
                max_wait_seconds=max_wait_seconds,
            )
        clear_response = await _try_clear_condition(client, selected_condition["seq"])
    finally:
        await client.close()

    if output == "json":
        return {
            "conditions": condition_rows,
            "selected_condition": selected_condition,
            "initial": initial_response,
            "realtime": realtime_messages,
            "realtime_rows": realtime_rows,
            "system": system_messages,
            "clear": clear_response,
        }

    return _to_dataframe_result(
        condition_rows=condition_rows,
        selected_condition=selected_condition,
        initial_response=initial_response,
        realtime_rows=realtime_rows,
        system_messages=system_messages,
    )


async def _send_and_receive(client: Any, body: dict[str, Any]) -> dict[str, Any]:
    await client._send_packet(body)
    response = await asyncio.wait_for(client._receive_message(), timeout=client.timeout_seconds)
    if not isinstance(response, dict):
        raise RuntimeError(f"unexpected websocket response type: {type(response).__name__}")
    return response


async def _collect_realtime_messages(
    client: Any,
    *,
    max_messages: int,
    max_wait_seconds: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    messages: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    system_messages: list[dict[str, Any]] = []
    loop = asyncio.get_running_loop()
    deadline = loop.time() + max_wait_seconds

    while len(messages) < max_messages:
        remaining = deadline - loop.time()
        if remaining <= 0:
            break
        try:
            message = await asyncio.wait_for(client._receive_message(), timeout=remaining)
        except TimeoutError:
            break
        if not isinstance(message, dict):
            continue

        received_trnm = str(message.get("trnm", "")).upper()
        if received_trnm == "REAL":
            messages.append(message)
            rows.extend(_realtime_rows(message))
            continue

        system_messages.append(message)
        return_code = message.get("return_code")
        if received_trnm == "SYSTEM" or return_code not in (None, 0, "0"):
            break

    return messages, rows, system_messages


async def _try_clear_condition(client: Any, seq: str) -> dict[str, Any]:
    try:
        return await _send_and_receive(client, {"trnm": CLEAR_TRNM, "seq": seq})
    except TimeoutError as exc:
        return {
            "trnm": CLEAR_TRNM,
            "seq": seq,
            "return_code": "TIMEOUT",
            "return_msg": str(exc),
        }


def _condition_rows(raw_rows: object) -> list[dict[str, str]]:
    if not isinstance(raw_rows, list):
        return []

    rows: list[dict[str, str]] = []
    for row in raw_rows:
        if isinstance(row, dict):
            seq = str(row.get("seq", "")).strip()
            name = str(row.get("name", "")).strip()
        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            seq = str(row[0]).strip()
            name = str(row[1]).strip()
        else:
            continue
        if seq:
            rows.append({"seq": seq, "name": name})
    return rows


def _select_condition(rows: list[dict[str, str]], *, preferred_seq: str | None) -> dict[str, str]:
    if not rows:
        raise RuntimeError("저장된 조건검색식이 없습니다. 영웅문4에서 조건검색식을 먼저 저장해 주세요.")

    if preferred_seq is not None:
        normalized = preferred_seq.strip()
        for row in rows:
            if row["seq"] == normalized:
                return row
        available = [row["seq"] for row in rows]
        raise ValueError(f"조건검색식 일련번호를 찾을 수 없습니다: {normalized}. available={available}")

    return rows[0]


def _initial_rows(response_body: dict[str, Any]) -> list[dict[str, Any]]:
    data = response_body.get("data")
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _realtime_rows(message: dict[str, Any]) -> list[dict[str, Any]]:
    data = message.get("data")
    if not isinstance(data, list):
        return []

    rows: list[dict[str, Any]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        values = entry.get("values")
        decoded_values = decode_values(str(entry.get("type", "")), values if isinstance(values, dict) else {})
        rows.append(
            {
                "item": entry.get("item", ""),
                "type": entry.get("type", ""),
                "name": entry.get("name", ""),
                **decoded_values,
            }
        )
    return rows


def _to_dataframe_result(
    *,
    condition_rows: list[dict[str, str]],
    selected_condition: dict[str, str] | None,
    initial_response: dict[str, Any],
    realtime_rows: list[dict[str, Any]],
    system_messages: list[dict[str, Any]],
) -> dict[str, pd.DataFrame]:
    initial_rows = _initial_rows(initial_response)
    summary_row = {
        "seq": selected_condition.get("seq") if selected_condition else None,
        "condition_name": selected_condition.get("name") if selected_condition else None,
        "return_code": initial_response.get("return_code"),
        "return_msg": initial_response.get("return_msg"),
        "initial_count": len(initial_rows),
        "realtime_count": len(realtime_rows),
    }
    result = {
        SUMMARY_KEY: pd.DataFrame([summary_row]).rename(columns=SUMMARY_COLUMNS),
        CONDITION_LIST_KEY: pd.DataFrame(condition_rows).rename(columns=CONDITION_COLUMNS),
        INITIAL_DATA_KEY: pd.DataFrame(initial_rows).rename(columns=INITIAL_COLUMNS),
        REALTIME_DATA_KEY: pd.DataFrame(realtime_rows).rename(columns=REALTIME_COLUMNS),
    }
    if system_messages:
        result[SYSTEM_KEY] = pd.DataFrame(system_messages)
    return result


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    result = await request_domestic_realtime_condition_search_async(
        seq=os.getenv("KIWOOM_CONDITION_SEQ") or None,
        max_messages=1,
        max_wait_seconds=15.0,
    )
    for k, v in result.items():
        print(f"\n[{k}]")
        print(_format_display(v).to_string(index=False) if isinstance(v, pd.DataFrame) else v)


if __name__ == "__main__":
    asyncio.run(main())
