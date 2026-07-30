# ---
# api_id: ka30004
# api_name: ELW괴리율요청
# category: 국내주식
# sub_category: ELW
# template: rest
# api_url: /api/dostk/elw
# menu_path: 국내주식 > ELW > ELW괴리율요청(ka30004)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka30004"
API_URL = "/api/dostk/elw"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "elwdispty_rt": "ELW괴리율"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "isscomp_nm": "발행사명",
    "sqnc": "회차",
    "base_aset_nm": "기초자산명",
    "rght_tp": "권리구분",
    "dispty_rt": "괴리율",
    "basis": "베이시스",
    "srvive_dys": "잔존일수",
    "theory_pric": "이론가",
    "cur_prc": "현재가",
    "pre_tp": "대비구분",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "trde_qty": "거래량",
    "stk_nm": "종목명"
}


NUMERIC_COLUMNS = (
    '거래량',
    '괴리율',
    '등락율',
    '이론가',
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

def get_domestic_elw_disparity_rate(
    isscomp_cd: str,
    bsis_aset_cd: str,
    rght_tp: str,
    lpcd: str,
    trde_end_elwskip: str,
) -> dict[str, pd.DataFrame]:
    """
    ELW괴리율요청[ka30004] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        isscomp_cd: 발행사코드 — 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17
        bsis_aset_cd: 기초자산코드 — 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200..
        rght_tp: 권리구분 — 000: 전체, 001: 콜, 002: 풋, 003: DC, 004: DP, 005: EX, 006: 조기종료콜, 007: 조기종료풋
        lpcd: LP코드 — 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17
        trde_end_elwskip: 거래종료ELW제외 — 1:거래종료ELW제외, 0:거래종료ELW포함

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_elw_disparity_rate(
        ...     isscomp_cd='000000000000',
        ...     bsis_aset_cd='000000000000',
        ...     rght_tp='000',
        ...     lpcd='000000000000',
        ...     trde_end_elwskip='0',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not isscomp_cd:
        raise ValueError('isscomp_cd is required.')
    if not bsis_aset_cd:
        raise ValueError('bsis_aset_cd is required.')
    if not rght_tp:
        raise ValueError('rght_tp is required.')
    if not lpcd:
        raise ValueError('lpcd is required.')
    if not trde_end_elwskip:
        raise ValueError('trde_end_elwskip is required.')

    # 2. 요청 파라미터 바디
    body = {
        "isscomp_cd": isscomp_cd,  # 발행사코드
        "bsis_aset_cd": bsis_aset_cd,  # 기초자산코드
        "rght_tp": rght_tp,  # 권리구분
        "lpcd": lpcd,  # LP코드
        "trde_end_elwskip": trde_end_elwskip,  # 거래종료ELW제외
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "elwdispty_rt": [],
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
        result = get_domestic_elw_disparity_rate(
            isscomp_cd='000000000000',
            bsis_aset_cd='000000000000',
            rght_tp='000',
            lpcd='000000000000',
            trde_end_elwskip='0',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
