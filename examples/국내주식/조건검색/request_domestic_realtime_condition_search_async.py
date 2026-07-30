# 수동 생성 필요: 이 API는 공통 생성 템플릿만으로 완전한 runnable 예제가 되지 않습니다.
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
from typing import Any, Literal

import pandas as pd

from kiwoom import get_ws_client
from kiwoom.realtime import collect_realtime

# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.

API_ID = "ka10173"
API_URL = "/api/dostk/websocket"
COLUMNS = {
    '841': '일련번호',
    '9001': '종목코드',
    '843': '삽입삭제 구분',
    '20': '체결시간',
    '907': '매도/수 구분',
}

async def request_domestic_realtime_condition_search_async(
    trnm: str,
    seq: str,
    search_type: str,
    stex_tp: str,
    output: Literal["dataframe", "json"] = "dataframe",
    max_messages: int = 10,
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """
    조건검색 요청 실시간[ka10173] API를 호출합니다.

    공통 WebSocket 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        trnm: 서비스명 — CNSRREQ 고정값
        seq: 조건검색식 일련번호
        search_type: 조회타입 — 1: 조건검색+실시간조건검색
        stex_tp: 거래소구분 — K:KRX
        output: "dataframe" 또는 "json".
        max_messages: 수집할 최대 실시간 메시지 수.

    Returns:
        실시간 수신 데이터를 반환합니다.

    Example:
        >>> result = await request_domestic_realtime_condition_search_async(
        ...     trnm='CNSRREQ',
        ...     seq='4',
        ...     search_type='1',
        ...     stex_tp='K',
        ... )
        >>> for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        ...     print(k, v.head() if isinstance(v, pd.DataFrame) else v)
    """
    if max_messages < 1:
        raise ValueError("max_messages must be greater than 0")

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

    return await collect_realtime(
        get_ws_client(),
        api_url=API_URL,
        body=body,
        columns=COLUMNS,
        output=output,
        max_messages=max_messages,
    )

async def main() -> None:
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # API 호출
    result = await request_domestic_realtime_condition_search_async(
        trnm='CNSRREQ',
        seq='4',
        search_type='1',
        stex_tp='K',
    )
    # 결과 출력
    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        print(k, v.head() if isinstance(v, pd.DataFrame) else v)


if __name__ == "__main__":
    asyncio.run(main())
