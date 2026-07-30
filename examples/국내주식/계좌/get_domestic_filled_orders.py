# ---
# api_id: ka10076
# api_name: 체결요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 체결요청(ka10076)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10076"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "cntr": "체결"
}
COLUMNS = {
    "ord_no": "주문번호",
    "stk_nm": "종목명",
    "io_tp_nm": "주문구분",
    "ord_pric": "주문가격",
    "ord_qty": "주문수량",
    "cntr_pric": "체결가",
    "cntr_qty": "체결량",
    "oso_qty": "미체결수량",
    "tdy_trde_cmsn": "당일매매수수료",
    "tdy_trde_tax": "당일매매세금",
    "ord_stt": "주문상태",
    "trde_tp": "매매구분",
    "orig_ord_no": "원주문번호",
    "ord_tm": "주문시간",
    "stk_cd": "종목코드",
    "stex_tp": "거래소구분",
    "stex_tp_txt": "거래소구분텍스트",
    "sor_yn": "SOR 여부값",
    "stop_pric": "스톱가"
}


NUMERIC_COLUMNS = (
    '당일매매세금',
    '당일매매수수료',
    '미체결수량',
    '스톱가',
    '주문가격',
    '주문수량',
    '체결가',
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

def get_domestic_filled_orders(
    qry_tp: str,
    sell_tp: str,
    stex_tp: str,
    stk_cd: str | None = '005930',
    ord_no: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    체결요청[ka10076] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        qry_tp: 조회구분 — 0:전체, 1:종목
        sell_tp: 매도수구분 — 0:전체, 1:매도, 2:매수
        stex_tp: 거래소구분 — 0 : 통합, 1 : KRX, 2 : NXT
        stk_cd: 종목코드 — 종목코드 6자리
        ord_no: 주문번호 — 검색 기준 값으로 입력한 주문번호 보다 과거에 체결된 내역이 조회됩니다.

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_filled_orders(
        ...     qry_tp='1',
        ...     sell_tp='0',
        ...     stex_tp='0',
        ...     stk_cd='005930',
        ...     ord_no='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not qry_tp:
        raise ValueError('qry_tp is required.')
    if not sell_tp:
        raise ValueError('sell_tp is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "qry_tp": qry_tp,  # 조회구분
        "sell_tp": sell_tp,  # 매도수구분
        "stex_tp": stex_tp,  # 거래소구분
    }
    if stk_cd is not None:
        body["stk_cd"] = stk_cd  # 종목코드
    if ord_no is not None:
        body["ord_no"] = ord_no  # 주문번호

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "cntr": [],
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
        result = get_domestic_filled_orders(
            qry_tp='1',
            sell_tp='0',
            stex_tp='0',
            stk_cd='005930',
            ord_no='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
