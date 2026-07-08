# ---
# api_id: ka10098
# api_name: 시간외단일가등락율순위요청
# category: 국내주식
# sub_category: 순위정보
# template: rest
# api_url: /api/dostk/rkinfo
# menu_path: 국내주식 > 순위정보 > 시간외단일가등락율순위요청(ka10098)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka10098"
API_URL = "/api/dostk/rkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "ovt_sigpric_flu_rt_rank": "시간외단일가등락율순위"
}
COLUMNS = {
    "rank": "순위",
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "cur_prc": "현재가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "sel_tot_req": "매도총잔량",
    "buy_tot_req": "매수총잔량",
    "acc_trde_qty": "누적거래량",
    "acc_trde_prica": "누적거래대금",
    "tdy_close_pric": "당일종가",
    "tdy_close_pric_flu_rt": "당일종가등락률"
}


NUMERIC_COLUMNS = (
    '누적거래대금',
    '누적거래량',
    '당일종가',
    '당일종가등락률',
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

def get_domestic_after_hours_single_price_change_rate_rank(
    mrkt_tp: str,
    sort_base: str,
    stk_cnd: str,
    trde_qty_cnd: str,
    crd_cnd: str,
    trde_prica: str,
) -> dict[str, pd.DataFrame]:
    """
    시간외단일가등락율순위요청[ka10098] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        mrkt_tp: 000:전체,001:코스피,101:코스닥
        sort_base: 1:상승률, 2:상승폭, 3:하락률, 4:하락폭, 5:보합
        stk_cnd: 0:전체조회,1:관리종목제외,2:정리매매종목제외,3:우선주제외,4:관리종목우선주제외,5:증100제외,6:증100만보기,7:증40만보기,8:증30만보기,9:증20만보기,12:증50만보기,13:증60만보기,14:ETF제외,15:스팩제외,16:ETF+ETN제외,17:ETN제외
        trde_qty_cnd: 0:전체조회, 10:백주이상,50:5백주이상,100;천주이상, 500:5천주이상, 1000:만주이상, 5000:5만주이상, 10000:10만주이상
        crd_cnd: 0:전체조회, 9:신용융자전체, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 8:신용대주, 5:신용한도초과제외
        trde_prica: 0:전체조회, 5:5백만원이상,10:1천만원이상, 30:3천만원이상, 50:5천만원이상, 100:1억원이상, 300:3억원이상, 500:5억원이상, 1000:10억원이상, 3000:30억원이상, 5000:50억원이상, 10000:100억원이상

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_after_hours_single_price_change_rate_rank(
        ...     mrkt_tp='000',
        ...     sort_base='5',
        ...     stk_cnd='0',
        ...     trde_qty_cnd='0',
        ...     crd_cnd='0',
        ...     trde_prica='0',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not sort_base:
        raise ValueError('sort_base is required.')
    if not stk_cnd:
        raise ValueError('stk_cnd is required.')
    if not trde_qty_cnd:
        raise ValueError('trde_qty_cnd is required.')
    if not crd_cnd:
        raise ValueError('crd_cnd is required.')
    if not trde_prica:
        raise ValueError('trde_prica is required.')

    # 2. 요청 파라미터 바디
    body = {
        "mrkt_tp": mrkt_tp,
        "sort_base": sort_base,
        "stk_cnd": stk_cnd,
        "trde_qty_cnd": trde_qty_cnd,
        "crd_cnd": crd_cnd,
        "trde_prica": trde_prica,
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "ovt_sigpric_flu_rt_rank": [],
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
    result = get_domestic_after_hours_single_price_change_rate_rank(
        mrkt_tp='000',
        sort_base='5',
        stk_cnd='0',
        trde_qty_cnd='0',
        crd_cnd='0',
        trde_prica='0',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
