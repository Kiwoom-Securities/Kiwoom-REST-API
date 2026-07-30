# ---
# api_id: ka10038
# api_name: 종목별증권사순위요청
# category: 국내주식
# sub_category: 순위정보
# template: rest
# api_url: /api/dostk/rkinfo
# menu_path: 국내주식 > 순위정보 > 종목별증권사순위요청(ka10038)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10038"
API_URL = "/api/dostk/rkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "stk_sec_rank": "종목별증권사순위"
}
COLUMNS = {
    "rank": "순위",
    "mmcm_nm": "회원사명",
    "buy_qty": "매수수량",
    "sell_qty": "매도수량",
    "acc_netprps_qty": "누적순매수수량"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "rank_1": "기간별 누적 매수량",
    "rank_2": "기간별 누적 매도량",
    "rank_3": "기간별 누적 순매수",
    "prid_trde_qty": "기간중거래량"
}


NUMERIC_COLUMNS = (
    '기간별 누적 매수량',
    '기간중거래량',
    '누적순매수수량',
    '매도수량',
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

def get_domestic_stock_broker_rank(
    stk_cd: str,
    qry_tp: str,
    strt_dt: str | None = '20241106',
    end_dt: str | None = '20241107',
    dt: str | None = '1',
) -> dict[str, pd.DataFrame]:
    """
    종목별증권사순위요청[ka10038] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)
        qry_tp: 조회구분 — 1:순매도순위정렬, 2:순매수순위정렬
        strt_dt: 시작일자 — YYYYMMDD
            (연도4자리, 월 2자리, 일 2자리 형식)
        end_dt: 종료일자 — YYYYMMDD
            (연도4자리, 월 2자리, 일 2자리 형식)
        dt: 기간 — 1:전일, 4:5일, 9:10일, 19:20일, 39:40일, 59:60일, 119:120일
            ※ 시작일자와 종료일자로 조회를 원하는 경우 기간(dt)값은 빈값('')으로 설정

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_stock_broker_rank(
        ...     stk_cd='005930',
        ...     qry_tp='2',
        ...     strt_dt='20241106',
        ...     end_dt='20241107',
        ...     dt='1',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not qry_tp:
        raise ValueError('qry_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
        "qry_tp": qry_tp,  # 조회구분
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
    summary_rows = []
    rows = {
        "stk_sec_rank": [],
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
        result = get_domestic_stock_broker_rank(
            stk_cd='005930',
            qry_tp='2',
            strt_dt='20241106',
            end_dt='20241107',
            dt='1',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
