# ---
# api_id: ka10002
# api_name: 주식거래원요청
# category: 국내주식
# sub_category: 종목정보
# template: rest
# api_url: /api/dostk/stkinfo
# menu_path: 국내주식 > 종목정보 > 주식거래원요청(ka10002)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10002"
API_URL = "/api/dostk/stkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "cur_prc": "현재가",
    "flu_smbol": "등락부호",
    "base_pric": "기준가",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "sel_trde_ori_nm_1": "매도거래원명1",
    "sel_trde_ori_1": "매도거래원1",
    "sel_trde_qty_1": "매도거래량1",
    "buy_trde_ori_nm_1": "매수거래원명1",
    "buy_trde_ori_1": "매수거래원1",
    "buy_trde_qty_1": "매수거래량1",
    "sel_trde_ori_nm_2": "매도거래원명2",
    "sel_trde_ori_2": "매도거래원2",
    "sel_trde_qty_2": "매도거래량2",
    "buy_trde_ori_nm_2": "매수거래원명2",
    "buy_trde_ori_2": "매수거래원2",
    "buy_trde_qty_2": "매수거래량2",
    "sel_trde_ori_nm_3": "매도거래원명3",
    "sel_trde_ori_3": "매도거래원3",
    "sel_trde_qty_3": "매도거래량3",
    "buy_trde_ori_nm_3": "매수거래원명3",
    "buy_trde_ori_3": "매수거래원3",
    "buy_trde_qty_3": "매수거래량3",
    "sel_trde_ori_nm_4": "매도거래원명4",
    "sel_trde_ori_4": "매도거래원4",
    "sel_trde_qty_4": "매도거래량4",
    "buy_trde_ori_nm_4": "매수거래원명4",
    "buy_trde_ori_4": "매수거래원4",
    "buy_trde_qty_4": "매수거래량4",
    "sel_trde_ori_nm_5": "매도거래원명5",
    "sel_trde_ori_5": "매도거래원5",
    "sel_trde_qty_5": "매도거래량5",
    "buy_trde_ori_nm_5": "매수거래원명5",
    "buy_trde_ori_5": "매수거래원5",
    "buy_trde_qty_5": "매수거래량5"
}


NUMERIC_COLUMNS = (
    '기준가',
    '등락율',
    '매도거래량1',
    '매도거래량2',
    '매도거래량3',
    '매도거래량4',
    '매도거래량5',
    '매수거래량1',
    '매수거래량2',
    '매수거래량3',
    '매수거래량4',
    '매수거래량5',
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

def get_domestic_stock_brokers(
    stk_cd: str,
) -> pd.DataFrame:
    """
    주식거래원요청[ka10002] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_stock_brokers(
        ...     stk_cd='005930',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')

    # 2. 요청 파라미터 바디
    body = {
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
        df = get_domestic_stock_brokers(
            stk_cd='005930',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
