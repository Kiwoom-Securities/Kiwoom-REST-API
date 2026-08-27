from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from kiwoom.core.auth import (
    KiwoomAuth,
    credential_fingerprint,
    get_base_url as _auth_base_url,
    get_ws_base_url as _auth_ws_base_url,
)
from kiwoom.core.client import KiwoomClient
from kiwoom.core.errors import ModeNotConfiguredError
from kiwoom.core.profiles import AuthProfile, get_current_profile, get_profile
from kiwoom.core.secrets import SecretProvider, default_secret_provider
from kiwoom.core.settings import (
    ACCESS_TOKEN_ENV_VAR,
    TOKEN_STORE_ENV_VAR,
    PreissuedToken,
    get_mode_from_env,
    get_preissued_token_from_env,
    get_profile_from_env,
    get_token_store_kind_from_env,
)
from kiwoom.core.token_store import FileTokenStore, MemoryTokenStore, TokenRecord
from kiwoom.core.types import Mode, TokenStoreKind, normalize_mode
from kiwoom.core.ws_client import KiwoomWebSocketClient

SelectionSource = Literal[
    "--profile",
    "KIWOOM_PROFILE",
    "--mode",
    "KIWOOM_MODE",
    "current_profile",
]


@dataclass(frozen=True)
class _Selection:
    """How `mode`/`profile` inputs resolved to a concrete auth target.

    Single source of truth shared by `resolve_mode`, `get_auth`, and
    `describe_selection` so the selection precedence cannot diverge.
    """

    source: SelectionSource
    profile: AuthProfile | None
    mode: Mode


def _resolve_selection(*, mode: str | None, profile: str | None) -> _Selection:
    explicit_profile = profile
    env_profile = get_profile_from_env() if profile is None else None
    profile_alias = explicit_profile if explicit_profile is not None else env_profile
    env_mode = None if mode is not None else get_mode_from_env()

    if profile_alias is not None:
        selected = get_profile(profile_alias)
        selected_mode = normalize_mode(mode) if mode is not None else env_mode
        if selected_mode is not None and selected_mode != selected.mode:
            raise ValueError("지정한 mode가 선택한 계좌 별칭의 mode와 일치하지 않습니다")
        source: SelectionSource = "--profile" if explicit_profile is not None else "KIWOOM_PROFILE"
        return _Selection(source=source, profile=selected, mode=selected.mode)

    if mode is not None:
        return _Selection(source="--mode", profile=None, mode=normalize_mode(mode))

    if env_mode is not None:
        return _Selection(source="KIWOOM_MODE", profile=None, mode=env_mode)

    current_profile = get_current_profile()
    if current_profile is not None:
        return _Selection(source="current_profile", profile=current_profile, mode=current_profile.mode)

    raise ModeNotConfiguredError()


@dataclass(frozen=True)
class SelectionContext:
    """Public description of which input won auth target selection."""

    selection_source: SelectionSource
    mode: Mode
    profile: str | None
    uses_profile: bool
    target_label: str


def describe_selection(mode: str | None = None, *, profile: str | None = None) -> SelectionContext:
    """Report how `mode`/`profile` resolve, without building an auth object.

    Raises `ModeNotConfiguredError` when nothing selects a target, matching
    `resolve_mode`/`get_auth`.
    """

    selection = _resolve_selection(mode=mode, profile=profile)
    alias = selection.profile.alias if selection.profile else None
    uses_profile = selection.profile is not None
    target_label = f"계좌 별칭 {alias}" if uses_profile else f"{selection.mode} mode"
    return SelectionContext(
        selection_source=selection.source,
        mode=selection.mode,
        profile=alias,
        uses_profile=uses_profile,
        target_label=target_label,
    )


def resolve_mode(mode: str | None = None, *, profile: str | None = None) -> Mode:
    return _resolve_selection(mode=mode, profile=profile).mode


def get_auth(
    mode: str | None = None,
    *,
    profile: str | None = None,
    secret_provider: SecretProvider | None = None,
    token_store_kind: TokenStoreKind | None = None,
) -> KiwoomAuth:
    """Build the auth object for the selected target.

    `token_store_kind=None` (the default) resolves via `resolve_token_store_kind`,
    i.e. `KIWOOM_TOKEN_STORE` when set, else the on-disk file cache. Pass an
    explicit kind to override the environment (setup does this for its
    throwaway validation auth).
    """
    selection = _resolve_selection(mode=mode, profile=profile)
    profile_alias = selection.profile.alias if selection.profile else None
    provider = secret_provider or default_secret_provider(profile=profile_alias)
    return KiwoomAuth(
        mode=selection.mode,
        profile=profile_alias,
        secret_provider=provider,
        token_store=_build_token_store(
            resolve_token_store_kind(token_store_kind),
            mode=selection.mode,
            profile=profile_alias,
            secret_provider=provider,
        ),
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


def resolve_token_store_kind(token_store_kind: TokenStoreKind | None = None) -> TokenStoreKind:
    """Explicit argument > `KIWOOM_TOKEN_STORE` > `file`."""
    if token_store_kind is not None:
        return token_store_kind
    return get_token_store_kind_from_env() or "file"


def _build_token_store(
    token_store_kind: TokenStoreKind,
    *,
    mode: Mode,
    profile: str | None,
    secret_provider: SecretProvider,
):
    preissued = get_preissued_token_from_env()
    if token_store_kind == "file":
        if preissued is not None:
            raise ValueError(f"{ACCESS_TOKEN_ENV_VAR} requires {TOKEN_STORE_ENV_VAR}=memory.")
        return FileTokenStore()
    if token_store_kind == "memory":
        store = MemoryTokenStore()
        if preissued is not None:
            _seed_preissued_token(store, preissued, mode=mode, profile=profile, secret_provider=secret_provider)
        return store
    raise ValueError(f"unsupported token_store_kind: {token_store_kind}")


def _seed_preissued_token(
    store: MemoryTokenStore,
    preissued: PreissuedToken,
    *,
    mode: Mode,
    profile: str | None,
    secret_provider: SecretProvider,
) -> None:
    """Place a token handed in via env into the in-memory store.

    The record carries the fingerprint of the credentials this process resolves,
    so `KiwoomAuth._load_valid_token` accepts it exactly as it would a token it
    issued itself; if the credentials are missing the token is not seeded and the
    usual credentials error surfaces on first use.
    """
    credentials = secret_provider.get_credentials(mode)
    if credentials is None:
        return
    store.save(
        TokenRecord(
            access_token=preissued.access_token,
            token_type="bearer",
            expires_at=preissued.expires_at.astimezone(UTC),
            mode=mode,
            profile=profile,
            credential_fingerprint=credential_fingerprint(credentials),
            saved_at=datetime.now(UTC),
        )
    )
