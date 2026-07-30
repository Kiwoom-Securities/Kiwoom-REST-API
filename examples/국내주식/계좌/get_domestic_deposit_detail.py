# ---
# api_id: kt00001
# api_name: 예수금상세현황요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 예수금상세현황요청(kt00001)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "kt00001"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "stk_entr_prst": "종목별예수금"
}
COLUMNS = {
    "crnc_cd": "통화코드",
    "fx_entr": "외화예수금",
    "fc_krw_repl_evlta": "원화대용평가금",
    "fc_trst_profa": "해외주식증거금",
    "pymn_alow_amt": "출금가능금액",
    "pymn_alow_amt_entr": "출금가능금액(예수금)",
    "ord_alow_amt_entr": "주문가능금액(예수금)",
    "fc_uncla": "외화미수(합계)",
    "fc_ch_uncla": "외화현금미수금",
    "dly_amt": "연체료",
    "d1_fx_entr": "d+1외화예수금",
    "d2_fx_entr": "d+2외화예수금",
    "d3_fx_entr": "d+3외화예수금",
    "d4_fx_entr": "d+4외화예수금"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "entr": "예수금",
    "profa_ch": "주식증거금현금",
    "bncr_profa_ch": "수익증권증거금현금",
    "nxdy_bncr_sell_exct": "익일수익증권매도정산대금",
    "fc_stk_krw_repl_set_amt": "해외주식원화대용설정금",
    "crd_grnta_ch": "신용보증금현금",
    "crd_grnt_ch": "신용담보금현금",
    "add_grnt_ch": "추가담보금현금",
    "etc_profa": "기타증거금",
    "uncl_stk_amt": "미수확보금",
    "shrts_prica": "공매도대금",
    "crd_set_grnta": "신용설정평가금",
    "chck_ina_amt": "수표입금액",
    "etc_chck_ina_amt": "기타수표입금액",
    "crd_grnt_ruse": "신용담보재사용",
    "knx_asset_evltv": "코넥스기본예탁금",
    "elwdpst_evlta": "ELW예탁평가금",
    "crd_ls_rght_frcs_amt": "신용대주권리예정금액",
    "lvlh_join_amt": "생계형가입금액",
    "lvlh_trns_alowa": "생계형입금가능금액",
    "repl_amt": "대용금평가금액(합계)",
    "remn_repl_evlta": "잔고대용평가금액",
    "trst_remn_repl_evlta": "위탁대용잔고평가금액",
    "bncr_remn_repl_evlta": "수익증권대용평가금액",
    "profa_repl": "위탁증거금대용",
    "crd_grnta_repl": "신용보증금대용",
    "crd_grnt_repl": "신용담보금대용",
    "add_grnt_repl": "추가담보금대용",
    "rght_repl_amt": "권리대용금",
    "pymn_alow_amt": "출금가능금액",
    "wrap_pymn_alow_amt": "랩출금가능금액",
    "ord_alow_amt": "주문가능금액",
    "bncr_buy_alowa": "수익증권매수가능금액",
    "20stk_ord_alow_amt": "20%종목주문가능금액",
    "30stk_ord_alow_amt": "30%종목주문가능금액",
    "40stk_ord_alow_amt": "40%종목주문가능금액",
    "100stk_ord_alow_amt": "100%종목주문가능금액",
    "ch_uncla": "현금미수금",
    "ch_uncla_dlfe": "현금미수연체료",
    "ch_uncla_tot": "현금미수금합계",
    "crd_int_npay": "신용이자미납",
    "int_npay_amt_dlfe": "신용이자미납연체료",
    "int_npay_amt_tot": "신용이자미납합계",
    "etc_loana": "기타대여금",
    "etc_loana_dlfe": "기타대여금연체료",
    "etc_loan_tot": "기타대여금합계",
    "nrpy_loan": "미상환융자금",
    "loan_sum": "융자금합계",
    "ls_sum": "대주금합계",
    "crd_grnt_rt": "신용담보비율",
    "mdstrm_usfe": "중도이용료",
    "min_ord_alow_yn": "최소주문가능금액",
    "loan_remn_evlt_amt": "대출총평가금액",
    "dpst_grntl_remn": "예탁담보대출잔고",
    "sell_grntl_remn": "매도담보대출잔고",
    "d1_entra": "d+1추정예수금",
    "d1_slby_exct_amt": "d+1매도매수정산금",
    "d1_buy_exct_amt": "d+1매수정산금",
    "d1_out_rep_mor": "d+1미수변제소요금",
    "d1_sel_exct_amt": "d+1매도정산금",
    "d1_pymn_alow_amt": "d+1출금가능금액",
    "d2_entra": "d+2추정예수금",
    "d2_slby_exct_amt": "d+2매도매수정산금",
    "d2_buy_exct_amt": "d+2매수정산금",
    "d2_out_rep_mor": "d+2미수변제소요금",
    "d2_sel_exct_amt": "d+2매도정산금",
    "d2_pymn_alow_amt": "d+2출금가능금액",
    "50stk_ord_alow_amt": "50%종목주문가능금액",
    "60stk_ord_alow_amt": "60%종목주문가능금액"
}


NUMERIC_COLUMNS = (
    '100%종목주문가능금액',
    '20%종목주문가능금액',
    '30%종목주문가능금액',
    '40%종목주문가능금액',
    '50%종목주문가능금액',
    '60%종목주문가능금액',
    'ELW예탁평가금',
    'd+1매도매수정산금',
    'd+1매도정산금',
    'd+1매수정산금',
    'd+1미수변제소요금',
    'd+1외화예수금',
    'd+1추정예수금',
    'd+1출금가능금액',
    'd+2매도매수정산금',
    'd+2매도정산금',
    'd+2매수정산금',
    'd+2미수변제소요금',
    'd+2외화예수금',
    'd+2추정예수금',
    'd+2출금가능금액',
    'd+3외화예수금',
    'd+4외화예수금',
    '공매도대금',
    '권리대용금',
    '기타대여금',
    '기타대여금연체료',
    '기타대여금합계',
    '기타수표입금액',
    '기타증거금',
    '대용금평가금액(합계)',
    '대주금합계',
    '대출총평가금액',
    '랩출금가능금액',
    '매도담보대출잔고',
    '미상환융자금',
    '미수확보금',
    '생계형가입금액',
    '생계형입금가능금액',
    '수익증권대용평가금액',
    '수익증권매수가능금액',
    '수익증권증거금현금',
    '수표입금액',
    '신용담보금대용',
    '신용담보금현금',
    '신용담보비율',
    '신용담보재사용',
    '신용대주권리예정금액',
    '신용보증금대용',
    '신용보증금현금',
    '신용설정평가금',
    '신용이자미납',
    '신용이자미납연체료',
    '신용이자미납합계',
    '예수금',
    '예탁담보대출잔고',
    '외화예수금',
    '외화현금미수금',
    '원화대용평가금',
    '위탁대용잔고평가금액',
    '위탁증거금대용',
    '융자금합계',
    '익일수익증권매도정산대금',
    '잔고대용평가금액',
    '주문가능금액',
    '주문가능금액(예수금)',
    '주식증거금현금',
    '중도이용료',
    '최소주문가능금액',
    '추가담보금대용',
    '추가담보금현금',
    '출금가능금액',
    '출금가능금액(예수금)',
    '코넥스기본예탁금',
    '해외주식원화대용설정금',
    '해외주식증거금',
    '현금미수금',
    '현금미수금합계',
    '현금미수연체료',
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

def get_domestic_deposit_detail(
    qry_tp: str,
) -> dict[str, pd.DataFrame]:
    """
    예수금상세현황요청[kt00001] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        qry_tp: 조회구분 — 3:추정조회, 2:일반조회

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_deposit_detail(
        ...     qry_tp='3',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not qry_tp:
        raise ValueError('qry_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "qry_tp": qry_tp,  # 조회구분
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    summary_rows = []
    rows = {
        "stk_entr_prst": [],
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
        result = get_domestic_deposit_detail(
            qry_tp='3',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
