# ---
# api_id: usa20590
# api_name: 미국주식 일별주가
# category: 미국주식
# sub_category: 시세
# template: rest
# api_url: /api/us/mrkcond
# menu_path: 미국주식 > 시세 > 미국주식 일별주가(usa20590)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "usa20590"
API_URL = "/api/us/mrkcond"
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
    "dt": "일자",
    "cur_prc": "현재가(종가)",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "acc_trde_qty": "누적거래량",
    "trde_prica": "누적금액",
    "open_pric": "시가",
    "high_pric": "고가",
    "low_pric": "저가",
    "base_pric": "기준가",
    "base_open_flu_rt": "기준가대비 시가등락율",
    "base_high_flu_rt": "기준가대비 고가등락율",
    "base_low_flu_rt": "기준가대비 저가등락율"
}


NUMERIC_COLUMNS = (
    '고가',
    '기준가',
    '기준가대비 고가등락율',
    '기준가대비 시가등락율',
    '기준가대비 저가등락율',
    '누적거래량',
    '누적금액',
    '등락률',
    '시가',
    '저가',
    '현재가(종가)',
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

def get_overseas_stock_daily_price(
    stex_tp: str | None = 'ND',
    stk_cd: str | None = 'NVDA',
    base_dt: str | None = '20260501',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 일별주가[usa20590] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stex_tp: 거래소구분 — NA:AMEX,ND:NASDAQ,NY:NYSE
        stk_cd: 종목코드
        base_dt: 기준일자 — 기준일자 이전 내역 조회

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_stock_daily_price(
        ...     stex_tp='ND',
        ...     stk_cd='NVDA',
        ...     base_dt='20260501',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }
    if stex_tp is not None:
        body["stex_tp"] = stex_tp  # 거래소구분
    if stk_cd is not None:
        body["stk_cd"] = stk_cd  # 종목코드
    if base_dt is not None:
        body["base_dt"] = base_dt  # 기준일자

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
        result = get_overseas_stock_daily_price(
            stex_tp='ND',
            stk_cd='NVDA',
            base_dt='20260501',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
