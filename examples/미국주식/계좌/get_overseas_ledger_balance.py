# ---
# api_id: ust21070
# api_name: 미국주식 원장잔고확인
# category: 미국주식
# sub_category: 계좌
# template: rest
# api_url: /api/us/acnt
# menu_path: 미국주식 > 계좌 > 미국주식 원장잔고확인(ust21070)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust21070"
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
    "stex_nm": "거래소명",
    "crnc_code": "통화코드",
    "stk_cd": "종목코드",
    "frgn_stk_nm": "종목명",
    "qty": "결제기준수량",
    "poss_qty": "보유수량",
    "sell_alowq": "매도가능수량",
    "pred_cntr_sellq": "전일매도수량",
    "pred_cntr_buyq": "전일매수수량",
    "tdy_cntr_sellq": "금일매도수량",
    "tdy_cntr_buyq": "금일매수수량",
    "frgn_stk_book_uv": "매입단가",
    "now_pric": "현재가",
    "evlt_amt": "평가금액",
    "pl_amt": "손익금액",
    "pl_rt": "손익율(%)",
    "evlt_amt_krw": "평가금액(원)",
    "pl_amt_krw": "손익금액(원)",
    "natn_nm": "국가명",
    "exch_rate": "환율",
    "frgn_stk_book_uv_krw": "매입단가(원)",
    "now_pric_krw": "현재가(원)",
    "frgn_stk_book_amt": "매입금액",
    "frgn_stk_book_amt_krw": "매입금액(원)"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "crnc_code": "통화코드",
    "tot_evlt_amt": "총평가금액",
    "tot_prch_amt": "총매입금액",
    "tot_pl_amt": "총손익금액",
    "tot_pl_rt": "총수익율",
    "tdy_book_amt": "당일실현손익매입금액",
    "tdy_pl_amt": "당일실현손익",
    "tdy_pl_rt": "당일실현손익율(%)",
    "tot_evlt_amt_krw": "총평가금액(원)",
    "tot_prch_amt_krw": "총매입금액(원)",
    "tot_pl_amt_krw": "총손익금액(원)",
    "tdy_book_amt_krw": "당일실현손익매입금액(원)",
    "tdy_pl_amt_krw": "당일실현손익(원)"
}


NUMERIC_COLUMNS = (
    '결제기준수량',
    '금일매도수량',
    '금일매수수량',
    '당일실현손익',
    '당일실현손익(원)',
    '당일실현손익매입금액',
    '당일실현손익매입금액(원)',
    '당일실현손익율(%)',
    '매도가능수량',
    '매입금액',
    '매입금액(원)',
    '매입단가',
    '매입단가(원)',
    '보유수량',
    '손익금액',
    '손익금액(원)',
    '손익율(%)',
    '전일매도수량',
    '전일매수수량',
    '총매입금액',
    '총매입금액(원)',
    '총손익금액',
    '총손익금액(원)',
    '총수익율',
    '총평가금액',
    '총평가금액(원)',
    '평가금액',
    '평가금액(원)',
    '현재가',
    '현재가(원)',
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

def get_overseas_ledger_balance(
    stex_tp: str | None = '',
    stk_cd: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 원장잔고확인[ust21070] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stex_tp: 거래소구분 — ND:NASDAQ,NY:NYSE,NA:AMEX
        stk_cd: 종목코드 — 미입력시 전체

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_ledger_balance(
        ...     stex_tp='',
        ...     stk_cd='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
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
        result = get_overseas_ledger_balance(
            stex_tp='',
            stk_cd='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
