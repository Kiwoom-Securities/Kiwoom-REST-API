from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone
import hashlib
import os
from typing import Literal

import requests

from kiwoom.core.errors import (
    AuthenticationError,
    CredentialsNotFoundError,
    HTTPRequestError,
    InvalidTokenCacheError,
    raise_for_error_code,
)
from kiwoom.core.secrets import CredentialSet, SecretProvider
from kiwoom.core.token_store import TokenRecord
from kiwoom.core.types import Mode, normalize_mode


KST = timezone(timedelta(hours=9))
TOKEN_PATH = "/oauth2/token"
REVOKE_PATH = "/oauth2/revoke"
BASE_URL_ENV_VARS: dict[Mode, str] = {
    "real": "PRD",
    "demo": "MOCK",
}
WS_BASE_URL_ENV_VARS: dict[Mode, str] = {
    "real": "W_PRD",
    "demo": "W_MOCK",
}
DEFAULT_BASE_URLS: dict[Mode, str] = {
    "real": "https://api.kiwoom.com",
    "demo": "https://mockapi.kiwoom.com",
}
DEFAULT_WS_BASE_URLS: dict[Mode, str] = {
    "real": "wss://api.kiwoom.com:10000",
    "demo": "wss://mockapi.kiwoom.com:10000",
}


def get_base_url(mode: Mode) -> str:
    resolved_mode = normalize_mode(mode)
    return _endpoint_from_env(BASE_URL_ENV_VARS[resolved_mode], DEFAULT_BASE_URLS[resolved_mode])


def get_ws_base_url(mode: Mode) -> str:
    resolved_mode = normalize_mode(mode)
    return _endpoint_from_env(WS_BASE_URL_ENV_VARS[resolved_mode], DEFAULT_WS_BASE_URLS[resolved_mode])


def endpoint_env_var_names(mode: Mode) -> tuple[str, str]:
    resolved_mode = normalize_mode(mode)
    return BASE_URL_ENV_VARS[resolved_mode], WS_BASE_URL_ENV_VARS[resolved_mode]


def _endpoint_from_env(name: str, default: str) -> str:
    value = os.getenv(name, "").strip()
    return value.rstrip("/") if value else default


NextAuthAction = Literal[
    "use_cached_token",
    "issue_before_request",
    "refresh_before_request",
    "credentials_missing",
]


@dataclass(frozen=True)
class AuthStatus:
    mode: Mode
    credential_source: str | None
    has_credentials: bool
    has_token: bool
    token_saved_at: datetime | None
    token_expires_at: datetime | None
    token_valid: bool
    token_reusable: bool
    next_auth_action: NextAuthAction
    token_warning: str | None
    profile: str | None = None


class KiwoomAuth:
    def __init__(
        self,
        mode: Mode,
        secret_provider: SecretProvider,
        token_store,
        *,
        profile: str | None = None,
        refresh_buffer_seconds: int = 600,
        timeout_seconds: int = 30,
    ) -> None:
        self.mode = normalize_mode(mode)
        self.secret_provider = secret_provider
        self.token_store = token_store
        self.profile = profile
        self.timeout_seconds = timeout_seconds

        if refresh_buffer_seconds < 0:
            raise ValueError("refresh_buffer_seconds는 0 이상이어야 합니다.")
        if refresh_buffer_seconds > 60 * 60 * 12:
            raise ValueError("refresh_buffer_seconds 값이 너무 큽니다.")
        self.refresh_buffer = timedelta(seconds=refresh_buffer_seconds)

    def get_access_token(self) -> str:
        record = self._load_valid_token()
        if record is not None:
            return record.access_token
        return self.refresh_access_token()

    def refresh_access_token(self) -> str:
        credentials = self.secret_provider.get_credentials(self.mode)
        if credentials is None:
            raise CredentialsNotFoundError(self.mode)

        payload = {
            "grant_type": "client_credentials",
            "appkey": credentials.appkey,
            "secretkey": credentials.secretkey,
        }
        response = requests.post(
            f"{get_base_url(self.mode)}{TOKEN_PATH}",
            json=payload,
            headers={"Content-Type": "application/json;charset=UTF-8"},
            timeout=self.timeout_seconds,
        )
        data = _safe_json(response)
        if response.status_code >= 400:
            _raise_structured_error(
                response.status_code,
                data,
                fallback_message="토큰 요청에 실패했습니다.",
            )
        if data.get("return_code") not in (None, 0):
            raise_for_error_code(
                int(data["return_code"]),
                str(data.get("return_msg", "인증에 실패했습니다.")),
            )

        access_token = data.get("token")
        token_type = str(data.get("token_type", "bearer")).lower()
        expires_dt = data.get("expires_dt")
        if not access_token or not expires_dt:
            raise AuthenticationError("토큰 응답에 필요한 값이 없습니다.")

        record = TokenRecord(
            access_token=access_token,
            token_type=token_type,
            expires_at=self._parse_kiwoom_expiry(expires_dt),
            mode=self.mode,
            profile=self.profile,
            credential_fingerprint=self._credential_fingerprint(credentials),
            saved_at=datetime.now(UTC),
        )
        self.token_store.save(record)
        return record.access_token

    def authorization_header(self) -> str:
        return f"Bearer {self.get_access_token()}"

    def clear_token(self) -> bool:
        return self.token_store.clear(self.mode, profile=self.profile)

    def recover_from_auth_failure(self) -> str:
        self.clear_token()
        return self.refresh_access_token()

    def revoke_access_token(self) -> None:
        record = self._load_cached_token_for_revoke()
        if record is None:
            raise AuthenticationError("폐기할 로컬 토큰 캐시가 없습니다. 먼저 토큰을 발급하거나 재발급해 주세요.")

        credentials = self.secret_provider.get_credentials(self.mode)
        if credentials is None:
            raise CredentialsNotFoundError(self.mode)

        response = requests.post(
            f"{get_base_url(self.mode)}{REVOKE_PATH}",
            json={
                "appkey": credentials.appkey,
                "secretkey": credentials.secretkey,
                "token": record.access_token,
            },
            headers={"Content-Type": "application/json;charset=UTF-8"},
            timeout=self.timeout_seconds,
        )
        data = _safe_json(response)
        if response.status_code >= 400:
            _raise_structured_error(
                response.status_code,
                data,
                fallback_message="토큰 폐기 요청에 실패했습니다.",
            )
        if "return_code" not in data:
            raise AuthenticationError("토큰 폐기 응답에 성공 여부가 없습니다.")
        if data.get("return_code") != 0:
            raise_for_error_code(
                int(data["return_code"]),
                str(data.get("return_msg", "토큰 폐기에 실패했습니다.")),
            )

        self.clear_token()

    def status(self) -> AuthStatus:
        credentials = self.secret_provider.get_credentials(self.mode)
        token = None
        token_warning = None
        try:
            inspect_token = getattr(self.token_store, "peek", self.token_store.load)
            token = inspect_token(self.mode, profile=self.profile)
        except (InvalidTokenCacheError, OSError) as exc:
            token_warning = str(exc)
            token = None

        token_valid = token is not None and self._is_not_expired(token) and self._has_compatible_credentials(
            token,
            credentials,
        )
        token_reusable = token_valid and token is not None and self._is_valid(token)
        if token_valid and not token_reusable:
            token_warning = token_warning or "토큰 만료가 가까워 다음 요청에서 재발급될 수 있습니다."
        return AuthStatus(
            mode=self.mode,
            profile=self.profile,
            credential_source=credentials.source if credentials else None,
            has_credentials=credentials is not None,
            has_token=token is not None,
            token_saved_at=token.saved_at if token else None,
            token_expires_at=token.expires_at if token else None,
            token_valid=token_valid,
            token_reusable=token_reusable,
            next_auth_action=self._next_auth_action(
                token=token,
                credentials=credentials,
                token_reusable=token_reusable,
            ),
            token_warning=token_warning,
        )

    def _load_valid_token(self) -> TokenRecord | None:
        try:
            record = self.token_store.load(self.mode, profile=self.profile)
        except (InvalidTokenCacheError, OSError):
            return None
        if record is None:
            return None
        if record.credential_fingerprint is None:
            self.clear_token()
            return None
        credentials = self.secret_provider.get_credentials(self.mode)
        if credentials is not None:
            if not self._credentials_match(record, credentials):
                self.clear_token()
                return None
        if not self._is_valid(record):
            self.clear_token()
            return None
        return record

    def _load_cached_token_for_revoke(self) -> TokenRecord | None:
        inspect_token = getattr(self.token_store, "peek", self.token_store.load)
        try:
            record = inspect_token(self.mode, profile=self.profile)
        except InvalidTokenCacheError as exc:
            self.clear_token()
            raise AuthenticationError("토큰 캐시가 손상되어 먼저 삭제했습니다. 필요하면 토큰을 다시 발급해 주세요.") from exc
        except OSError:
            return None
        if record is None:
            return None
        if record.credential_fingerprint is None:
            self.clear_token()
            return None
        credentials = self.secret_provider.get_credentials(self.mode)
        if credentials is not None and not self._credentials_match(record, credentials):
            self.clear_token()
            return None
        if not self._is_not_expired(record):
            self.clear_token()
            return None
        return record

    def _is_valid(self, record: TokenRecord) -> bool:
        now_utc = datetime.now(UTC)
        return now_utc < (record.expires_at - self.refresh_buffer)

    def _is_not_expired(self, record: TokenRecord) -> bool:
        return datetime.now(UTC) < record.expires_at

    def _credentials_match(self, record: TokenRecord, credentials: CredentialSet) -> bool:
        if record.credential_fingerprint is None:
            return False
        return record.credential_fingerprint == self._credential_fingerprint(credentials)

    def _has_compatible_credentials(
        self,
        record: TokenRecord,
        credentials: CredentialSet | None,
    ) -> bool:
        if record.credential_fingerprint is None:
            return False
        if credentials is None:
            return True
        return self._credentials_match(record, credentials)

    def _next_auth_action(
        self,
        *,
        token: TokenRecord | None,
        credentials: CredentialSet | None,
        token_reusable: bool,
    ) -> NextAuthAction:
        if token_reusable:
            return "use_cached_token"
        if credentials is None:
            return "credentials_missing"
        if token is None:
            return "issue_before_request"
        return "refresh_before_request"

    @staticmethod
    def _parse_kiwoom_expiry(value: str) -> datetime:
        parsed = datetime.strptime(value, "%Y%m%d%H%M%S")
        return parsed.replace(tzinfo=KST).astimezone(UTC)

    @staticmethod
    def _credential_fingerprint(credentials: CredentialSet) -> str:
        return credential_fingerprint(credentials)


def credential_fingerprint(credentials: CredentialSet) -> str:
    """Non-reversible identity of an appkey/secret pair.

    Stored beside a cached token so a token issued for one key pair is never
    reused after the credentials change (`_load_valid_token`), and used by the
    runtime to seed a pre-issued token (`KIWOOM_ACCESS_TOKEN`) with the
    fingerprint the auth object will check it against.
    """
    raw = f"{credentials.appkey}:{credentials.secretkey}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _safe_json(response: requests.Response) -> dict:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def _raise_structured_error(status_code: int, payload: dict, *, fallback_message: str) -> None:
    if payload.get("return_code") not in (None, 0):
        raise_for_error_code(
            int(payload["return_code"]),
            str(payload.get("return_msg", fallback_message)),
        )
    raise HTTPRequestError(status_code, fallback_message)
