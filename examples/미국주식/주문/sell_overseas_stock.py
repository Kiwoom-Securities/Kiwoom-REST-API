# ---
# api_id: ust20001
# api_name: 미국주식 매도 주문
# category: 미국주식
# sub_category: 주문
# template: rest
# api_url: /api/us/ordr
# menu_path: 미국주식 > 주문 > 미국주식 매도 주문(ust20001)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust20001"
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
    "poss_qty": "보유수량",
    "tdy_resel_usedq": "금일재매도사용수량",
    "pred_resel_usedq": "전일재매도사용수량"
}


NUMERIC_COLUMNS = (
    '금일재매도사용수량',
    '보유수량',
    '전일재매도사용수량',
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

def sell_overseas_stock(
    stk_cd: str,
    stex_tp: str,
    ord_qty: str,
    trde_tp: str,
    ord_uv: str | None = '210.05',
    stop_pric: str | None = '',
) -> pd.DataFrame:
    """
    미국주식 매도 주문[ust20001] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드
        stex_tp: 거래소구분 — NA: AMEX, ND: NASDAQ, NY: NYSE
        ord_qty: 주문수량
        trde_tp: 매매구분 — 00:지정가 03시장가 26:VWAP지정가 27:TWAP지정가 30:LOC 33:MOC 36:VWAP시장가 37:TWAP시장가 35:STOP 34:STOP LIMIT
        ord_uv: 주문단가 — trde_tp가 00(지정가),30(LOC)...인 경우 필수 입력, 그 외 시장가 거래유형 설정 시 입력 값은 빈 값 처리
        stop_pric: STOP가격 — trde_tp가 34(STOP LIMIT) 또는 35(STOP)인 경우 필수 입력, 그 외 거래유형(지정가,시장가 등) 설정 시 입력 값은 무시되거나 빈 값처리.

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = sell_overseas_stock(
        ...     stk_cd='NVDA',
        ...     stex_tp='ND',
        ...     ord_qty='10',
        ...     trde_tp='00',
        ...     ord_uv='210.05',
        ...     stop_pric='',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')
    if not ord_qty:
        raise ValueError('ord_qty is required.')
    if not trde_tp:
        raise ValueError('trde_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
        "stex_tp": stex_tp,  # 거래소구분
        "ord_qty": ord_qty,  # 주문수량
        "trde_tp": trde_tp,  # 매매구분
    }
    if ord_uv is not None:
        body["ord_uv"] = ord_uv  # 주문단가
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
        df = sell_overseas_stock(
            stk_cd='NVDA',
            stex_tp='ND',
            ord_qty='10',
            trde_tp='00',
            ord_uv='210.05',
            stop_pric='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
