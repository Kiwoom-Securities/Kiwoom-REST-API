import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from kiwoom.core.errors import InvalidModeError, SettingsError
from kiwoom.core.platform_paths import config_dir, ensure_private_directory, protect_file
from kiwoom.core.types import Mode, normalize_mode


SETTINGS_FILE_NAME = "settings.json"
MODE_ENV_VAR = "KIWOOM_MODE"


def get_mode_from_env() -> Mode | None:
    value = os.getenv(MODE_ENV_VAR)
    if not value:
        return None
    try:
        return normalize_mode(value)
    except ValueError as exc:
        raise InvalidModeError(value) from exc


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
