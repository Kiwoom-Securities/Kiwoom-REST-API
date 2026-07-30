# ---
# api_id: usa26412
# api_name: 미국주식 연도별 ETF 카테고리별 종목등락률
# category: 미국주식
# sub_category: 종목정보
# template: rest
# api_url: /api/us/stkinfo
# menu_path: 미국주식 > 종목정보 > 미국주식 연도별 ETF 카테고리별 종목등락률(usa26412)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "usa26412"
API_URL = "/api/us/stkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "result_list": "결과리스트"
}
COLUMNS = {
    "stex_tp": "거래소구분",
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "stk_enm": "종목영문명",
    "m01_prft_rt": "1월 수익률",
    "m02_prft_rt": "2월 수익률",
    "m03_prft_rt": "3월 수익률",
    "m04_prft_rt": "4월 수익률",
    "m05_prft_rt": "5월 수익률",
    "m06_prft_rt": "6월 수익률",
    "m07_prft_rt": "7월 수익률",
    "m08_prft_rt": "8월 수익률",
    "m09_prft_rt": "9월 수익률",
    "m10_prft_rt": "10월 수익률",
    "m11_prft_rt": "11월 수익률",
    "m12_prft_rt": "12월 수익률"
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

def get_overseas_yearly_change_rate_by_etf_category(
    etf_cat1: str | None = '',
    etf_cat2: str | None = '',
    srch_yr: str | None = '2026',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 연도별 ETF 카테고리별 종목등락률[usa26412] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        etf_cat1: ETF카테고리코드1 — stk_tp(종목구분) 2일 경우 ETF 대카테고리코드 (ETF이고 대분류일 경우 사용), usa10105 cate1 속성 참고
        etf_cat2: ETF카테고리코드2 — stk_tp(종목구분) 2일 경우 ETF 중카테고리코드 (ETF이고 중분류일 경우 사용), usa10105 cate2 속성 참고
        srch_yr: 조회연도 — YYYY

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_yearly_change_rate_by_etf_category(
        ...     etf_cat1='',
        ...     etf_cat2='',
        ...     srch_yr='2026',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }
    if etf_cat1 is not None:
        body["etf_cat1"] = etf_cat1  # ETF카테고리코드1
    if etf_cat2 is not None:
        body["etf_cat2"] = etf_cat2  # ETF카테고리코드2
    if srch_yr is not None:
        body["srch_yr"] = srch_yr  # 조회연도

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "result_list": [],
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
                column_keys = list(COLUMNS)
                for record in records:
                    if isinstance(record, dict):
                        rows[key].append(record)
                    elif isinstance(record, (list, tuple)):
                        rows[key].append(dict(zip(column_keys, record)))

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
    try:
        result = get_overseas_yearly_change_rate_by_etf_category(
            etf_cat1='',
            etf_cat2='',
            srch_yr='2026',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
