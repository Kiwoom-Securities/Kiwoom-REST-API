# ---
# api_id: kt00017
# api_name: 계좌별당일현황요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 계좌별당일현황요청(kt00017)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "kt00017"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "d2_entra": "D+2추정예수금",
    "crd_int_npay_gold": "신용이자미납금",
    "etc_loana": "기타대여금",
    "gnrl_stk_evlt_amt_d2": "일반주식평가금액D+2",
    "dpst_grnt_use_amt_d2": "예탁담보대출금D+2",
    "crd_stk_evlt_amt_d2": "예탁담보주식평가금액D+2",
    "crd_loan_d2": "신용융자금D+2",
    "crd_loan_evlta_d2": "신용융자평가금D+2",
    "crd_ls_grnt_d2": "신용대주담보금D+2",
    "crd_ls_evlta_d2": "신용대주평가금D+2",
    "ina_amt": "입금금액",
    "outa": "출금금액",
    "inq_amt": "입고금액",
    "outq_amt": "출고금액",
    "sell_amt": "매도금액",
    "buy_amt": "매수금액",
    "cmsn": "수수료",
    "tax": "세금",
    "stk_pur_cptal_loan_amt": "주식매입자금대출금",
    "rp_evlt_amt": "RP평가금액",
    "bd_evlt_amt": "채권평가금액",
    "elsevlt_amt": "ELS평가금액",
    "crd_int_amt": "신용이자금액",
    "sel_prica_grnt_loan_int_amt_amt": "매도대금담보대출이자금액",
    "dvida_amt": "배당금액"
}


NUMERIC_COLUMNS = (
    'D+2추정예수금',
    'ELS평가금액',
    'RP평가금액',
    '기타대여금',
    '매도금액',
    '매도대금담보대출이자금액',
    '매수금액',
    '배당금액',
    '세금',
    '수수료',
    '신용대주담보금D+2',
    '신용대주평가금D+2',
    '신용융자금D+2',
    '신용융자평가금D+2',
    '신용이자금액',
    '신용이자미납금',
    '예탁담보대출금D+2',
    '예탁담보주식평가금액D+2',
    '일반주식평가금액D+2',
    '입고금액',
    '입금금액',
    '주식매입자금대출금',
    '채권평가금액',
    '출고금액',
    '출금금액',
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

def get_domestic_account_today_status(
) -> pd.DataFrame:
    """
    계좌별당일현황요청[kt00017] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_account_today_status(
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
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
    df = get_domestic_account_today_status(
    )
    # 결과 출력
    print(_format_display(df))
