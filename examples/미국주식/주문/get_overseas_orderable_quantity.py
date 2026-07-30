# ---
# api_id: ust31490
# api_name: 미국주식 주문가능수량(종목/증거금률별)
# category: 미국주식
# sub_category: 주문
# template: rest
# api_url: /api/us/ordr
# menu_path: 미국주식 > 주문 > 미국주식 주문가능수량(종목/증거금률별)(ust31490)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust31490"
API_URL = "/api/us/ordr"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "stk_profa_rt": "종목증거금율",
    "profa_rt": "계좌증거금율",
    "aplc_rt": "적용증거금율",
    "krw_ord_rqst_yn": "원화주문신청여부",
    "krw_ord_alowa_50": "증거금50%종목 원화주문가능금액",
    "krw_ord_alowq_50": "증거금50%종목 원화주문가능수량",
    "ord_alowa_50": "증거금50%종목 주문가능금액",
    "ord_alowq_50": "증거금50%종목 주문가능수량",
    "pred_rebuy_alowa_50": "증거금50%종목 전일재사용금액",
    "tdy_rebuy_alowa_50": "증거금50%종목 금일재사용금액",
    "krw_ord_alowa_100": "증거금100%종목원화주문가능금액",
    "krw_ord_alowq_100": "증거금100%종목원화주문가능수량",
    "ord_alowa_100": "증거금100%종목 주문가능금액",
    "ord_alowq_100": "증거금100%종목 주문가능수량",
    "pred_rebuy_alowa_100": "증거금100%종목 전일재사용금액",
    "tdy_rebuy_alowa_100": "증거금100%종목 금일재사용금액",
    "min_krw_ord_alowa": "미수불가 원화주문가능금액",
    "min_krw_ord_alowq": "미수불가 원화주문가능수량",
    "min_ord_alowa": "미수불가 주문가능금액",
    "min_ord_alowq": "미수불가 주문가능수량",
    "min_pred_rebuy_alowa": "미수불가 전일재사용금액",
    "min_tdy_rebuy_alowa": "미수불가 금일재사용금액",
    "krw_entra": "원화예수금",
    "fc_entra": "외화예수금",
    "fc_uncl_amt": "외화미수금",
    "ord_alowa": "주문가능현금",
    "krw_ord_set_amt": "해외원화주문설정금",
    "krw_ord_evlt_amt": "해외원화주문평가금",
    "crnc_code": "통화"
}


NUMERIC_COLUMNS = (
    '계좌증거금율',
    '미수불가 금일재사용금액',
    '미수불가 원화주문가능금액',
    '미수불가 원화주문가능수량',
    '미수불가 전일재사용금액',
    '미수불가 주문가능금액',
    '미수불가 주문가능수량',
    '외화미수금',
    '외화예수금',
    '원화예수금',
    '적용증거금율',
    '종목증거금율',
    '주문가능현금',
    '증거금100%종목 금일재사용금액',
    '증거금100%종목 전일재사용금액',
    '증거금100%종목 주문가능금액',
    '증거금100%종목 주문가능수량',
    '증거금100%종목원화주문가능금액',
    '증거금100%종목원화주문가능수량',
    '증거금50%종목 금일재사용금액',
    '증거금50%종목 원화주문가능금액',
    '증거금50%종목 원화주문가능수량',
    '증거금50%종목 전일재사용금액',
    '증거금50%종목 주문가능금액',
    '증거금50%종목 주문가능수량',
    '해외원화주문설정금',
    '해외원화주문평가금',
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

def get_overseas_orderable_quantity(
    stk_cd: str,
    uv: str,
    stex_tp: str | None = 'ND',
) -> pd.DataFrame:
    """
    미국주식 주문가능수량(종목/증거금률별)[ust31490] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드
        uv: 매수가격
        stex_tp: 거래소구분 — NA :AMEX, ND :NASDAQ, NY:NYSE

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_overseas_orderable_quantity(
        ...     stk_cd='NVDA',
        ...     uv='200',
        ...     stex_tp='ND',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not uv:
        raise ValueError('uv is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
        "uv": uv,  # 매수가격
    }
    if stex_tp is not None:
        body["stex_tp"] = stex_tp  # 거래소구분

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
        df = get_overseas_orderable_quantity(
            stk_cd='NVDA',
            uv='200',
            stex_tp='ND',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
