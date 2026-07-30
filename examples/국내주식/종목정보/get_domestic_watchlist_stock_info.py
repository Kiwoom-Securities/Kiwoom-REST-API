# ---
# api_id: ka10095
# api_name: 지정종목 정보요청
# category: 국내주식
# sub_category: 종목정보
# template: rest
# api_url: /api/dostk/stkinfo
# menu_path: 국내주식 > 종목정보 > 지정종목 정보요청(ka10095)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10095"
API_URL = "/api/dostk/stkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "atn_stk_infr": "관심종목정보"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "cur_prc": "현재가",
    "base_pric": "기준가",
    "pred_pre": "전일대비",
    "pred_pre_sig": "전일대비기호",
    "flu_rt": "등락율",
    "trde_qty": "거래량",
    "trde_prica": "거래대금",
    "cntr_qty": "체결량",
    "cntr_str": "체결강도",
    "pred_trde_qty_pre": "전일거래량대비",
    "sel_bid": "매도호가",
    "buy_bid": "매수호가",
    "sel_1th_bid": "매도1차호가",
    "sel_2th_bid": "매도2차호가",
    "sel_3th_bid": "매도3차호가",
    "sel_4th_bid": "매도4차호가",
    "sel_5th_bid": "매도5차호가",
    "buy_1th_bid": "매수1차호가",
    "buy_2th_bid": "매수2차호가",
    "buy_3th_bid": "매수3차호가",
    "buy_4th_bid": "매수4차호가",
    "buy_5th_bid": "매수5차호가",
    "upl_pric": "상한가",
    "lst_pric": "하한가",
    "open_pric": "시가",
    "high_pric": "고가",
    "low_pric": "저가",
    "close_pric": "종가",
    "cntr_tm": "체결시간",
    "exp_cntr_pric": "예상체결가",
    "exp_cntr_qty": "예상체결량",
    "cap": "자본금",
    "fav": "액면가",
    "mac": "시가총액",
    "stkcnt": "주식수",
    "bid_tm": "호가시간",
    "dt": "일자",
    "pri_sel_req": "우선매도잔량",
    "pri_buy_req": "우선매수잔량",
    "pri_sel_cnt": "우선매도건수",
    "pri_buy_cnt": "우선매수건수",
    "tot_sel_req": "총매도잔량",
    "tot_buy_req": "총매수잔량",
    "tot_sel_cnt": "총매도건수",
    "tot_buy_cnt": "총매수건수",
    "prty": "패리티",
    "gear": "기어링",
    "pl_qutr": "손익분기",
    "cap_support": "자본지지",
    "elwexec_pric": "ELW행사가",
    "cnvt_rt": "전환비율",
    "elwexpr_dt": "ELW만기일",
    "cntr_engg": "미결제약정",
    "cntr_pred_pre": "미결제전일대비",
    "theory_pric": "이론가",
    "innr_vltl": "내재변동성",
    "delta": "델타",
    "gam": "감마",
    "theta": "쎄타",
    "vega": "베가",
    "law": "로"
}


NUMERIC_COLUMNS = (
    'ELW행사가',
    '거래대금',
    '거래량',
    '고가',
    '기준가',
    '등락율',
    '매도1차호가',
    '매도2차호가',
    '매도3차호가',
    '매도4차호가',
    '매도5차호가',
    '매도호가',
    '매수1차호가',
    '매수2차호가',
    '매수3차호가',
    '매수4차호가',
    '매수5차호가',
    '매수호가',
    '베가',
    '상한가',
    '손익분기',
    '시가',
    '시가총액',
    '액면가',
    '예상체결가',
    '이론가',
    '자본금',
    '저가',
    '전일거래량대비',
    '전환비율',
    '종가',
    '하한가',
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

def get_domestic_watchlist_stock_info(
    stk_cd: str,
) -> dict[str, pd.DataFrame]:
    """
    지정종목 정보요청[ka10095] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)
            여러개의 종목코드 입력시 | 로 구분

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_watchlist_stock_info(
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
    rows = {
        "atn_stk_infr": [],
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
        result = get_domestic_watchlist_stock_info(
            stk_cd='005930',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
