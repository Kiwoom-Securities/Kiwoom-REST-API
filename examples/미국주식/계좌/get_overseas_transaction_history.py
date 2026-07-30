# ---
# api_id: ust21100
# api_name: 미국주식 거래내역
# category: 미국주식
# sub_category: 계좌
# template: rest
# api_url: /api/us/acnt
# menu_path: 미국주식 > 계좌 > 미국주식 거래내역(ust21100)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust21100"
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
    "deal_dt": "거래일자",
    "deal_kind_nm": "거래종류명",
    "rmrk_nm": "적요명",
    "deal_amt": "거래금액",
    "tax_tot_amt": "소득/주민세",
    "exct_amt": "정산금액",
    "uncl_ocr": "미수(원/주)",
    "fc_uncl_ocr": "미수(외)",
    "entra_remn": "예수금잔고",
    "deal_no": "거래번호",
    "stk_nm": "종목명",
    "deal_qty": "거래수량",
    "fc_deal_tax": "거래세(외)",
    "frgn_pay_txam": "외국납부세액(외)",
    "rpym_sum": "변제합",
    "fc_rpym_sum": "변제합(외)",
    "fc_entra": "외화예수금잔고",
    "mdia_nm": "메체구분명",
    "orig_deal_no": "원거래번호",
    "stk_cd": "종목코드",
    "uv_exrt": "거래단가/환율",
    "fc_cmsn": "수수료(외)",
    "fc_exct_amt": "정산금액(외)",
    "dly_sum": "연체합",
    "fc_dly_sum": "연체합(외)",
    "vlbl_nowrm": "유가금잔",
    "stex_nm": "거래소구분명",
    "fc_deal_amt": "거래금액(외)",
    "proc_time": "처리시간",
    "crnc_code": "통화코드"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "acnt_print": "계좌번호",
    "sell_sum": "매도합계",
    "buy_sum": "매수합계"
}


NUMERIC_COLUMNS = (
    '거래금액',
    '거래금액(외)',
    '거래단가/환율',
    '거래수량',
    '수수료(외)',
    '예수금잔고',
    '외화예수금잔고',
    '유가금잔',
    '정산금액',
    '정산금액(외)',
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

def get_overseas_transaction_history(
    strt_dt: str,
    end_dt: str,
    tp: str | None = '',
    stex_tp: str | None = '',
    stk_cd: str | None = '',
    krw_repl_skip_yn: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 거래내역[ust21100] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        strt_dt: 시작일자 — YYYYMMDD
        end_dt: 종료일자 — YYYYMMDD
        tp: 구분 — 0:전체,1:입출금,2:입출고,3:매매,4:매수,5:매도,F:환전, M:입출금+환전(매체전용), G:환전매수, H:환전매도, I:환전정산입금, J:환전정산출금, 6:입금, 7:출금 8:배당금입금 K:환전+환전정산입출금
        stex_tp: 거래소구분 — ND:NASDAQ,NY:NYSE,NA:AMEX
        stk_cd: 종목코드
        krw_repl_skip_yn: 원화대용입출금제외여부 — Y:제외,N:비제외

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_transaction_history(
        ...     strt_dt='20260601',
        ...     end_dt='20260613',
        ...     tp='',
        ...     stex_tp='',
        ...     stk_cd='',
        ...     krw_repl_skip_yn='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not strt_dt:
        raise ValueError('strt_dt is required.')
    if not end_dt:
        raise ValueError('end_dt is required.')

    # 2. 요청 파라미터 바디
    body = {
        "strt_dt": strt_dt,  # 시작일자
        "end_dt": end_dt,  # 종료일자
    }
    if tp is not None:
        body["tp"] = tp  # 구분
    if stex_tp is not None:
        body["stex_tp"] = stex_tp  # 거래소구분
    if stk_cd is not None:
        body["stk_cd"] = stk_cd  # 종목코드
    if krw_repl_skip_yn is not None:
        body["krw_repl_skip_yn"] = krw_repl_skip_yn  # 원화대용입출금제외여부

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
        result = get_overseas_transaction_history(
            strt_dt='20260601',
            end_dt='20260613',
            tp='',
            stex_tp='',
            stk_cd='',
            krw_repl_skip_yn='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
