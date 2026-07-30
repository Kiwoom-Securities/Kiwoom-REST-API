# ---
# api_id: 0B
# api_name: 주식체결
# category: 국내주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 실시간시세 > 주식체결(0B)
# ---

import asyncio
import logging
from typing import Any

from kiwoom import get_ws_client
from kiwoom.realtime import event_to_dataframe, run_pubsub

# 주식체결(0B) 실시간 구독 — 한 스트림을 여러 소비자에 분배
# in-process Pub/Sub(asyncio.Queue). LOGIN/PING은 공통 클라이언트가 처리합니다.

API_URL = "/api/dostk/websocket"
COLUMNS = {
    '20': '체결시간',
    '10': '현재가',
    '11': '전일대비',
    '12': '등락율',
    '27': '(최우선)매도호가',
    '28': '(최우선)매수호가',
    '15': '거래량',
    '13': '누적거래량',
    '14': '누적거래대금',
    '16': '시가',
    '17': '고가',
    '18': '저가',
    '25': '전일대비기호',
    '26': '전일거래량대비(계약,주)',
    '29': '거래대금증감',
    '30': '전일거래량대비(비율)',
    '31': '거래회전율',
    '32': '거래비용',
    '228': '체결강도',
    '311': '시가총액(억)',
    '290': '장구분',
    '691': 'K.O 접근도',
    '567': '상한가발생시간',
    '568': '하한가발생시간',
    '851': '전일 동시간 거래량 비율',
    '1890': '시가시간',
    '1891': '고가시간',
    '1892': '저가시간',
    '1030': '매도체결량',
    '1031': '매수체결량',
    '1032': '매수비율',
    '1071': '매도체결건수',
    '1072': '매수체결건수',
    '1313': '순간거래대금',
    '1315': '매도체결량_단건',
    '1316': '매수체결량_단건',
    '1314': '순매수체결량',
    '1497': 'CFD증거금',
    '1498': '유지증거금',
    '620': '당일거래평균가',
    '732': 'CFD거래비용',
    '852': '대주거래비용',
    '9081': '거래소구분',
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
        "data": [{"item": ['005930'], "type": ['0B']}],
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
