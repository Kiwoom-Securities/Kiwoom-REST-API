# ---
# api_id: ka10054
# api_name: 변동성완화장치발동종목요청
# category: 국내주식
# sub_category: 종목정보
# template: rest
# api_url: /api/dostk/stkinfo
# menu_path: 국내주식 > 종목정보 > 변동성완화장치발동종목요청(ka10054)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka10054"
API_URL = "/api/dostk/stkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "motn_stk": "발동종목"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "acc_trde_qty": "누적거래량",
    "motn_pric": "발동가격",
    "dynm_dispty_rt": "동적괴리율",
    "trde_cntr_proc_time": "매매체결처리시각",
    "virelis_time": "VI해제시각",
    "viaplc_tp": "VI적용구분",
    "dynm_stdpc": "동적기준가격",
    "static_stdpc": "정적기준가격",
    "static_dispty_rt": "정적괴리율",
    "open_pric_pre_flu_rt": "시가대비등락률",
    "vimotn_cnt": "VI발동횟수",
    "stex_tp": "거래소구분"
}


NUMERIC_COLUMNS = (
    '동적기준가격',
    '발동가격',
    '시가대비등락률',
    '정적기준가격',
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

def get_domestic_vi_triggered_stocks(
    mrkt_tp: str,
    bf_mkrt_tp: str,
    motn_tp: str,
    skip_stk: str,
    trde_qty_tp: str,
    min_trde_qty: str,
    max_trde_qty: str,
    trde_prica_tp: str,
    min_trde_prica: str,
    max_trde_prica: str,
    motn_drc: str,
    stex_tp: str,
    stk_cd: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    변동성완화장치발동종목요청[ka10054] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        mrkt_tp: 000:전체, 001: 코스피, 101:코스닥
        bf_mkrt_tp: 0:전체, 1:정규시장,2:시간외단일가
        motn_tp: 0:전체, 1:정적VI, 2:동적VI, 3:동적VI + 정적VI
        skip_stk: 전종목포함 조회시 9개 0으로 설정(000000000),전종목제외 조회시 9개 1으로 설정(111111111),9개 종목조회여부를 조회포함(0), 조회제외(1)로 설정하며 종목순서는 우선주,관리종목,투자경고/위험,투자주의,환기종목,단기과열종목,증거금100%,ETF,ETN가 됨.우선주만 조회시"011111111"", 관리종목만 조회시 ""101111111"" 설정"
        trde_qty_tp: 0:사용안함, 1:사용
        min_trde_qty: 0 주 이상, 거래량구분이 1일때만 입력(공백허용)
        max_trde_qty: 100000000 주 이하, 거래량구분이 1일때만 입력(공백허용)
        trde_prica_tp: 0:사용안함, 1:사용
        min_trde_prica: 0 백만원 이상, 거래대금구분 1일때만 입력(공백허용)
        max_trde_prica: 100000000 백만원 이하, 거래대금구분 1일때만 입력(공백허용)
        motn_drc: 0:전체, 1:상승, 2:하락
        stex_tp: 1:KRX, 2:NXT 3.통합
        stk_cd: 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)
            공백입력시 시장구분으로 설정한 전체종목조회

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_vi_triggered_stocks(
        ...     mrkt_tp='000',
        ...     bf_mkrt_tp='0',
        ...     motn_tp='0',
        ...     skip_stk='000000000',
        ...     trde_qty_tp='0',
        ...     min_trde_qty='0',
        ...     max_trde_qty='0',
        ...     trde_prica_tp='0',
        ...     min_trde_prica='0',
        ...     max_trde_prica='0',
        ...     motn_drc='0',
        ...     stex_tp='3',
        ...     stk_cd='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not bf_mkrt_tp:
        raise ValueError('bf_mkrt_tp is required.')
    if not motn_tp:
        raise ValueError('motn_tp is required.')
    if not skip_stk:
        raise ValueError('skip_stk is required.')
    if not trde_qty_tp:
        raise ValueError('trde_qty_tp is required.')
    if not min_trde_qty:
        raise ValueError('min_trde_qty is required.')
    if not max_trde_qty:
        raise ValueError('max_trde_qty is required.')
    if not trde_prica_tp:
        raise ValueError('trde_prica_tp is required.')
    if not min_trde_prica:
        raise ValueError('min_trde_prica is required.')
    if not max_trde_prica:
        raise ValueError('max_trde_prica is required.')
    if not motn_drc:
        raise ValueError('motn_drc is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "mrkt_tp": mrkt_tp,
        "bf_mkrt_tp": bf_mkrt_tp,
        "motn_tp": motn_tp,
        "skip_stk": skip_stk,
        "trde_qty_tp": trde_qty_tp,
        "min_trde_qty": min_trde_qty,
        "max_trde_qty": max_trde_qty,
        "trde_prica_tp": trde_prica_tp,
        "min_trde_prica": min_trde_prica,
        "max_trde_prica": max_trde_prica,
        "motn_drc": motn_drc,
        "stex_tp": stex_tp,
    }
    if stk_cd is not None:
        body["stk_cd"] = stk_cd

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "motn_stk": [],
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
    result = get_domestic_vi_triggered_stocks(
        mrkt_tp='000',
        bf_mkrt_tp='0',
        motn_tp='0',
        skip_stk='000000000',
        trde_qty_tp='0',
        min_trde_qty='0',
        max_trde_qty='0',
        trde_prica_tp='0',
        min_trde_prica='0',
        max_trde_prica='0',
        motn_drc='0',
        stex_tp='3',
        stk_cd='',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
