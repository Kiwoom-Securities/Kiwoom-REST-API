# ---
# api_id: ust21510
# api_name: 미국주식 당일 주문체결 확인
# category: 미국주식
# sub_category: 계좌
# template: rest
# api_url: /api/us/acnt
# menu_path: 미국주식 > 계좌 > 미국주식 당일 주문체결 확인(ust21510)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust21510"
API_URL = "/api/us/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "result_list": "조회결과리스트"
}
COLUMNS = {
    "ord_no": "주문번호",
    "orig_ord_no": "원주문번호",
    "stex_nm": "거래소명",
    "crnc_code": "통화코드",
    "stk_cd": "종목코드",
    "frgn_stk_nm": "종목명",
    "frgn_trde_tp": "매매구분",
    "frgn_trde_nm": "매매구분명",
    "slby_tp": "매도매수구분",
    "slby_tp_nm": "매도매수구분명",
    "ord_qty": "주문수량",
    "ord_uv": "주문단가",
    "stop_pric": "STOP가격",
    "cntr_qty": "체결수량",
    "cntr_uv": "체결단가",
    "cnfm_qty": "확인수량",
    "ord_remnq": "주문잔량",
    "ord_time": "주문시간",
    "ord_resp_time": "주문응답시간",
    "ord_stat": "주문상태명",
    "rsrv_tp": "예약주문구분",
    "natn_nm": "국가명",
    "cntr_time": "체결시간"
}


NUMERIC_COLUMNS = (
    'STOP가격',
    '주문단가',
    '주문수량',
    '체결단가',
    '체결수량',
    '확인수량',
)

def _format_display(df: pd.DataFrame) -> pd.DataFrame:
    display = df.copy()
    for column in tuple(NUMERIC_COLUMNS):
        if column in display.columns:
            display[column] = display[column].map(_format_display_value)
    return display


def _format_display_value(value: object) -> object:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return value
    try:
        if pd.isna(value):
            return value
    except (TypeError, ValueError):
        return value
    text = str(value).strip()
    sign = "-" if text.startswith("-") else ""
    unsigned = text[1:] if sign else text
    if "." in unsigned:
        integer, fraction = unsigned.split(".", 1)
        if integer.isdigit() and fraction.isdigit():
            return f"{sign}{int(integer or '0'):,}.{fraction}"
        return value
    if unsigned.isdigit() and len(unsigned) >= 6:
        return f"{sign}{int(unsigned or '0'):,}"
    return value

def get_overseas_today_order_fills(
    slby_tp: str | None = '0',
    stex_tp: str | None = '',
    stk_cd: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 당일 주문체결 확인[ust21510] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        slby_tp: 매도매수구분 — 0:전체,1:매도,2:매수
        stex_tp: 거래소구분 — 종목코드 입력시
        stk_cd: 종목코드 — 미입력시 전체

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_today_order_fills(
        ...     slby_tp='0',
        ...     stex_tp='',
        ...     stk_cd='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }
    if slby_tp is not None:
        body["slby_tp"] = slby_tp  # 매도매수구분
    if stex_tp is not None:
        body["stex_tp"] = stex_tp  # 거래소구분
    if stk_cd is not None:
        body["stk_cd"] = stk_cd  # 종목코드

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "result_list": [],
    }
    # 5. API 호출 및 연속조회
    next_cont_yn = None
    next_key = None

    for page in range(MAX_PAGES):
        response = client.fetch_page(
            api_id=API_ID,
            path=API_URL,
            body=body,
            cont_yn=next_cont_yn,
            next_key=next_key,
        )
        response_body = response.body
        if response_body.get("return_code") not in (None, 0):
            message_rows.append({
                key: response_body.get(key)
                for key in MESSAGE_COLUMNS
            })
        for key in rows:
            records = response_body.get(key, [])
            if isinstance(records, list):
                column_keys = list(COLUMNS)
                for record in records:
                    if isinstance(record, dict):
                        rows[key].append(record)
                    elif isinstance(record, (list, tuple)):
                        rows[key].append(dict(zip(column_keys, record)))

        next_cont_yn = response.continuation.cont_yn
        next_key = response.continuation.next_key

        if next_cont_yn != "Y":
            break

        if page + 1 >= MAX_PAGES:
            break

        time.sleep(REQUEST_DELAY_SECONDS)

    # 6. DataFrame 변환
    result = {
        TABLE_KEYS.get(key, key): pd.DataFrame(records).rename(columns=COLUMNS)
        for key, records in rows.items()
    }
    if message_rows:
        result = {
            MESSAGE_KEY: pd.DataFrame(message_rows).rename(columns=MESSAGE_COLUMNS),
            **result,
        }
    return result


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    try:
        result = get_overseas_today_order_fills(
            slby_tp='0',
            stex_tp='',
            stk_cd='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
