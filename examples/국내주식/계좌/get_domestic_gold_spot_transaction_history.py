# ---
# api_id: kt50032
# api_name: 금현물 거래내역조회
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 금현물 거래내역조회(kt50032)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "kt50032"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "gold_trde_hist": "금현물거래내역"
}
COLUMNS = {
    "deal_dt": "거래일자",
    "deal_no": "거래번호",
    "rmrk_nm": "적요명",
    "deal_qty": "거래수량",
    "gold_spot_vat": "금현물부가가치세",
    "exct_amt": "정산금액",
    "dly_sum": "연체합",
    "entra_remn": "예수금잔고",
    "mdia_nm": "메체구분명",
    "orig_deal_no": "원거래번호",
    "stk_nm": "종목명",
    "uv_exrt": "거래단가",
    "cmsn": "수수료",
    "uncl_ocr": "미수(원/g)",
    "rpym_sum": "변제합",
    "spot_remn": "현물잔고",
    "proc_time": "처리시간",
    "rcpy_no": "출납번호",
    "stk_cd": "종목코드",
    "deal_amt": "거래금액",
    "tax_tot_amt": "소득/주민세",
    "cntr_dt": "체결일",
    "proc_brch_nm": "처리점",
    "prcsr": "처리자"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "acnt_print": "계좌번호"
}


NUMERIC_COLUMNS = (
    '거래금액',
    '거래단가',
    '거래수량',
    '금현물부가가치세',
    '수수료',
    '예수금잔고',
    '정산금액',
    '현물잔고',
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

def get_domestic_gold_spot_transaction_history(
    strt_dt: str | None = '20250819',
    end_dt: str | None = '20250820',
    tp: str | None = '0',
    stk_cd: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    금현물 거래내역조회[kt50032] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        strt_dt: 시작일자
        end_dt: 종료일자
        tp: 0:전체, 1:입출금, 2:출고, 3:매매, 4:매수, 5:매도, 6:입금, 7:출금
        stk_cd: 종목코드

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_gold_spot_transaction_history(
        ...     strt_dt='20250819',
        ...     end_dt='20250820',
        ...     tp='0',
        ...     stk_cd='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }
    if strt_dt is not None:
        body["strt_dt"] = strt_dt
    if end_dt is not None:
        body["end_dt"] = end_dt
    if tp is not None:
        body["tp"] = tp
    if stk_cd is not None:
        body["stk_cd"] = stk_cd

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "gold_trde_hist": [],
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
    result = get_domestic_gold_spot_transaction_history(
        strt_dt='20250819',
        end_dt='20250820',
        tp='0',
        stk_cd='',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
