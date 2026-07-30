# ---
# api_id: 0I
# api_name: 국제금환산가격
# category: 국내주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 실시간시세 > 국제금환산가격(0I)
# ---

import asyncio
import logging

from kiwoom import get_ws_client
from kiwoom.realtime import collect_realtime

# 국제금환산가격(0I) 실시간 구독 예제
# LOGIN/PING과 수신 루프는 공통 WebSocket 클라이언트가 처리합니다.

API_URL = "/api/dostk/websocket"
COLUMNS = {
    '10': '현재가',
    '25': '전일대비기호',
    '11': '전일대비',
    '12': '등락율',
}


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # Kiwoom 실시간 등록 패킷(REG) — 공식 문서/원본 샘플과 동일한 형태
    body = {
        "trnm": "REG",  # 등록("0"이면 해제)
        "grp_no": "1",  # 그룹번호
        "refresh": "1",  # 기존 등록 유지 여부
        # 등록할 종목(item)과 실시간 타입(type)
        "data": [{"item": ['MGD'], "type": ['0I']}],
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
