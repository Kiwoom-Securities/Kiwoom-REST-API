# ---
# api_id: 0g
# api_name: 주식종목정보
# category: 국내주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 실시간시세 > 주식종목정보(0g)
# ---

import asyncio
import logging

from kiwoom import get_ws_client
from kiwoom.realtime import collect_realtime

# 주식종목정보(0g) 실시간 구독 예제
# LOGIN/PING과 수신 루프는 공통 WebSocket 클라이언트가 처리합니다.

API_URL = "/api/dostk/websocket"
COLUMNS = {
    '297': '임의연장',
    '592': '장전임의연장',
    '593': '장후임의연장',
    '305': '상한가',
    '306': '하한가',
    '307': '기준가',
    '689': '조기종료ELW발생',
    '594': '통화단위',
    '382': '증거금율표시',
    '370': '종목정보',
}


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    # Kiwoom 실시간 등록 패킷(REG) — 공식 문서/원본 샘플과 동일한 형태
    body = {
        "trnm": "REG",  # 등록("0"이면 해제)
        "grp_no": "1",  # 그룹번호
        "refresh": "1",  # 기존 등록 유지 여부
        # 등록할 종목(item)과 실시간 타입(type)
        "data": [{"item": ['005930'], "type": ['0g']}],
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
