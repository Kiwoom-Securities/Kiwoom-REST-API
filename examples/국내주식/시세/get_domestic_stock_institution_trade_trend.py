# ---
# api_id: ka10045
# api_name: 종목별기관매매추이요청
# category: 국내주식
# sub_category: 시세
# template: rest
# api_url: /api/dostk/mrkcond
# menu_path: 국내주식 > 시세 > 종목별기관매매추이요청(ka10045)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10045"
API_URL = "/api/dostk/mrkcond"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "stk_orgn_trde_trnsn": "종목별기관매매추이"
}
COLUMNS = {
    "dt": "일자",
    "close_pric": "종가",
    "pre_sig": "대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "trde_qty": "거래량",
    "orgn_dt_acc": "기관기간누적",
    "orgn_daly_nettrde_qty": "기관일별순매매수량",
    "for_dt_acc": "외인기간누적",
    "for_daly_nettrde_qty": "외인일별순매매수량",
    "limit_exh_rt": "한도소진율"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "orgn_prsm_avg_pric": "기관추정평균가",
    "for_prsm_avg_pric": "외인추정평균가"
}


NUMERIC_COLUMNS = (
    '거래량',
    '기관일별순매매수량',
    '기관추정평균가',
    '등락율',
    '외인일별순매매수량',
    '외인추정평균가',
    '종가',
    '한도소진율',
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

def get_domestic_stock_institution_trade_trend(
    stk_cd: str,
    strt_dt: str,
    end_dt: str,
    orgn_prsm_unp_tp: str,
    for_prsm_unp_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    종목별기관매매추이요청[ka10045] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드 — 거래소별 종목코드
            (KRX:039490,NXT:039490_NX,SOR:039490_AL)
        strt_dt: 시작일자 — YYYYMMDD
        end_dt: 종료일자 — YYYYMMDD
        orgn_prsm_unp_tp: 기관추정단가구분 — 1:매수단가, 2:매도단가
        for_prsm_unp_tp: 외인추정단가구분 — 1:매수단가, 2:매도단가

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_stock_institution_trade_trend(
        ...     stk_cd='005930',
        ...     strt_dt='20241007',
        ...     end_dt='20241107',
        ...     orgn_prsm_unp_tp='1',
        ...     for_prsm_unp_tp='1',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')
    if not strt_dt:
        raise ValueError('strt_dt is required.')
    if not end_dt:
        raise ValueError('end_dt is required.')
    if not orgn_prsm_unp_tp:
        raise ValueError('orgn_prsm_unp_tp is required.')
    if not for_prsm_unp_tp:
        raise ValueError('for_prsm_unp_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
        "strt_dt": strt_dt,  # 시작일자
        "end_dt": end_dt,  # 종료일자
        "orgn_prsm_unp_tp": orgn_prsm_unp_tp,  # 기관추정단가구분
        "for_prsm_unp_tp": for_prsm_unp_tp,  # 외인추정단가구분
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "stk_orgn_trde_trnsn": [],
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
    try:
        result = get_domestic_stock_institution_trade_trend(
            stk_cd='005930',
            strt_dt='20241007',
            end_dt='20241107',
            orgn_prsm_unp_tp='1',
            for_prsm_unp_tp='1',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
