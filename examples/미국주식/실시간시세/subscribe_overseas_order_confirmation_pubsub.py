# ---
# api_id: F4
# api_name: 미국주식 실시간 주문 확인
# category: 미국주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/us/websocket
# menu_path: 미국주식 > 실시간시세 > 미국주식 실시간 주문 확인(F4)
# ---

import asyncio
import logging
from typing import Any

from kiwoom import get_ws_client
from kiwoom.realtime import event_to_dataframe, run_pubsub

# 미국주식 실시간 주문 확인(F4) 실시간 구독 — 한 스트림을 여러 소비자에 분배
# in-process Pub/Sub(asyncio.Queue). LOGIN/PING은 공통 클라이언트가 처리합니다.

API_URL = "/api/us/websocket"
COLUMNS = {
    '9201': '계좌번호',
    '9203': '주문번호',
    '9001': '종목,업종코드',
    '905': '주문구분',
    '907': '매도수구분',
    '904': '원주문번호',
    '900': '주문수량',
    '901': '주문가격',
    '906': '매매구분',
    '913': '주문상태',
    '908': '주문/체결시간',
    '50810': '주문STOP가격',
    '8043': '통화코드',
    '50841': '예약구분',
    '55190': '(재무)국가코드 사용',
    '1091': '국가명',
    '50072': '매도수구분명',
    '302': '종목명',
    '50073': '매매구분명',
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
        "data": [{"item": [{'jmcode': 'NVDA', 'stex_tp': 'ND'}], "type": ['F4']}],
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
