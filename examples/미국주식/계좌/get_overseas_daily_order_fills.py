# ---
# api_id: ust21150
# api_name: 미국주식 일별 주문체결내역
# category: 미국주식
# sub_category: 계좌
# template: rest
# api_url: /api/us/acnt
# menu_path: 미국주식 > 계좌 > 미국주식 일별 주문체결내역(ust21150)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust21150"
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
    "ord_no": "주문번호",
    "crnc_code": "통화코드",
    "stk_cd": "종목코드",
    "isin_code": "국제표준코드",
    "frgn_trde_tp": "매매구분",
    "ord_qty": "주문수량",
    "cntr_qty": "체결수량",
    "mdfy_qty": "정정수량",
    "cncl_qty": "취소수량",
    "frgn_msg_code": "해외메세지코드",
    "rsrv_tp": "예약구분",
    "oppo_trde_tp_nm": "반대매매구분명",
    "comm_ord_tp_nm": "통신주문구분명",
    "ord_time": "주문시간",
    "crnc_nm": "통화코드명",
    "stex_nm": "거래소코드명",
    "frgn_stk_nm": "종목명",
    "slby_tp_nm": "매도매수구분명",
    "ord_uv": "주문단가",
    "stop_pric": "STOP가격",
    "cntr_uv": "체결단가",
    "mdfy_uv": "정정단가",
    "ord_remnq": "주문잔량",
    "ord_stat_nm": "주문상태명",
    "text1": "거부사유",
    "inpt_chnl_tp": "입력매체구분명",
    "ord_resp_time": "주문응답수신시간",
    "cntr_time": "체결시간"
}


NUMERIC_COLUMNS = (
    'STOP가격',
    '정정단가',
    '정정수량',
    '주문단가',
    '주문수량',
    '체결단가',
    '체결수량',
    '취소수량',
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

def get_overseas_daily_order_fills(
    query_tp: str,
    slby_tp: str,
    ord_dt: str | None = '',
    stex_tp: str | None = '',
    stk_cd: str | None = '',
    oppo_trde_tp: str | None = '',
    fr_ord_no: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 일별 주문체결내역[ust21150] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        query_tp: 조회구분 — 1:주문순,2:주문역순,3:미체결주문순,4:미체결역순,5:체결주문순,6:체결역순
        slby_tp: 매도수구분 — 0:전체,1:매도,2:매수
        ord_dt: 주문일자 — 미입력시 오늘 날짜로 조회
        stex_tp: 거래소구분 — ND:NASDAQ,NY:NYSE,NA:AMEX
        stk_cd: 종목코드 — 미입력시 전체
        oppo_trde_tp: 반대매매구분 — %:전체,0:일반,1:반대매매
        fr_ord_no: 시작주문번호

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_daily_order_fills(
        ...     query_tp='1',
        ...     slby_tp='0',
        ...     ord_dt='',
        ...     stex_tp='',
        ...     stk_cd='',
        ...     oppo_trde_tp='',
        ...     fr_ord_no='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not query_tp:
        raise ValueError('query_tp is required.')
    if not slby_tp:
        raise ValueError('slby_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "query_tp": query_tp,  # 조회구분
        "slby_tp": slby_tp,  # 매도수구분
    }
    if ord_dt is not None:
        body["ord_dt"] = ord_dt  # 주문일자
    if stex_tp is not None:
        body["stex_tp"] = stex_tp  # 거래소구분
    if stk_cd is not None:
        body["stk_cd"] = stk_cd  # 종목코드
    if oppo_trde_tp is not None:
        body["oppo_trde_tp"] = oppo_trde_tp  # 반대매매구분
    if fr_ord_no is not None:
        body["fr_ord_no"] = fr_ord_no  # 시작주문번호

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
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
        result = get_overseas_daily_order_fills(
            query_tp='1',
            slby_tp='0',
            ord_dt='',
            stex_tp='',
            stk_cd='',
            oppo_trde_tp='',
            fr_ord_no='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
