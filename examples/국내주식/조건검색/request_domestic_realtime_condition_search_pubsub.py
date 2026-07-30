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
from typing import Any

from kiwoom import get_ws_client
from kiwoom.realtime import (
    AsyncPubSub,
    event_to_dataframe,
    run_pubsub,
)

# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.
# asyncio.Queue 기반 in-process Pub/Sub로 한 스트림을 여러 소비자에 분배합니다.

API_ID = "ka10173"
API_URL = "/api/dostk/websocket"
COLUMNS = {
    '841': '일련번호',
    '9001': '종목코드',
    '843': '삽입삭제 구분',
    '20': '체결시간',
    '907': '매도/수 구분',
}


async def strategy_subscriber(queue: asyncio.Queue[Any]) -> None:
    """전략 로직 소비자 예시: 실시간 event를 DataFrame으로 처리합니다."""
    while True:
        event = await queue.get()
        if isinstance(event, dict) and str(event.get("trnm", "")).upper() == "REAL":
            print("[strategy]", event_to_dataframe(event), flush=True)
        else:
            print("[strategy]", event, flush=True)


async def logger_subscriber(queue: asyncio.Queue[Any]) -> None:
    """로그/저장 로직 소비자 예시."""
    while True:
        event = await queue.get()
        print("[logger]", event, flush=True)

async def request_domestic_realtime_condition_search_pubsub(
    trnm: str,
    seq: str,
    search_type: str,
    stex_tp: str,
    pubsub: AsyncPubSub | None = None,
    max_messages: int | None = None,
) -> None:
    """
    조건검색 요청 실시간[ka10173] WebSocket 메시지를 Pub/Sub로 분배합니다.

    공통 WebSocket 클라이언트가 캐시 토큰을 쓰거나 없으면 자동 발급합니다.
    """
    if max_messages is not None and max_messages < 1:
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

    await run_pubsub(
        get_ws_client(),
        api_url=API_URL,
        bodies=body,
        consumers={
            "kiwoom.realtime": strategy_subscriber,
            "kiwoom.all": logger_subscriber,
        },
        columns=COLUMNS,
        pubsub=pubsub,
        max_messages=max_messages,
    )


async def main() -> None:
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 구독 시작 (소비자가 수신 데이터를 출력)
    await request_domestic_realtime_condition_search_pubsub(
        trnm='CNSRREQ',
        seq='4',
        search_type='1',
        stex_tp='K',
        max_messages=10,
    )


if __name__ == "__main__":
    asyncio.run(main())
