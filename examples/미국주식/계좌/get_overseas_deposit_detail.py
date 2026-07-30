# ---
# api_id: ust21160
# api_name: 미국주식 예수금 상세
# category: 미국주식
# sub_category: 계좌
# template: rest
# api_url: /api/us/acnt
# menu_path: 미국주식 > 계좌 > 미국주식 예수금 상세(ust21160)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust21160"
API_URL = "/api/us/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "won_entr": "원화 예수금",
    "won_dfr_amt": "미수금",
    "won_etc_loana": "기타 대여금",
    "krw_ord_set_amt": "해외원화주문설정금",
    "usd_exch_rate": "매도환율(USD)",
    "d0_setl_dt": "D0 국내결제일자",
    "d0_won_conv_alow_ch": "D0 원화환산추정인출가능금",
    "d0_usd_fx_entr": "D0 외화예수금(USD)",
    "d1_setl_dt": "D1 국내결제일자",
    "d1_won_conv_alow_ch": "D1 원화환산추정인출가능금",
    "d1_usd_fx_entr": "D1 외화예수금(USD)",
    "d1_usd_exct_amt": "D1 해외정산금(USD)",
    "d1_usd_buy_excta": "D1 해외매수정산금(USD)",
    "d1_usd_sell_excta": "D1 해외매도정산금(USD)",
    "d2_setl_dt": "D2 국내결제일자",
    "d2_won_conv_alow_ch": "D2 원화환산추정인출가능금",
    "d2_usd_fx_entr": "D2 외화예수금(USD)",
    "d2_usd_exct_amt": "D2 해외정산금(USD)",
    "d2_usd_buy_excta": "D2 해외매수정산금(USD)",
    "d2_usd_sell_excta": "D2 해외매도정산금(USD)",
    "d3_setl_dt": "D3 국내결제일자",
    "d3_won_conv_alow_ch": "D3 원화환산추정인출가능금",
    "d3_usd_fx_entr": "D3 외화예수금(USD)",
    "d3_usd_exct_amt": "D3 해외정산금(USD)",
    "d3_usd_buy_excta": "D3 해외매수정산금(USD)",
    "d3_usd_sell_excta": "D3 해외매도정산금(USD)",
    "d4_setl_dt": "D4 국내결제일자",
    "d4_won_conv_alow_ch": "D4 원화환산추정인출가능금",
    "d4_usd_fx_entr": "D4 외화예수금(USD)",
    "d4_usd_exct_amt": "D4 해외정산금(USD)",
    "d4_usd_buy_excta": "D4 해외매수정산금(USD)",
    "d4_usd_sell_excta": "D4 해외매도정산금(USD)"
}


NUMERIC_COLUMNS = (
    'D0 외화예수금(USD)',
    'D0 원화환산추정인출가능금',
    'D1 외화예수금(USD)',
    'D1 원화환산추정인출가능금',
    'D1 해외매도정산금(USD)',
    'D1 해외매수정산금(USD)',
    'D1 해외정산금(USD)',
    'D2 외화예수금(USD)',
    'D2 원화환산추정인출가능금',
    'D2 해외매도정산금(USD)',
    'D2 해외매수정산금(USD)',
    'D2 해외정산금(USD)',
    'D3 외화예수금(USD)',
    'D3 원화환산추정인출가능금',
    'D3 해외매도정산금(USD)',
    'D3 해외매수정산금(USD)',
    'D3 해외정산금(USD)',
    'D4 외화예수금(USD)',
    'D4 원화환산추정인출가능금',
    'D4 해외매도정산금(USD)',
    'D4 해외매수정산금(USD)',
    'D4 해외정산금(USD)',
    '기타 대여금',
    '매도환율(USD)',
    '미수금',
    '원화 예수금',
    '해외원화주문설정금',
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

def get_overseas_deposit_detail(
) -> pd.DataFrame:
    """
    미국주식 예수금 상세[ust21160] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_overseas_deposit_detail(
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
    try:
        df = get_overseas_deposit_detail(
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
