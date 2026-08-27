import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from kiwoom.core.errors import InvalidModeError, SettingsError
from kiwoom.core.platform_paths import config_dir, ensure_private_directory, protect_file
from kiwoom.core.types import Mode, TokenStoreKind, normalize_mode, normalize_token_store_kind


SETTINGS_FILE_NAME = "settings.json"
MODE_ENV_VAR = "KIWOOM_MODE"
PROFILE_ENV_VAR = "KIWOOM_PROFILE"
TOKEN_STORE_ENV_VAR = "KIWOOM_TOKEN_STORE"
ACCESS_TOKEN_ENV_VAR = "KIWOOM_ACCESS_TOKEN"
ACCESS_TOKEN_EXPIRES_AT_ENV_VAR = "KIWOOM_ACCESS_TOKEN_EXPIRES_AT"


def get_mode_from_env() -> Mode | None:
    value = os.getenv(MODE_ENV_VAR)
    if not value:
        return None
    try:
        return normalize_mode(value)
    except ValueError as exc:
        raise InvalidModeError(value) from exc


def get_profile_from_env() -> str | None:
    value = os.getenv(PROFILE_ENV_VAR)
    if not value:
        return None
    return value.strip() or None


def get_token_store_kind_from_env() -> TokenStoreKind | None:
    """Return the token store kind selected by KIWOOM_TOKEN_STORE, or None.

    `file` (default when unset) caches the access token under the user cache
    directory; `memory` keeps it in-process only, so a short-lived process
    (e.g. one MCP request → one kiwoomcli subprocess) leaves no token on disk.
    """
    value = os.getenv(TOKEN_STORE_ENV_VAR)
    if not value:
        return None
    return normalize_token_store_kind(value.strip().lower())


@dataclass(frozen=True)
class PreissuedToken:
    access_token: str
    expires_at: datetime


def get_preissued_token_from_env() -> PreissuedToken | None:
    """Return the token in KIWOOM_ACCESS_TOKEN + KIWOOM_ACCESS_TOKEN_EXPIRES_AT, or None.

    A caller that already holds a valid token for the same credentials (e.g. a
    server that issued it once and keeps it in memory) hands it to a short-lived
    process this way, so the process does not spend a `/oauth2/token` call of
    its own. Both variables must be set together; expires_at is ISO 8601 with a
    timezone. Only meaningful with KIWOOM_TOKEN_STORE=memory (see runtime).
    """
    token = os.getenv(ACCESS_TOKEN_ENV_VAR)
    expires_raw = os.getenv(ACCESS_TOKEN_EXPIRES_AT_ENV_VAR)
    if not token and not expires_raw:
        return None
    if not token or not expires_raw:
        raise ValueError(
            f"{ACCESS_TOKEN_ENV_VAR} and {ACCESS_TOKEN_EXPIRES_AT_ENV_VAR} must be set together."
        )
    try:
        expires_at = datetime.fromisoformat(expires_raw.strip())
    except ValueError as exc:
        raise ValueError(f"{ACCESS_TOKEN_EXPIRES_AT_ENV_VAR} must be an ISO 8601 datetime.") from exc
    if expires_at.tzinfo is None:
        raise ValueError(f"{ACCESS_TOKEN_EXPIRES_AT_ENV_VAR} must include a timezone offset.")
    return PreissuedToken(access_token=token.strip(), expires_at=expires_at)


def settings_path() -> Path:
    return config_dir() / SETTINGS_FILE_NAME


def snapshot_settings() -> str | None:
    path = settings_path()
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SettingsError("settings.json 파일을 읽을 수 없습니다.") from exc


def restore_settings(snapshot: str | None) -> None:
    path = settings_path()
    if snapshot is None:
        path.unlink(missing_ok=True)
        return

    directory = ensure_private_directory(config_dir(), strict=False)
    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=directory,
        delete=False,
    ) as tmp:
        tmp.write(snapshot)
        temp_path = Path(tmp.name)

    protect_file(temp_path, strict=False)
    temp_path.replace(path)
    protect_file(path, strict=False)
