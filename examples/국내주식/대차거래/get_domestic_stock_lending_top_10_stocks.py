# ---
# api_id: ka10069
# api_name: 대차거래상위10종목요청
# category: 국내주식
# sub_category: 대차거래
# template: rest
# api_url: /api/dostk/slb
# menu_path: 국내주식 > 대차거래 > 대차거래상위10종목요청(ka10069)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka10069"
API_URL = "/api/dostk/slb"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "dbrt_trde_upper_10stk": "대차거래상위10종목"
}
COLUMNS = {
    "stk_nm": "종목명",
    "stk_cd": "종목코드",
    "dbrt_trde_cntrcnt": "대차거래체결주수",
    "dbrt_trde_rpy": "대차거래상환주수",
    "rmnd": "잔고주수",
    "remn_amt": "잔고금액"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "dbrt_trde_cntrcnt_sum": "대차거래체결주수합",
    "dbrt_trde_rpy_sum": "대차거래상환주수합",
    "rmnd_sum": "잔고주수합",
    "remn_amt_sum": "잔고금액합",
    "dbrt_trde_cntrcnt_rt": "대차거래체결주수비율",
    "dbrt_trde_rpy_rt": "대차거래상환주수비율",
    "rmnd_rt": "잔고주수비율",
    "remn_amt_rt": "잔고금액비율"
}


NUMERIC_COLUMNS = (
    '대차거래상환주수비율',
    '대차거래체결주수비율',
    '잔고금액',
    '잔고금액비율',
    '잔고금액합',
    '잔고주수',
    '잔고주수비율',
    '잔고주수합',
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

def get_domestic_stock_lending_top_10_stocks(
    strt_dt: str,
    mrkt_tp: str,
    end_dt: str | None = '20241125',
) -> dict[str, pd.DataFrame]:
    """
    대차거래상위10종목요청[ka10069] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        strt_dt: YYYYMMDD
            (연도4자리, 월 2자리, 일 2자리 형식)
        mrkt_tp: 001:코스피, 101:코스닥
        end_dt: YYYYMMDD
            (연도4자리, 월 2자리, 일 2자리 형식)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_stock_lending_top_10_stocks(
        ...     strt_dt='20241110',
        ...     mrkt_tp='001',
        ...     end_dt='20241125',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not strt_dt:
        raise ValueError('strt_dt is required.')
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "strt_dt": strt_dt,
        "mrkt_tp": mrkt_tp,
    }
    if end_dt is not None:
        body["end_dt"] = end_dt

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "dbrt_trde_upper_10stk": [],
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
        summary_rows.append({
            key: response_body.get(key)
            for key in SUMMARY_COLUMNS
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
    result = {
        SUMMARY_KEY: pd.DataFrame(summary_rows).rename(columns=SUMMARY_COLUMNS),
        **result,
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
    result = get_domestic_stock_lending_top_10_stocks(
        strt_dt='20241110',
        mrkt_tp='001',
        end_dt='20241125',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
