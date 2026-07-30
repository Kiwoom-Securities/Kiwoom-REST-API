# ---
# api_id: ka10029
# api_name: 예상체결등락률상위요청
# category: 국내주식
# sub_category: 순위정보
# template: rest
# api_url: /api/dostk/rkinfo
# menu_path: 국내주식 > 순위정보 > 예상체결등락률상위요청(ka10029)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10029"
API_URL = "/api/dostk/rkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "exp_cntr_flu_rt_upper": "예상체결등락률상위"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "exp_cntr_pric": "예상체결가",
    "base_pric": "기준가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "exp_cntr_qty": "예상체결량",
    "sel_req": "매도잔량",
    "sel_bid": "매도호가",
    "buy_bid": "매수호가",
    "buy_req": "매수잔량"
}


NUMERIC_COLUMNS = (
    '기준가',
    '등락률',
    '매도호가',
    '매수호가',
    '예상체결가',
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

def get_domestic_expected_execution_change_rate_top(
    mrkt_tp: str,
    sort_tp: str,
    trde_qty_cnd: str,
    stk_cnd: str,
    crd_cnd: str,
    pric_cnd: str,
    stex_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    예상체결등락률상위요청[ka10029] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        mrkt_tp: 시장구분 — 000:전체, 001:코스피, 101:코스닥
        sort_tp: 정렬구분 — 1:상승률, 2:상승폭, 3:보합, 4:하락률, 5:하락폭, 6:체결량, 7:상한, 8:하한
        trde_qty_cnd: 거래량조건 — 0:전체조회, 1;천주이상, 3:3천주, 5:5천주, 10:만주이상, 50:5만주이상, 100:10만주이상
        stk_cnd: 종목조건 — 0:전체조회, 1:관리종목제외, 3:우선주제외, 4:관리종목,우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 11:정리매매종목제외, 12:증50만보기, 13:증60만보기, 14:ETF제외, 15:스팩제외, 16:ETF+ETN제외
        crd_cnd: 신용조건 — 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 5:신용한도초과제외, 7:신용융자E군, 8:신용대주, 9:신용융자전체
        pric_cnd: 가격조건 — 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~5천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상, 10:1만원미만
        stex_tp: 거래소구분 — 1:KRX, 2:NXT 3.통합

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_expected_execution_change_rate_top(
        ...     mrkt_tp='000',
        ...     sort_tp='1',
        ...     trde_qty_cnd='0',
        ...     stk_cnd='0',
        ...     crd_cnd='0',
        ...     pric_cnd='0',
        ...     stex_tp='3',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not sort_tp:
        raise ValueError('sort_tp is required.')
    if not trde_qty_cnd:
        raise ValueError('trde_qty_cnd is required.')
    if not stk_cnd:
        raise ValueError('stk_cnd is required.')
    if not crd_cnd:
        raise ValueError('crd_cnd is required.')
    if not pric_cnd:
        raise ValueError('pric_cnd is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "mrkt_tp": mrkt_tp,  # 시장구분
        "sort_tp": sort_tp,  # 정렬구분
        "trde_qty_cnd": trde_qty_cnd,  # 거래량조건
        "stk_cnd": stk_cnd,  # 종목조건
        "crd_cnd": crd_cnd,  # 신용조건
        "pric_cnd": pric_cnd,  # 가격조건
        "stex_tp": stex_tp,  # 거래소구분
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "exp_cntr_flu_rt_upper": [],
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
        result = get_domestic_expected_execution_change_rate_top(
            mrkt_tp='000',
            sort_tp='1',
            trde_qty_cnd='0',
            stk_cnd='0',
            crd_cnd='0',
            pric_cnd='0',
            stex_tp='3',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
