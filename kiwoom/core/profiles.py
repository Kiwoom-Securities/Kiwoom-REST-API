import json
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from kiwoom.core.errors import SettingsError
from kiwoom.core.platform_paths import config_dir, ensure_private_directory, protect_file
from kiwoom.core.settings import SETTINGS_FILE_NAME, settings_path
from kiwoom.core.types import Mode, normalize_mode

PROFILE_ALIAS_MAX_LENGTH = 64
PROFILE_ALIAS_ALLOWED_PUNCTUATION = {" ", ".", "_", "-"}
PROFILE_ALIAS_FORBIDDEN_CHARACTERS = {"/", "\\", ":"}


@dataclass(frozen=True)
class AuthProfile:
    alias: str
    mode: Mode


def validate_profile_alias(alias: str) -> str:
    normalized = alias.strip()
    if not normalized:
        raise ValueError("계좌 별칭을 입력해 주세요. 예: 모의계좌, 실전계좌, family-demo")
    if len(normalized) > PROFILE_ALIAS_MAX_LENGTH:
        raise ValueError("계좌 별칭은 64자 이하여야 합니다.")
    if normalized in {".", ".."}:
        raise ValueError("계좌 별칭으로 '.', '..'는 사용할 수 없습니다.")
    if any(character in PROFILE_ALIAS_FORBIDDEN_CHARACTERS for character in normalized):
        raise ValueError("계좌 별칭에는 '/', '\\', ':' 문자를 사용할 수 없습니다.")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError("계좌 별칭에는 제어 문자를 사용할 수 없습니다.")
    if not any(character.isalnum() for character in normalized):
        raise ValueError("계좌 별칭에는 한글/영문/숫자 중 하나 이상이 포함되어야 합니다.")
    invalid_characters = [
        character
        for character in normalized
        if not character.isalnum() and character not in PROFILE_ALIAS_ALLOWED_PUNCTUATION
    ]
    if invalid_characters:
        raise ValueError("계좌 별칭에는 한글, 영문, 숫자, 공백, '.', '_', '-'만 사용할 수 있습니다.")
    return normalized


def load_profiles() -> dict[str, AuthProfile]:
    payload = _load_settings_payload()
    raw_profiles = payload.get("profiles", {})
    if not isinstance(raw_profiles, dict):
        raise SettingsError("settings.json의 profiles 값은 객체(JSON object)여야 합니다.")

    profiles: dict[str, AuthProfile] = {}
    for alias, raw in raw_profiles.items():
        if not isinstance(alias, str) or not isinstance(raw, dict):
            raise SettingsError("settings.json의 profiles 항목 형식이 올바르지 않습니다.")
        profile_alias = validate_profile_alias(alias)
        mode_value = raw.get("mode")
        if not isinstance(mode_value, str):
            raise SettingsError(f"profile {alias!r}의 mode 값은 문자열이어야 합니다.")
        profiles[profile_alias] = AuthProfile(alias=profile_alias, mode=normalize_mode(mode_value))
    return profiles


def get_profile(alias: str) -> AuthProfile:
    profile_alias = validate_profile_alias(alias)
    profiles = load_profiles()
    try:
        return profiles[profile_alias]
    except KeyError as exc:
        raise SettingsError(f"저장된 Kiwoom 계좌 별칭을 찾을 수 없습니다: {profile_alias}") from exc


def get_current_profile() -> AuthProfile | None:
    payload = _load_settings_payload()
    current = payload.get("current_profile")
    if current is None:
        return None
    if not isinstance(current, str):
        raise SettingsError("settings.json의 current_profile 값은 문자열이어야 합니다.")
    profiles = load_profiles()
    return profiles.get(validate_profile_alias(current))


def save_profile(alias: str, mode: Mode, *, make_current: bool = True) -> AuthProfile:
    profile = AuthProfile(alias=validate_profile_alias(alias), mode=normalize_mode(mode))
    payload = _load_settings_payload()
    profiles = payload.get("profiles", {})
    if not isinstance(profiles, dict):
        profiles = {}
    profiles[profile.alias] = {"mode": profile.mode}
    payload["profiles"] = profiles
    if make_current:
        payload["current_profile"] = profile.alias
    _write_settings_payload(payload)
    return profile


def set_current_profile(alias: str) -> AuthProfile:
    profile = get_profile(alias)
    payload = _load_settings_payload()
    payload["current_profile"] = profile.alias
    _write_settings_payload(payload)
    return profile


def delete_profile(alias: str) -> None:
    profile_alias = validate_profile_alias(alias)
    payload = _load_settings_payload()
    profiles = payload.get("profiles", {})
    if isinstance(profiles, dict):
        profiles.pop(profile_alias, None)
        payload["profiles"] = profiles
    if payload.get("current_profile") == profile_alias:
        payload.pop("current_profile", None)
    _write_settings_payload(payload)


def _load_settings_payload() -> dict:
    path = settings_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SettingsError("settings.json 파일 형식이 올바르지 않습니다.") from exc
    except OSError as exc:
        raise SettingsError("settings.json 파일을 읽을 수 없습니다.") from exc
    if not isinstance(payload, dict):
        raise SettingsError("settings.json 최상위 형식은 객체(JSON object)여야 합니다.")
    return payload


def _write_settings_payload(payload: dict) -> Path:
    directory = ensure_private_directory(config_dir(), strict=False)
    path = directory / SETTINGS_FILE_NAME
    rendered = json.dumps(payload, ensure_ascii=True, indent=2)
    with NamedTemporaryFile("w", encoding="utf-8", dir=directory, delete=False) as tmp:
        tmp.write(rendered)
        temp_path = Path(tmp.name)
    protect_file(temp_path, strict=False)
    temp_path.replace(path)
    protect_file(path, strict=False)
    return path
