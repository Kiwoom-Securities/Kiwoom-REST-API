# ---
# api_id: FE
# api_name: 미국주식 실시간 체결가
# category: 미국주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/us/websocket
# menu_path: 미국주식 > 실시간시세 > 미국주식 실시간 체결가(FE)
# ---

import asyncio
import logging

from kiwoom import get_ws_client
from kiwoom.realtime import collect_realtime

# 미국주식 실시간 체결가(FE) 실시간 구독 예제
# LOGIN/PING과 수신 루프는 공통 WebSocket 클라이언트가 처리합니다.

API_URL = "/api/us/websocket"
COLUMNS = {
    '10': '현재가',
    '11': '전일대비',
    '12': '등락율',
    '13': '누적거래량',
    '14': '누적거래대금',
    '15': '체결량',
    '16': '시가',
    '17': '고가',
    '18': '저가',
    '20': '시간',
    '22': '체결일자',
    '25': '전일대비기호',
    '27': '(최우선)매도호가',
    '28': '(최우선)매수호가',
    '30': '전일거래량대비(비율)',
    '228': '체결강도',
    '290': '장구분',
    '51020': '현지 체결시간',
}


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # Kiwoom 실시간 등록 패킷(REG) — 공식 문서/원본 샘플과 동일한 형태
    body = {
        "trnm": "REG",  # 등록("0"이면 해제)
        "grp_no": "1",  # 그룹번호
        "refresh": "1",  # 기존 등록 유지 여부
        # 등록할 종목(item)과 실시간 타입(type)
        "data": [{"item": [{'jmcode': 'NVDA', 'stex_tp': 'ND'}], "type": ['FE']}],
    }

    # 등록 후 실시간 10건을 모아 반환(DataFrame)
    result = await collect_realtime(
        get_ws_client(),
        api_url=API_URL,
        body=body,
        columns=COLUMNS,
        max_messages=10,
    )
    print(result["data"])


if __name__ == "__main__":
    asyncio.run(main())
