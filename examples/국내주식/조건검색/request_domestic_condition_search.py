# 수동 생성 필요: 이 API는 공통 생성 템플릿만으로 완전한 runnable 예제가 되지 않습니다.
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
from typing import Any, Literal

import pandas as pd

from kiwoom import get_ws_client, KiwoomError

# WebSocket 클라이언트가 LOGIN 패킷을 자동 처리합니다.

API_ID = "ka10172"
API_URL = "/api/dostk/websocket"
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
    "next_key": "연속조회키"
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
    trnm: str,
    seq: str,
    search_type: str,
    stex_tp: str,
    cont_yn: str | None = 'N',
    next_key: str | None = '',
    output: Literal["dataframe", "json"] = "dataframe",
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """
    조건검색 요청 일반[ka10172] API를 호출합니다.

    공통 WebSocket 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        trnm: 서비스명 — CNSRREQ 고정값
        seq: 조건검색식 일련번호
        search_type: 조회타입 — 0:조건검색
        stex_tp: 거래소구분 — K:KRX
        cont_yn: 연속조회여부 — Y:연속조회요청,N:연속조회미요청
        next_key: 연속조회키
        output: "dataframe" 또는 "json".

    Returns:
        WebSocket 응답 데이터를 반환합니다.

    Example:
        >>> result = await request_domestic_condition_search(
        ...     trnm='CNSRREQ',
        ...     seq='4',
        ...     search_type='0',
        ...     stex_tp='K',
        ...     cont_yn='N',
        ...     next_key='',
        ... )
        >>> for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        ...     print(k, v.head() if isinstance(v, pd.DataFrame) else v)
    """

    # 1. 필수 파라미터 검증
    if not trnm:
        raise ValueError('trnm is required.')
    if not seq:
        raise ValueError('seq is required.')
    if not search_type:
        raise ValueError('search_type is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "trnm": trnm,  # 서비스명
        "seq": seq,  # 조건검색식 일련번호
        "search_type": search_type,  # 조회타입
        "stex_tp": stex_tp,  # 거래소구분
    }
    if cont_yn is not None:
        body["cont_yn"] = cont_yn  # 연속조회여부
    if next_key is not None:
        body["next_key"] = next_key  # 연속조회키

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
    summary_row = {
        key: response_body.get(key)
        for key in SUMMARY_COLUMNS
    }
    current_data = {
        SUMMARY_KEY: pd.DataFrame([summary_row]).rename(columns=SUMMARY_COLUMNS),
        **current_data,
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
        result = await request_domestic_condition_search(
            trnm='CNSRREQ',
            seq='4',
            search_type='0',
            stex_tp='K',
            cont_yn='N',
            next_key='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        print(k, _format_display(v).head() if isinstance(v, pd.DataFrame) else v)


if __name__ == "__main__":
    asyncio.run(main())
