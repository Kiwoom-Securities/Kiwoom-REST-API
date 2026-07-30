# ---
# api_id: ka90010
# api_name: 프로그램매매추이요청 일자별
# category: 국내주식
# sub_category: 시세
# template: rest
# api_url: /api/dostk/mrkcond
# menu_path: 국내주식 > 시세 > 프로그램매매추이요청 일자별(ka90010)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka90010"
API_URL = "/api/dostk/mrkcond"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "prm_trde_trnsn": "프로그램매매추이"
}
COLUMNS = {
    "cntr_tm": "체결시간",
    "dfrt_trde_sel": "차익거래매도",
    "dfrt_trde_buy": "차익거래매수",
    "dfrt_trde_netprps": "차익거래순매수",
    "ndiffpro_trde_sel": "비차익거래매도",
    "ndiffpro_trde_buy": "비차익거래매수",
    "ndiffpro_trde_netprps": "비차익거래순매수",
    "dfrt_trde_sell_qty": "차익거래매도수량",
    "dfrt_trde_buy_qty": "차익거래매수수량",
    "dfrt_trde_netprps_qty": "차익거래순매수수량",
    "ndiffpro_trde_sell_qty": "비차익거래매도수량",
    "ndiffpro_trde_buy_qty": "비차익거래매수수량",
    "ndiffpro_trde_netprps_qty": "비차익거래순매수수량",
    "all_sel": "전체매도",
    "all_buy": "전체매수",
    "all_netprps": "전체순매수",
    "kospi200": "KOSPI200",
    "basis": "BASIS"
}


NUMERIC_COLUMNS = (
    '비차익거래매도수량',
    '비차익거래매수수량',
    '비차익거래순매수수량',
    '차익거래매도수량',
    '차익거래매수수량',
    '차익거래순매수수량',
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

def get_domestic_program_trade_daily_trend(
    date: str,
    amt_qty_tp: str,
    mrkt_tp: str,
    min_tic_tp: str,
    stex_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    프로그램매매추이요청 일자별[ka90010] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        date: 날짜 — YYYYMMDD
        amt_qty_tp: 금액수량구분 — 1:금액(백만원), 2:수량(천주)
        mrkt_tp: 시장구분 — 코스피- 거래소구분값 1일경우:P00101, 2일경우:P001_NX01, 3일경우:P001_AL01
            코스닥- 거래소구분값 1일경우:P10102, 2일경우:P101_NX02, 3일경우:P001_AL02
        min_tic_tp: 분틱구분 — 0:틱, 1:분
        stex_tp: 거래소구분 — 1:KRX, 2:NXT 3.통합

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_program_trade_daily_trend(
        ...     date='20241125',
        ...     amt_qty_tp='1',
        ...     mrkt_tp='P00101',
        ...     min_tic_tp='0',
        ...     stex_tp='1',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not date:
        raise ValueError('date is required.')
    if not amt_qty_tp:
        raise ValueError('amt_qty_tp is required.')
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not min_tic_tp:
        raise ValueError('min_tic_tp is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "date": date,  # 날짜
        "amt_qty_tp": amt_qty_tp,  # 금액수량구분
        "mrkt_tp": mrkt_tp,  # 시장구분
        "min_tic_tp": min_tic_tp,  # 분틱구분
        "stex_tp": stex_tp,  # 거래소구분
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "prm_trde_trnsn": [],
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
        result = get_domestic_program_trade_daily_trend(
            date='20241125',
            amt_qty_tp='1',
            mrkt_tp='P00101',
            min_tic_tp='0',
            stex_tp='1',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
