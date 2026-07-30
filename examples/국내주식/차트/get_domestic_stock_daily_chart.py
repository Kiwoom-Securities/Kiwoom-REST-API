# ---
# api_id: ka10081
# api_name: 주식일봉차트조회요청
# category: 국내주식
# sub_category: 차트
# template: rest
# api_url: /api/dostk/chart
# menu_path: 국내주식 > 차트 > 주식일봉차트조회요청(ka10081)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10081"
API_URL = "/api/dostk/chart"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "stk_dt_pole_chart_qry": "주식일봉차트조회"
}
COLUMNS = {
    "cur_prc": "현재가",
    "trde_qty": "거래량",
    "trde_prica": "거래대금",
    "dt": "일자",
    "open_pric": "시가",
    "high_pric": "고가",
    "low_pric": "저가",
    "pred_pre": "전일대비",
    "pred_pre_sig": "전일대비기호",
    "trde_tern_rt": "거래회전율"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "stk_cd": "종목코드"
}


NUMERIC_COLUMNS = (
    '거래대금',
    '거래량',
    '거래회전율',
    '고가',
    '시가',
    '저가',
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

def get_domestic_stock_daily_chart(
    stk_cd: str,
    base_dt: str,
    upd_stkpc_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    주식일봉차트조회요청[ka10081] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)
        base_dt: 기준일자 — YYYYMMDD
        upd_stkpc_tp: 수정주가구분 — 0 or 1 / 수정주가 적용을 원하시는 경우, 권리발생일 이후 일자를 base_dt에 넣어 조회 또는 연속조회해주시기 바랍니다. 예를 들어 삼성전자 2018년 05월 04일 (액면분할 권리발생일)을 base_dt에 넣고 수정주가적용(1)로 조회하면 2018년 05월 04일 이전 데이터는 수정주가 적용된 3만원대 가격이 나옵니다. 연속조회도 동일합니다. 권리 발생일 이전인 2018년 05월 03일 이전 일자로 base_dt 조회 시 수정주가 적용되지 않아 200만원 이상 가격대가 나옵니다. 수정주가 적용을 원하는 과거 차트 데이터 조회를 위해서는 해당 권리발생일 이후로 base_dt를 세팅하고, 수정주가 적용(1)로 세팅하고 조회 및 연속조회하여야합니다.

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_stock_daily_chart(
        ...     stk_cd='005930',
        ...     base_dt='20250908',
        ...     upd_stkpc_tp='1',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not base_dt:
        raise ValueError('base_dt is required.')
    if not upd_stkpc_tp:
        raise ValueError('upd_stkpc_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
        "base_dt": base_dt,  # 기준일자
        "upd_stkpc_tp": upd_stkpc_tp,  # 수정주가구분
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "stk_dt_pole_chart_qry": [],
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
        summary_rows.append({
            key: response_body.get(key)
            for key in SUMMARY_COLUMNS
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
    result = {
        SUMMARY_KEY: pd.DataFrame(summary_rows).rename(columns=SUMMARY_COLUMNS),
        **result,
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
        result = get_domestic_stock_daily_chart(
            stk_cd='005930',
            base_dt='20250908',
            upd_stkpc_tp='1',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
