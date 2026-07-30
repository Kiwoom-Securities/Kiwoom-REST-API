# ---
# api_id: ka30012
# api_name: ELW종목상세정보요청
# category: 국내주식
# sub_category: ELW
# template: rest
# api_url: /api/dostk/elw
# menu_path: 국내주식 > ELW > ELW종목상세정보요청(ka30012)
# ---

import logging
import time

import pandas as pd

from kiwoom import get_client, KiwoomError

API_ID = "ka30012"
API_URL = "/api/dostk/elw"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "aset_cd": "자산코드",
    "cur_prc": "현재가",
    "pred_pre_sig": "전일대비기호",
    "pred_pre": "전일대비",
    "flu_rt": "등락율",
    "lpmmcm_nm": "LP회원사명",
    "lpmmcm_nm_1": "LP회원사명1",
    "lpmmcm_nm_2": "LP회원사명2",
    "elwrght_cntn": "ELW권리내용",
    "elwexpr_evlt_pric": "ELW만기평가가격",
    "elwtheory_pric": "ELW이론가",
    "dispty_rt": "괴리율",
    "elwinnr_vltl": "ELW내재변동성",
    "exp_rght_pric": "예상권리가",
    "elwpl_qutr_rt": "ELW손익분기율",
    "elwexec_pric": "ELW행사가",
    "elwcnvt_rt": "ELW전환비율",
    "elwcmpn_rt": "ELW보상율",
    "elwpric_rising_part_rt": "ELW가격상승참여율",
    "elwrght_type": "ELW권리유형",
    "elwsrvive_dys": "ELW잔존일수",
    "stkcnt": "상장주식수",
    "elwlpord_pos": "ELWLP주문가능",
    "lpposs_rt": "LP보유비율",
    "lprmnd_qty": "LP보유수량",
    "elwspread": "ELW스프레드",
    "elwprty": "ELW패리티",
    "elwgear": "ELW기어링",
    "elwflo_dt": "ELW상장일",
    "elwfin_trde_dt": "ELW최종거래일",
    "expr_dt": "만기일",
    "exec_dt": "행사일",
    "lpsuply_end_dt": "LP공급종료일",
    "elwpay_dt": "ELW지급일",
    "elwinvt_ix_comput": "ELW투자지표산출",
    "elwpay_agnt": "ELW지급대리인",
    "elwappr_way": "ELW결재방법",
    "elwrght_exec_way": "ELW권리행사방식",
    "elwpblicte_orgn": "ELW발행기관",
    "dcsn_pay_amt": "확정지급액",
    "kobarr": "KO베리어",
    "iv": "IV",
    "clsprd_end_elwocr": "종기종료ELW발생",
    "bsis_aset_1": "기초자산1",
    "bsis_aset_comp_rt_1": "기초자산구성비율1",
    "bsis_aset_2": "기초자산2",
    "bsis_aset_comp_rt_2": "기초자산구성비율2",
    "bsis_aset_3": "기초자산3",
    "bsis_aset_comp_rt_3": "기초자산구성비율3",
    "bsis_aset_4": "기초자산4",
    "bsis_aset_comp_rt_4": "기초자산구성비율4",
    "bsis_aset_5": "기초자산5",
    "bsis_aset_comp_rt_5": "기초자산구성비율5",
    "fr_dt": "평가시작일자",
    "to_dt": "평가종료일자",
    "fr_tm": "평가시작시간",
    "evlt_end_tm": "평가종료시간",
    "evlt_pric": "평가가격",
    "evlt_fnsh_yn": "평가완료여부",
    "all_hgst_pric": "전체최고가",
    "all_lwst_pric": "전체최저가",
    "imaf_hgst_pric": "직후최고가",
    "imaf_lwst_pric": "직후최저가",
    "sndhalf_mrkt_hgst_pric": "후반장최고가",
    "sndhalf_mrkt_lwst_pric": "후반장최저가"
}


NUMERIC_COLUMNS = (
    'ELWLP주문가능',
    'ELW가격상승참여율',
    'ELW만기평가가격',
    'ELW보상율',
    'ELW손익분기율',
    'ELW이론가',
    'ELW전환비율',
    'ELW행사가',
    'LP보유비율',
    'LP보유수량',
    '괴리율',
    '기초자산1',
    '기초자산2',
    '기초자산3',
    '기초자산4',
    '기초자산5',
    '기초자산구성비율1',
    '기초자산구성비율2',
    '기초자산구성비율3',
    '기초자산구성비율4',
    '기초자산구성비율5',
    '등락율',
    '예상권리가',
    '전체최고가',
    '전체최저가',
    '직후최고가',
    '직후최저가',
    '평가가격',
    '평가완료여부',
    '현재가',
    '후반장최고가',
    '후반장최저가',
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

def get_domestic_elw_detail(
    stk_cd: str,
) -> pd.DataFrame:
    """
    ELW종목상세정보요청[ka30012] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_elw_detail(
        ...     stk_cd='57JBHH',
        ... )
        >>> print(df)
    """

    # 1. 필수 파라미터 검증
    if not stk_cd:
        raise ValueError('stk_cd is required.')

    # 2. 요청 파라미터 바디
    body = {
        "stk_cd": stk_cd,  # 종목코드
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
        df = get_domestic_elw_detail(
            stk_cd='57JBHH',
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(_format_display(df))
