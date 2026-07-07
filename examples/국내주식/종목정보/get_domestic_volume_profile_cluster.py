# ---
# api_id: ka10025
# api_name: 매물대집중요청
# category: 국내주식
# sub_category: 종목정보
# template: rest
# api_url: /api/dostk/stkinfo
# menu_path: 국내주식 > 종목정보 > 매물대집중요청(ka10025)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka10025"
API_URL = "/api/dostk/stkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "prps_cnctr": "매물대집중"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "cur_prc": "현재가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "now_trde_qty": "현재거래량",
    "pric_strt": "가격대시작",
    "pric_end": "가격대끝",
    "prps_qty": "매물량",
    "prps_rt": "매물비"
}


NUMERIC_COLUMNS = (
    '가격대끝',
    '가격대시작',
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

def get_domestic_volume_profile_cluster(
    mrkt_tp: str,
    prps_cnctr_rt: str,
    cur_prc_entry: str,
    prpscnt: str,
    cycle_tp: str,
    stex_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    매물대집중요청[ka10025] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        mrkt_tp: 000:전체, 001:코스피, 101:코스닥
        prps_cnctr_rt: 0~100 입력
        cur_prc_entry: 0:현재가 매물대 진입 포함안함, 1:현재가 매물대 진입포함
        prpscnt: 숫자입력
        cycle_tp: 50:50일, 100:100일, 150:150일, 200:200일, 250:250일, 300:300일
        stex_tp: 1:KRX, 2:NXT 3.통합

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_volume_profile_cluster(
        ...     mrkt_tp='000',
        ...     prps_cnctr_rt='50',
        ...     cur_prc_entry='0',
        ...     prpscnt='10',
        ...     cycle_tp='50',
        ...     stex_tp='3',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not prps_cnctr_rt:
        raise ValueError('prps_cnctr_rt is required.')
    if not cur_prc_entry:
        raise ValueError('cur_prc_entry is required.')
    if not prpscnt:
        raise ValueError('prpscnt is required.')
    if not cycle_tp:
        raise ValueError('cycle_tp is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "mrkt_tp": mrkt_tp,
        "prps_cnctr_rt": prps_cnctr_rt,
        "cur_prc_entry": cur_prc_entry,
        "prpscnt": prpscnt,
        "cycle_tp": cycle_tp,
        "stex_tp": stex_tp,
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "prps_cnctr": [],
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
    result = get_domestic_volume_profile_cluster(
        mrkt_tp='000',
        prps_cnctr_rt='50',
        cur_prc_entry='0',
        prpscnt='10',
        cycle_tp='50',
        stex_tp='3',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
