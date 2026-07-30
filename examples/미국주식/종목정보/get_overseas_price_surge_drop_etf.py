# ---
# api_id: usa20931
# api_name: 미국주식 가격급등락(ETF)
# category: 미국주식
# sub_category: 종목정보
# template: rest
# api_url: /api/us/stkinfo
# menu_path: 미국주식 > 종목정보 > 미국주식 가격급등락(ETF)(usa20931)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "usa20931"
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
    "stk_nm": "종목명한글",
    "stk_enm": "영문종목명",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "base_pric": "기준가",
    "cur_prc": "현재가",
    "base_pre": "기준대비",
    "acc_trde_qty": "거래량",
    "sdnin_rt": "급증률"
}


NUMERIC_COLUMNS = (
    '거래량',
    '기준가',
    '등락률',
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

def get_overseas_price_surge_drop_etf(
    stex_tp: str | None = '0',
    etf_cat1: str | None = '',
    etf_cat2: str | None = '',
    stk_cnd: str | None = '1',
    flu_tp: str | None = '2',
    tm_tp: str | None = '1',
    tm: str | None = '0',
    pric_cnd: str | None = '0',
    trde_qty_tp: str | None = '0',
    trde_prica_cnd: str | None = '0',
) -> dict[str, pd.DataFrame]:
    """
    미국주식 가격급등락(ETF)[usa20931] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stex_tp: 거래소구분 — 0:전체,1:NYSE,2:NASDAQ,3:AMEX
        etf_cat1: ETF카테고리코드1 — ETF 대카테고리코드 (ETF이고 대분류일 경우 사용), usa10105 cate1 속성 참고
        etf_cat2: ETF카테고리코드2 — ETF 중카테고리코드 (ETF이고 중분류일 경우 사용), usa10105 cate2 속성 참고
        stk_cnd: 종목조건 — 0:전체,1:증100%,2:증50%
        flu_tp: 급등.급락 구분 — 1:급등,2:급락
        tm_tp: 분전, 전일 구분 — 1:분전,2:일전,3:지정일
        tm: 분,일자 설정 — XX분전(최대30) or XX일전(최대30) or  tm_tp :3 입력 시, 기간(1:1일전,2:5일전,3:1개월전,4:3개월전,5:6개월전,6:연중,7:1년전,8:3년전,9:5년전)
        pric_cnd: 가격조건 — 0:전체,1:5미만,2:10미만,3:10이상,4:10~20,5:20~50,6:50이상,7:50~100,8:100미만,9:100이상,10:500이상
        trde_qty_tp: 거래량조건 — 0:전체, 10,15,20,30,50,100,300,500(1만단위) 이상 (ex. 50: 50만 이상)
        trde_prica_cnd: 거래대금조건 — 0:전체 1,3,5,10,30,50,100,300,500,1000,3000,5000(USD, 1만단위) 이상 (ex. 50: USD 50만 이상)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_overseas_price_surge_drop_etf(
        ...     stex_tp='0',
        ...     etf_cat1='',
        ...     etf_cat2='',
        ...     stk_cnd='1',
        ...     flu_tp='2',
        ...     tm_tp='1',
        ...     tm='0',
        ...     pric_cnd='0',
        ...     trde_qty_tp='0',
        ...     trde_prica_cnd='0',
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
    if etf_cat1 is not None:
        body["etf_cat1"] = etf_cat1  # ETF카테고리코드1
    if etf_cat2 is not None:
        body["etf_cat2"] = etf_cat2  # ETF카테고리코드2
    if stk_cnd is not None:
        body["stk_cnd"] = stk_cnd  # 종목조건
    if flu_tp is not None:
        body["flu_tp"] = flu_tp  # 급등.급락 구분
    if tm_tp is not None:
        body["tm_tp"] = tm_tp  # 분전, 전일 구분
    if tm is not None:
        body["tm"] = tm  # 분,일자 설정
    if pric_cnd is not None:
        body["pric_cnd"] = pric_cnd  # 가격조건
    if trde_qty_tp is not None:
        body["trde_qty_tp"] = trde_qty_tp  # 거래량조건
    if trde_prica_cnd is not None:
        body["trde_prica_cnd"] = trde_prica_cnd  # 거래대금조건

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
        result = get_overseas_price_surge_drop_etf(
            stex_tp='0',
            etf_cat1='',
            etf_cat2='',
            stk_cnd='1',
            flu_tp='2',
            tm_tp='1',
            tm='0',
            pric_cnd='0',
            trde_qty_tp='0',
            trde_prica_cnd='0',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
