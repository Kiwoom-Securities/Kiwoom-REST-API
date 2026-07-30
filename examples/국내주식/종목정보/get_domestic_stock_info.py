# ---
# api_id: ka10001
# api_name: 주식기본정보요청
# category: 국내주식
# sub_category: 종목정보
# template: rest
# api_url: /api/dostk/stkinfo
# menu_path: 국내주식 > 종목정보 > 주식기본정보요청(ka10001)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10001"
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
    "setl_mm": "결산월",
    "fav": "액면가",
    "cap": "자본금",
    "flo_stk": "상장주식",
    "crd_rt": "신용비율",
    "oyr_hgst": "연중최고",
    "oyr_lwst": "연중최저",
    "mac": "시가총액",
    "mac_wght": "시가총액비중",
    "for_exh_rt": "외인소진률",
    "repl_pric": "대용가",
    "per": "PER",
    "eps": "EPS",
    "roe": "ROE",
    "pbr": "PBR",
    "ev": "EV",
    "bps": "BPS",
    "sale_amt": "매출액",
    "bus_pro": "영업이익",
    "cup_nga": "당기순이익",
    "250hgst": "250최고",
    "250lwst": "250최저",
    "high_pric": "고가",
    "open_pric": "시가",
    "low_pric": "저가",
    "upl_pric": "상한가",
    "lst_pric": "하한가",
    "base_pric": "기준가",
    "exp_cntr_pric": "예상체결가",
    "exp_cntr_qty": "예상체결수량",
    "250hgst_pric_dt": "250최고가일",
    "250hgst_pric_pre_rt": "250최고가대비율",
    "250lwst_pric_dt": "250최저가일",
    "250lwst_pric_pre_rt": "250최저가대비율",
    "cur_prc": "현재가",
    "pre_sig": "대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "trde_qty": "거래량",
    "trde_pre": "거래대비",
    "fav_unit": "액면가단위",
    "dstr_stk": "유통주식",
    "dstr_rt": "유통비율"
}


NUMERIC_COLUMNS = (
    '250최고가대비율',
    '250최고가일',
    '250최저가대비율',
    '250최저가일',
    'BPS',
    'EPS',
    'PBR',
    'PER',
    'ROE',
    '거래량',
    '고가',
    '기준가',
    '대용가',
    '등락율',
    '상한가',
    '시가',
    '시가총액',
    '시가총액비중',
    '신용비율',
    '액면가',
    '액면가단위',
    '예상체결가',
    '예상체결수량',
    '유통비율',
    '자본금',
    '저가',
    '하한가',
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

def get_domestic_stock_info(
    stk_cd: str,
) -> pd.DataFrame:
    """
    주식기본정보요청[ka10001] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_stock_info(
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
        df = get_domestic_stock_info(
            stk_cd='005930',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
