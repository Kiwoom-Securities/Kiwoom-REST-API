# ---
# api_id: ust20002
# api_name: 미국주식 정정 주문
# category: 미국주식
# sub_category: 주문
# template: rest
# api_url: /api/us/ordr
# menu_path: 미국주식 > 주문 > 미국주식 정정 주문(ust20002)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust20002"
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
    "stk_nm": "종목명",
    "ord_no": "주문번호",
    "fc_entra": "외화예수금",
    "tdy_rebuy_useda": "금일재매수사용금액",
    "pred_rebuy_useda": "전일재매수사용금액",
    "trst_prof_ch": "사용증거금",
    "mdfy_ord_qty": "정정주문수량"
}


NUMERIC_COLUMNS = (
    '금일재매수사용금액',
    '사용증거금',
    '외화예수금',
    '전일재매수사용금액',
    '정정주문수량',
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

def modify_overseas_stock_order(
    orig_ord_no: str,
    stex_tp: str,
    stk_cd: str,
    mdfy_uv: str | None = '210',
    stop_pric: str | None = '',
) -> pd.DataFrame:
    """
    미국주식 정정 주문[ust20002] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        orig_ord_no: 원주문번호 — 주문 요청 응답 결과로 받은 ord_no를 설정
        stex_tp: 거래소구분 — NA: AMEX, ND: NASDAQ, NY: NYSE
        stk_cd: 종목코드
        mdfy_uv: 정정단가
        stop_pric: STOP가격 — 원주문 trde_tp가 34(STOP LIMIT) 또는 35(STOP)인 경우 필수 입력, 그 외 거래유형(지정가 등) 설정 시 입력 값은 무시되거나 빈 값처리.

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = modify_overseas_stock_order(
        ...     orig_ord_no='000000050',
        ...     stex_tp='ND',
        ...     stk_cd='NVDA',
        ...     mdfy_uv='210',
        ...     stop_pric='',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not orig_ord_no:
        raise ValueError('orig_ord_no is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')
    if not stk_cd:
        raise ValueError('stk_cd is required.')

    # 2. 요청 파라미터 바디
    body = {
        "orig_ord_no": orig_ord_no,  # 원주문번호
        "stex_tp": stex_tp,  # 거래소구분
        "stk_cd": stk_cd,  # 종목코드
    }
    if mdfy_uv is not None:
        body["mdfy_uv"] = mdfy_uv  # 정정단가
    if stop_pric is not None:
        body["stop_pric"] = stop_pric  # STOP가격

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
        df = modify_overseas_stock_order(
            orig_ord_no='000000050',
            stex_tp='ND',
            stk_cd='NVDA',
            mdfy_uv='210',
            stop_pric='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
