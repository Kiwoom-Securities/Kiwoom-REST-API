# ---
# api_id: kt00016
# api_name: 일별계좌수익률상세현황요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 일별계좌수익률상세현황요청(kt00016)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "kt00016"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "mang_empno": "관리사원번호",
    "mngr_nm": "관리자명",
    "dept_nm": "관리자지점",
    "entr_fr": "예수금_초",
    "entr_to": "예수금_말",
    "scrt_evlt_amt_fr": "유가증권평가금액_초",
    "scrt_evlt_amt_to": "유가증권평가금액_말",
    "ls_grnt_fr": "대주담보금_초",
    "ls_grnt_to": "대주담보금_말",
    "crd_loan_fr": "신용융자금_초",
    "crd_loan_to": "신용융자금_말",
    "ch_uncla_fr": "현금미수금_초",
    "ch_uncla_to": "현금미수금_말",
    "krw_asgna_fr": "원화대용금_초",
    "krw_asgna_to": "원화대용금_말",
    "ls_evlta_fr": "대주평가금_초",
    "ls_evlta_to": "대주평가금_말",
    "rght_evlta_fr": "권리평가금_초",
    "rght_evlta_to": "권리평가금_말",
    "loan_amt_fr": "대출금_초",
    "loan_amt_to": "대출금_말",
    "etc_loana_fr": "기타대여금_초",
    "etc_loana_to": "기타대여금_말",
    "crd_int_npay_gold_fr": "신용이자미납금_초",
    "crd_int_npay_gold_to": "신용이자미납금_말",
    "crd_int_fr": "신용이자_초",
    "crd_int_to": "신용이자_말",
    "tot_amt_fr": "순자산액계_초",
    "tot_amt_to": "순자산액계_말",
    "invt_bsamt": "투자원금평잔",
    "evltv_prft": "평가손익",
    "prft_rt": "수익률",
    "tern_rt": "회전율",
    "termin_tot_trns": "기간내총입금",
    "termin_tot_pymn": "기간내총출금",
    "termin_tot_inq": "기간내총입고",
    "termin_tot_outq": "기간내총출고",
    "futr_repl_sella": "선물대용매도금액",
    "trst_repl_sella": "위탁대용매도금액"
}


NUMERIC_COLUMNS = (
    '권리평가금_말',
    '권리평가금_초',
    '기간내총입금',
    '기간내총출금',
    '기타대여금_말',
    '기타대여금_초',
    '대주담보금_말',
    '대주담보금_초',
    '대주평가금_말',
    '대주평가금_초',
    '대출금_말',
    '대출금_초',
    '선물대용매도금액',
    '순자산액계_말',
    '순자산액계_초',
    '신용융자금_말',
    '신용융자금_초',
    '신용이자_말',
    '신용이자_초',
    '신용이자미납금_말',
    '신용이자미납금_초',
    '예수금_말',
    '예수금_초',
    '원화대용금_말',
    '원화대용금_초',
    '위탁대용매도금액',
    '유가증권평가금액_말',
    '유가증권평가금액_초',
    '투자원금평잔',
    '평가손익',
    '현금미수금_말',
    '현금미수금_초',
    '회전율',
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

def get_domestic_daily_account_return_rate_detail(
    fr_dt: str,
    to_dt: str,
) -> pd.DataFrame:
    """
    일별계좌수익률상세현황요청[kt00016] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        fr_dt: 평가시작일 — YYYYMMDD
        to_dt: 평가종료일 — YYYYMMDD

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_daily_account_return_rate_detail(
        ...     fr_dt='20241111',
        ...     to_dt='20241125',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not fr_dt:
        raise ValueError('fr_dt is required.')
    if not to_dt:
        raise ValueError('to_dt is required.')

    # 2. 요청 파라미터 바디
    body = {
        "fr_dt": fr_dt,  # 평가시작일
        "to_dt": to_dt,  # 평가종료일
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = []
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
        row = {
            key: response_body.get(key)
            for key in COLUMNS
        }
        if row:
            rows.append(row)

        next_cont_yn = response.continuation.cont_yn
        next_key = response.continuation.next_key

        if next_cont_yn != "Y":
            break

        if page + 1 >= MAX_PAGES:
            break

        time.sleep(REQUEST_DELAY_SECONDS)

    # 6. DataFrame 변환
    result = pd.DataFrame(rows).rename(columns=COLUMNS)
    if message_rows:
        message_df = pd.DataFrame(message_rows).rename(columns=MESSAGE_COLUMNS)
        result = pd.concat([message_df, result], axis=1)
    return result


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    try:
        df = get_domestic_daily_account_return_rate_detail(
            fr_dt='20241111',
            to_dt='20241125',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
