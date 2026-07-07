# ---
# api_id: kt10007
# api_name: 신용 매도주문
# category: 국내주식
# sub_category: 신용주문
# template: rest
# api_url: /api/dostk/crdordr
# menu_path: 국내주식 > 신용주문 > 신용 매도주문(kt10007)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "kt10007"
API_URL = "/api/dostk/crdordr"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "ord_no": "주문번호",
    "dmst_stex_tp": "국내거래소구분"
}


NUMERIC_COLUMNS = ()

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

def sell_domestic_credit_stock(
    dmst_stex_tp: str,
    stk_cd: str,
    ord_qty: str,
    trde_tp: str,
    crd_deal_tp: str,
    ord_uv: str | None = '6450',
    crd_loan_dt: str | None = '',
    cond_uv: str | None = '',
) -> pd.DataFrame:
    """
    신용 매도주문[kt10007] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        dmst_stex_tp: KRX,NXT,SOR
        stk_cd: 종목코드
        ord_qty: 주문수량
        trde_tp: 0:보통 , 3:시장가 , 5:조건부지정가 , 81:장마감후시간외 , 61:장시작전시간외, 62:시간외단일가 , 6:최유리지정가 , 7:최우선지정가 , 10:보통(IOC) , 13:시장가(IOC) , 16:최유리(IOC) , 20:보통(FOK) , 23:시장가(FOK) , 26:최유리(FOK) , 28:스톱지정가,29:중간가,30:중간가(IOC),31:중간가(FOK)
        crd_deal_tp: 33:융자 , 99:융자합
        ord_uv: 주문단가
        crd_loan_dt: YYYYMMDD(융자일경우필수)
        cond_uv: 조건단가

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = sell_domestic_credit_stock(
        ...     dmst_stex_tp='KRX',
        ...     stk_cd='005930',
        ...     ord_qty='3',
        ...     trde_tp='0',
        ...     crd_deal_tp='99',
        ...     ord_uv='6450',
        ...     crd_loan_dt='',
        ...     cond_uv='',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not dmst_stex_tp:
        raise ValueError('dmst_stex_tp is required.')
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not ord_qty:
        raise ValueError('ord_qty is required.')
    if not trde_tp:
        raise ValueError('trde_tp is required.')
    if not crd_deal_tp:
        raise ValueError('crd_deal_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "dmst_stex_tp": dmst_stex_tp,
        "stk_cd": stk_cd,
        "ord_qty": ord_qty,
        "trde_tp": trde_tp,
        "crd_deal_tp": crd_deal_tp,
    }
    if ord_uv is not None:
        body["ord_uv"] = ord_uv
    if crd_loan_dt is not None:
        body["crd_loan_dt"] = crd_loan_dt
    if cond_uv is not None:
        body["cond_uv"] = cond_uv

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
    df = sell_domestic_credit_stock(
        dmst_stex_tp='KRX',
        stk_cd='005930',
        ord_qty='3',
        trde_tp='0',
        crd_deal_tp='99',
        ord_uv='6450',
        crd_loan_dt='',
        cond_uv='',
    )
    # 결과 출력
    print(_format_display(df))
