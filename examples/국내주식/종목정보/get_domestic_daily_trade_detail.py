# ---
# api_id: ka10015
# api_name: 일별거래상세요청
# category: 국내주식
# sub_category: 종목정보
# template: rest
# api_url: /api/dostk/stkinfo
# menu_path: 국내주식 > 종목정보 > 일별거래상세요청(ka10015)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10015"
API_URL = "/api/dostk/stkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "daly_trde_dtl": "일별거래상세"
}
COLUMNS = {
    "dt": "일자",
    "close_pric": "종가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "trde_qty": "거래량",
    "trde_prica": "거래대금",
    "bf_mkrt_trde_qty": "장전거래량",
    "bf_mkrt_trde_wght": "장전거래비중",
    "opmr_trde_qty": "장중거래량",
    "opmr_trde_wght": "장중거래비중",
    "af_mkrt_trde_qty": "장후거래량",
    "af_mkrt_trde_wght": "장후거래비중",
    "tot_3": "합계3",
    "prid_trde_qty": "기간중거래량",
    "cntr_str": "체결강도",
    "for_poss": "외인보유",
    "for_wght": "외인비중",
    "for_netprps": "외인순매수",
    "orgn_netprps": "기관순매수",
    "ind_netprps": "개인순매수",
    "frgn": "외국계",
    "crd_remn_rt": "신용잔고율",
    "prm": "프로그램",
    "bf_mkrt_trde_prica": "장전거래대금",
    "bf_mkrt_trde_prica_wght": "장전거래대금비중",
    "opmr_trde_prica": "장중거래대금",
    "opmr_trde_prica_wght": "장중거래대금비중",
    "af_mkrt_trde_prica": "장후거래대금",
    "af_mkrt_trde_prica_wght": "장후거래대금비중"
}


NUMERIC_COLUMNS = (
    '거래대금',
    '거래량',
    '기간중거래량',
    '등락율',
    '신용잔고율',
    '외인비중',
    '장전거래대금',
    '장전거래대금비중',
    '장전거래량',
    '장전거래비중',
    '장중거래대금',
    '장중거래대금비중',
    '장중거래량',
    '장중거래비중',
    '장후거래대금',
    '장후거래대금비중',
    '장후거래량',
    '장후거래비중',
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

def get_domestic_daily_trade_detail(
    stk_cd: str,
    strt_dt: str,
) -> dict[str, pd.DataFrame]:
    """
    일별거래상세요청[ka10015] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)
        strt_dt: 시작일자 — YYYMMDD, 시작일자 기준으로 이전 일별 거래 정보를 조회

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_daily_trade_detail(
        ...     stk_cd='005930',
        ...     strt_dt='20241105',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not strt_dt:
        raise ValueError('strt_dt is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
        "strt_dt": strt_dt,  # 시작일자
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "daly_trde_dtl": [],
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
        result = get_domestic_daily_trade_detail(
            stk_cd='005930',
            strt_dt='20241105',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
