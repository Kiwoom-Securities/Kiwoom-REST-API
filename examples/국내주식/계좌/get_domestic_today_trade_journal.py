# ---
# api_id: ka10170
# api_name: 당일매매일지요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 당일매매일지요청(ka10170)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka10170"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "tdy_trde_diary": "당일매매일지"
}
COLUMNS = {
    "stk_nm": "종목명",
    "buy_avg_pric": "매수평균가",
    "buy_qty": "매수수량",
    "sel_avg_pric": "매도평균가",
    "sell_qty": "매도수량",
    "cmsn_alm_tax": "수수료_제세금",
    "pl_amt": "손익금액",
    "sell_amt": "매도금액",
    "buy_amt": "매수금액",
    "prft_rt": "수익률",
    "stk_cd": "종목코드"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "tot_sell_amt": "총매도금액",
    "tot_buy_amt": "총매수금액",
    "tot_cmsn_tax": "총수수료_세금",
    "tot_exct_amt": "총정산금액",
    "tot_pl_amt": "총손익금액",
    "tot_prft_rt": "총수익률"
}


NUMERIC_COLUMNS = (
    '매도금액',
    '매도수량',
    '매도평균가',
    '매수금액',
    '매수수량',
    '매수평균가',
    '손익금액',
    '수수료_제세금',
    '총매도금액',
    '총매수금액',
    '총손익금액',
    '총수수료_세금',
    '총정산금액',
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

def get_domestic_today_trade_journal(
    ottks_tp: str,
    ch_crd_tp: str,
    base_dt: str | None = '20241120',
) -> dict[str, pd.DataFrame]:
    """
    당일매매일지요청[ka10170] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        ottks_tp: 1:당일매수에 대한 당일매도,2:당일매도 전체
        ch_crd_tp: 0:전체, 1:현금매매만, 2:신용매매만
        base_dt: YYYYMMDD(공백입력시 금일데이터,최근 2개월까지 제공)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_today_trade_journal(
        ...     ottks_tp='1',
        ...     ch_crd_tp='0',
        ...     base_dt='20241120',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not ottks_tp:
        raise ValueError('ottks_tp is required.')
    if not ch_crd_tp:
        raise ValueError('ch_crd_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "ottks_tp": ottks_tp,
        "ch_crd_tp": ch_crd_tp,
    }
    if base_dt is not None:
        body["base_dt"] = base_dt

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "tdy_trde_diary": [],
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
    result = get_domestic_today_trade_journal(
        ottks_tp='1',
        ch_crd_tp='0',
        base_dt='20241120',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
