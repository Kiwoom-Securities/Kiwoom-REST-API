# ---
# api_id: usa20881
# api_name: 키움 거래 상위 종목(미국 ETF)
# category: 미국주식
# sub_category: 순위정보
# template: rest
# api_url: /api/us/rkinfo
# menu_path: 미국주식 > 순위정보 > 키움 거래 상위 종목(미국 ETF)(usa20881)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "usa20881"
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
    "stex_tp": "거래소구분",
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "stk_enm": "종목영문명",
    "kw_high_rank": "키움상위순위",
    "kw_high_rank_sig": "키움상위순위등락부호",
    "kw_high_rank_hl": "키움상위 순위등락폭",
    "cur_prc": "현재가",
    "flu_rt": "등락률"
}


NUMERIC_COLUMNS = (
    '등락률',
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

def get_overseas_kiwoom_trade_top_etf(
    qry_tp: str | None = '7',
    dt_unit_tp: str | None = '8',
) -> dict[str, pd.DataFrame]:
    """
    키움 거래 상위 종목(미국 ETF)[usa20881] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        qry_tp: 조회구분 — 1:매수상위,2:매도상위,3:순매수상위,4:보유잔고상위,5:보유고객상위,6:거래비중상위(미국,미국 ETF 분단위만 존재),7:거래대금상위(미국,미국 ETF 분단위만 존재)
        dt_unit_tp: 일,주,월단위구분 — 1:일,2:주,3:월,4:년,분단위(5:10분,6:30분,7:60분,8:5분)-미국/미국ETF 만 존재

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_kiwoom_trade_top_etf(
        ...     qry_tp='7',
        ...     dt_unit_tp='8',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }
    if qry_tp is not None:
        body["qry_tp"] = qry_tp  # 조회구분
    if dt_unit_tp is not None:
        body["dt_unit_tp"] = dt_unit_tp  # 일,주,월단위구분

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
        result = get_overseas_kiwoom_trade_top_etf(
            qry_tp='7',
            dt_unit_tp='8',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
