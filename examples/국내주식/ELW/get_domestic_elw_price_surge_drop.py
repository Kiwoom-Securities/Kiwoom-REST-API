# ---
# api_id: ka30001
# api_name: ELW가격급등락요청
# category: 국내주식
# sub_category: ELW
# template: rest
# api_url: /api/dostk/elw
# menu_path: 국내주식 > ELW > ELW가격급등락요청(ka30001)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka30001"
API_URL = "/api/dostk/elw"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "elwpric_jmpflu": "ELW가격급등락"
}
COLUMNS = {
    "stk_cd": "종목코드",
    "rank": "순위",
    "stk_nm": "종목명",
    "pre_sig": "대비기호",
    "pred_pre": "전일대비",
    "trde_end_elwbase_pric": "거래종료ELW기준가",
    "cur_prc": "현재가",
    "base_pre": "기준대비",
    "trde_qty": "거래량",
    "jmp_rt": "급등율"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "base_pric_tm": "기준가시간"
}


NUMERIC_COLUMNS = (
    '거래량',
    '거래종료ELW기준가',
    '급등율',
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

def get_domestic_elw_price_surge_drop(
    flu_tp: str,
    tm_tp: str,
    tm: str,
    trde_qty_tp: str,
    isscomp_cd: str,
    bsis_aset_cd: str,
    rght_tp: str,
    lpcd: str,
    trde_end_elwskip: str,
) -> dict[str, pd.DataFrame]:
    """
    ELW가격급등락요청[ka30001] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        flu_tp: 등락구분 — 1:급등, 2:급락
        tm_tp: 시간구분 — 1:분전, 2:일전
        tm: 시간 — 분 혹은 일입력 (예 1, 3, 5)
        trde_qty_tp: 거래량구분 — 0:전체, 10:만주이상, 50:5만주이상, 100:10만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상
        isscomp_cd: 발행사코드 — 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17
        bsis_aset_cd: 기초자산코드 — 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200..
        rght_tp: 권리구분 — 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 005:EX, 006:조기종료콜, 007:조기종료풋
        lpcd: LP코드 — 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17
        trde_end_elwskip: 거래종료ELW제외 — 0:포함, 1:제외

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_elw_price_surge_drop(
        ...     flu_tp='1',
        ...     tm_tp='2',
        ...     tm='1',
        ...     trde_qty_tp='0',
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
    if not flu_tp:
        raise ValueError('flu_tp is required.')
    if not tm_tp:
        raise ValueError('tm_tp is required.')
    if not tm:
        raise ValueError('tm is required.')
    if not trde_qty_tp:
        raise ValueError('trde_qty_tp is required.')
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
        "flu_tp": flu_tp,  # 등락구분
        "tm_tp": tm_tp,  # 시간구분
        "tm": tm,  # 시간
        "trde_qty_tp": trde_qty_tp,  # 거래량구분
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
    summary_rows = []
    rows = {
        "elwpric_jmpflu": [],
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
        result = get_domestic_elw_price_surge_drop(
            flu_tp='1',
            tm_tp='2',
            tm='1',
            trde_qty_tp='0',
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
