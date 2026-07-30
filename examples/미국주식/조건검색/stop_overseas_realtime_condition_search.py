# 수동 생성 필요: 이 API는 공통 생성 템플릿만으로 완전한 runnable 예제가 되지 않습니다.
# generator marker: MANUAL_REQUIRED_API_IDS
# ---
# api_id: usa20291
# api_name: 미국주식 조건검색 실시간 해제
# category: 미국주식
# sub_category: 조건검색
# template: websocket_request_once
# api_url: /api/us/websocket
# menu_path: 미국주식 > 조건검색 > 미국주식 조건검색 실시간 해제(usa20291)
# ---

import asyncio
import logging
from typing import Any, Literal

import pandas as pd

from kiwoom import get_ws_client, KiwoomError

# WebSocket 클라이언트가 LOGIN 패킷을 자동 처리합니다.

API_ID = "usa20291"
API_URL = "/api/us/websocket"
TABLE_KEYS = {}
COLUMNS = {
    "seq": "조건검색식 일련번호"
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

async def stop_overseas_realtime_condition_search(
    trnm: str,
    seq: str,
    output: Literal["dataframe", "json"] = "dataframe",
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """
    미국주식 조건검색 실시간 해제[usa20291] API를 호출합니다.

    공통 WebSocket 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        trnm: 서비스명 — GCNSRCLR 고정값
        seq: 조건검색식 일련번호
        output: "dataframe" 또는 "json".

    Returns:
        WebSocket 응답 데이터를 반환합니다.

    Example:
        >>> result = await stop_overseas_realtime_condition_search(
        ...     trnm='GCNSRCLR',
        ...     seq='1',
        ... )
        >>> for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        ...     print(k, v.head() if isinstance(v, pd.DataFrame) else v)
    """

    # 1. 필수 파라미터 검증
    if not trnm:
        raise ValueError('trnm is required.')
    if not seq:
        raise ValueError('seq is required.')

    # 2. 요청 파라미터 바디
    body = {
        "trnm": trnm,  # 서비스명
        "seq": seq,  # 조건검색식 일련번호
    }

    response_body = await get_ws_client().request_once(api_url=API_URL, body=body)

    if output == "json":
        return response_body
    scalar_values = {
        key: value
        for key, value in response_body.items()
        if key not in {"return_code", "return_msg", "trnm"} and not isinstance(value, (dict, list))
    }
    current_data = pd.DataFrame([scalar_values]) if scalar_values else pd.DataFrame()
    current_data = current_data.rename(columns=COLUMNS)
    return current_data


async def main() -> None:
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    try:
        result = await stop_overseas_realtime_condition_search(
            trnm='GCNSRCLR',
            seq='1',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        print(k, _format_display(v).head() if isinstance(v, pd.DataFrame) else v)


if __name__ == "__main__":
    asyncio.run(main())
