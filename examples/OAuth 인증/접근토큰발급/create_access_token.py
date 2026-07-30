# ---
# api_id: au10001
# api_name: 접근토큰 발급
# category: OAuth 인증
# sub_category: 접근토큰발급
# template: oauth
# api_url: /oauth2/token
# menu_path: OAuth 인증 > 접근토큰발급 > 접근토큰 발급(au10001)
# ---

import logging
from typing import Any, Literal

import pandas as pd

from kiwoom import get_auth, KiwoomError

API_ID = "au10001"
API_PATH = "/oauth2/token"
COLUMNS = {
    "expires_dt": "만료일",
    "token_type": "토큰타입",
    "token": "접근토큰"
}

def create_access_token(
    output: Literal["dataframe", "json"] = "dataframe",
    mode: Literal["real", "demo"] | None = None,
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """
    접근토큰 발급[au10001] API를 호출합니다.

    발급된 토큰은 공통 토큰 저장소에 저장되며 토큰 값은 출력하지 않습니다.

    Args:
        output: "dataframe" 또는 "json".
        mode: "real" 또는 "demo". 생략하면 current auth profile을 사용합니다.

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> result = create_access_token(
        ... )
        >>> for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        ...     print(k, v.head() if isinstance(v, pd.DataFrame) else v)
    """

    auth = get_auth(mode=mode)
    auth.refresh_access_token()
    status = auth.status()
    response_body = {
        "mode": status.mode,
        "issued": True,
        "token_saved_at": status.token_saved_at.isoformat() if status.token_saved_at else None,
        "expires_dt": status.token_expires_at.isoformat() if status.token_expires_at else None,
        "token_valid": status.token_valid,
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
        result = create_access_token(
        )
    except KiwoomError as exc:
        raise SystemExit(str(exc))
    # 결과 출력
    print(result)
