# ---
# api_id: ka10171
# api_name: 조건검색 목록조회
# category: 국내주식
# sub_category: 조건검색
# template: websocket_request_once
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 조건검색 > 조건검색 목록조회(ka10171)
# ---

import asyncio
import logging
from typing import Any, Literal

import pandas as pd

from kiwoom import get_ws_client, KiwoomError

# WebSocket 클라이언트가 LOGIN 패킷을 자동 처리합니다.

API_ID = "ka10171"
API_URL = "/api/dostk/websocket"
TABLE_KEYS = {
    "data": "조건검색식 목록"
}
COLUMNS = {
    "seq": "조건검색식 일련번호",
    "name": "조건검색식 명"
}


NUMERIC_COLUMNS = ()

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

async def list_domestic_condition_searches(
    trnm: str,
    output: Literal["dataframe", "json"] = "dataframe",
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """
    조건검색 목록조회[ka10171] API를 호출합니다.

    공통 WebSocket 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        trnm: TR명 — CNSRLST고정값
        output: "dataframe" 또는 "json".

    Returns:
        WebSocket 응답 데이터를 반환합니다.

    Example:
        >>> result = await list_domestic_condition_searches(
        ...     trnm='CNSRLST',
        ... )
        >>> for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        ...     print(k, v.head() if isinstance(v, pd.DataFrame) else v)
    """

    # 1. 필수 파라미터 검증
    if not trnm:
        raise ValueError('trnm is required.')

    # 2. 요청 파라미터 바디
    body = {
        "trnm": trnm,  # TR명
    }

    response_body = await get_ws_client().request_once(api_url=API_URL, body=body)

    if output == "json":
        return response_body
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
    return current_data


async def main() -> None:
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    try:
        result = await list_domestic_condition_searches(
            trnm='CNSRLST',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        print(k, _format_display(v).head() if isinstance(v, pd.DataFrame) else v)


if __name__ == "__main__":
    asyncio.run(main())
