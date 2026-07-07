# ---
# api_id: ka40009
# api_name: ETF시간대별체결요청
# category: 국내주식
# sub_category: ETF
# template: rest
# api_url: /api/dostk/etf
# menu_path: 국내주식 > ETF > ETF시간대별체결요청(ka40009)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka40009"
API_URL = "/api/dostk/etf"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "etfnavarray": "ETFNAV배열"
}
COLUMNS = {
    "nav": "NAV",
    "navpred_pre": "NAV전일대비",
    "navflu_rt": "NAV등락율",
    "trace_eor_rt": "추적오차율",
    "dispty_rt": "괴리율",
    "stkcnt": "주식수",
    "base_pric": "기준가",
    "for_rmnd_qty": "외인보유수량",
    "repl_pric": "대용가",
    "conv_pric": "환산가격",
    "drstk": "DR/주",
    "wonju_pric": "원주가격"
}


NUMERIC_COLUMNS = (
    'NAV등락율',
    '괴리율',
    '기준가',
    '대용가',
    '외인보유수량',
    '원주가격',
    '추적오차율',
    '환산가격',
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

def get_domestic_etf_intraday_nav_status(
    stk_cd: str,
) -> dict[str, pd.DataFrame]:
    """
    ETF시간대별체결요청[ka40009] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_etf_intraday_nav_status(
        ...     stk_cd='069500',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "etfnavarray": [],
    }
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
        for key in rows:
            records = response_body.get(key, [])
            if isinstance(records, list):
                rows[key].extend(
                    record for record in records if isinstance(record, dict)
                )

        next_cont_yn = response.continuation.cont_yn
        next_key = response.continuation.next_key

        if next_cont_yn != "Y":
            break

        if page + 1 >= MAX_PAGES:
            break

        time.sleep(REQUEST_DELAY_SECONDS)

    # 6. DataFrame 변환
    result = {
        TABLE_KEYS.get(key, key): pd.DataFrame(records).rename(columns=COLUMNS)
        for key, records in rows.items()
    }
    if message_rows:
        result = {
            MESSAGE_KEY: pd.DataFrame(message_rows).rename(columns=MESSAGE_COLUMNS),
            **result,
        }
    return result


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    result = get_domestic_etf_intraday_nav_status(
        stk_cd='069500',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
