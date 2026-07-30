# ---
# api_id: ka10086
# api_name: 일별주가요청
# category: 국내주식
# sub_category: 시세
# template: rest
# api_url: /api/dostk/mrkcond
# menu_path: 국내주식 > 시세 > 일별주가요청(ka10086)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10086"
API_URL = "/api/dostk/mrkcond"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "daly_stkpc": "일별주가"
}
COLUMNS = {
    "date": "날짜",
    "open_pric": "시가",
    "high_pric": "고가",
    "low_pric": "저가",
    "close_pric": "종가",
    "pred_rt": "전일비",
    "flu_rt": "등락률",
    "trde_qty": "거래량",
    "amt_mn": "금액(백만)",
    "crd_rt": "신용비",
    "ind": "개인",
    "orgn": "기관",
    "for_qty": "외인수량",
    "frgn": "외국계",
    "prm": "프로그램",
    "for_rt": "외인비",
    "for_poss": "외인보유",
    "for_wght": "외인비중",
    "for_netprps": "외인순매수",
    "orgn_netprps": "기관순매수",
    "ind_netprps": "개인순매수",
    "crd_remn_rt": "신용잔고율"
}


NUMERIC_COLUMNS = (
    '거래량',
    '고가',
    '금액(백만)',
    '등락률',
    '시가',
    '신용잔고율',
    '외인비중',
    '외인수량',
    '저가',
    '종가',
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

def get_domestic_daily_stock_price(
    stk_cd: str,
    qry_dt: str,
    indc_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    일별주가요청[ka10086] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)
        qry_dt: 조회일자 — YYYYMMDD
        indc_tp: 표시구분 — 0:수량, 1:금액(백만원)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_daily_stock_price(
        ...     stk_cd='005930',
        ...     qry_dt='20241125',
        ...     indc_tp='0',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not qry_dt:
        raise ValueError('qry_dt is required.')
    if not indc_tp:
        raise ValueError('indc_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
        "qry_dt": qry_dt,  # 조회일자
        "indc_tp": indc_tp,  # 표시구분
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "daly_stkpc": [],
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
        result = get_domestic_daily_stock_price(
            stk_cd='005930',
            qry_dt='20241125',
            indc_tp='0',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
