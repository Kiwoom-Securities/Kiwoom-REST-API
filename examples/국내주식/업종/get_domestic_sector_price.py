# ---
# api_id: ka20001
# api_name: 업종현재가요청
# category: 국내주식
# sub_category: 업종
# template: rest
# api_url: /api/dostk/sect
# menu_path: 국내주식 > 업종 > 업종현재가요청(ka20001)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client

API_ID = "ka20001"
API_URL = "/api/dostk/sect"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "inds_cur_prc_tm": "업종현재가_시간별"
}
COLUMNS = {
    "tm_n": "시간n",
    "cur_prc_n": "현재가n",
    "pred_pre_sig_n": "전일대비기호n",
    "pred_pre_n": "전일대비n",
    "flu_rt_n": "등락률n",
    "trde_qty_n": "거래량n",
    "acc_trde_qty_n": "누적거래량n"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "cur_prc": "현재가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락률",
    "trde_qty": "거래량",
    "trde_prica": "거래대금",
    "trde_frmatn_stk_num": "거래형성종목수",
    "trde_frmatn_rt": "거래형성비율",
    "open_pric": "시가",
    "high_pric": "고가",
    "low_pric": "저가",
    "upl": "상한",
    "rising": "상승",
    "stdns": "보합",
    "fall": "하락",
    "lst": "하한",
    "52wk_hgst_pric": "52주최고가",
    "52wk_hgst_pric_dt": "52주최고가일",
    "52wk_hgst_pric_pre_rt": "52주최고가대비율",
    "52wk_lwst_pric": "52주최저가",
    "52wk_lwst_pric_dt": "52주최저가일",
    "52wk_lwst_pric_pre_rt": "52주최저가대비율"
}


NUMERIC_COLUMNS = (
    '52주최고가',
    '52주최고가대비율',
    '52주최고가일',
    '52주최저가',
    '52주최저가대비율',
    '52주최저가일',
    '거래대금',
    '거래량',
    '거래량n',
    '거래형성비율',
    '고가',
    '누적거래량n',
    '등락률',
    '등락률n',
    '시가',
    '저가',
    '현재가',
    '현재가n',
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

def get_domestic_sector_price(
    mrkt_tp: str,
    inds_cd: str,
) -> dict[str, pd.DataFrame]:
    """
    업종현재가요청[ka20001] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        mrkt_tp: 0:코스피, 1:코스닥, 2:코스피200
        inds_cd: 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_sector_price(
        ...     mrkt_tp='0',
        ...     inds_cd='001',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not inds_cd:
        raise ValueError('inds_cd is required.')

    # 2. 요청 파라미터 바디
    body = {
        "mrkt_tp": mrkt_tp,
        "inds_cd": inds_cd,
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "inds_cur_prc_tm": [],
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
    result = get_domestic_sector_price(
        mrkt_tp='0',
        inds_cd='001',
    )
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
