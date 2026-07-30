# ---
# api_id: ka10052
# api_name: 거래원순간거래량요청
# category: 국내주식
# sub_category: 종목정보
# template: rest
# api_url: /api/dostk/stkinfo
# menu_path: 국내주식 > 종목정보 > 거래원순간거래량요청(ka10052)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10052"
API_URL = "/api/dostk/stkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "trde_ori_mont_trde_qty": "거래원순간거래량"
}
COLUMNS = {
    "tm": "시간",
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "trde_ori_nm": "거래원명",
    "tp": "구분",
    "mont_trde_qty": "순간거래량",
    "acc_netprps": "누적순매수",
    "cur_prc": "현재가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락율"
}


NUMERIC_COLUMNS = (
    '등락율',
    '순간거래량',
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

def get_domestic_broker_instant_volume(
    mmcm_cd: str,
    mrkt_tp: str,
    qty_tp: str,
    pric_tp: str,
    stex_tp: str,
    stk_cd: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    거래원순간거래량요청[ka10052] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        mmcm_cd: 회원사코드 — 회원사 코드는 ka10102 조회
        mrkt_tp: 시장구분 — 0:전체, 1:코스피, 2:코스닥, 3:종목
        qty_tp: 수량구분 — 0:전체, 1:1000주, 2:2000주, 3:, 5:, 10:10000주, 30: 30000주, 50: 50000주, 100: 100000주
        pric_tp: 가격구분 — 0:전체, 1:1천원 미만, 8:1천원 이상, 2:1천원 ~ 2천원, 3:2천원 ~ 5천원, 4:5천원 ~ 1만원, 5:1만원 이상
        stex_tp: 거래소구분 — 1:KRX, 2:NXT 3.통합
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_broker_instant_volume(
        ...     mmcm_cd='888',
        ...     mrkt_tp='0',
        ...     qty_tp='0',
        ...     pric_tp='0',
        ...     stex_tp='3',
        ...     stk_cd='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not mmcm_cd:
        raise ValueError('mmcm_cd is required.')
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not qty_tp:
        raise ValueError('qty_tp is required.')
    if not pric_tp:
        raise ValueError('pric_tp is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "mmcm_cd": mmcm_cd,  # 회원사코드
        "mrkt_tp": mrkt_tp,  # 시장구분
        "qty_tp": qty_tp,  # 수량구분
        "pric_tp": pric_tp,  # 가격구분
        "stex_tp": stex_tp,  # 거래소구분
    }
    if stk_cd is not None:
        body["stk_cd"] = stk_cd  # 종목코드

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "trde_ori_mont_trde_qty": [],
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
        result = get_domestic_broker_instant_volume(
            mmcm_cd='888',
            mrkt_tp='0',
            qty_tp='0',
            pric_tp='0',
            stex_tp='3',
            stk_cd='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
