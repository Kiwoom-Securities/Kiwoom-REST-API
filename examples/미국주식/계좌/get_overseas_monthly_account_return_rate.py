# ---
# api_id: usa21680
# api_name: 미국주식 월별계좌수익률현황
# category: 미국주식
# sub_category: 계좌
# template: rest
# api_url: /api/us/acnt
# menu_path: 미국주식 > 계좌 > 미국주식 월별계좌수익률현황(usa21680)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "usa21680"
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
    "base_dt": "기준일",
    "stk_evlta": "주식평가금",
    "pl_amt": "손익금액",
    "dvid_amt": "배당금액",
    "cmsn_tax": "수수료+세금",
    "acum_pl_amt": "누적손익",
    "pymn_amt": "출금금액",
    "dast": "예탁자산",
    "dly_amt": "연체금액",
    "sell_amt": "매도금액",
    "buy_amt": "매수금액",
    "prft_rt": "수익률",
    "frgn_stk_outq_amt": "출고금액",
    "frgn_stk_inq_amt": "입고금액",
    "ina_amt": "입금금액",
    "exrt": "환율"
}


NUMERIC_COLUMNS = (
    '누적손익',
    '매도금액',
    '매수금액',
    '배당금액',
    '손익금액',
    '수수료+세금',
    '연체금액',
    '예탁자산',
    '입고금액',
    '입금금액',
    '주식평가금',
    '출고금액',
    '출금금액',
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

def get_overseas_monthly_account_return_rate(
    from_value: str,
    to: str,
) -> dict[str, pd.DataFrame]:
    """
    미국주식 월별계좌수익률현황[usa21680] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        from_value: from 년월 — YYYYMM
        to: to 년월 — YYYYMM

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_monthly_account_return_rate(
        ...     from_value='202605',
        ...     to='202605',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not from_value:
        raise ValueError('from_value is required.')
    if not to:
        raise ValueError('to is required.')

    # 2. 요청 파라미터 바디
    body = {
        "from": from_value,  # from 년월
        "to": to,  # to 년월
    }

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
        result = get_overseas_monthly_account_return_rate(
            from_value='202605',
            to='202605',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
