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

from kiwoom import get_ws_client
from kiwoom.realtime import collect_realtime

# ETF NAV(0G) 실시간 구독 예제
# LOGIN/PING과 수신 루프는 공통 WebSocket 클라이언트가 처리합니다.

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


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # Kiwoom 실시간 등록 패킷(REG) — 공식 문서/원본 샘플과 동일한 형태
    body = {
        "trnm": "REG",  # 등록("0"이면 해제)
        "grp_no": "1",  # 그룹번호
        "refresh": "1",  # 기존 등록 유지 여부
        # 등록할 종목(item)과 실시간 타입(type)
        "data": [{"item": ['069500'], "type": ['0G']}],
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
