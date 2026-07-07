# ---
# api_id: ka90001
# api_name: 테마그룹별요청
# category: 국내주식
# sub_category: 테마
# template: rest
# api_url: /api/dostk/thme
# menu_path: 국내주식 > 테마 > 테마그룹별요청(ka90001)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka90001"
API_URL = "/api/dostk/thme"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "thema_grp": "테마그룹별"
}
COLUMNS = {
    "thema_grp_cd": "테마그룹코드",
    "thema_nm": "테마명",
    "stk_num": "종목수",
    "flu_sig": "등락기호",
    "flu_rt": "등락율",
    "rising_stk_num": "상승종목수",
    "fall_stk_num": "하락종목수",
    "dt_prft_rt": "기간수익률",
    "main_stk": "주요종목"
}


NUMERIC_COLUMNS = ('등락율',)

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

def get_domestic_theme_groups(
    qry_tp: str,
    date_tp: str,
    flu_pl_amt_tp: str,
    stex_tp: str,
    stk_cd: str | None = '',
    thema_nm: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    테마그룹별요청[ka90001] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        qry_tp: 0:전체검색, 1:테마검색, 2:종목검색
        date_tp: n일전 (1일 ~ 99일 날짜입력)
        flu_pl_amt_tp: 1:상위기간수익률, 2:하위기간수익률, 3:상위등락률, 4:하위등락률
        stex_tp: 1:KRX, 2:NXT 3.통합
        stk_cd: 검색하려는 종목코드
        thema_nm: 검색하려는 테마명

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_theme_groups(
        ...     qry_tp='0',
        ...     date_tp='10',
        ...     flu_pl_amt_tp='1',
        ...     stex_tp='1',
        ...     stk_cd='',
        ...     thema_nm='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not qry_tp:
        raise ValueError('qry_tp is required.')
    if not date_tp:
        raise ValueError('date_tp is required.')
    if not flu_pl_amt_tp:
        raise ValueError('flu_pl_amt_tp is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "qry_tp": qry_tp,
        "date_tp": date_tp,
        "flu_pl_amt_tp": flu_pl_amt_tp,
        "stex_tp": stex_tp,
    }
    if stk_cd is not None:
        body["stk_cd"] = stk_cd
    if thema_nm is not None:
        body["thema_nm"] = thema_nm

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "thema_grp": [],
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
    result = get_domestic_theme_groups(
        qry_tp='0',
        date_tp='10',
        flu_pl_amt_tp='1',
        stex_tp='1',
        stk_cd='',
        thema_nm='',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
