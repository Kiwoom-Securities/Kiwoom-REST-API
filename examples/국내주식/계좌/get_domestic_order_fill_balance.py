# ---
# api_id: kt00005
# api_name: 체결잔고요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 체결잔고요청(kt00005)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "kt00005"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "stk_cntr_remn": "종목별체결잔고"
}
COLUMNS = {
    "crd_tp": "신용구분",
    "loan_dt": "대출일",
    "expr_dt": "만기일",
    "stk_cd": "종목번호",
    "stk_nm": "종목명",
    "setl_remn": "결제잔고",
    "cur_qty": "현재잔고",
    "cur_prc": "현재가",
    "buy_uv": "매입단가",
    "pur_amt": "매입금액",
    "evlt_amt": "평가금액",
    "evltv_prft": "평가손익",
    "pl_rt": "손익률"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "entr": "예수금",
    "entr_d1": "예수금D+1",
    "entr_d2": "예수금D+2",
    "pymn_alow_amt": "출금가능금액",
    "uncl_stk_amt": "미수확보금",
    "repl_amt": "대용금",
    "rght_repl_amt": "권리대용금",
    "ord_alowa": "주문가능현금",
    "ch_uncla": "현금미수금",
    "crd_int_npay_gold": "신용이자미납금",
    "etc_loana": "기타대여금",
    "nrpy_loan": "미상환융자금",
    "profa_ch": "증거금현금",
    "repl_profa": "증거금대용",
    "stk_buy_tot_amt": "주식매수총액",
    "evlt_amt_tot": "평가금액합계",
    "tot_pl_tot": "총손익합계",
    "tot_pl_rt": "총손익률",
    "tot_re_buy_alowa": "총재매수가능금액",
    "20ord_alow_amt": "20%주문가능금액",
    "30ord_alow_amt": "30%주문가능금액",
    "40ord_alow_amt": "40%주문가능금액",
    "50ord_alow_amt": "50%주문가능금액",
    "60ord_alow_amt": "60%주문가능금액",
    "100ord_alow_amt": "100%주문가능금액",
    "crd_loan_tot": "신용융자합계",
    "crd_loan_ls_tot": "신용융자대주합계",
    "crd_grnt_rt": "신용담보비율",
    "dpst_grnt_use_amt_amt": "예탁담보대출금액",
    "grnt_loan_amt": "매도담보대출금액"
}


NUMERIC_COLUMNS = (
    '100%주문가능금액',
    '20%주문가능금액',
    '30%주문가능금액',
    '40%주문가능금액',
    '50%주문가능금액',
    '60%주문가능금액',
    '결제잔고',
    '권리대용금',
    '기타대여금',
    '대용금',
    '매도담보대출금액',
    '매입금액',
    '매입단가',
    '미상환융자금',
    '미수확보금',
    '손익률',
    '신용담보비율',
    '신용이자미납금',
    '예수금',
    '예수금D+1',
    '예수금D+2',
    '예탁담보대출금액',
    '주문가능현금',
    '주식매수총액',
    '증거금대용',
    '증거금현금',
    '총손익률',
    '총손익합계',
    '총재매수가능금액',
    '출금가능금액',
    '평가금액',
    '평가금액합계',
    '평가손익',
    '현금미수금',
    '현재가',
    '현재잔고',
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

def get_domestic_order_fill_balance(
    dmst_stex_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    체결잔고요청[kt00005] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        dmst_stex_tp: 국내거래소구분 — KRX:한국거래소,NXT:넥스트트레이드

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_order_fill_balance(
        ...     dmst_stex_tp='KRX',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not dmst_stex_tp:
        raise ValueError('dmst_stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "dmst_stex_tp": dmst_stex_tp,  # 국내거래소구분
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "stk_cntr_remn": [],
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
        result = get_domestic_order_fill_balance(
            dmst_stex_tp='KRX',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
