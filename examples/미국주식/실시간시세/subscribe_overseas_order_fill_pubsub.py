# ---
# api_id: F5
# api_name: 미국주식 실시간 체결
# category: 미국주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/us/websocket
# menu_path: 미국주식 > 실시간시세 > 미국주식 실시간 체결(F5)
# ---

import asyncio
import logging
from typing import Any

from kiwoom import get_ws_client
from kiwoom.realtime import event_to_dataframe, run_pubsub

# 미국주식 실시간 체결(F5) 실시간 구독 — 한 스트림을 여러 소비자에 분배
# in-process Pub/Sub(asyncio.Queue). LOGIN/PING은 공통 클라이언트가 처리합니다.

API_URL = "/api/us/websocket"
COLUMNS = {
    '1091': '국가명',
    '8046': '거래소코드',
    '9001': '종목코드',
    '302': '종목명',
    '904': '원주문번호',
    '9203': '주문번호',
    '905': '주문구분',
    '907': '매도수구분',
    '908': '주문/체결시간',
    '913': '주문상태',
    '900': '주문수량',
    '901': '주문가격',
    '902': '미체결수량',
    '909': '체결번호',
    '910': '체결가',
    '911': '체결량',
    '930': '보유수량',
    '931': '매입단가',
    '934': '당일매도수량 사용',
    '936': '당일매수수량 사용',
    '8004': '전일매도수량',
    '8005': '전일매수수량',
    '8018': '손익금액',
    '8019': '손익율',
    '8043': '통화코드',
    '8075': '세금 사용',
    '9201': '계좌번호',
    '13006': '수수료 사용',
    '50072': '매도수구분명',
    '50073': '매매구분명',
    '50724': '실현손익매입금 사용',
    '50725': '환전실현손익매입금액 사용',
    '50810': '주문STOP가격',
    '50841': '예약구분',
    '50844': '환전실현손익금액 사용',
    '55190': '(재무)국가코드 사용',
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
        "data": [{"item": [{'jmcode': 'NVDA', 'stex_tp': 'ND'}], "type": ['F5']}],
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
