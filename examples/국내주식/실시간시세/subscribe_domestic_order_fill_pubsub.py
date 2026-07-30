# ---
# api_id: 00
# api_name: 주문체결
# category: 국내주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 실시간시세 > 주문체결(00)
# ---

import asyncio
import logging
from typing import Any

from kiwoom import get_ws_client
from kiwoom.realtime import event_to_dataframe, run_pubsub

# 주문체결(00) 실시간 구독 — 한 스트림을 여러 소비자에 분배
# in-process Pub/Sub(asyncio.Queue). LOGIN/PING은 공통 클라이언트가 처리합니다.

API_URL = "/api/dostk/websocket"
COLUMNS = {
    '9201': '계좌번호',
    '9203': '주문번호',
    '9205': '관리자사번',
    '9001': '종목코드,업종코드',
    '912': '주문업무분류',
    '913': '주문상태',
    '302': '종목명',
    '900': '주문수량',
    '901': '주문가격',
    '902': '미체결수량',
    '903': '체결누계금액',
    '904': '원주문번호',
    '905': '주문구분',
    '906': '매매구분',
    '907': '매도수구분',
    '908': '주문/체결시간',
    '909': '체결번호',
    '910': '체결가',
    '911': '체결량',
    '10': '현재가',
    '27': '(최우선)매도호가',
    '28': '(최우선)매수호가',
    '914': '단위체결가',
    '915': '단위체결량',
    '938': '당일매매수수료',
    '939': '당일매매세금',
    '919': '거부사유',
    '920': '화면번호',
    '921': '터미널번호',
    '922': '신용구분',
    '923': '대출일',
    '10010': '시간외단일가_현재가',
    '2134': '거래소구분',
    '2135': '거래소구분명',
    '2136': 'SOR여부',
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
        "data": [{"item": [], "type": ['00']}],
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
