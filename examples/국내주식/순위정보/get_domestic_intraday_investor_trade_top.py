# ---
# api_id: ka10065
# api_name: 장중투자자별매매상위요청
# category: 국내주식
# sub_category: 순위정보
# template: rest
# api_url: /api/dostk/rkinfo
# menu_path: 국내주식 > 순위정보 > 장중투자자별매매상위요청(ka10065)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10065"
API_URL = "/api/dostk/rkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "opmr_invsr_trde_upper": "장중투자자별매매상위"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "sel_qty": "매도금액/매도량",
    "buy_qty": "매수금액/매수량",
    "netslmt": "순매수/순매도"
}


NUMERIC_COLUMNS = (
    '매도금액/매도량',
    '매수금액/매수량',
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

def get_domestic_intraday_investor_trade_top(
    trde_tp: str,
    mrkt_tp: str,
    orgn_tp: str,
    amt_qty_tp: str | None = '1',
) -> dict[str, pd.DataFrame]:
    """
    장중투자자별매매상위요청[ka10065] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        trde_tp: 매매구분 — 1:순매수, 2:순매도
        mrkt_tp: 시장구분 — 000:전체, 001:코스피, 101:코스닥
        orgn_tp: 기관구분 — 9000:외국인, 9100:외국계, 1000:금융투자, 3000:투신, 5000:기타금융, 4000:은행, 2000:보험, 6000:연기금, 7000:국가, 7100:기타법인, 9999:기관계
        amt_qty_tp: 금액수량구분 — 1:금액, 2:수량

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_intraday_investor_trade_top(
        ...     trde_tp='1',
        ...     mrkt_tp='000',
        ...     orgn_tp='9000',
        ...     amt_qty_tp='1',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not trde_tp:
        raise ValueError('trde_tp is required.')
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not orgn_tp:
        raise ValueError('orgn_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "trde_tp": trde_tp,  # 매매구분
        "mrkt_tp": mrkt_tp,  # 시장구분
        "orgn_tp": orgn_tp,  # 기관구분
    }
    if amt_qty_tp is not None:
        body["amt_qty_tp"] = amt_qty_tp  # 금액수량구분

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "opmr_invsr_trde_upper": [],
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
        result = get_domestic_intraday_investor_trade_top(
            trde_tp='1',
            mrkt_tp='000',
            orgn_tp='9000',
            amt_qty_tp='1',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
