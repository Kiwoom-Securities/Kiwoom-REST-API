# ---
# api_id: ust31302
# api_name: 환전 신청
# category: 미국주식
# sub_category: 환전
# template: rest
# api_url: /api/us/exchange
# menu_path: 미국주식 > 환전 > 환전 신청(ust31302)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust31302"
API_URL = "/api/us/exchange"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "sell_aplc_exrt": "매도적용환율",
    "buy_aplc_exrt": "매수적용환율",
    "aplc_exrt": "적용환율",
    "entra_prerm": "예수금전잔",
    "ch_uncla_prerm": "현금미수금전잔",
    "etc_loana_prerm": "기타대여금전잔",
    "entra_nowrm": "예수금금잔",
    "ch_uncla_nowrm": "현금미수금금잔",
    "etc_loana_nowrm": "기타대여금금잔",
    "krw_exmn_alow_amt": "원화환전가능금액",
    "ch_uncl_rpym_amt": "현금미수변제금",
    "ch_uncl_dlfe": "현금미수연체료",
    "etc_loan_npay_rpym_amt": "기타대여미납변제금",
    "etc_loan_npay_dlfe": "기타대여미납연체료",
    "fc_entra_prerm": "외화예수금전잔",
    "fc_ch_uncla_prerm": "외화현금미수금전잔",
    "fc_etc_loana_prerm": "외화기타대여금전잔",
    "fc_entra_nowrm": "외화예수금금잔",
    "fc_ch_uncla_nowrm": "외화현금미수금금잔",
    "fc_etc_loana_nowrm": "외화기타대여금금잔",
    "fc_exmn_alow_amt": "외화환전가능금액",
    "fc_ch_uncl_rpym_amt": "외화현금미수변제금",
    "fc_ch_uncl_dlfe": "외화현금미수연체료",
    "fc_etc_loan_npay_rpym_amt": "외화기타대여미납변제금",
    "fc_etc_loan_npay_dlfe": "외화기타대여미납연체료",
    "krw_exmn_amt": "원화환전금액",
    "sell_fc_amt": "매도외화금액",
    "buy_fc_amt": "매수외화금액"
}


NUMERIC_COLUMNS = (
    '기타대여금금잔',
    '기타대여금전잔',
    '기타대여미납변제금',
    '매도외화금액',
    '매도적용환율',
    '매수외화금액',
    '매수적용환율',
    '예수금금잔',
    '예수금전잔',
    '외화기타대여금금잔',
    '외화기타대여금전잔',
    '외화기타대여미납변제금',
    '외화예수금금잔',
    '외화예수금전잔',
    '외화현금미수금금잔',
    '외화현금미수금전잔',
    '외화현금미수변제금',
    '외화현금미수연체료',
    '외화환전가능금액',
    '원화환전가능금액',
    '원화환전금액',
    '적용환율',
    '현금미수금금잔',
    '현금미수금전잔',
    '현금미수변제금',
    '현금미수연체료',
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

def request_overseas_currency_exchange(
    exch_tp: str,
    fc_exmn_amt: str,
) -> pd.DataFrame:
    """
    환전 신청[ust31302] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        exch_tp: 환전구분 — 1:원화(KRW)->달러(USD), 2:달러(USD)->원화(KRW)
        fc_exmn_amt: 매도통화기준 환전금액
            (EXCH_TP = 1 인 경우, 매도통화는 KRW 이며, 입력한 금액의 원화를 달러로 환전합니다)
            (EXCH_TP = 2 인 경우, 매도통화: USD이며, 입력한 금액의 달러를 원화로 환전합니다.)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = request_overseas_currency_exchange(
        ...     exch_tp='1',
        ...     fc_exmn_amt='2000',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not exch_tp:
        raise ValueError('exch_tp is required.')
    if not fc_exmn_amt:
        raise ValueError('fc_exmn_amt is required.')

    # 2. 요청 파라미터 바디
    body = {
        "exch_tp": exch_tp,  # 환전구분
        "fc_exmn_amt": fc_exmn_amt,  # 매도통화기준 환전금액
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
        df = request_overseas_currency_exchange(
            exch_tp='1',
            fc_exmn_amt='2000',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
