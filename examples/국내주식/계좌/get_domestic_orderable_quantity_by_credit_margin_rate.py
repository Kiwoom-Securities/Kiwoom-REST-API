# ---
# api_id: kt00012
# api_name: 신용보증금율별주문가능수량조회요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 신용보증금율별주문가능수량조회요청(kt00012)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "kt00012"
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
    "stk_assr_rt": "종목보증금율",
    "stk_assr_rt_nm": "종목보증금율명",
    "assr_30ord_alow_amt": "보증금30%주문가능금액",
    "assr_30ord_alowq": "보증금30%주문가능수량",
    "assr_30pred_reu_amt": "보증금30%전일재사용금액",
    "assr_30tdy_reu_amt": "보증금30%금일재사용금액",
    "assr_40ord_alow_amt": "보증금40%주문가능금액",
    "assr_40ord_alowq": "보증금40%주문가능수량",
    "assr_40pred_reu_amt": "보증금40%전일재사용금액",
    "assr_40tdy_reu_amt": "보증금40%금일재사용금액",
    "assr_50ord_alow_amt": "보증금50%주문가능금액",
    "assr_50ord_alowq": "보증금50%주문가능수량",
    "assr_50pred_reu_amt": "보증금50%전일재사용금액",
    "assr_50tdy_reu_amt": "보증금50%금일재사용금액",
    "assr_60ord_alow_amt": "보증금60%주문가능금액",
    "assr_60ord_alowq": "보증금60%주문가능수량",
    "assr_60pred_reu_amt": "보증금60%전일재사용금액",
    "assr_60tdy_reu_amt": "보증금60%금일재사용금액",
    "entr": "예수금",
    "repl_amt": "대용금",
    "uncla": "미수금",
    "ord_pos_repl": "주문가능대용",
    "ord_alowa": "주문가능현금",
    "out_alowa": "미수가능금액",
    "out_pos_qty": "미수가능수량",
    "min_amt": "미수불가금액",
    "min_qty": "미수불가수량"
}


NUMERIC_COLUMNS = (
    '대용금',
    '미수가능금액',
    '미수가능수량',
    '미수금',
    '미수불가금액',
    '미수불가수량',
    '보증금30%금일재사용금액',
    '보증금30%전일재사용금액',
    '보증금30%주문가능금액',
    '보증금30%주문가능수량',
    '보증금40%금일재사용금액',
    '보증금40%전일재사용금액',
    '보증금40%주문가능금액',
    '보증금40%주문가능수량',
    '보증금50%금일재사용금액',
    '보증금50%전일재사용금액',
    '보증금50%주문가능금액',
    '보증금50%주문가능수량',
    '보증금60%금일재사용금액',
    '보증금60%전일재사용금액',
    '보증금60%주문가능금액',
    '보증금60%주문가능수량',
    '예수금',
    '종목보증금율',
    '주문가능대용',
    '주문가능현금',
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

def get_domestic_orderable_quantity_by_credit_margin_rate(
    stk_cd: str,
    uv: str | None = '',
) -> pd.DataFrame:
    """
    신용보증금율별주문가능수량조회요청[kt00012] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목번호
        uv: 매수가격

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_orderable_quantity_by_credit_margin_rate(
        ...     stk_cd='005930',
        ...     uv='',
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
    if uv is not None:
        body["uv"] = uv

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
    df = get_domestic_orderable_quantity_by_credit_margin_rate(
        stk_cd='005930',
        uv='',
    )
    # 결과 출력
    print(_format_display(df))
