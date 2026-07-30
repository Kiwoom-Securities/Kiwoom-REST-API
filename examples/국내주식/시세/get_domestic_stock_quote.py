# ---
# api_id: ka10004
# api_name: 주식호가요청
# category: 국내주식
# sub_category: 시세
# template: rest
# api_url: /api/dostk/mrkcond
# menu_path: 국내주식 > 시세 > 주식호가요청(ka10004)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10004"
API_URL = "/api/dostk/mrkcond"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "bid_req_base_tm": "호가잔량기준시간",
    "sel_10th_pre_req_pre": "매도10차선잔량대비",
    "sel_10th_pre_req": "매도10차선잔량",
    "sel_10th_pre_bid": "매도10차선호가",
    "sel_9th_pre_req_pre": "매도9차선잔량대비",
    "sel_9th_pre_req": "매도9차선잔량",
    "sel_9th_pre_bid": "매도9차선호가",
    "sel_8th_pre_req_pre": "매도8차선잔량대비",
    "sel_8th_pre_req": "매도8차선잔량",
    "sel_8th_pre_bid": "매도8차선호가",
    "sel_7th_pre_req_pre": "매도7차선잔량대비",
    "sel_7th_pre_req": "매도7차선잔량",
    "sel_7th_pre_bid": "매도7차선호가",
    "sel_6th_pre_req_pre": "매도6차선잔량대비",
    "sel_6th_pre_req": "매도6차선잔량",
    "sel_6th_pre_bid": "매도6차선호가",
    "sel_5th_pre_req_pre": "매도5차선잔량대비",
    "sel_5th_pre_req": "매도5차선잔량",
    "sel_5th_pre_bid": "매도5차선호가",
    "sel_4th_pre_req_pre": "매도4차선잔량대비",
    "sel_4th_pre_req": "매도4차선잔량",
    "sel_4th_pre_bid": "매도4차선호가",
    "sel_3th_pre_req_pre": "매도3차선잔량대비",
    "sel_3th_pre_req": "매도3차선잔량",
    "sel_3th_pre_bid": "매도3차선호가",
    "sel_2th_pre_req_pre": "매도2차선잔량대비",
    "sel_2th_pre_req": "매도2차선잔량",
    "sel_2th_pre_bid": "매도2차선호가",
    "sel_1th_pre_req_pre": "매도1차선잔량대비",
    "sel_fpr_req": "매도최우선잔량",
    "sel_fpr_bid": "매도최우선호가",
    "buy_fpr_bid": "매수최우선호가",
    "buy_fpr_req": "매수최우선잔량",
    "buy_1th_pre_req_pre": "매수1차선잔량대비",
    "buy_2th_pre_bid": "매수2차선호가",
    "buy_2th_pre_req": "매수2차선잔량",
    "buy_2th_pre_req_pre": "매수2차선잔량대비",
    "buy_3th_pre_bid": "매수3차선호가",
    "buy_3th_pre_req": "매수3차선잔량",
    "buy_3th_pre_req_pre": "매수3차선잔량대비",
    "buy_4th_pre_bid": "매수4차선호가",
    "buy_4th_pre_req": "매수4차선잔량",
    "buy_4th_pre_req_pre": "매수4차선잔량대비",
    "buy_5th_pre_bid": "매수5차선호가",
    "buy_5th_pre_req": "매수5차선잔량",
    "buy_5th_pre_req_pre": "매수5차선잔량대비",
    "buy_6th_pre_bid": "매수6차선호가",
    "buy_6th_pre_req": "매수6차선잔량",
    "buy_6th_pre_req_pre": "매수6차선잔량대비",
    "buy_7th_pre_bid": "매수7차선호가",
    "buy_7th_pre_req": "매수7차선잔량",
    "buy_7th_pre_req_pre": "매수7차선잔량대비",
    "buy_8th_pre_bid": "매수8차선호가",
    "buy_8th_pre_req": "매수8차선잔량",
    "buy_8th_pre_req_pre": "매수8차선잔량대비",
    "buy_9th_pre_bid": "매수9차선호가",
    "buy_9th_pre_req": "매수9차선잔량",
    "buy_9th_pre_req_pre": "매수9차선잔량대비",
    "buy_10th_pre_bid": "매수10차선호가",
    "buy_10th_pre_req": "매수10차선잔량",
    "buy_10th_pre_req_pre": "매수10차선잔량대비",
    "tot_sel_req_jub_pre": "총매도잔량직전대비",
    "tot_sel_req": "총매도잔량",
    "tot_buy_req": "총매수잔량",
    "tot_buy_req_jub_pre": "총매수잔량직전대비",
    "ovt_sel_req_pre": "시간외매도잔량대비",
    "ovt_sel_req": "시간외매도잔량",
    "ovt_buy_req": "시간외매수잔량",
    "ovt_buy_req_pre": "시간외매수잔량대비"
}


NUMERIC_COLUMNS = (
    '매도10차선호가',
    '매도2차선호가',
    '매도3차선호가',
    '매도4차선호가',
    '매도5차선호가',
    '매도6차선호가',
    '매도7차선호가',
    '매도8차선호가',
    '매도9차선호가',
    '매도최우선호가',
    '매수10차선호가',
    '매수2차선호가',
    '매수3차선호가',
    '매수4차선호가',
    '매수5차선호가',
    '매수6차선호가',
    '매수7차선호가',
    '매수8차선호가',
    '매수9차선호가',
    '매수최우선호가',
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

def get_domestic_stock_quote(
    stk_cd: str,
) -> pd.DataFrame:
    """
    주식호가요청[ka10004] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_stock_quote(
        ...     stk_cd='005930',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = []
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
        row = {
            key: response_body.get(key)
            for key in COLUMNS
        }
        if row:
            rows.append(row)

        next_cont_yn = response.continuation.cont_yn
        next_key = response.continuation.next_key

        if next_cont_yn != "Y":
            break

        if page + 1 >= MAX_PAGES:
            break

        time.sleep(REQUEST_DELAY_SECONDS)

    # 6. DataFrame 변환
    result = pd.DataFrame(rows).rename(columns=COLUMNS)
    if message_rows:
        message_df = pd.DataFrame(message_rows).rename(columns=MESSAGE_COLUMNS)
        result = pd.concat([message_df, result], axis=1)
    return result


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    try:
        df = get_domestic_stock_quote(
            stk_cd='005930',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
