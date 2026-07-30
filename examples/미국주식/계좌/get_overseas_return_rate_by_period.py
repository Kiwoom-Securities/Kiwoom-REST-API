# ---
# api_id: ust21650
# api_name: 미국주식 기간별 수익률 현황
# category: 미국주식
# sub_category: 계좌
# template: rest
# api_url: /api/us/acnt
# menu_path: 미국주식 > 계좌 > 미국주식 기간별 수익률 현황(ust21650)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ust21650"
API_URL = "/api/us/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "fr_entr": "기간초예수금",
    "fr_dfr_amt": "기간초현금미수금",
    "fr_etc_loana": "기간초기타대여금",
    "fr_fc_entr": "기간초외화예수금",
    "fr_fc_dfr_amt": "기간초외화미수금",
    "fr_fc_etc_loana": "기간초외화기타대여금",
    "fr_frgn_stk_evltv": "기간초해외증권평가금",
    "fr_tot_evltv": "기간초순자산액계",
    "to_entr": "기간말예수금",
    "to_dfr_amt": "기간말현금미수금",
    "to_etc_loana": "기간말기타대여금",
    "to_fc_entr": "기간말외화예수금",
    "to_fc_dfr_amt": "기간말외화미수금",
    "to_fc_etc_loana": "기간말외화기타대여금",
    "to_frgn_stk_evltv": "기간말해외증권평가금",
    "to_tot_evltv": "기간말순자산액계",
    "fc_rcpta": "기간내총외화입금",
    "fc_payma": "기간내총외화출금",
    "chg_rcpta": "기간내외화매도",
    "chg_payma": "기간내외화매수",
    "frgn_stk_inqa": "기간내해외증권입고",
    "frgn_stk_outqa": "기간내해외증권출고",
    "invt_bsamt": "투자원금평잔",
    "evlt_profit": "평가손익",
    "profit_rate": "수익율",
    "io_bsamt": "기간내총입출금고평잔",
    "tern_rt": "회전율"
}


NUMERIC_COLUMNS = (
    '기간내총외화입금',
    '기간내총외화출금',
    '기간내총입출금고평잔',
    '기간말기타대여금',
    '기간말순자산액계',
    '기간말예수금',
    '기간말외화기타대여금',
    '기간말외화미수금',
    '기간말외화예수금',
    '기간말해외증권평가금',
    '기간말현금미수금',
    '기간초기타대여금',
    '기간초순자산액계',
    '기간초예수금',
    '기간초외화기타대여금',
    '기간초외화미수금',
    '기간초외화예수금',
    '기간초해외증권평가금',
    '기간초현금미수금',
    '수익율',
    '투자원금평잔',
    '평가손익',
    '회전율',
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

def get_overseas_return_rate_by_period(
    fr_dt: str,
    to_dt: str,
) -> pd.DataFrame:
    """
    미국주식 기간별 수익률 현황[ust21650] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        fr_dt: 조회시작일자 — YYYYMMDD
        to_dt: 조회종료일자 — YYYYMMDD

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_overseas_return_rate_by_period(
        ...     fr_dt='20260501',
        ...     to_dt='20260507',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not fr_dt:
        raise ValueError('fr_dt is required.')
    if not to_dt:
        raise ValueError('to_dt is required.')

    # 2. 요청 파라미터 바디
    body = {
        "fr_dt": fr_dt,  # 조회시작일자
        "to_dt": to_dt,  # 조회종료일자
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = []
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
        row = {
            key: response_body.get(key)
            for key in COLUMNS
        }
        if row:
            rows.append(row)

        next_cont_yn = response.continuation.cont_yn
        next_key = response.continuation.next_key

        if next_cont_yn != "Y":
            break

        if page + 1 >= MAX_PAGES:
            break

        time.sleep(REQUEST_DELAY_SECONDS)

    # 6. DataFrame 변환
    result = pd.DataFrame(rows).rename(columns=COLUMNS)
    if message_rows:
        message_df = pd.DataFrame(message_rows).rename(columns=MESSAGE_COLUMNS)
        result = pd.concat([message_df, result], axis=1)
    return result


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    try:
        df = get_overseas_return_rate_by_period(
            fr_dt='20260501',
            to_dt='20260507',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
