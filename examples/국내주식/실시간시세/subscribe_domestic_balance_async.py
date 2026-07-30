# ---
# api_id: 04
# api_name: 잔고
# category: 국내주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 실시간시세 > 잔고(04)
# ---

import asyncio
import logging

from kiwoom import get_ws_client
from kiwoom.realtime import collect_realtime

# 잔고(04) 실시간 구독 예제
# LOGIN/PING과 수신 루프는 공통 WebSocket 클라이언트가 처리합니다.

API_URL = "/api/dostk/websocket"
COLUMNS = {
    '9201': '계좌번호',
    '9001': '종목코드,업종코드',
    '917': '신용구분',
    '916': '대출일',
    '302': '종목명',
    '10': '현재가',
    '930': '보유수량',
    '931': '매입단가',
    '932': '총매입가(당일누적)',
    '933': '주문가능수량',
    '945': '당일순매수량',
    '946': '매도/매수구분',
    '950': '당일총매도손익',
    '951': 'Extra Item',
    '27': '(최우선)매도호가',
    '28': '(최우선)매수호가',
    '307': '기준가',
    '8019': '손익률(실현손익)',
    '957': '신용금액',
    '958': '신용이자',
    '918': '만기일',
    '990': '당일실현손익(유가)',
    '991': '당일실현손익율(유가)',
    '992': '당일실현손익(신용)',
    '993': '당일실현손익율(신용)',
    '959': '담보대출수량',
    '924': 'Extra Item',
}


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # Kiwoom 실시간 등록 패킷(REG) — 공식 문서/원본 샘플과 동일한 형태
    body = {
        "trnm": "REG",  # 등록("0"이면 해제)
        "grp_no": "1",  # 그룹번호
        "refresh": "1",  # 기존 등록 유지 여부
        # 등록할 종목(item)과 실시간 타입(type)
        "data": [{"item": [], "type": ['04']}],
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
