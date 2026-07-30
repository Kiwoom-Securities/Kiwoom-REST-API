# ---
# api_id: ka10051
# api_name: 업종별투자자순매수요청
# category: 국내주식
# sub_category: 업종
# template: rest
# api_url: /api/dostk/sect
# menu_path: 국내주식 > 업종 > 업종별투자자순매수요청(ka10051)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka10051"
API_URL = "/api/dostk/sect"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "inds_netprps": "업종별순매수"
}
COLUMNS = {
    "inds_cd": "업종코드",
    "inds_nm": "업종명",
    "cur_prc": "현재가",
    "pre_smbol": "대비부호",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "trde_qty": "거래량",
    "sc_netprps": "증권순매수",
    "insrnc_netprps": "보험순매수",
    "invtrt_netprps": "투신순매수",
    "bank_netprps": "은행순매수",
    "jnsinkm_netprps": "종신금순매수",
    "endw_netprps": "기금순매수",
    "etc_corp_netprps": "기타법인순매수",
    "ind_netprps": "개인순매수",
    "frgnr_netprps": "외국인순매수",
    "native_trmt_frgnr_netprps": "내국인대우외국인순매수",
    "natn_netprps": "국가순매수",
    "samo_fund_netprps": "사모펀드순매수",
    "orgn_netprps": "기관계순매수"
}


NUMERIC_COLUMNS = (
    '거래량',
    '국가순매수',
    '기금순매수',
    '등락율',
    '종신금순매수',
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

def get_domestic_sector_investor_net_buy(
    mrkt_tp: str,
    amt_qty_tp: str,
    stex_tp: str,
    base_dt: str | None = '20241107',
) -> dict[str, pd.DataFrame]:
    """
    업종별투자자순매수요청[ka10051] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        mrkt_tp: 시장구분 — 코스피:0, 코스닥:1
        amt_qty_tp: 금액수량구분 — 금액:0, 수량:1
        stex_tp: 거래소구분 — 1:KRX, 2:NXT, 3:통합
        base_dt: 기준일자 — YYYYMMDD

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_sector_investor_net_buy(
        ...     mrkt_tp='0',
        ...     amt_qty_tp='0',
        ...     stex_tp='3',
        ...     base_dt='20241107',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not amt_qty_tp:
        raise ValueError('amt_qty_tp is required.')
    if not stex_tp:
        raise ValueError('stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "mrkt_tp": mrkt_tp,  # 시장구분
        "amt_qty_tp": amt_qty_tp,  # 금액수량구분
        "stex_tp": stex_tp,  # 거래소구분
    }
    if base_dt is not None:
        body["base_dt"] = base_dt  # 기준일자

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "inds_netprps": [],
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
        result = get_domestic_sector_investor_net_buy(
            mrkt_tp='0',
            amt_qty_tp='0',
            stex_tp='3',
            base_dt='20241107',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
