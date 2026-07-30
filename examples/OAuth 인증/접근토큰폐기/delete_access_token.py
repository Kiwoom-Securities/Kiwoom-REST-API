# ---
# api_id: au10002
# api_name: 접근토큰폐기
# category: OAuth 인증
# sub_category: 접근토큰폐기
# template: oauth
# api_url: /oauth2/revoke
# menu_path: OAuth 인증 > 접근토큰폐기 > 접근토큰폐기(au10002)
# ---

import logging
from typing import Any, Literal

import pandas as pd

from kiwoom import get_auth, KiwoomError

API_ID = "au10002"
API_PATH = "/oauth2/revoke"
COLUMNS = {}

def delete_access_token(
    output: Literal["dataframe", "json"] = "dataframe",
    mode: Literal["real", "demo"] | None = None,
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """
    접근토큰폐기[au10002] API를 호출합니다.

    공통 토큰 저장소의 현재 토큰을 서버에서 폐기하고 로컬 캐시도 삭제합니다.

    Args:
        output: "dataframe" 또는 "json".
        mode: "real" 또는 "demo". 생략하면 current auth profile을 사용합니다.

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = delete_access_token(
        ... )
        >>> for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        ...     print(k, v.head() if isinstance(v, pd.DataFrame) else v)
    """

    auth = get_auth(mode=mode)
    auth.revoke_access_token()
    response_body = {
        "mode": mode,
        "revoked": True,
        "return_code": 0,
        "return_msg": "토큰 폐기 완료",
    }

    if output == "json":
        return response_body
    scalar_values = {
        key: value
        for key, value in response_body.items()
        if key not in {"return_code", "return_msg", "trnm"} and not isinstance(value, (dict, list))
    }
    current_data = pd.DataFrame([scalar_values]) if scalar_values else pd.DataFrame()
    current_data = current_data.rename(columns=COLUMNS)
    return current_data


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    try:
        result = delete_access_token(
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(result)
