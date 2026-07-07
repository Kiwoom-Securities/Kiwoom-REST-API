# ---
# api_id: kt00007
# api_name: 계좌별주문체결내역상세요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 계좌별주문체결내역상세요청(kt00007)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "kt00007"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "acnt_ord_cntr_prps_dtl": "계좌별주문체결내역상세"
}
COLUMNS = {
    "ord_no": "주문번호",
    "stk_cd": "종목번호",
    "trde_tp": "매매구분",
    "crd_tp": "신용구분",
    "ord_qty": "주문수량",
    "ord_uv": "주문단가",
    "cnfm_qty": "확인수량",
    "acpt_tp": "접수구분",
    "rsrv_tp": "반대여부",
    "ord_tm": "주문시간",
    "ori_ord": "원주문",
    "stk_nm": "종목명",
    "io_tp_nm": "주문구분",
    "loan_dt": "대출일",
    "cntr_qty": "체결수량",
    "cntr_uv": "체결단가",
    "ord_remnq": "주문잔량",
    "comm_ord_tp": "통신구분",
    "mdfy_cncl": "정정취소",
    "cnfm_tm": "확인시간",
    "dmst_stex_tp": "국내거래소구분",
    "cond_uv": "스톱가"
}


NUMERIC_COLUMNS = (
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

def get_domestic_account_order_fill_detail(
    qry_tp: str,
    stk_bond_tp: str,
    sell_tp: str,
    dmst_stex_tp: str,
    ord_dt: str | None = '',
    stk_cd: str | None = '005930',
    fr_ord_no: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    계좌별주문체결내역상세요청[kt00007] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        qry_tp: 1:주문순, 2:역순, 3:미체결, 4:체결내역만
        stk_bond_tp: 0:전체, 1:주식, 2:채권
        sell_tp: 0:전체, 1:매도, 2:매수
        dmst_stex_tp: %:(전체),KRX:한국거래소,NXT:넥스트트레이드,SOR:최선주문집행
        ord_dt: YYYYMMDD
        stk_cd: 공백허용 (공백일때 전체종목)
        fr_ord_no: 공백허용 (공백일때 전체주문)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_account_order_fill_detail(
        ...     qry_tp='1',
        ...     stk_bond_tp='0',
        ...     sell_tp='0',
        ...     dmst_stex_tp='%',
        ...     ord_dt='',
        ...     stk_cd='005930',
        ...     fr_ord_no='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not qry_tp:
        raise ValueError('qry_tp is required.')
    if not stk_bond_tp:
        raise ValueError('stk_bond_tp is required.')
    if not sell_tp:
        raise ValueError('sell_tp is required.')
    if not dmst_stex_tp:
        raise ValueError('dmst_stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "qry_tp": qry_tp,
        "stk_bond_tp": stk_bond_tp,
        "sell_tp": sell_tp,
        "dmst_stex_tp": dmst_stex_tp,
    }
    if ord_dt is not None:
        body["ord_dt"] = ord_dt
    if stk_cd is not None:
        body["stk_cd"] = stk_cd
    if fr_ord_no is not None:
        body["fr_ord_no"] = fr_ord_no

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "acnt_ord_cntr_prps_dtl": [],
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
    result = get_domestic_account_order_fill_detail(
        qry_tp='1',
        stk_bond_tp='0',
        sell_tp='0',
        dmst_stex_tp='%',
        ord_dt='',
        stk_cd='005930',
        fr_ord_no='',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
