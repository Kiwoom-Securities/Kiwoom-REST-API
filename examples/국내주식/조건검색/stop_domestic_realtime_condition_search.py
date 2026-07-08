# 수동 생성 필요: CNSRCLR는 같은 WebSocket 연결에서 실시간 조건검색 등록 후 해제해야 성공 응답을 받습니다.
# generator marker: MANUAL_REQUIRED_API_IDS
# ---
# api_id: ka10174
# api_name: 조건검색 실시간 해제
# category: 국내주식
# sub_category: 조건검색
# template: websocket_request_once
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 조건검색 > 조건검색 실시간 해제(ka10174)
# ---

import asyncio
import logging
import os
from typing import Any, Literal

import pandas as pd

from kiwoom import get_ws_client

# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.
# CNSRCLR는 단독 호출 대상이 아니라 등록된 실시간 조건검색을 해제하는 ACK API입니다.
# 이 예제는 증적 대상인 CNSRCLR 성공 응답을 만들기 위해 같은 세션에서 CNSRLST → CNSRREQ를 먼저 수행합니다.

API_ID = "ka10174"
API_URL = "/api/dostk/websocket"
LIST_TRNM = "CNSRLST"
REQUEST_TRNM = "CNSRREQ"
CLEAR_TRNM = "CNSRCLR"

CLEAR_COLUMNS = {
    "trnm": "서비스명",
    "seq": "조건검색식 일련번호",
    "return_code": "응답코드",
    "return_msg": "응답메시지",
}
SETUP_COLUMNS = {
    "seq": "조건검색식 일련번호",
    "condition_name": "조건검색식 명",
    "request_return_code": "등록응답코드",
    "request_return_msg": "등록응답메시지",
    "initial_count": "초기조회건수",
}


def _format_display(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()


async def stop_domestic_realtime_condition_search(
    trnm: str = CLEAR_TRNM,
    seq: str | None = None,
    output: Literal["dataframe", "json"] = "dataframe",
    setup_search_type: str = "1",
    stex_tp: str = "K",
) -> dict[str, pd.DataFrame] | dict[str, Any]:
    """
    조건검색 실시간 해제[ka10174] API를 호출합니다.

    CNSRCLR는 이미 등록된 실시간 조건검색을 해제하는 요청입니다. 성공 증적을 위해 같은 WebSocket
    연결에서 CNSRLST로 조건식을 확인하고, CNSRREQ(search_type=1)로 실시간 조건검색을 등록한 뒤
    CNSRCLR를 호출합니다. 출력의 핵심 데이터는 CNSRCLR 해제 응답입니다.

    Args:
        trnm: CNSRCLR 고정값
        seq: 조건검색식 일련번호. 생략 시 CNSRLST의 첫 번째 seq 사용.
        output: "dataframe" 또는 "json".
        setup_search_type: 선행 실시간 등록용 조회타입. 기본값 "1".
        stex_tp: K:KRX, N:NXT, A:통합

    Returns:
        해제 응답 중심의 결과를 반환합니다.

    Example:
        >>> result = await stop_domestic_realtime_condition_search()
        >>> for key, df in result.items():
        ...     print(key, df)
    """
    if not trnm:
        raise ValueError("trnm is required.")
    if not setup_search_type:
        raise ValueError("setup_search_type is required.")
    if not stex_tp:
        raise ValueError("stex_tp is required.")

    client = get_ws_client()
    selected_condition: dict[str, str] | None = None
    request_response: dict[str, Any] = {}
    clear_response: dict[str, Any] = {}

    try:
        await client.connect(api_url=API_URL)
        list_response = await _send_and_receive(client, {"trnm": LIST_TRNM})
        condition_rows = _condition_rows(list_response.get("data"))
        selected_condition = _select_condition(condition_rows, preferred_seq=seq)

        request_response = await _send_and_receive(
            client,
            {
                "trnm": REQUEST_TRNM,
                "seq": selected_condition["seq"],
                "search_type": setup_search_type,
                "stex_tp": stex_tp,
            },
        )
        request_return_code = request_response.get("return_code")
        if request_return_code not in (None, 0, "0"):
            raise RuntimeError(f"조건검색 실시간 선행 등록 실패: {request_response}")

        clear_response = await _send_and_receive(
            client,
            {
                "trnm": trnm,
                "seq": selected_condition["seq"],
            },
        )
    finally:
        await client.close()

    if output == "json":
        return {
            "selected_condition": selected_condition,
            "setup_request": request_response,
            "clear": clear_response,
        }

    return _to_dataframe_result(
        selected_condition=selected_condition,
        request_response=request_response,
        clear_response=clear_response,
    )


async def _send_and_receive(client: Any, body: dict[str, Any]) -> dict[str, Any]:
    await client._send_packet(body)
    response = await asyncio.wait_for(client._receive_message(), timeout=client.timeout_seconds)
    if not isinstance(response, dict):
        raise RuntimeError(f"unexpected websocket response type: {type(response).__name__}")
    return response


def _condition_rows(raw_rows: object) -> list[dict[str, str]]:
    if not isinstance(raw_rows, list):
        return []

    rows: list[dict[str, str]] = []
    for row in raw_rows:
        if isinstance(row, dict):
            seq_value = str(row.get("seq", "")).strip()
            name = str(row.get("name", "")).strip()
        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            seq_value = str(row[0]).strip()
            name = str(row[1]).strip()
        else:
            continue
        if seq_value:
            rows.append({"seq": seq_value, "name": name})
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


def _to_dataframe_result(
    *,
    selected_condition: dict[str, str] | None,
    request_response: dict[str, Any],
    clear_response: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    initial_data = request_response.get("data")
    initial_count = len(initial_data) if isinstance(initial_data, list) else 0
    setup_row = {
        "seq": selected_condition.get("seq") if selected_condition else None,
        "condition_name": selected_condition.get("name") if selected_condition else None,
        "request_return_code": request_response.get("return_code"),
        "request_return_msg": request_response.get("return_msg"),
        "initial_count": initial_count,
    }
    clear_row = {
        "trnm": clear_response.get("trnm"),
        "seq": clear_response.get("seq"),
        "return_code": clear_response.get("return_code"),
        "return_msg": clear_response.get("return_msg"),
    }
    return {
        "해제응답": pd.DataFrame([clear_row]).rename(columns=CLEAR_COLUMNS),
        "선행등록요약": pd.DataFrame([setup_row]).rename(columns=SETUP_COLUMNS),
    }


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    result = await stop_domestic_realtime_condition_search(
        seq=os.getenv("KIWOOM_CONDITION_SEQ") or None,
    )
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df).to_string(index=False))


if __name__ == "__main__":
    asyncio.run(main())
