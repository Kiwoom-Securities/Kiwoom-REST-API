# ---
# api_id: kt50030
# api_name: 금현물 주문체결전체조회
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 금현물 주문체결전체조회(kt50030)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "kt50030"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "acnt_ord_cntr_prst": "계좌별주문체결현황"
}
COLUMNS = {
    "stk_bond_tp": "주식채권구분",
    "ord_no": "주문번호",
    "stk_cd": "상품코드",
    "trde_tp": "매매구분",
    "io_tp_nm": "주문유형구분",
    "ord_qty": "주문수량",
    "ord_uv": "주문단가",
    "cnfm_qty": "확인수량",
    "data_send_end_tp": "접수구분",
    "mrkt_deal_tp": "시장구분",
    "rsrv_tp": "예약/반대여부",
    "orig_ord_no": "원주문번호",
    "stk_nm": "종목명",
    "dcd_tp_nm": "결제구분",
    "crd_deal_tp": "신용거래구분",
    "cntr_qty": "체결수량",
    "cntr_uv": "체결단가",
    "ord_remnq": "미체결수량",
    "comm_ord_tp": "통신구분",
    "mdfy_cncl_tp": "정정취소구분",
    "dmst_stex_tp": "국내거래소구분",
    "cond_uv": "스톱가"
}


NUMERIC_COLUMNS = (
    '미체결수량',
    '스톱가',
    '주문단가',
    '주문수량',
    '체결단가',
    '체결수량',
    '확인수량',
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

def get_domestic_all_gold_spot_order_fills(
    ord_dt: str,
    mrkt_deal_tp: str,
    stk_bond_tp: str,
    slby_tp: str,
    qry_tp: str | None = '1',
    stk_cd: str | None = 'M04020000',
    fr_ord_no: str | None = '',
    dmst_stex_tp: str | None = 'KRX',
) -> dict[str, pd.DataFrame]:
    """
    금현물 주문체결전체조회[kt50030] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        ord_dt: 주문일자 — YYYYMMDD
        mrkt_deal_tp: 시장구분 — 5:KRX금현물, 5값으로 고정
        stk_bond_tp: 주식채권구분 — 0:전체, 1:주식, 2:채권
        slby_tp: 매도수구분 — 0:전체, 1:매도, 2:매수
        qry_tp: 조회구분 — 1: 주문순, 2: 역순
        stk_cd: 종목코드 — M04020000: 금 99.99_1kg, M04020100: 미니금 99.99_100g, 전체 조회는 빈값('')으로 설정
        fr_ord_no: 시작주문번호 — 시작주문번호 입력 시 이전 주문은 조회되지 않음, 전체 조회는 빈값('')으로 설정
        dmst_stex_tp: 국내거래소구분 — %:(전체), KRX, NXT, SOR

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_all_gold_spot_order_fills(
        ...     ord_dt='20250821',
        ...     mrkt_deal_tp='1',
        ...     stk_bond_tp='0',
        ...     slby_tp='0',
        ...     qry_tp='1',
        ...     stk_cd='M04020000',
        ...     fr_ord_no='',
        ...     dmst_stex_tp='KRX',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not ord_dt:
        raise ValueError('ord_dt is required.')
    if not mrkt_deal_tp:
        raise ValueError('mrkt_deal_tp is required.')
    if not stk_bond_tp:
        raise ValueError('stk_bond_tp is required.')
    if not slby_tp:
        raise ValueError('slby_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "ord_dt": ord_dt,  # 주문일자
        "mrkt_deal_tp": mrkt_deal_tp,  # 시장구분
        "stk_bond_tp": stk_bond_tp,  # 주식채권구분
        "slby_tp": slby_tp,  # 매도수구분
    }
    if qry_tp is not None:
        body["qry_tp"] = qry_tp  # 조회구분
    if stk_cd is not None:
        body["stk_cd"] = stk_cd  # 종목코드
    if fr_ord_no is not None:
        body["fr_ord_no"] = fr_ord_no  # 시작주문번호
    if dmst_stex_tp is not None:
        body["dmst_stex_tp"] = dmst_stex_tp  # 국내거래소구분

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "acnt_ord_cntr_prst": [],
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
        result = get_domestic_all_gold_spot_order_fills(
            ord_dt='20250821',
            mrkt_deal_tp='1',
            stk_bond_tp='0',
            slby_tp='0',
            qry_tp='1',
            stk_cd='M04020000',
            fr_ord_no='',
            dmst_stex_tp='KRX',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
