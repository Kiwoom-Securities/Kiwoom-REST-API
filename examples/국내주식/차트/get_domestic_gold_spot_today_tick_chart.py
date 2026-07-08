# ---
# api_id: ka50091
# api_name: 금현물당일틱차트조회요청
# category: 국내주식
# sub_category: 차트
# template: rest
# api_url: /api/dostk/chart
# menu_path: 국내주식 > 차트 > 금현물당일틱차트조회요청(ka50091)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka50091"
API_URL = "/api/dostk/chart"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "gds_tic_chart_qry": "금현물일봉차트조회"
}
COLUMNS = {
    "cntr_pric": "체결가",
    "pred_pre": "전일 대비(원)",
    "trde_qty": "거래량(체결량)",
    "open_pric": "시가",
    "high_pric": "고가",
    "low_pric": "저가",
    "cntr_tm": "체결시간",
    "dt": "일자",
    "pred_pre_sig": "전일대비기호"
}


NUMERIC_COLUMNS = (
    '거래량(체결량)',
    '고가',
    '시가',
    '저가',
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

def get_domestic_gold_spot_today_tick_chart(
    stk_cd: str,
    tic_scope: str,
) -> dict[str, pd.DataFrame]:
    """
    금현물당일틱차트조회요청[ka50091] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: M04020000 금 99.99_1kg, M04020100 미니금 99.99_100g
        tic_scope: 틱범위

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_gold_spot_today_tick_chart(
        ...     stk_cd='M04020000',
        ...     tic_scope='1',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not tic_scope:
        raise ValueError('tic_scope is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,
        "tic_scope": tic_scope,
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "gds_tic_chart_qry": [],
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
    result = get_domestic_gold_spot_today_tick_chart(
        stk_cd='M04020000',
        tic_scope='1',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
