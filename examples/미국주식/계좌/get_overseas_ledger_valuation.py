# ---
# api_id: ust21121
# api_name: 해외증권 원장 평가금액현황
# category: 미국주식
# sub_category: 계좌
# template: rest
# api_url: /api/us/acnt
# menu_path: 미국주식 > 계좌 > 해외증권 원장 평가금액현황(ust21121)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust21121"
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
    "natn_nm": "국가명",
    "stex_nm": "거래소코드명",
    "crnc_code": "통화코드",
    "crnc_nm": "통화코드명",
    "evlt_amt": "평가금액",
    "chg_evlt_amt": "환전평가금액",
    "pl_rt": "평가수익율(%)",
    "pl_amt": "평가손익",
    "chg_profit_amt": "환전평가손익",
    "evlt_amt_wght": "평가금액비중"
}


NUMERIC_COLUMNS = (
    '평가금액',
    '평가금액비중',
    '평가손익',
    '평가수익율(%)',
    '환전평가금액',
    '환전평가손익',
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

def get_overseas_ledger_valuation(
    cmsn_incl_tp: str | None = '',
    exrt_tp: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    해외증권 원장 평가금액현황[ust21121] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        cmsn_incl_tp: 수수료포함구분 — 0:미포함,1:포함
        exrt_tp: 환율구분 — 0:기준환율,1:계좌적용환율,2:전일최종환율

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_ledger_valuation(
        ...     cmsn_incl_tp='',
        ...     exrt_tp='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }
    if cmsn_incl_tp is not None:
        body["cmsn_incl_tp"] = cmsn_incl_tp  # 수수료포함구분
    if exrt_tp is not None:
        body["exrt_tp"] = exrt_tp  # 환율구분

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
        result = get_overseas_ledger_valuation(
            cmsn_incl_tp='',
            exrt_tp='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
