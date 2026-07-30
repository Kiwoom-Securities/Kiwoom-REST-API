# ---
# api_id: usa20961
# api_name: 미국주식 전일 거래상위(ETF)
# category: 미국주식
# sub_category: 순위정보
# template: rest
# api_url: /api/us/rkinfo
# menu_path: 미국주식 > 순위정보 > 미국주식 전일 거래상위(ETF)(usa20961)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "usa20961"
API_URL = "/api/us/rkinfo"
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
    "rank": "순위",
    "stex_tp": "거래소구분",
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "stk_enm": "종목영문명",
    "cur_prc": "현재가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "pred_rt": "전일비",
    "acc_trde_qty": "당일거래량"
}


NUMERIC_COLUMNS = (
    '당일거래량',
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

def get_overseas_prev_day_trade_top_etf(
    stex_tp: str | None = '0',
    etf_cat1: str | None = '',
    etf_cat2: str | None = '',
    qry_tp: str | None = '0',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 전일 거래상위(ETF)[usa20961] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stex_tp: 거래소 구분 — 0:전체,1:NYSE,2:AMEX,3:NASDAQ
        etf_cat1: ETF카테고리코드1 — ETF 대카테고리코드 (ETF이고 대분류일 경우 사용), usa10105 cate1 속성 참고
        etf_cat2: ETF카테고리코드2 — ETF 중카테고리코드 (ETF이고 중분류일 경우 사용), usa10105 cate2 속성 참고
        qry_tp: 정렬기준구분 — 0:전일거래량상위,1:전일거래대금상위

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_prev_day_trade_top_etf(
        ...     stex_tp='0',
        ...     etf_cat1='',
        ...     etf_cat2='',
        ...     qry_tp='0',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }
    if stex_tp is not None:
        body["stex_tp"] = stex_tp  # 거래소 구분
    if etf_cat1 is not None:
        body["etf_cat1"] = etf_cat1  # ETF카테고리코드1
    if etf_cat2 is not None:
        body["etf_cat2"] = etf_cat2  # ETF카테고리코드2
    if qry_tp is not None:
        body["qry_tp"] = qry_tp  # 정렬기준구분

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
        result = get_overseas_prev_day_trade_top_etf(
            stex_tp='0',
            etf_cat1='',
            etf_cat2='',
            qry_tp='0',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
