# ---
# api_id: ka40004
# api_name: ETF전체시세요청
# category: 국내주식
# sub_category: ETF
# template: rest
# api_url: /api/dostk/etf
# menu_path: 국내주식 > ETF > ETF전체시세요청(ka40004)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka40004"
API_URL = "/api/dostk/etf"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "etfall_mrpr": "ETF전체시세"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_cls": "종목분류",
    "stk_nm": "종목명",
    "close_pric": "종가",
    "pre_sig": "대비기호",
    "pred_pre": "전일대비",
    "pre_rt": "대비율",
    "trde_qty": "거래량",
    "nav": "NAV",
    "trace_eor_rt": "추적오차율",
    "txbs": "과표기준",
    "dvid_bf_base": "배당전기준",
    "pred_dvida": "전일배당금",
    "trace_idex_nm": "추적지수명",
    "drng": "배수",
    "trace_idex_cd": "추적지수코드",
    "trace_idex": "추적지수",
    "trace_flu_rt": "추적등락율"
}


NUMERIC_COLUMNS = (
    '거래량',
    '대비율',
    '전일배당금',
    '종가',
    '추적등락율',
    '추적오차율',
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

def get_domestic_etf_all_quotes(
    txon_type: str,
    navpre: str,
    mngmcomp: str,
    txon_yn: str,
    trace_idex: str,
    stex_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    ETF전체시세요청[ka40004] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        txon_type: 0:전체, 1:비과세, 2:보유기간과세, 3:회사형, 4:외국, 5:비과세해외(보유기간관세)
        navpre: 0:전체, 1:NAV > 전일종가, 2:NAV < 전일종가
        mngmcomp: 0000:전체, 3020:KODEX(삼성), 3027:KOSEF(키움), 3191:TIGER(미래에셋), 3228:KINDEX(한국투자), 3023:KStar(KB), 3022:아리랑(한화), 9999:기타운용사
        txon_yn: 0:전체, 1:과세, 2:비과세
        trace_idex: 0:전체
        stex_tp: 1:KRX, 2:NXT, 3:통합

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_etf_all_quotes(
        ...     txon_type='0',
        ...     navpre='0',
        ...     mngmcomp='0000',
        ...     txon_yn='0',
        ...     trace_idex='0',
        ...     stex_tp='1',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not txon_type:
        raise ValueError('txon_type is required.')
    if not navpre:
        raise ValueError('navpre is required.')
    if not mngmcomp:
        raise ValueError('mngmcomp is required.')
    if not txon_yn:
        raise ValueError('txon_yn is required.')
    if not trace_idex:
        raise ValueError('trace_idex is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "txon_type": txon_type,
        "navpre": navpre,
        "mngmcomp": mngmcomp,
        "txon_yn": txon_yn,
        "trace_idex": trace_idex,
        "stex_tp": stex_tp,
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "etfall_mrpr": [],
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
    result = get_domestic_etf_all_quotes(
        txon_type='0',
        navpre='0',
        mngmcomp='0000',
        txon_yn='0',
        trace_idex='0',
        stex_tp='1',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
