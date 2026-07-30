# ---
# api_id: ust21640
# api_name: 미국주식 일별 종목별 실현손익
# category: 미국주식
# sub_category: 계좌
# template: rest
# api_url: /api/us/acnt
# menu_path: 미국주식 > 계좌 > 미국주식 일별 종목별 실현손익(ust21640)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust21640"
API_URL = "/api/us/acnt"
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
    "stex_nm": "거래소코드명",
    "stk_nm": "종목명",
    "crnc_code": "통화코드",
    "cntr_sellq": "체결매도수량",
    "avg_buy_uv": "매입평균가",
    "cntr_sella": "체결매도가",
    "pl_amt": "실현손익",
    "pl_rt": "실현수익률",
    "stk_cd": "종목코드",
    "cmsn": "수수료",
    "altx": "제세금",
    "exch_rate": "환율",
    "natn_nm": "국가명"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "tot_pl_amt": "총실현손익",
    "tot_pl_amt_krw": "총실현손익(원)"
}


NUMERIC_COLUMNS = (
    '매입평균가',
    '수수료',
    '실현손익',
    '제세금',
    '체결매도가',
    '체결매도수량',
    '총실현손익',
    '총실현손익(원)',
    '환율',
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

def get_overseas_realized_pnl_by_date_and_stock(
    cntr_dt: str,
    fc_krw_tp: str,
    stex_tp: str | None = '',
    stk_cd: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 일별 종목별 실현손익[ust21640] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        cntr_dt: 체결일자 — YYYYMMDD
        fc_krw_tp: 외화원화구분 — 0:외화,1:원화
        stex_tp: 거래소구분 — ND:NASDAQ,NY:NYSE,NA:AMEX
        stk_cd: 종목코드

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_realized_pnl_by_date_and_stock(
        ...     cntr_dt='20260611',
        ...     fc_krw_tp='0',
        ...     stex_tp='',
        ...     stk_cd='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not cntr_dt:
        raise ValueError('cntr_dt is required.')
    if not fc_krw_tp:
        raise ValueError('fc_krw_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "cntr_dt": cntr_dt,  # 체결일자
        "fc_krw_tp": fc_krw_tp,  # 외화원화구분
    }
    if stex_tp is not None:
        body["stex_tp"] = stex_tp  # 거래소구분
    if stk_cd is not None:
        body["stk_cd"] = stk_cd  # 종목코드

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
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
        summary_rows.append({
            key: response_body.get(key)
            for key in SUMMARY_COLUMNS
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
    try:
        result = get_overseas_realized_pnl_by_date_and_stock(
            cntr_dt='20260611',
            fc_krw_tp='0',
            stex_tp='',
            stk_cd='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
