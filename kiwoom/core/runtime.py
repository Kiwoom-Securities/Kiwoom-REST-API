from typing import Literal

from kiwoom.core.auth import KiwoomAuth, get_base_url as _auth_base_url, get_ws_base_url as _auth_ws_base_url
from kiwoom.core.client import KiwoomClient
from kiwoom.core.errors import ModeNotConfiguredError
from kiwoom.core.profiles import AuthProfile, get_current_profile, get_profile
from kiwoom.core.secrets import SecretProvider, default_secret_provider
from kiwoom.core.settings import get_mode_from_env
from kiwoom.core.token_store import FileTokenStore, MemoryTokenStore
from kiwoom.core.types import Mode, normalize_mode
from kiwoom.core.ws_client import KiwoomWebSocketClient

TokenStoreKind = Literal["file", "memory"]


def resolve_mode(mode: str | None = None, *, profile: str | None = None) -> Mode:
    if profile is not None:
        selected = get_profile(profile)
        if mode is not None and normalize_mode(mode) != selected.mode:
            raise ValueError("지정한 mode가 선택한 계좌 별칭의 mode와 일치하지 않습니다")
        return selected.mode

    if mode is not None:
        return normalize_mode(mode)

    current_profile = get_current_profile()
    if current_profile is not None:
        return current_profile.mode

    env_mode = get_mode_from_env()
    if env_mode is not None:
        return env_mode

    raise ModeNotConfiguredError()


def get_auth(
    mode: str | None = None,
    *,
    profile: str | None = None,
    secret_provider: SecretProvider | None = None,
    token_store_kind: TokenStoreKind = "file",
) -> KiwoomAuth:
    selected_profile = _resolve_profile(mode=mode, profile=profile)
    resolved_mode = selected_profile.mode if selected_profile else resolve_mode(mode)
    profile_alias = selected_profile.alias if selected_profile else None
    return KiwoomAuth(
        mode=resolved_mode,
        profile=profile_alias,
        secret_provider=secret_provider or default_secret_provider(profile=profile_alias),
        token_store=_build_token_store(token_store_kind),
    )


def get_client(
    mode: str | None = None,
    *,
    profile: str | None = None,
    auth: KiwoomAuth | None = None,
    timeout_seconds: int = 30,
) -> KiwoomClient:
    if auth is not None and (mode is not None or profile is not None):
        raise ValueError("mode/profile and auth cannot be used together")
    return KiwoomClient(auth or get_auth(mode, profile=profile), timeout_seconds=timeout_seconds)


def get_ws_client(
    mode: str | None = None,
    *,
    profile: str | None = None,
    auth: KiwoomAuth | None = None,
) -> KiwoomWebSocketClient:
    if auth is not None and (mode is not None or profile is not None):
        raise ValueError("mode/profile and auth cannot be used together")
    return KiwoomWebSocketClient(auth or get_auth(mode, profile=profile))


def get_base_url(mode: str | None = None, *, profile: str | None = None) -> str:
    return _auth_base_url(resolve_mode(mode, profile=profile))


def get_ws_base_url(mode: str | None = None, *, profile: str | None = None) -> str:
    return _auth_ws_base_url(resolve_mode(mode, profile=profile))


def _resolve_profile(*, mode: str | None, profile: str | None) -> AuthProfile | None:
    if profile is not None:
        selected = get_profile(profile)
        if mode is not None and normalize_mode(mode) != selected.mode:
            raise ValueError("지정한 mode가 선택한 계좌 별칭의 mode와 일치하지 않습니다")
        return selected
    if mode is not None:
        return None
    return get_current_profile()


def _build_token_store(token_store_kind: TokenStoreKind):
    if token_store_kind == "file":
        return FileTokenStore()
    if token_store_kind == "memory":
        return MemoryTokenStore()
    raise ValueError(f"unsupported token_store_kind: {token_store_kind}")
