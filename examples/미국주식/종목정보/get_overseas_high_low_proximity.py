# ---
# api_id: usa20970
# api_name: 미국주식 고가/저가 접근(주식/업종)
# category: 미국주식
# sub_category: 종목정보
# template: rest
# api_url: /api/us/stkinfo
# menu_path: 미국주식 > 종목정보 > 미국주식 고가/저가 접근(주식/업종)(usa20970)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "usa20970"
API_URL = "/api/us/stkinfo"
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
    "mgn_type": "증거금률",
    "stex_tp": "거래소구분",
    "stk_cd": "종목코드",
    "stk_nm": "종목명",
    "stk_enm": "종목영문명",
    "cur_prc": "현재가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "acc_trde_qty": "거래량",
    "sel_bid": "매도호가",
    "buy_bid": "매수호가",
    "high_pric": "당일고가",
    "low_pric": "당일저가"
}


NUMERIC_COLUMNS = (
    '거래량',
    '당일고가',
    '당일저가',
    '등락률',
    '매도호가',
    '매수호가',
    '증거금률',
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

def get_overseas_high_low_proximity(
    stex_tp: str | None = '0',
    inds_cd: str | None = '',
    stk_tp: str | None = '0',
    high_low_tp: str | None = '1',
    alacc_rt: str | None = '0.5',
    stk_cnd: str | None = '0',
    pric_cnd_st: str | None = '',
    pric_cnd_ed: str | None = '',
    trde_pric_cnd_st: str | None = '0',
    trde_qty_cnd_fr: str | None = '0',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 고가/저가 접근(주식/업종)[usa20970] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stex_tp: 거래소구분 — 0:전체,1:NYSE,2:AMEX,3:NASDAQ
        inds_cd: 업종코드 — 000:전체, usa10101 API 참고, stk_tp(종목구분) 1일 경우
        stk_tp: 종목구분 — 0:전체,1:주식
        high_low_tp: 고가,저가구분 — 1:고가,2:저가
        alacc_rt: 근접률 — 0.5:0.5%, 1.0:1.0%, 1.5:1.5%, 2.0:2.0%, 2.5:2.5%, 3.5:3.5%
        stk_cnd: 종목조건 — 0:전체,1:증100%,2:증50%
        pric_cnd_st: 가격조건 시작 — USD, 가격조건 끝으로만 조회할 경우 0
        pric_cnd_ed: 가격조건 끝 — USD, 가격조건 시작으로만 조회할 경우 0
        trde_pric_cnd_st: 거래대금조건 — 0:전체 1,3,5,10,30,50,100,300,500,1000,3000,5000(USD, 1만단위) 이상 (ex. 50: USD 50만 이상)
        trde_qty_cnd_fr: 거래량조건 — 0:전체 10,15,20,30,50,100,300,500(1만단위) 이상 (ex. 50: 50만 이상)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_high_low_proximity(
        ...     stex_tp='0',
        ...     inds_cd='',
        ...     stk_tp='0',
        ...     high_low_tp='1',
        ...     alacc_rt='0.5',
        ...     stk_cnd='0',
        ...     pric_cnd_st='',
        ...     pric_cnd_ed='',
        ...     trde_pric_cnd_st='0',
        ...     trde_qty_cnd_fr='0',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }
    if stex_tp is not None:
        body["stex_tp"] = stex_tp  # 거래소구분
    if inds_cd is not None:
        body["inds_cd"] = inds_cd  # 업종코드
    if stk_tp is not None:
        body["stk_tp"] = stk_tp  # 종목구분
    if high_low_tp is not None:
        body["high_low_tp"] = high_low_tp  # 고가,저가구분
    if alacc_rt is not None:
        body["alacc_rt"] = alacc_rt  # 근접률
    if stk_cnd is not None:
        body["stk_cnd"] = stk_cnd  # 종목조건
    if pric_cnd_st is not None:
        body["pric_cnd_st"] = pric_cnd_st  # 가격조건 시작
    if pric_cnd_ed is not None:
        body["pric_cnd_ed"] = pric_cnd_ed  # 가격조건 끝
    if trde_pric_cnd_st is not None:
        body["trde_pric_cnd_st"] = trde_pric_cnd_st  # 거래대금조건
    if trde_qty_cnd_fr is not None:
        body["trde_qty_cnd_fr"] = trde_qty_cnd_fr  # 거래량조건

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
        result = get_overseas_high_low_proximity(
            stex_tp='0',
            inds_cd='',
            stk_tp='0',
            high_low_tp='1',
            alacc_rt='0.5',
            stk_cnd='0',
            pric_cnd_st='',
            pric_cnd_ed='',
            trde_pric_cnd_st='0',
            trde_qty_cnd_fr='0',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
