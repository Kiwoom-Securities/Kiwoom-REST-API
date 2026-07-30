# ---
# api_id: kt00015
# api_name: 위탁종합거래내역요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 위탁종합거래내역요청(kt00015)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "kt00015"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {
    "trst_ovrl_trde_prps_array": "위탁종합거래내역배열"
}
COLUMNS = {
    "trde_dt": "거래일자",
    "trde_no": "거래번호",
    "rmrk_nm": "적요명",
    "crd_deal_tp_nm": "신용거래구분명",
    "exct_amt": "정산금액",
    "loan_amt_rpya": "대출금상환",
    "fc_trde_amt": "거래금액(외)",
    "fc_exct_amt": "정산금액(외)",
    "entra_remn": "예수금잔고",
    "crnc_cd": "통화코드",
    "trde_ocr_tp": "거래종류구분",
    "trde_kind_nm": "거래종류명",
    "stk_nm": "종목명",
    "trde_amt": "거래금액",
    "trde_agri_tax": "거래및농특세",
    "rpy_diffa": "상환차금",
    "fc_trde_tax": "거래세(외)",
    "dly_sum": "연체합",
    "fc_entra": "외화예수금잔고",
    "mdia_tp_nm": "매체구분명",
    "io_tp": "입출구분",
    "io_tp_nm": "입출구분명",
    "orig_deal_no": "원거래번호",
    "stk_cd": "종목코드",
    "trde_qty_jwa_cnt": "거래수량/좌수",
    "cmsn": "수수료",
    "int_ls_usfe": "이자/대주이용",
    "fc_cmsn": "수수료(외)",
    "fc_dly_sum": "연체합(외)",
    "vlbl_nowrm": "유가금잔",
    "proc_tm": "처리시간",
    "isin_cd": "ISIN코드",
    "stex_cd": "거래소코드",
    "stex_nm": "거래소명",
    "trde_unit": "거래단가/환율",
    "incm_resi_tax": "소득/주민세",
    "loan_dt": "대출일",
    "uncl_ocr": "미수(원/주)",
    "rpym_sum": "변제합",
    "cntr_dt": "체결일",
    "rcpy_no": "출납번호",
    "prcsr": "처리자",
    "proc_brch": "처리점",
    "trde_stle": "매매형태",
    "txon_base_pric": "과세기준가",
    "tax_sum_cmsn": "세금수수료합",
    "frgn_pay_txam": "외국납부세액(외)",
    "fc_uncl_ocr": "미수(외)",
    "rpym_sum_fr": "변제합(외)",
    "rcpmnyer": "입금자",
    "trde_prtc_tp": "거래내역구분"
}


NUMERIC_COLUMNS = (
    '거래금액',
    '거래금액(외)',
    '거래단가/환율',
    '거래수량/좌수',
    '과세기준가',
    '대출금상환',
    '상환차금',
    '세금수수료합',
    '수수료',
    '수수료(외)',
    '예수금잔고',
    '외화예수금잔고',
    '유가금잔',
    '입금자',
    '정산금액',
    '정산금액(외)',
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

def get_domestic_brokerage_account_transaction_history(
    strt_dt: str,
    end_dt: str,
    tp: str,
    gds_tp: str,
    dmst_stex_tp: str,
    stk_cd: str | None = '',
    crnc_cd: str | None = '',
    frgn_stex_code: str | None = '',
    qry_sort_tp: str | None = '',
) -> dict[str, pd.DataFrame]:
    """
    위탁종합거래내역요청[kt00015] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        strt_dt: 시작일자 — YYYYMMDD
        end_dt: 종료일자 — YYYYMMDD
        tp: 구분 — 0:전체,1:입출금,2:입출고,3:매매,4:매수,5:매도,6:입금,7:출금,A:예탁담보대출입금,B:매도담보대출입금,C:현금상환(융자,담보상환),F:환전,M:입출금+환전,G:외화매수,H:외화매도,I:환전정산입금,J:환전정산출금
        gds_tp: 상품구분 — 0:전체, 1:국내주식, 2:수익증권, 3:해외주식, 4:금융상품
        dmst_stex_tp: 국내거래소구분 — %:(전체),KRX:한국거래소,NXT:넥스트트레이드
        stk_cd: 종목코드 — 종목 코드 입력
        crnc_cd: 통화코드 — 통화코드 3자리
        frgn_stex_code: 해외거래소코드
        qry_sort_tp: 조회정렬구분 — 1:최근거래순, 2:과거거래순(미입력시 과거거래순)

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = get_domestic_brokerage_account_transaction_history(
        ...     strt_dt='20241121',
        ...     end_dt='20241125',
        ...     tp='0',
        ...     gds_tp='0',
        ...     dmst_stex_tp='%',
        ...     stk_cd='',
        ...     crnc_cd='',
        ...     frgn_stex_code='',
        ...     qry_sort_tp='',
        ... )
        >>> for key, df in result.items():
        ...     print(key, df)
    """

    # 1. 필수 파라미터 검증
    if not strt_dt:
        raise ValueError('strt_dt is required.')
    if not end_dt:
        raise ValueError('end_dt is required.')
    if not tp:
        raise ValueError('tp is required.')
    if not gds_tp:
        raise ValueError('gds_tp is required.')
    if not dmst_stex_tp:
        raise ValueError('dmst_stex_tp is required.')

    # 2. 요청 파라미터 바디
    body = {
        "strt_dt": strt_dt,  # 시작일자
        "end_dt": end_dt,  # 종료일자
        "tp": tp,  # 구분
        "gds_tp": gds_tp,  # 상품구분
        "dmst_stex_tp": dmst_stex_tp,  # 국내거래소구분
    }
    if stk_cd is not None:
        body["stk_cd"] = stk_cd  # 종목코드
    if crnc_cd is not None:
        body["crnc_cd"] = crnc_cd  # 통화코드
    if frgn_stex_code is not None:
        body["frgn_stex_code"] = frgn_stex_code  # 해외거래소코드
    if qry_sort_tp is not None:
        body["qry_sort_tp"] = qry_sort_tp  # 조회정렬구분

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = {
        "trst_ovrl_trde_prps_array": [],
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
        result = get_domestic_brokerage_account_transaction_history(
            strt_dt='20241121',
            end_dt='20241125',
            tp='0',
            gds_tp='0',
            dmst_stex_tp='%',
            stk_cd='',
            crnc_cd='',
            frgn_stex_code='',
            qry_sort_tp='',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    for key, df in result.items():
        print(f"\n[{key}]")
        print(_format_display(df))
