# ---
# api_id: ka10063
# api_name: 장중투자자별매매요청
# category: 국내주식
# sub_category: 시세
# template: rest
# api_url: /api/dostk/mrkcond
# menu_path: 국내주식 > 시세 > 장중투자자별매매요청(ka10063)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10063"
API_URL = "/api/dostk/mrkcond"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "opmr_invsr_trde": "장중투자자별매매"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "cur_prc": "현재가",
    "pre_sig": "대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "acc_trde_qty": "누적거래량",
    "netprps_amt": "순매수금액",
    "prev_netprps_amt": "이전순매수금액",
    "buy_amt": "매수금액",
    "netprps_amt_irds": "순매수금액증감",
    "buy_amt_irds": "매수금액증감",
    "sell_amt": "매도금액",
    "sell_amt_irds": "매도금액증감",
    "netprps_qty": "순매수수량",
    "prev_pot_netprps_qty": "이전시점순매수수량",
    "netprps_irds": "순매수증감",
    "buy_qty": "매수수량",
    "buy_qty_irds": "매수수량증감",
    "sell_qty": "매도수량",
    "sell_qty_irds": "매도수량증감"
}


NUMERIC_COLUMNS = (
    '누적거래량',
    '등락율',
    '매도금액',
    '매도금액증감',
    '매도수량',
    '매도수량증감',
    '매수금액',
    '매수금액증감',
    '매수수량',
    '매수수량증감',
    '순매수금액',
    '순매수금액증감',
    '순매수수량',
    '이전순매수금액',
    '이전시점순매수수량',
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

def get_domestic_intraday_investor_trade(
    mrkt_tp: str,
    amt_qty_tp: str,
    invsr: str,
    frgn_all: str,
    smtm_netprps_tp: str,
    stex_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    장중투자자별매매요청[ka10063] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        mrkt_tp: 시장구분 — 000:전체, 001:코스피, 101:코스닥
        amt_qty_tp: 금액수량구분 — 1: 금액&수량
        invsr: 투자자별 — 6:외국인, 7:기관계, 1:투신, 0:보험, 2:은행, 3:연기금, 4:국가, 5:기타법인
        frgn_all: 외국계전체 — 1:체크, 0:미체크
        smtm_netprps_tp: 동시순매수구분 — 1:체크, 0:미체크
        stex_tp: 거래소구분 — 1:KRX, 2:NXT 3.통합

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_intraday_investor_trade(
        ...     mrkt_tp='000',
        ...     amt_qty_tp='1',
        ...     invsr='6',
        ...     frgn_all='0',
        ...     smtm_netprps_tp='0',
        ...     stex_tp='3',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not amt_qty_tp:
        raise ValueError('amt_qty_tp is required.')
    if not invsr:
        raise ValueError('invsr is required.')
    if not frgn_all:
        raise ValueError('frgn_all is required.')
    if not smtm_netprps_tp:
        raise ValueError('smtm_netprps_tp is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "mrkt_tp": mrkt_tp,  # 시장구분
        "amt_qty_tp": amt_qty_tp,  # 금액수량구분
        "invsr": invsr,  # 투자자별
        "frgn_all": frgn_all,  # 외국계전체
        "smtm_netprps_tp": smtm_netprps_tp,  # 동시순매수구분
        "stex_tp": stex_tp,  # 거래소구분
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "opmr_invsr_trde": [],
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
        result = get_domestic_intraday_investor_trade(
            mrkt_tp='000',
            amt_qty_tp='1',
            invsr='6',
            frgn_all='0',
            smtm_netprps_tp='0',
            stex_tp='3',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
