# ---
# api_id: ka10039
# api_name: 증권사별매매상위요청
# category: 국내주식
# sub_category: 순위정보
# template: rest
# api_url: /api/dostk/rkinfo
# menu_path: 국내주식 > 순위정보 > 증권사별매매상위요청(ka10039)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka10039"
API_URL = "/api/dostk/rkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "sec_trde_upper": "증권사별매매상위"
}
COLUMNS = {
    "rank": "순위",
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "prid_stkpc_flu": "기간중주가등락",
    "flu_rt": "등락율",
    "prid_trde_qty": "기간중거래량",
    "netprps": "순매수",
    "buy_trde_qty": "매수거래량",
    "sel_trde_qty": "매도거래량",
    "netprps_amt": "순매수금액",
    "buy_amt": "매수금액",
    "sell_amt": "매도금액"
}


NUMERIC_COLUMNS = (
    '기간중거래량',
    '기간중주가등락',
    '등락율',
    '매도거래량',
    '매도금액',
    '매수거래량',
    '매수금액',
    '순매수금액',
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

def get_domestic_broker_trade_top(
    mmcm_cd: str,
    trde_qty_tp: str,
    trde_tp: str,
    dt: str,
    stex_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    증권사별매매상위요청[ka10039] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        mmcm_cd: 회원사 코드는 ka10102 조회
        trde_qty_tp: 0:전체, 5:5000주, 10:1만주, 50:5만주, 100:10만주, 500:50만주, 1000: 100만주
        trde_tp: 1:순매수, 2:순매도
        dt: 1:전일, 5:5일, 10:10일, 60:60일
        stex_tp: 1:KRX, 2:NXT 3.통합

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_broker_trade_top(
        ...     mmcm_cd='001',
        ...     trde_qty_tp='0',
        ...     trde_tp='1',
        ...     dt='1',
        ...     stex_tp='3',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not mmcm_cd:
        raise ValueError('mmcm_cd is required.')
    if not trde_qty_tp:
        raise ValueError('trde_qty_tp is required.')
    if not trde_tp:
        raise ValueError('trde_tp is required.')
    if not dt:
        raise ValueError('dt is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "mmcm_cd": mmcm_cd,
        "trde_qty_tp": trde_qty_tp,
        "trde_tp": trde_tp,
        "dt": dt,
        "stex_tp": stex_tp,
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "sec_trde_upper": [],
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
    result = get_domestic_broker_trade_top(
        mmcm_cd='001',
        trde_qty_tp='0',
        trde_tp='1',
        dt='1',
        stex_tp='3',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
