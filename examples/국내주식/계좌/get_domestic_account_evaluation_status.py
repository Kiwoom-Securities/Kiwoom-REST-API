# ---
# api_id: kt00004
# api_name: 계좌평가현황요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 계좌평가현황요청(kt00004)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "kt00004"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "stk_acnt_evlt_prst": "종목별계좌평가현황"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "rmnd_qty": "보유수량",
    "avg_prc": "평균단가",
    "cur_prc": "현재가",
    "evlt_amt": "평가금액",
    "pl_amt": "손익금액",
    "pl_rt": "손익율",
    "loan_dt": "대출일",
    "pur_amt": "매입금액",
    "setl_remn": "결제잔고",
    "pred_buyq": "전일매수수량",
    "pred_sellq": "전일매도수량",
    "tdy_buyq": "금일매수수량",
    "tdy_sellq": "금일매도수량"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "acnt_nm": "계좌명",
    "brch_nm": "지점명",
    "entr": "예수금",
    "d2_entra": "D+2추정예수금",
    "tot_est_amt": "유가잔고평가액",
    "aset_evlt_amt": "예탁자산평가액",
    "tot_pur_amt": "총매입금액",
    "prsm_dpst_aset_amt": "추정예탁자산",
    "tot_grnt_sella": "매도담보대출금",
    "tdy_lspft_amt": "당일투자원금",
    "invt_bsamt": "당월투자원금",
    "lspft_amt": "누적투자원금",
    "tdy_lspft": "당일투자손익",
    "lspft2": "당월투자손익",
    "lspft": "누적투자손익",
    "tdy_lspft_rt": "당일손익율",
    "lspft_ratio": "당월손익율",
    "lspft_rt": "누적손익율"
}


NUMERIC_COLUMNS = (
    'D+2추정예수금',
    '결제잔고',
    '금일매도수량',
    '금일매수수량',
    '누적손익율',
    '누적투자손익',
    '누적투자원금',
    '당월손익율',
    '당월투자손익',
    '당월투자원금',
    '당일손익율',
    '당일투자손익',
    '당일투자원금',
    '매도담보대출금',
    '매입금액',
    '보유수량',
    '손익금액',
    '손익율',
    '예수금',
    '예탁자산평가액',
    '유가잔고평가액',
    '전일매도수량',
    '전일매수수량',
    '총매입금액',
    '추정예탁자산',
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

def get_domestic_account_evaluation_status(
    qry_tp: str,
    dmst_stex_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    계좌평가현황요청[kt00004] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        qry_tp: 0:전체, 1:상장폐지종목제외
        dmst_stex_tp: KRX:한국거래소,NXT:넥스트트레이드

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_account_evaluation_status(
        ...     qry_tp='0',
        ...     dmst_stex_tp='KRX',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not qry_tp:
        raise ValueError('qry_tp is required.')
    if not dmst_stex_tp:
        raise ValueError('dmst_stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "qry_tp": qry_tp,
        "dmst_stex_tp": dmst_stex_tp,
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "stk_acnt_evlt_prst": [],
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
    result = get_domestic_account_evaluation_status(
        qry_tp='0',
        dmst_stex_tp='KRX',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
