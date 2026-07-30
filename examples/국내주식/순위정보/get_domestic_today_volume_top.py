# ---
# api_id: ka10030
# api_name: 당일거래량상위요청
# category: 국내주식
# sub_category: 순위정보
# template: rest
# api_url: /api/dostk/rkinfo
# menu_path: 국내주식 > 순위정보 > 당일거래량상위요청(ka10030)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10030"
API_URL = "/api/dostk/rkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "tdy_trde_qty_upper": "당일거래량상위"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "cur_prc": "현재가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "trde_qty": "거래량",
    "pred_rt": "전일비",
    "trde_tern_rt": "거래회전율",
    "trde_amt": "거래금액",
    "opmr_trde_qty": "장중거래량",
    "opmr_pred_rt": "장중전일비",
    "opmr_trde_rt": "장중거래회전율",
    "opmr_trde_amt": "장중거래금액",
    "af_mkrt_trde_qty": "장후거래량",
    "af_mkrt_pred_rt": "장후전일비",
    "af_mkrt_trde_rt": "장후거래회전율",
    "af_mkrt_trde_amt": "장후거래금액",
    "bf_mkrt_trde_qty": "장전거래량",
    "bf_mkrt_pred_rt": "장전전일비",
    "bf_mkrt_trde_rt": "장전거래회전율",
    "bf_mkrt_trde_amt": "장전거래금액"
}


NUMERIC_COLUMNS = (
    '거래금액',
    '거래량',
    '거래회전율',
    '등락률',
    '장전거래금액',
    '장전거래량',
    '장전거래회전율',
    '장중거래금액',
    '장중거래량',
    '장중거래회전율',
    '장후거래금액',
    '장후거래량',
    '장후거래회전율',
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

def get_domestic_today_volume_top(
    mrkt_tp: str,
    sort_tp: str,
    mang_stk_incls: str,
    crd_tp: str,
    trde_qty_tp: str,
    pric_tp: str,
    trde_prica_tp: str,
    mrkt_open_tp: str,
    stex_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    당일거래량상위요청[ka10030] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        mrkt_tp: 시장구분 — 000:전체, 001:코스피, 101:코스닥
        sort_tp: 정렬구분 — 1:거래량, 2:거래회전율, 3:거래대금
        mang_stk_incls: 관리종목포함 — 0:관리종목 포함, 1:관리종목 미포함, 3:우선주제외, 11:정리매매종목제외, 4:관리종목, 우선주제외, 5:증100제외, 6:증100마나보기, 13:증60만보기, 12:증50만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 14:ETF제외, 15:스팩제외, 16:ETF+ETN제외
        crd_tp: 신용구분 — 0:전체조회, 9:신용융자전체, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 8:신용대주
        trde_qty_tp: 거래량구분 — 0:전체조회, 5:5천주이상, 10:1만주이상, 50:5만주이상, 100:10만주이상, 200:20만주이상, 300:30만주이상, 500:500만주이상, 1000:백만주이상
        pric_tp: 가격구분 — 0:전체조회, 1:1천원미만, 2:1천원이상, 3:1천원~2천원, 4:2천원~5천원, 5:5천원이상, 6:5천원~1만원, 10:1만원미만, 7:1만원이상, 8:5만원이상, 9:10만원이상
        trde_prica_tp: 거래대금구분 — 0:전체조회, 1:1천만원이상, 3:3천만원이상, 4:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상
        mrkt_open_tp: 장운영구분 — 0:전체조회, 1:장중, 2:장전시간외, 3:장후시간외
        stex_tp: 거래소구분 — 1:KRX, 2:NXT 3.통합

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_today_volume_top(
        ...     mrkt_tp='000',
        ...     sort_tp='1',
        ...     mang_stk_incls='0',
        ...     crd_tp='0',
        ...     trde_qty_tp='0',
        ...     pric_tp='0',
        ...     trde_prica_tp='0',
        ...     mrkt_open_tp='0',
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
    if not mang_stk_incls:
        raise ValueError('mang_stk_incls is required.')
    if not crd_tp:
        raise ValueError('crd_tp is required.')
    if not trde_qty_tp:
        raise ValueError('trde_qty_tp is required.')
    if not pric_tp:
        raise ValueError('pric_tp is required.')
    if not trde_prica_tp:
        raise ValueError('trde_prica_tp is required.')
    if not mrkt_open_tp:
        raise ValueError('mrkt_open_tp is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "mrkt_tp": mrkt_tp,  # 시장구분
        "sort_tp": sort_tp,  # 정렬구분
        "mang_stk_incls": mang_stk_incls,  # 관리종목포함
        "crd_tp": crd_tp,  # 신용구분
        "trde_qty_tp": trde_qty_tp,  # 거래량구분
        "pric_tp": pric_tp,  # 가격구분
        "trde_prica_tp": trde_prica_tp,  # 거래대금구분
        "mrkt_open_tp": mrkt_open_tp,  # 장운영구분
        "stex_tp": stex_tp,  # 거래소구분
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "tdy_trde_qty_upper": [],
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
        result = get_domestic_today_volume_top(
            mrkt_tp='000',
            sort_tp='1',
            mang_stk_incls='0',
            crd_tp='0',
            trde_qty_tp='0',
            pric_tp='0',
            trde_prica_tp='0',
            mrkt_open_tp='0',
            stex_tp='3',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
