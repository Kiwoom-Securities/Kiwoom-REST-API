# ---
# api_id: ka10042
# api_name: 순매수거래원순위요청
# category: 국내주식
# sub_category: 순위정보
# template: rest
# api_url: /api/dostk/rkinfo
# menu_path: 국내주식 > 순위정보 > 순매수거래원순위요청(ka10042)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10042"
API_URL = "/api/dostk/rkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "netprps_trde_ori_rank": "순매수거래원순위"
}
COLUMNS = {
    "rank": "순위",
    "mmcm_cd": "회원사코드",
    "mmcm_nm": "회원사명"
}


NUMERIC_COLUMNS = ()

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

def get_domestic_net_buy_broker_rank(
    stk_cd: str,
    qry_dt_tp: str,
    pot_tp: str,
    sort_base: str,
    strt_dt: str | None = '20241031',
    end_dt: str | None = '20241107',
    dt: str | None = '5',
) -> dict[str, pd.DataFrame]:
    """
    순매수거래원순위요청[ka10042] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)
        qry_dt_tp: 조회기간구분 — 0:기간으로 조회, 1:시작일자, 종료일자로 조회
        pot_tp: 시점구분 — 0:당일, 1:전일
        sort_base: 정렬기준 — 1:종가순, 2:날짜순
        strt_dt: 시작일자 — YYYYMMDD
            (연도4자리, 월 2자리, 일 2자리 형식)
        end_dt: 종료일자 — YYYYMMDD
            (연도4자리, 월 2자리, 일 2자리 형식)
        dt: 기간 — 5:5일, 10:10일, 20:20일, 40:40일, 60:60일, 120:120일

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_net_buy_broker_rank(
        ...     stk_cd='005930',
        ...     qry_dt_tp='0',
        ...     pot_tp='0',
        ...     sort_base='1',
        ...     strt_dt='20241031',
        ...     end_dt='20241107',
        ...     dt='5',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not qry_dt_tp:
        raise ValueError('qry_dt_tp is required.')
    if not pot_tp:
        raise ValueError('pot_tp is required.')
    if not sort_base:
        raise ValueError('sort_base is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
        "qry_dt_tp": qry_dt_tp,  # 조회기간구분
        "pot_tp": pot_tp,  # 시점구분
        "sort_base": sort_base,  # 정렬기준
    }
    if strt_dt is not None:
        body["strt_dt"] = strt_dt  # 시작일자
    if end_dt is not None:
        body["end_dt"] = end_dt  # 종료일자
    if dt is not None:
        body["dt"] = dt  # 기간

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "netprps_trde_ori_rank": [],
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
        result = get_domestic_net_buy_broker_rank(
            stk_cd='005930',
            qry_dt_tp='0',
            pot_tp='0',
            sort_base='1',
            strt_dt='20241031',
            end_dt='20241107',
            dt='5',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
