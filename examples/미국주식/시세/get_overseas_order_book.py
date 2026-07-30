# ---
# api_id: usa20101
# api_name: 미국주식 현재가 10호가
# category: 미국주식
# sub_category: 시세
# template: rest
# api_url: /api/us/mrkcond
# menu_path: 미국주식 > 시세 > 미국주식 현재가 10호가(usa20101)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "usa20101"
API_URL = "/api/us/mrkcond"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "stex_tp": "거래소구분",
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "stk_enm": "종목영문명",
    "cur_prc": "현재가",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "trde_qty": "거래량",
    "trde_prica": "거래대금",
    "open_pric": "시가",
    "high_pric": "고가",
    "low_pric": "저가",
    "bid_tm": "호가시간",
    "dt": "일자",
    "pred_pre_sig": "전일대비기호",
    "fpr_sel_bid": "최우선매도호가",
    "fpr_buy_bid": "최우선매수호가",
    "pre_trde_rt": "전일거래대비",
    "trde_tern_rt": "거래회전율",
    "sel_1bid": "매도1호가",
    "sel_2bid": "매도2호가",
    "sel_3bid": "매도3호가",
    "sel_4bid": "매도4호가",
    "sel_5bid": "매도5호가",
    "sel_6bid": "매도6호가",
    "sel_7bid": "매도7호가",
    "sel_8bid": "매도8호가",
    "sel_9bid": "매도9호가",
    "sel_10bid": "매도10호가",
    "buy_1bid": "매수1호가",
    "buy_2bid": "매수2호가",
    "buy_3bid": "매수3호가",
    "buy_4bid": "매수4호가",
    "buy_5bid": "매수5호가",
    "buy_6bid": "매수6호가",
    "buy_7bid": "매수7호가",
    "buy_8bid": "매수8호가",
    "buy_9bid": "매수9호가",
    "buy_10bid": "매수10호가",
    "sel_1bid_req": "매도1호가잔량",
    "sel_2bid_req": "매도2호가잔량",
    "sel_3bid_req": "매도3호가잔량",
    "sel_4bid_req": "매도4호가잔량",
    "sel_5bid_req": "매도5호가잔량",
    "sel_6bid_req": "매도6호가잔량",
    "sel_7bid_req": "매도7호가잔량",
    "sel_8bid_req": "매도8호가잔량",
    "sel_9bid_req": "매도9호가잔량",
    "sel_10bid_req": "매도10호가잔량",
    "buy_1bid_req": "매수1호가잔량",
    "buy_2bid_req": "매수2호가잔량",
    "buy_3bid_req": "매수3호가잔량",
    "buy_4bid_req": "매수4호가잔량",
    "buy_5bid_req": "매수5호가잔량",
    "buy_6bid_req": "매수6호가잔량",
    "buy_7bid_req": "매수7호가잔량",
    "buy_8bid_req": "매수8호가잔량",
    "buy_9bid_req": "매수9호가잔량",
    "buy_10bid_req": "매수10호가잔량",
    "sel_1bid_jub_pre": "매도1호가직전대비",
    "sel_2bid_jub_pre": "매도2호가직전대비",
    "sel_3bid_jub_pre": "매도3호가직전대비",
    "sel_4bid_jub_pre": "매도4호가직전대비",
    "sel_5bid_jub_pre": "매도5호가직전대비",
    "sel_6bid_jub_pre": "매도6호가직전대비",
    "sel_7bid_jub_pre": "매도7호가직전대비",
    "sel_8bid_jub_pre": "매도8호가직전대비",
    "sel_9bid_jub_pre": "매도9호가직전대비",
    "sel_10bid_jub_pre": "매도10호가직전대비",
    "buy_1th_pre_req_pre": "매수1차선잔량대비",
    "buy_1bid_jub_pre": "매수1호가직전대비",
    "buy_2bid_jub_pre": "매수2호가직전대비",
    "buy_3bid_jub_pre": "매수3호가직전대비",
    "buy_4bid_jub_pre": "매수4호가직전대비",
    "buy_5bid_jub_pre": "매수5호가직전대비",
    "buy_6bid_jub_pre": "매수6호가직전대비",
    "buy_7bid_jub_pre": "매수7호가직전대비",
    "buy_8bid_jub_pre": "매수8호가직전대비",
    "buy_9bid_jub_pre": "매수9호가직전대비",
    "buy_10bid_jub_pre": "매수10호가직전대비",
    "tot_sel_req": "총매도잔량",
    "sel_bid_tot_req_jub_pre": "매도호가총잔량직전대비",
    "tot_buy_req": "총매수잔량",
    "buy_bid_tot_req_jub_pre": "매수호가총잔량직전대비",
    "netprps_req": "순매수잔량",
    "netslmt_req": "순매도잔량",
    "upl_pric": "상한가",
    "base_pric": "기준가"
}


NUMERIC_COLUMNS = (
    '거래대금',
    '거래량',
    '거래회전율',
    '고가',
    '기준가',
    '등락률',
    '매도10호가',
    '매도10호가잔량',
    '매도10호가직전대비',
    '매도1호가',
    '매도1호가잔량',
    '매도1호가직전대비',
    '매도2호가',
    '매도2호가잔량',
    '매도2호가직전대비',
    '매도3호가',
    '매도3호가잔량',
    '매도3호가직전대비',
    '매도4호가',
    '매도4호가잔량',
    '매도4호가직전대비',
    '매도5호가',
    '매도5호가잔량',
    '매도5호가직전대비',
    '매도6호가',
    '매도6호가잔량',
    '매도6호가직전대비',
    '매도7호가',
    '매도7호가잔량',
    '매도7호가직전대비',
    '매도8호가',
    '매도8호가잔량',
    '매도8호가직전대비',
    '매도9호가',
    '매도9호가잔량',
    '매도9호가직전대비',
    '매도호가총잔량직전대비',
    '매수10호가',
    '매수10호가잔량',
    '매수10호가직전대비',
    '매수1호가',
    '매수1호가잔량',
    '매수1호가직전대비',
    '매수2호가',
    '매수2호가잔량',
    '매수2호가직전대비',
    '매수3호가',
    '매수3호가잔량',
    '매수3호가직전대비',
    '매수4호가',
    '매수4호가잔량',
    '매수4호가직전대비',
    '매수5호가',
    '매수5호가잔량',
    '매수5호가직전대비',
    '매수6호가',
    '매수6호가잔량',
    '매수6호가직전대비',
    '매수7호가',
    '매수7호가잔량',
    '매수7호가직전대비',
    '매수8호가',
    '매수8호가잔량',
    '매수8호가직전대비',
    '매수9호가',
    '매수9호가잔량',
    '매수9호가직전대비',
    '매수호가총잔량직전대비',
    '상한가',
    '시가',
    '저가',
    '최우선매도호가',
    '최우선매수호가',
    '현재가',
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

def get_overseas_order_book(
    stex_tp: str,
    stk_cd: str,
) -> pd.DataFrame:
    """
    미국주식 현재가 10호가[usa20101] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stex_tp: 거래소구분 — NA: AMEX, ND: NASDAQ, NY: NYSE
        stk_cd: 종목코드

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_overseas_order_book(
        ...     stex_tp='ND',
        ...     stk_cd='NVDA',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not stex_tp:
        raise ValueError('stex_tp is required.')
    if not stk_cd:
        raise ValueError('stk_cd is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stex_tp": stex_tp,  # 거래소구분
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
        df = get_overseas_order_book(
            stex_tp='ND',
            stk_cd='NVDA',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
