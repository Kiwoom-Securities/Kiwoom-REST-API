# ---
# api_id: ka10062
# api_name: 동일순매매순위요청
# category: 국내주식
# sub_category: 순위정보
# template: rest
# api_url: /api/dostk/rkinfo
# menu_path: 국내주식 > 순위정보 > 동일순매매순위요청(ka10062)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka10062"
API_URL = "/api/dostk/rkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "eql_nettrde_rank": "동일순매매순위"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "rank": "순위",
    "stk_nm": "종목명",
    "cur_prc": "현재가",
    "pre_sig": "대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "acc_trde_qty": "누적거래량",
    "orgn_nettrde_qty": "기관순매매수량",
    "orgn_nettrde_amt": "기관순매매금액",
    "orgn_nettrde_avg_pric": "기관순매매평균가",
    "for_nettrde_qty": "외인순매매수량",
    "for_nettrde_amt": "외인순매매금액",
    "for_nettrde_avg_pric": "외인순매매평균가",
    "nettrde_qty": "순매매수량",
    "nettrde_amt": "순매매금액"
}


NUMERIC_COLUMNS = (
    '기관순매매금액',
    '기관순매매수량',
    '기관순매매평균가',
    '누적거래량',
    '등락율',
    '순매매금액',
    '순매매수량',
    '외인순매매금액',
    '외인순매매수량',
    '외인순매매평균가',
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

def get_domestic_same_direction_net_trade_rank(
    strt_dt: str,
    mrkt_tp: str,
    trde_tp: str,
    sort_cnd: str,
    unit_tp: str,
    stex_tp: str,
    end_dt: str | None = '20241107',
) -> dict[str, pd.DataFrame]:
    """
    동일순매매순위요청[ka10062] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        strt_dt: YYYYMMDD
            (연도4자리, 월 2자리, 일 2자리 형식)
        mrkt_tp: 000:전체, 001: 코스피, 101:코스닥
        trde_tp: 1:순매수, 2:순매도
        sort_cnd: 1:수량, 2:금액
        unit_tp: 1:단주, 1000:천주
        stex_tp: 1:KRX, 2:NXT 3.통합
        end_dt: YYYYMMDD
            (연도4자리, 월 2자리, 일 2자리 형식)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_same_direction_net_trade_rank(
        ...     strt_dt='20241106',
        ...     mrkt_tp='000',
        ...     trde_tp='1',
        ...     sort_cnd='1',
        ...     unit_tp='1',
        ...     stex_tp='3',
        ...     end_dt='20241107',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not strt_dt:
        raise ValueError('strt_dt is required.')
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not trde_tp:
        raise ValueError('trde_tp is required.')
    if not sort_cnd:
        raise ValueError('sort_cnd is required.')
    if not unit_tp:
        raise ValueError('unit_tp is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "strt_dt": strt_dt,
        "mrkt_tp": mrkt_tp,
        "trde_tp": trde_tp,
        "sort_cnd": sort_cnd,
        "unit_tp": unit_tp,
        "stex_tp": stex_tp,
    }
    if end_dt is not None:
        body["end_dt"] = end_dt

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "eql_nettrde_rank": [],
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
    result = get_domestic_same_direction_net_trade_rank(
        strt_dt='20241106',
        mrkt_tp='000',
        trde_tp='1',
        sort_cnd='1',
        unit_tp='1',
        stex_tp='3',
        end_dt='20241107',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
