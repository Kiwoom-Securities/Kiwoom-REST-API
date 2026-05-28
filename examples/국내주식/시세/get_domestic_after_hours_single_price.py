# ---
# api_id: ka10087
# api_name: 시간외단일가요청
# category: 국내주식
# sub_category: 시세
# template: rest
# api_url: /api/dostk/mrkcond
# menu_path: 국내주식 > 시세 > 시간외단일가요청(ka10087)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka10087"
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
    "ovt_sigpric_sel_bid_jub_pre_5": "시간외단일가_매도호가직전대비5",
    "ovt_sigpric_sel_bid_jub_pre_4": "시간외단일가_매도호가직전대비4",
    "ovt_sigpric_sel_bid_jub_pre_3": "시간외단일가_매도호가직전대비3",
    "ovt_sigpric_sel_bid_jub_pre_2": "시간외단일가_매도호가직전대비2",
    "ovt_sigpric_sel_bid_jub_pre_1": "시간외단일가_매도호가직전대비1",
    "ovt_sigpric_sel_bid_qty_5": "시간외단일가_매도호가수량5",
    "ovt_sigpric_sel_bid_qty_4": "시간외단일가_매도호가수량4",
    "ovt_sigpric_sel_bid_qty_3": "시간외단일가_매도호가수량3",
    "ovt_sigpric_sel_bid_qty_2": "시간외단일가_매도호가수량2",
    "ovt_sigpric_sel_bid_qty_1": "시간외단일가_매도호가수량1",
    "ovt_sigpric_sel_bid_5": "시간외단일가_매도호가5",
    "ovt_sigpric_sel_bid_4": "시간외단일가_매도호가4",
    "ovt_sigpric_sel_bid_3": "시간외단일가_매도호가3",
    "ovt_sigpric_sel_bid_2": "시간외단일가_매도호가2",
    "ovt_sigpric_sel_bid_1": "시간외단일가_매도호가1",
    "ovt_sigpric_buy_bid_1": "시간외단일가_매수호가1",
    "ovt_sigpric_buy_bid_2": "시간외단일가_매수호가2",
    "ovt_sigpric_buy_bid_3": "시간외단일가_매수호가3",
    "ovt_sigpric_buy_bid_4": "시간외단일가_매수호가4",
    "ovt_sigpric_buy_bid_5": "시간외단일가_매수호가5",
    "ovt_sigpric_buy_bid_qty_1": "시간외단일가_매수호가수량1",
    "ovt_sigpric_buy_bid_qty_2": "시간외단일가_매수호가수량2",
    "ovt_sigpric_buy_bid_qty_3": "시간외단일가_매수호가수량3",
    "ovt_sigpric_buy_bid_qty_4": "시간외단일가_매수호가수량4",
    "ovt_sigpric_buy_bid_qty_5": "시간외단일가_매수호가수량5",
    "ovt_sigpric_buy_bid_jub_pre_1": "시간외단일가_매수호가직전대비1",
    "ovt_sigpric_buy_bid_jub_pre_2": "시간외단일가_매수호가직전대비2",
    "ovt_sigpric_buy_bid_jub_pre_3": "시간외단일가_매수호가직전대비3",
    "ovt_sigpric_buy_bid_jub_pre_4": "시간외단일가_매수호가직전대비4",
    "ovt_sigpric_buy_bid_jub_pre_5": "시간외단일가_매수호가직전대비5",
    "ovt_sigpric_sel_bid_tot_req": "시간외단일가_매도호가총잔량",
    "ovt_sigpric_buy_bid_tot_req": "시간외단일가_매수호가총잔량",
    "sel_bid_tot_req_jub_pre": "매도호가총잔량직전대비",
    "sel_bid_tot_req": "매도호가총잔량",
    "buy_bid_tot_req": "매수호가총잔량",
    "buy_bid_tot_req_jub_pre": "매수호가총잔량직전대비",
    "ovt_sel_bid_tot_req_jub_pre": "시간외매도호가총잔량직전대비",
    "ovt_sel_bid_tot_req": "시간외매도호가총잔량",
    "ovt_buy_bid_tot_req": "시간외매수호가총잔량",
    "ovt_buy_bid_tot_req_jub_pre": "시간외매수호가총잔량직전대비",
    "ovt_sigpric_cur_prc": "시간외단일가_현재가",
    "ovt_sigpric_pred_pre_sig": "시간외단일가_전일대비기호",
    "ovt_sigpric_pred_pre": "시간외단일가_전일대비",
    "ovt_sigpric_flu_rt": "시간외단일가_등락률",
    "ovt_sigpric_acc_trde_qty": "시간외단일가_누적거래량"
}


NUMERIC_COLUMNS = (
    '매도호가총잔량',
    '매도호가총잔량직전대비',
    '매수호가총잔량',
    '매수호가총잔량직전대비',
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

def get_domestic_after_hours_single_price(
    stk_cd: str,
) -> pd.DataFrame:
    """
    시간외단일가요청[ka10087] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_after_hours_single_price(
        ...     stk_cd='005930',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,
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
    df = get_domestic_after_hours_single_price(
        stk_cd='005930',
    )
    # 결과 출력
    print(_format_display(df))
