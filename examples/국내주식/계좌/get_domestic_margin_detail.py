# ---
# api_id: kt00013
# api_name: 증거금세부내역조회요청
# category: 국내주식
# sub_category: 계좌
# template: rest
# api_url: /api/dostk/acnt
# menu_path: 국내주식 > 계좌 > 증거금세부내역조회요청(kt00013)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "kt00013"
API_URL = "/api/dostk/acnt"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "tdy_reu_objt_amt": "금일재사용대상금액",
    "tdy_reu_use_amt": "금일재사용사용금액",
    "tdy_reu_alowa": "금일재사용가능금액",
    "tdy_reu_lmtt_amt": "금일재사용제한금액",
    "tdy_reu_alowa_fin": "금일재사용가능금액최종",
    "pred_reu_objt_amt": "전일재사용대상금액",
    "pred_reu_use_amt": "전일재사용사용금액",
    "pred_reu_alowa": "전일재사용가능금액",
    "pred_reu_lmtt_amt": "전일재사용제한금액",
    "pred_reu_alowa_fin": "전일재사용가능금액최종",
    "ch_amt": "현금금액",
    "ch_profa": "현금증거금",
    "use_pos_ch": "사용가능현금",
    "ch_use_lmtt_amt": "현금사용제한금액",
    "use_pos_ch_fin": "사용가능현금최종",
    "repl_amt_amt": "대용금액",
    "repl_profa": "대용증거금",
    "use_pos_repl": "사용가능대용",
    "repl_use_lmtt_amt": "대용사용제한금액",
    "use_pos_repl_fin": "사용가능대용최종",
    "crd_grnta_ch": "신용보증금현금",
    "crd_grnta_repl": "신용보증금대용",
    "crd_grnt_ch": "신용담보금현금",
    "crd_grnt_repl": "신용담보금대용",
    "uncla": "미수금",
    "ls_grnt_reu_gold": "대주담보금재사용금",
    "20ord_alow_amt": "20%주문가능금액",
    "30ord_alow_amt": "30%주문가능금액",
    "40ord_alow_amt": "40%주문가능금액",
    "50ord_alow_amt": "50%주문가능금액",
    "60ord_alow_amt": "60%주문가능금액",
    "100ord_alow_amt": "100%주문가능금액",
    "tdy_crd_rpya_loss_amt": "금일신용상환손실금액",
    "pred_crd_rpya_loss_amt": "전일신용상환손실금액",
    "tdy_ls_rpya_loss_repl_profa": "금일대주상환손실대용증거금",
    "pred_ls_rpya_loss_repl_profa": "전일대주상환손실대용증거금",
    "evlt_repl_amt_spg_use_skip": "평가대용금(현물사용제외)",
    "evlt_repl_rt": "평가대용비율",
    "crd_repl_profa": "신용대용증거금",
    "ch_ord_repl_profa": "현금주문대용증거금",
    "crd_ord_repl_profa": "신용주문대용증거금",
    "crd_repl_conv_gold": "신용대용환산금",
    "repl_alowa": "대용가능금액(현금제한)",
    "repl_alowa_2": "대용가능금액2(신용제한)",
    "ch_repl_lck_gold": "현금대용부족금",
    "crd_repl_lck_gold": "신용대용부족금",
    "ch_ord_alow_repla": "현금주문가능대용금",
    "crd_ord_alow_repla": "신용주문가능대용금",
    "d2vexct_entr": "D2가정산예수금",
    "d2ch_ord_alow_amt": "D2현금주문가능금액"
}


NUMERIC_COLUMNS = (
    '100%주문가능금액',
    '20%주문가능금액',
    '30%주문가능금액',
    '40%주문가능금액',
    '50%주문가능금액',
    '60%주문가능금액',
    'D2가정산예수금',
    'D2현금주문가능금액',
    '금일대주상환손실대용증거금',
    '금일신용상환손실금액',
    '금일재사용가능금액',
    '금일재사용가능금액최종',
    '금일재사용대상금액',
    '금일재사용사용금액',
    '금일재사용제한금액',
    '대용가능금액(현금제한)',
    '대용가능금액2(신용제한)',
    '대용금액',
    '대용사용제한금액',
    '대용증거금',
    '대주담보금재사용금',
    '미수금',
    '사용가능대용',
    '사용가능대용최종',
    '사용가능현금',
    '사용가능현금최종',
    '신용담보금대용',
    '신용담보금현금',
    '신용대용부족금',
    '신용대용증거금',
    '신용대용환산금',
    '신용보증금대용',
    '신용보증금현금',
    '신용주문가능대용금',
    '신용주문대용증거금',
    '전일대주상환손실대용증거금',
    '전일신용상환손실금액',
    '전일재사용가능금액',
    '전일재사용가능금액최종',
    '전일재사용대상금액',
    '전일재사용사용금액',
    '전일재사용제한금액',
    '평가대용금(현물사용제외)',
    '평가대용비율',
    '현금금액',
    '현금대용부족금',
    '현금사용제한금액',
    '현금주문가능대용금',
    '현금주문대용증거금',
    '현금증거금',
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

def get_domestic_margin_detail(
) -> pd.DataFrame:
    """
    증거금세부내역조회요청[kt00013] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_margin_detail(
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증

    # 2. 요청 파라미터 바디
    body = {
    }

    # 3. 인증 클라이언트
    client = get_client()

    # 4. 응답 데이터 저장소
    message_rows = []
    rows = []
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
        row = {
            key: response_body.get(key)
            for key in COLUMNS
        }
        if row:
            rows.append(row)

        next_cont_yn = response.continuation.cont_yn
        next_key = response.continuation.next_key

        if next_cont_yn != "Y":
            break

        if page + 1 >= MAX_PAGES:
            break

        time.sleep(REQUEST_DELAY_SECONDS)

    # 6. DataFrame 변환
    result = pd.DataFrame(rows).rename(columns=COLUMNS)
    if message_rows:
        message_df = pd.DataFrame(message_rows).rename(columns=MESSAGE_COLUMNS)
        result = pd.concat([message_df, result], axis=1)
    return result


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    try:
        df = get_domestic_margin_detail(
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
