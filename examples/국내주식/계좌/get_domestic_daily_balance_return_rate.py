# ---
# api_id: ka01690
# api_name: 일별잔고수익률
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 일별잔고수익률(ka01690)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka01690"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "day_bal_rt": "일별잔고수익률"
}
COLUMNS = {
    "cur_prc": "현재가",
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "rmnd_qty": "보유 수량",
    "buy_uv": "매입 단가",
    "buy_wght": "매수비중",
    "evltv_prft": "평가손익",
    "prft_rt": "수익률",
    "evlt_amt": "평가금액",
    "evlt_wght": "평가비중"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "dt": "일자",
    "tot_buy_amt": "총 매입가",
    "tot_evlt_amt": "총 평가금액",
    "tot_evltv_prft": "총 평가손익",
    "tot_prft_rt": "수익률",
    "dbst_bal": "예수금",
    "day_stk_asst": "추정자산",
    "buy_wght": "현금비중"
}


NUMERIC_COLUMNS = (
    '매수비중',
    '매입 단가',
    '보유 수량',
    '예수금',
    '총 매입가',
    '총 평가금액',
    '총 평가손익',
    '추정자산',
    '평가금액',
    '평가비중',
    '평가손익',
    '현금비중',
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

def get_domestic_daily_balance_return_rate(
    qry_dt: str,
) -> dict[str, pd.DataFrame]:
    """
    일별잔고수익률[ka01690] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        qry_dt: 조회일자 — YYYYMMDD

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_daily_balance_return_rate(
        ...     qry_dt='20250825',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not qry_dt:
        raise ValueError('qry_dt is required.')

    # 2. 요청 파라미터 바디
    body = {
        "qry_dt": qry_dt,  # 조회일자
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "day_bal_rt": [],
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
        result = get_domestic_daily_balance_return_rate(
            qry_dt='20250825',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
