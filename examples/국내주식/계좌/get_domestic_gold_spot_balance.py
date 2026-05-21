# ---
# api_id: kt50020
# api_name: 금현물 잔고확인
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 금현물 잔고확인(kt50020)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "kt50020"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "gold_acnt_evlt_prst": "금현물계좌평가현황"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "real_qty": "보유수량",
    "avg_prc": "평균단가",
    "cur_prc": "현재가",
    "est_amt": "평가금액",
    "est_lspft": "손익금액",
    "est_ratio": "손익율",
    "cmsn": "수수료",
    "vlad_tax": "부가가치세",
    "book_amt2": "매입금액",
    "pl_prch_prc": "손익분기매입가",
    "qty": "결제잔고",
    "buy_qty": "매수수량",
    "sell_qty": "매도수량",
    "able_qty": "가능수량"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "tot_entr": "예수금",
    "net_entr": "추정예수금",
    "tot_est_amt": "잔고평가액",
    "net_amt": "예탁자산평가액",
    "tot_book_amt2": "총매입금액",
    "tot_dep_amt": "추정예탁자산",
    "paym_alowa": "출금가능금액",
    "pl_amt": "실현손익"
}


NUMERIC_COLUMNS = (
    '가능수량',
    '결제잔고',
    '매도수량',
    '매수수량',
    '매입금액',
    '보유수량',
    '부가가치세',
    '손익금액',
    '손익분기매입가',
    '손익율',
    '수수료',
    '실현손익',
    '예수금',
    '예탁자산평가액',
    '잔고평가액',
    '총매입금액',
    '추정예수금',
    '추정예탁자산',
    '출금가능금액',
    '평가금액',
    '평균단가',
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

def get_domestic_gold_spot_balance(
) -> dict[str, pd.DataFrame]:
    """
    금현물 잔고확인[kt50020] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_gold_spot_balance(
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "gold_acnt_evlt_prst": [],
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
    result = get_domestic_gold_spot_balance(
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
