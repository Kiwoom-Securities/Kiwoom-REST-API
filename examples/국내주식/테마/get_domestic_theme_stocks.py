# ---
# api_id: ka90002
# api_name: 테마구성종목요청
# category: 국내주식
# sub_category: 테마
# template: rest
# api_url: /api/dostk/thme
# menu_path: 국내주식 > 테마 > 테마구성종목요청(ka90002)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka90002"
API_URL = "/api/dostk/thme"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "thema_comp_stk": "테마구성종목"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "cur_prc": "현재가",
    "flu_sig": "등락기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "acc_trde_qty": "누적거래량",
    "sel_bid": "매도호가",
    "sel_req": "매도잔량",
    "buy_bid": "매수호가",
    "buy_req": "매수잔량",
    "dt_prft_rt_n": "기간수익률n"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "flu_rt": "등락률",
    "dt_prft_rt": "기간수익률"
}


NUMERIC_COLUMNS = (
    '누적거래량',
    '등락률',
    '등락율',
    '매도호가',
    '매수호가',
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

def get_domestic_theme_stocks(
    thema_grp_cd: str,
    stex_tp: str,
    date_tp: str | None = '2',
) -> dict[str, pd.DataFrame]:
    """
    테마구성종목요청[ka90002] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        thema_grp_cd: 테마그룹코드 번호
        stex_tp: 1:KRX, 2:NXT 3.통합
        date_tp: 1일 ~ 99일 날짜입력

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_theme_stocks(
        ...     thema_grp_cd='100',
        ...     stex_tp='1',
        ...     date_tp='2',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not thema_grp_cd:
        raise ValueError('thema_grp_cd is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "thema_grp_cd": thema_grp_cd,
        "stex_tp": stex_tp,
    }
    if date_tp is not None:
        body["date_tp"] = date_tp

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "thema_comp_stk": [],
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
        summary_rows.append({
            key: response_body.get(key)
            for key in SUMMARY_COLUMNS
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
    result = {
        SUMMARY_KEY: pd.DataFrame(summary_rows).rename(columns=SUMMARY_COLUMNS),
        **result,
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
    result = get_domestic_theme_stocks(
        thema_grp_cd='100',
        stex_tp='1',
        date_tp='2',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
