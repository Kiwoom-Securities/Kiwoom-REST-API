# ---
# api_id: usa20100
# api_name: 미국주식 현재가 종목정보
# category: 미국주식
# sub_category: 시세
# template: rest
# api_url: /api/us/mrkcond
# menu_path: 미국주식 > 시세 > 미국주식 현재가 종목정보(usa20100)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "usa20100"
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
    "52wk_hgst_pric": "52주 최고가",
    "52wk_hgst_pric_pre_rt": "52주 최고가 대비율",
    "52wk_hgst_pric_dt": "52주 최고가일",
    "52wk_lwst_pric": "52주 최저가",
    "52wk_lwst_pric_pre_rt": "52주 최저가 대비율",
    "52wk_lwst_pric_dt": "52주 최저가일",
    "stk_cnt": "주식수",
    "mac": "시가총액",
    "setl_mm": "결산월",
    "lg_inds_cd": "대업종구분",
    "sm_inds_cd": "소업종구분",
    "cur_prc": "현재가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "acc_trde_qty": "누적거래량",
    "oyr_hgst": "연중최고가",
    "oyr_hgst_dt": "연중최고가일",
    "oyr_hgst_pre_rt": "연중최고가 대비율",
    "oyr_lwst": "연중최저가",
    "oyr_lwst_dt": "연중최저가일",
    "oyr_lwst_pre_rt": "연중최저가 대비율",
    "pre_open_pric": "전일시가",
    "pre_high_pric": "전일고가",
    "pre_low_pric": "전일저가",
    "base_close_pric": "전일종가",
    "upl_pric": "상한가",
    "lst_pric": "하한가",
    "trde_qty_unit": "매매수량단위",
    "uncert_lv": "불확실성",
    "comp_adv_tp": "경쟁우위",
    "curr_unit": "통화단위",
    "open_pric": "시가",
    "high_pric": "고가",
    "low_pric": "저가",
    "trd_susp_tp": "거래정지여부",
    "base_exrt": "환율"
}


NUMERIC_COLUMNS = (
    '52주 최고가',
    '52주 최고가 대비율',
    '52주 최고가일',
    '52주 최저가',
    '52주 최저가 대비율',
    '52주 최저가일',
    '고가',
    '누적거래량',
    '등락률',
    '매매수량단위',
    '상한가',
    '시가',
    '시가총액',
    '연중최고가',
    '연중최고가 대비율',
    '연중최고가일',
    '연중최저가',
    '연중최저가 대비율',
    '연중최저가일',
    '저가',
    '전일고가',
    '전일저가',
    '전일종가',
    '하한가',
    '현재가',
    '환율',
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

def get_overseas_stock_quote(
    stex_tp: str,
    stk_cd: str,
) -> pd.DataFrame:
    """
    미국주식 현재가 종목정보[usa20100] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stex_tp: 거래소구분 — NA: AMEX, ND: NASDAQ, NY: NYSE
        stk_cd: 종목코드

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_overseas_stock_quote(
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
        df = get_overseas_stock_quote(
            stex_tp='ND',
            stk_cd='NVDA',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
