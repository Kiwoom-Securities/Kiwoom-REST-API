# ---
# api_id: 1h
# api_name: VI발동/해제
# category: 국내주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 실시간시세 > VI발동/해제(1h)
# ---

import asyncio
import logging
from typing import Any

from kiwoom import get_ws_client
from kiwoom.realtime import event_to_dataframe, run_pubsub

# VI발동/해제(1h) 실시간 구독 — 한 스트림을 여러 소비자에 분배
# in-process Pub/Sub(asyncio.Queue). LOGIN/PING은 공통 클라이언트가 처리합니다.

API_URL = "/api/dostk/websocket"
COLUMNS = {
    '9001': '종목코드',
    '302': '종목명',
    '13': '누적거래량',
    '14': '누적거래대금',
    '9068': 'VI발동구분',
    '9008': 'KOSPI,KOSDAQ,전체구분',
    '9075': '장전구분',
    '1221': 'VI발동가격',
    '1223': '매매체결처리시각',
    '1224': 'VI해제시각',
    '1225': 'VI적용구분',
    '1236': '기준가격 정적',
    '1237': '기준가격 동적',
    '1238': '괴리율 정적',
    '1239': '괴리율 동적',
    '1489': 'VI발동가 등락율',
    '1490': 'VI발동횟수',
    '9069': '발동방향구분',
    '1279': 'Extra Item',
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
        "data": [{"item": [], "type": ['1h']}],
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
