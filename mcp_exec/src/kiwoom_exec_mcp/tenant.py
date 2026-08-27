"""요청 한 건의 테넌트 자격증명 — HTTP 헤더에서 읽어 subprocess env로 건너가는 값의 타입.

- 헤더 이름은 여기서만 정의한다(`get_http_headers`는 소문자로 돌려준다).
- 시크릿은 헤더로만 받는다. URL query는 읽지 않는다(로그 유출 방지). 키를 인자로 받는
  도구는 만들지 않는다.
- 값은 strip한다 — 플랫폼 입력 폼에서 복붙된 공백·개행 하나로 키 검증이 깨진다.
- mode는 대소문자 무관하게 받는다(DEMO/Demo도 모의투자). 미전달 시 real.
- 서버가 발급해 둔 접근 토큰이 있으면 `with_token`으로 얹어 subprocess에 함께 넘긴다.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime

HEADER_APP_KEY = "x-kiwoom-app-key"
HEADER_APP_SECRET = "x-kiwoom-app-secret"
HEADER_MODE = "x-kiwoom-mode"
CREDENTIAL_HEADERS = (HEADER_APP_KEY, HEADER_APP_SECRET, HEADER_MODE)


@dataclass(frozen=True)
class TenantCredentials:
    appkey: str
    secretkey: str
    mode: str  # "real" | "demo" (검증은 kwcli가 한다)
    access_token: str | None = None
    access_token_expires_at: datetime | None = None

    @classmethod
    def from_headers(cls, headers: Mapping[str, str]) -> TenantCredentials | None:
        """헤더에 app-key가 있으면 자격증명, 없으면(stdio 등) None."""
        appkey = (headers.get(HEADER_APP_KEY) or "").strip()
        if not appkey:
            return None
        return cls(
            appkey=appkey,
            secretkey=(headers.get(HEADER_APP_SECRET) or "").strip(),
            mode=(headers.get(HEADER_MODE) or "real").strip().lower() or "real",
        )

    def with_token(self, access_token: str, expires_at: datetime) -> TenantCredentials:
        return replace(self, access_token=access_token, access_token_expires_at=expires_at)

    def secret_values(self) -> list[str]:
        """오류 출력에서 마스킹할 값들."""
        return [value for value in (self.appkey, self.secretkey, self.access_token) if value]
