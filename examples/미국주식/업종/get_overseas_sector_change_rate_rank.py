# ---
# api_id: usa23100
# api_name: 미국주식 업종별 등락률 상위/하위 조회
# category: 미국주식
# sub_category: 업종
# template: rest
# api_url: /api/us/sect
# menu_path: 미국주식 > 업종 > 미국주식 업종별 등락률 상위/하위 조회(usa23100)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "usa23100"
API_URL = "/api/us/sect"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "result_list": "결과리스트"
}
COLUMNS = {
    "stex_tp": "거래소구분",
    "stk_cd": "종목코드",
    "stk_nm": "한글종목명",
    "stk_enm": "영문종목명",
    "cur_prc": "현재가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "acc_trde_qty": "거래량",
    "sel_bid": "매도호가",
    "buy_bid": "매수호가",
    "open_pric": "시가",
    "high_pric": "고가",
    "low_pric": "저가",
    "cntr_tm": "시간"
}


NUMERIC_COLUMNS = (
    '거래량',
    '고가',
    '등락률',
    '매도호가',
    '매수호가',
    '시가',
    '저가',
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

def get_overseas_sector_change_rate_rank(
    stex_tp: str | None = '0',
    sort_tp: str | None = '1',
    inds_cd: str | None = '000',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 업종별 등락률 상위/하위 조회[usa23100] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stex_tp: 거래소 구분 — 0:전체,1:NY(NYSE),2:NA(AMEX),3:ND(NASDAQ)
        sort_tp: 정렬기준구분 — 1:등락율상위,2:등락율하위
        inds_cd: 업종코드 — 000:전체(기본값), usa10101 참고

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_sector_change_rate_rank(
        ...     stex_tp='0',
        ...     sort_tp='1',
        ...     inds_cd='000',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }
    if stex_tp is not None:
        body["stex_tp"] = stex_tp  # 거래소 구분
    if sort_tp is not None:
        body["sort_tp"] = sort_tp  # 정렬기준구분
    if inds_cd is not None:
        body["inds_cd"] = inds_cd  # 업종코드

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "result_list": [],
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
        result = get_overseas_sector_change_rate_rank(
            stex_tp='0',
            sort_tp='1',
            inds_cd='000',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
