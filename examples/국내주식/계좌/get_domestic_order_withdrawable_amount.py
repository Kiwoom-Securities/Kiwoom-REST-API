# ---
# api_id: kt00010
# api_name: 주문인출가능금액요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 주문인출가능금액요청(kt00010)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "kt00010"
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
    "profa_20ord_alow_amt": "증거금20%주문가능금액",
    "profa_20ord_alowq": "증거금20%주문가능수량",
    "profa_30ord_alow_amt": "증거금30%주문가능금액",
    "profa_30ord_alowq": "증거금30%주문가능수량",
    "profa_40ord_alow_amt": "증거금40%주문가능금액",
    "profa_40ord_alowq": "증거금40%주문가능수량",
    "profa_50ord_alow_amt": "증거금50%주문가능금액",
    "profa_50ord_alowq": "증거금50%주문가능수량",
    "profa_60ord_alow_amt": "증거금60%주문가능금액",
    "profa_60ord_alowq": "증거금60%주문가능수량",
    "profa_rdex_60ord_alow_amt": "증거금감면60%주문가능금",
    "profa_rdex_60ord_alowq": "증거금감면60%주문가능수",
    "profa_100ord_alow_amt": "증거금100%주문가능금액",
    "profa_100ord_alowq": "증거금100%주문가능수량",
    "pred_reu_alowa": "전일재사용가능금액",
    "tdy_reu_alowa": "금일재사용가능금액",
    "entr": "예수금",
    "repl_amt": "대용금",
    "uncla": "미수금",
    "ord_pos_repl": "주문가능대용",
    "ord_alowa": "주문가능현금",
    "wthd_alowa": "인출가능금액",
    "nxdy_wthd_alowa": "익일인출가능금액",
    "pur_amt": "매입금액",
    "cmsn": "수수료",
    "pur_exct_amt": "매입정산금",
    "d2entra": "D2추정예수금",
    "profa_rdex_aplc_tp": "증거금감면적용구분"
}


NUMERIC_COLUMNS = (
    'D2추정예수금',
    '금일재사용가능금액',
    '대용금',
    '매입금액',
    '매입정산금',
    '미수금',
    '수수료',
    '예수금',
    '익일인출가능금액',
    '인출가능금액',
    '전일재사용가능금액',
    '주문가능대용',
    '주문가능현금',
    '증거금100%주문가능금액',
    '증거금100%주문가능수량',
    '증거금20%주문가능금액',
    '증거금20%주문가능수량',
    '증거금30%주문가능금액',
    '증거금30%주문가능수량',
    '증거금40%주문가능금액',
    '증거금40%주문가능수량',
    '증거금50%주문가능금액',
    '증거금50%주문가능수량',
    '증거금60%주문가능금액',
    '증거금60%주문가능수량',
    '증거금감면60%주문가능금',
    '증거금감면60%주문가능수',
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

def get_domestic_order_withdrawable_amount(
    stk_cd: str,
    trde_tp: str,
    uv: str,
    io_amt: str | None = '',
    trde_qty: str | None = '',
    exp_buy_unp: str | None = '',
) -> pd.DataFrame:
    """
    주문인출가능금액요청[kt00010] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목번호 — 종목 코드 입력
        trde_tp: 매매구분 — 1:매도, 2:매수
        uv: 매수가격 — 단위: 원
        io_amt: 입출금액 — 단위: 원
        trde_qty: 매매수량 — 단위: 1주
        exp_buy_unp: 예상매수단가 — 단위: 원

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_order_withdrawable_amount(
        ...     stk_cd='005930',
        ...     trde_tp='2',
        ...     uv='267000',
        ...     io_amt='',
        ...     trde_qty='',
        ...     exp_buy_unp='',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not trde_tp:
        raise ValueError('trde_tp is required.')
    if not uv:
        raise ValueError('uv is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목번호
        "trde_tp": trde_tp,  # 매매구분
        "uv": uv,  # 매수가격
    }
    if io_amt is not None:
        body["io_amt"] = io_amt  # 입출금액
    if trde_qty is not None:
        body["trde_qty"] = trde_qty  # 매매수량
    if exp_buy_unp is not None:
        body["exp_buy_unp"] = exp_buy_unp  # 예상매수단가

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
        df = get_domestic_order_withdrawable_amount(
            stk_cd='005930',
            trde_tp='2',
            uv='267000',
            io_amt='',
            trde_qty='',
            exp_buy_unp='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
