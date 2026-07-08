# ---
# api_id: ka90003
# api_name: 프로그램순매수상위50요청
# category: 국내주식
# sub_category: 종목정보
# template: rest
# api_url: /api/dostk/stkinfo
# menu_path: 국내주식 > 종목정보 > 프로그램순매수상위50요청(ka90003)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka90003"
API_URL = "/api/dostk/stkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "prm_netprps_upper_50": "프로그램순매수상위50"
}
COLUMNS = {
    "rank": "순위",
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "cur_prc": "현재가",
    "flu_sig": "등락기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "acc_trde_qty": "누적거래량",
    "prm_sell_amt": "프로그램매도금액",
    "prm_buy_amt": "프로그램매수금액",
    "prm_netprps_amt": "프로그램순매수금액"
}


NUMERIC_COLUMNS = (
    '프로그램매도금액',
    '프로그램매수금액',
    '프로그램순매수금액',
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

def get_domestic_program_net_buy_top_50(
    trde_upper_tp: str,
    amt_qty_tp: str,
    mrkt_tp: str,
    stex_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    프로그램순매수상위50요청[ka90003] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        trde_upper_tp: 1:순매도상위, 2:순매수상위
        amt_qty_tp: 1:금액, 2:수량
        mrkt_tp: P00101:코스피, P10102:코스닥
        stex_tp: 1:KRX, 2:NXT 3.통합

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_program_net_buy_top_50(
        ...     trde_upper_tp='1',
        ...     amt_qty_tp='1',
        ...     mrkt_tp='P00101',
        ...     stex_tp='1',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not trde_upper_tp:
        raise ValueError('trde_upper_tp is required.')
    if not amt_qty_tp:
        raise ValueError('amt_qty_tp is required.')
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "trde_upper_tp": trde_upper_tp,
        "amt_qty_tp": amt_qty_tp,
        "mrkt_tp": mrkt_tp,
        "stex_tp": stex_tp,
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "prm_netprps_upper_50": [],
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
    result = get_domestic_program_net_buy_top_50(
        trde_upper_tp='1',
        amt_qty_tp='1',
        mrkt_tp='P00101',
        stex_tp='1',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
