# ---
# api_id: 0G
# api_name: ETF NAV
# category: 국내주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 실시간시세 > ETF NAV(0G)
# ---

import asyncio
import logging
from typing import Any

from kiwoom import get_ws_client
from kiwoom.realtime import event_to_dataframe, run_pubsub

# ETF NAV(0G) 실시간 구독 — 한 스트림을 여러 소비자에 분배
# in-process Pub/Sub(asyncio.Queue). LOGIN/PING은 공통 클라이언트가 처리합니다.

API_URL = "/api/dostk/websocket"
COLUMNS = {
    '36': 'NAV',
    '37': 'NAV전일대비',
    '38': 'NAV등락율',
    '39': '추적오차율',
    '20': '체결시간',
    '10': '현재가',
    '11': '전일대비',
    '12': '등락율',
    '13': '누적거래량',
    '25': '전일대비기호',
    '667': 'ELW기어링비율',
    '668': 'ELW손익분기율',
    '669': 'ELW자본지지점',
    '265': 'NAV/지수괴리율',
    '266': 'NAV/ETF괴리율',
}


async def print_dataframe(queue: asyncio.Queue[Any]) -> None:
    # "kiwoom.realtime" 토픽: REAL 이벤트만 도착 → DataFrame으로 출력
    while True:
        event = await queue.get()
        print(event_to_dataframe(event), flush=True)


async def log_raw(queue: asyncio.Queue[Any]) -> None:
    # "kiwoom.all" 토픽: REG/SYSTEM 포함 모든 메시지를 원본 그대로 출력
    while True:
        event = await queue.get()
        print(event, flush=True)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # Kiwoom 실시간 등록 패킷(REG)
    body = {
        "trnm": "REG",  # 등록("0"이면 해제)
        "grp_no": "1",  # 그룹번호
        "refresh": "1",  # 기존 등록 유지 여부
        # 등록할 종목(item)과 실시간 타입(type)
        "data": [{"item": ['069500'], "type": ['0G']}],
    }

    # 같은 스트림을 두 소비자에 분배: 가공(print_dataframe) / 원본 로깅(log_raw)
    await run_pubsub(
        get_ws_client(),
        api_url=API_URL,
        bodies=body,
        consumers={
            "kiwoom.realtime": print_dataframe,
            "kiwoom.all": log_raw,
        },
        columns=COLUMNS,
        max_messages=10,
    )


if __name__ == "__main__":
    asyncio.run(main())
