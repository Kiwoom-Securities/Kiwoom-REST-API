# ---
# api_id: ka10040
# api_name: 당일주요거래원요청
# category: 국내주식
# sub_category: 순위정보
# template: rest
# api_url: /api/dostk/rkinfo
# menu_path: 국내주식 > 순위정보 > 당일주요거래원요청(ka10040)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10040"
API_URL = "/api/dostk/rkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "tdy_main_trde_ori": "당일주요거래원"
}
COLUMNS = {
    "sel_scesn_tm": "매도이탈시간",
    "sell_qty": "매도수량",
    "sel_upper_scesn_ori": "매도상위이탈원",
    "buy_scesn_tm": "매수이탈시간",
    "buy_qty": "매수수량",
    "buy_upper_scesn_ori": "매수상위이탈원",
    "qry_dt": "조회일자",
    "qry_tm": "조회시간"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "sel_trde_ori_irds_1": "매도거래원별증감1",
    "sel_trde_ori_qty_1": "매도거래원수량1",
    "sel_trde_ori_1": "매도거래원1",
    "sel_trde_ori_cd_1": "매도거래원코드1",
    "buy_trde_ori_1": "매수거래원1",
    "buy_trde_ori_cd_1": "매수거래원코드1",
    "buy_trde_ori_qty_1": "매수거래원수량1",
    "buy_trde_ori_irds_1": "매수거래원별증감1",
    "sel_trde_ori_irds_2": "매도거래원별증감2",
    "sel_trde_ori_qty_2": "매도거래원수량2",
    "sel_trde_ori_2": "매도거래원2",
    "sel_trde_ori_cd_2": "매도거래원코드2",
    "buy_trde_ori_2": "매수거래원2",
    "buy_trde_ori_cd_2": "매수거래원코드2",
    "buy_trde_ori_qty_2": "매수거래원수량2",
    "buy_trde_ori_irds_2": "매수거래원별증감2",
    "sel_trde_ori_irds_3": "매도거래원별증감3",
    "sel_trde_ori_qty_3": "매도거래원수량3",
    "sel_trde_ori_3": "매도거래원3",
    "sel_trde_ori_cd_3": "매도거래원코드3",
    "buy_trde_ori_3": "매수거래원3",
    "buy_trde_ori_cd_3": "매수거래원코드3",
    "buy_trde_ori_qty_3": "매수거래원수량3",
    "buy_trde_ori_irds_3": "매수거래원별증감3",
    "sel_trde_ori_irds_4": "매도거래원별증감4",
    "sel_trde_ori_qty_4": "매도거래원수량4",
    "sel_trde_ori_4": "매도거래원4",
    "sel_trde_ori_cd_4": "매도거래원코드4",
    "buy_trde_ori_4": "매수거래원4",
    "buy_trde_ori_cd_4": "매수거래원코드4",
    "buy_trde_ori_qty_4": "매수거래원수량4",
    "buy_trde_ori_irds_4": "매수거래원별증감4",
    "sel_trde_ori_irds_5": "매도거래원별증감5",
    "sel_trde_ori_qty_5": "매도거래원수량5",
    "sel_trde_ori_5": "매도거래원5",
    "sel_trde_ori_cd_5": "매도거래원코드5",
    "buy_trde_ori_5": "매수거래원5",
    "buy_trde_ori_cd_5": "매수거래원코드5",
    "buy_trde_ori_qty_5": "매수거래원수량5",
    "buy_trde_ori_irds_5": "매수거래원별증감5",
    "frgn_sel_prsm_sum_chang": "외국계매도추정합변동",
    "frgn_sel_prsm_sum": "외국계매도추정합",
    "frgn_buy_prsm_sum": "외국계매수추정합",
    "frgn_buy_prsm_sum_chang": "외국계매수추정합변동"
}


NUMERIC_COLUMNS = (
    '매도거래원수량1',
    '매도거래원수량2',
    '매도거래원수량3',
    '매도거래원수량4',
    '매도거래원수량5',
    '매도수량',
    '매수거래원수량1',
    '매수거래원수량2',
    '매수거래원수량3',
    '매수거래원수량4',
    '매수거래원수량5',
    '매수수량',
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

def get_domestic_today_major_brokers(
    stk_cd: str,
) -> dict[str, pd.DataFrame]:
    """
    당일주요거래원요청[ka10040] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_today_major_brokers(
        ...     stk_cd='005930',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "tdy_main_trde_ori": [],
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
        result = get_domestic_today_major_brokers(
            stk_cd='005930',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
