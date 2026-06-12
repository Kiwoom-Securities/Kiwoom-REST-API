# 수동 생성 필요: CNSRREQ는 같은 WebSocket 연결에서 CNSRLST 선행 호출 후 요청해야 안정적으로 응답합니다.
# generator marker: MANUAL_REQUIRED_API_IDS
# ---
# api_id: ka10172
# api_name: 조건검색 요청 일반
# category: 국내주식
# sub_category: 조건검색
# template: websocket_request_once
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 조건검색 > 조건검색 요청 일반(ka10172)
# ---

import asyncio
import logging
import os
from typing import Any, Literal

import pandas as pd

from kiwoom import get_ws_client

# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.
# 이 API는 CNSRREQ 단독 호출 시 응답 없이 PING만 올 수 있으므로,
# 같은 WebSocket 연결에서 CNSRLST를 먼저 호출한 뒤 CNSRREQ를 보냅니다.

API_ID = "ka10172"
API_URL = "/api/dostk/websocket"
LIST_TRNM = "CNSRLST"
TABLE_KEYS = {
    "data": "검색결과데이터"
}
COLUMNS = {
    "9001": "종목코드",
    "302": "종목명",
    "10": "현재가",
    "25": "전일대비기호",
    "11": "전일대비",
    "12": "등락율",
    "13": "누적거래량",
    "16": "시가",
    "17": "고가",
    "18": "저가"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "seq": "조건검색식 일련번호",
    "cont_yn": "연속조회여부",
    "next_key": "연속조회키",
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}


NUMERIC_COLUMNS = (
    '고가',
    '누적거래량',
    '등락율',
    '시가',
    '저가',
    '현재가',
)


def _format_display(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()
    for column in tuple(NUMERIC_COLUMNS):
        if column in display.columns:
            display[column] = display[column].map(_format_display_value)
    return display


def _format_display_value(value: object) -> object:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return value
    try:
        if pd.isna(value):
            return value
    except (TypeError, ValueError):
        return value
    text = str(value).strip()
    sign = "-" if text.startswith("-") else ""
    unsigned = text[1:] if sign else text
    if "." in unsigned:
        integer, fraction = unsigned.split(".", 1)
        if integer.isdigit() and fraction.isdigit():
            return f"{sign}{int(integer or '0'):,}.{fraction}"
        return value
    if unsigned.isdigit() and len(unsigned) >= 6:
        return f"{sign}{int(unsigned or '0'):,}"
    return value


async def request_domestic_condition_search(
    trnm: str = "CNSRREQ",
    seq: str | None = None,
    search_type: str = "0",
    stex_tp: str = "K",
    cont_yn: str | None = "N",
    next_key: str | None = "",
    output: Literal["dataframe", "json"] = "dataframe",
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """
    조건검색 요청 일반[ka10172] API를 호출합니다.

    CNSRREQ는 조건검색 목록조회(CNSRLST)를 먼저 수행한 뒤 요청해야 안정적으로 응답합니다.
    seq를 생략하면 CNSRLST 응답의 첫 번째 조건검색식 일련번호를 사용합니다.
    특정 조건식을 재현하려면 seq를 명시하세요.

    Args:
        trnm: CNSRREQ 고정값
        seq: 조건검색식 일련번호. 생략 시 CNSRLST의 첫 번째 seq 사용.
        search_type: 0:조건검색
        stex_tp: K:KRX, N:NXT, A:통합
        cont_yn: Y:연속조회요청,N:연속조회미요청
        next_key: 연속조회키
        output: "dataframe" 또는 "json".

    Returns:
        WebSocket 응답 데이터를 반환합니다.

    Example:
        >>> result = await request_domestic_condition_search(
        seq=os.getenv("KIWOOM_CONDITION_SEQ") or None,
    )
        >>> for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        ...     print(k, v.to_string(index=False) if isinstance(v, pd.DataFrame) else v)
    """

    if not trnm:
        raise ValueError('trnm is required.')
    if not search_type:
        raise ValueError('search_type is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    client = get_ws_client()
    try:
        await client.connect(api_url=API_URL)
        list_response = await _send_and_receive(client, {"trnm": LIST_TRNM})
        selected_seq = _select_condition_seq(list_response, preferred_seq=seq)

        body = {
            "trnm": trnm,
            "seq": selected_seq,
            "search_type": search_type,
            "stex_tp": stex_tp,
        }
        if cont_yn is not None:
            body["cont_yn"] = cont_yn
        if next_key is not None:
            body["next_key"] = next_key

        response_body = await _send_and_receive(client, body)
    finally:
        await client.close()

    if output == "json":
        return response_body
    return _to_dataframe_result(response_body)


async def _send_and_receive(client: Any, body: dict[str, Any]) -> dict[str, Any]:
    await client._send_packet(body)
    response = await asyncio.wait_for(client._receive_message(), timeout=client.timeout_seconds)
    if not isinstance(response, dict):
        raise RuntimeError(f"unexpected websocket response type: {type(response).__name__}")
    return response


def _select_condition_seq(list_response: dict[str, Any], *, preferred_seq: str | None) -> str:
    raw_rows = list_response.get("data")
    rows = _condition_rows(raw_rows)
    if not rows:
        raise RuntimeError("저장된 조건검색식이 없습니다. 영웅문4에서 조건검색식을 먼저 저장해 주세요.")

    available = {row["seq"] for row in rows}
    if preferred_seq is not None:
        normalized = preferred_seq.strip()
        if normalized not in available:
            raise ValueError(f"조건검색식 일련번호를 찾을 수 없습니다: {normalized}. available={sorted(available)}")
        return normalized

    return rows[0]["seq"]


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


def _to_dataframe_result(response_body: dict[str, Any]) -> dict[str, pd.DataFrame]:
    table_rows = {
        "data": [],
    }
    for key in table_rows:
        records = response_body.get(key, [])
        if isinstance(records, list):
            column_keys = list(COLUMNS)
            for record in records:
                if isinstance(record, dict):
                    table_rows[key].append(record)
                elif isinstance(record, (list, tuple)):
                    table_rows[key].append(dict(zip(column_keys, record)))

    current_data = {
        TABLE_KEYS.get(key, key): pd.DataFrame(records).rename(columns=COLUMNS)
        for key, records in table_rows.items()
    }
    summary_row = {
        key: response_body.get(key)
        for key in SUMMARY_COLUMNS
    }
    return {
        SUMMARY_KEY: pd.DataFrame([summary_row]).rename(columns=SUMMARY_COLUMNS),
        **current_data,
    }


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    result = await request_domestic_condition_search(
        seq=os.getenv("KIWOOM_CONDITION_SEQ") or None,
    )
    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        print(k, _format_display(v).to_string(index=False) if isinstance(v, pd.DataFrame) else v)


if __name__ == "__main__":
    asyncio.run(main())
