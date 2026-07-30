# ---
# api_id: kt00009
# api_name: 계좌별주문체결현황요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 계좌별주문체결현황요청(kt00009)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "kt00009"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "acnt_ord_cntr_prst_array": "계좌별주문체결현황배열"
}
COLUMNS = {
    "stk_bond_tp": "주식채권구분",
    "ord_no": "주문번호",
    "stk_cd": "종목번호",
    "trde_tp": "매매구분",
    "io_tp_nm": "주문유형구분",
    "ord_qty": "주문수량",
    "ord_uv": "주문단가",
    "cnfm_qty": "확인수량",
    "rsrv_oppo": "예약/반대",
    "cntr_no": "체결번호",
    "acpt_tp": "접수구분",
    "orig_ord_no": "원주문번호",
    "stk_nm": "종목명",
    "setl_tp": "결제구분",
    "crd_deal_tp": "신용거래구분",
    "cntr_qty": "체결수량",
    "cntr_uv": "체결단가",
    "comm_ord_tp": "통신구분",
    "mdfy_cncl_tp": "정정/취소구분",
    "cntr_tm": "체결시간",
    "dmst_stex_tp": "국내거래소구분",
    "cond_uv": "스톱가"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "sell_grntl_engg_amt": "매도약정금액",
    "buy_engg_amt": "매수약정금액",
    "engg_amt": "약정금액"
}


NUMERIC_COLUMNS = (
    '매도약정금액',
    '매수약정금액',
    '스톱가',
    '약정금액',
    '주문단가',
    '주문수량',
    '체결단가',
    '체결수량',
    '확인수량',
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

def get_domestic_account_order_fill_status(
    stk_bond_tp: str,
    mrkt_tp: str,
    sell_tp: str,
    qry_tp: str,
    dmst_stex_tp: str,
    ord_dt: str | None = '',
    stk_cd: str | None = '',
    fr_ord_no: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    계좌별주문체결현황요청[kt00009] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_bond_tp: 주식채권구분 — 0:전체, 1:주식, 2:채권
        mrkt_tp: 시장구분 — 0:전체, 1:코스피, 2:코스닥, 3:OTCBB, 4:ECN
        sell_tp: 매도수구분 — 0:전체, 1:매도, 2:매수
        qry_tp: 조회구분 — 0:전체, 1:체결
        dmst_stex_tp: 국내거래소구분 — %:(전체),KRX:한국거래소,NXT:넥스트트레이드,SOR:최선주문집행
        ord_dt: 주문일자 — YYYYMMDD
        stk_cd: 종목코드 — 전문 조회할 종목코드
        fr_ord_no: 시작주문번호 — 시작주문번호의 이전 주문은 조회 되지 않으며 약정금액에도 포함 되지 않음

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_account_order_fill_status(
        ...     stk_bond_tp='0',
        ...     mrkt_tp='0',
        ...     sell_tp='0',
        ...     qry_tp='0',
        ...     dmst_stex_tp='KRX',
        ...     ord_dt='',
        ...     stk_cd='',
        ...     fr_ord_no='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not stk_bond_tp:
        raise ValueError('stk_bond_tp is required.')
    if not mrkt_tp:
        raise ValueError('mrkt_tp is required.')
    if not sell_tp:
        raise ValueError('sell_tp is required.')
    if not qry_tp:
        raise ValueError('qry_tp is required.')
    if not dmst_stex_tp:
        raise ValueError('dmst_stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_bond_tp": stk_bond_tp,  # 주식채권구분
        "mrkt_tp": mrkt_tp,  # 시장구분
        "sell_tp": sell_tp,  # 매도수구분
        "qry_tp": qry_tp,  # 조회구분
        "dmst_stex_tp": dmst_stex_tp,  # 국내거래소구분
    }
    if ord_dt is not None:
        body["ord_dt"] = ord_dt  # 주문일자
    if stk_cd is not None:
        body["stk_cd"] = stk_cd  # 종목코드
    if fr_ord_no is not None:
        body["fr_ord_no"] = fr_ord_no  # 시작주문번호

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "acnt_ord_cntr_prst_array": [],
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
        result = get_domestic_account_order_fill_status(
            stk_bond_tp='0',
            mrkt_tp='0',
            sell_tp='0',
            qry_tp='0',
            dmst_stex_tp='KRX',
            ord_dt='',
            stk_cd='',
            fr_ord_no='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
