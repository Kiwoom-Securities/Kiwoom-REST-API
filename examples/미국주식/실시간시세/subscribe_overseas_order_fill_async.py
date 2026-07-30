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

from kiwoom import get_ws_client
from kiwoom.realtime import collect_realtime

# 미국주식 실시간 체결(F5) 실시간 구독 예제
# LOGIN/PING과 수신 루프는 공통 WebSocket 클라이언트가 처리합니다.

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


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # Kiwoom 실시간 등록 패킷(REG) — 공식 문서/원본 샘플과 동일한 형태
    body = {
        "trnm": "REG",  # 등록("0"이면 해제)
        "grp_no": "1",  # 그룹번호
        "refresh": "1",  # 기존 등록 유지 여부
        # 등록할 종목(item)과 실시간 타입(type)
        "data": [{"item": [{'jmcode': 'NVDA', 'stex_tp': 'ND'}], "type": ['F5']}],
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
