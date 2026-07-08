import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from stat import S_IMODE
from tempfile import NamedTemporaryFile

from kiwoom.core.errors import InvalidTokenCacheError
from kiwoom.core.platform_paths import cache_dir, ensure_private_directory, protect_file
from kiwoom.core.profiles import validate_profile_alias
from kiwoom.core.types import Mode


VALID_TOKEN_TYPES = {"bearer"}


@dataclass(frozen=True)
class TokenRecord:
    access_token: str
    token_type: str
    expires_at: datetime
    mode: Mode
    profile: str | None = None
    credential_fingerprint: str | None = None
    saved_at: datetime | None = None

    def to_json(self) -> dict[str, str]:
        payload = {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_at": self.expires_at.astimezone(UTC).isoformat(),
            "mode": self.mode,
        }
        if self.profile:
            payload["profile"] = self.profile
        if self.credential_fingerprint:
            payload["credential_fingerprint"] = self.credential_fingerprint
        if self.saved_at:
            payload["saved_at"] = self.saved_at.astimezone(UTC).isoformat()
        return payload

    @classmethod
    def from_json(cls, payload: dict[str, str], *, path: Path) -> "TokenRecord":
        try:
            token_type = payload["token_type"].lower()
            expires_at = datetime.fromisoformat(payload["expires_at"])
            saved_at_value = payload.get("saved_at")
            saved_at = datetime.fromisoformat(saved_at_value) if saved_at_value else None
            mode = payload["mode"]
            access_token = payload["access_token"]
        except KeyError as exc:
            raise InvalidTokenCacheError(path, f"필수 필드가 없습니다: {exc.args[0]}") from exc
        except ValueError as exc:
            raise InvalidTokenCacheError(path, f"필드 형식이 올바르지 않습니다: {exc}") from exc

        if token_type not in VALID_TOKEN_TYPES:
            raise InvalidTokenCacheError(path, f"지원하지 않는 token_type 값입니다: {token_type}")
        if not access_token:
            raise InvalidTokenCacheError(path, "access_token 값이 비어 있습니다.")
        if expires_at.tzinfo is None:
            raise InvalidTokenCacheError(path, "expires_at에는 시간대 정보가 포함되어야 합니다.")
        if saved_at is not None and saved_at.tzinfo is None:
            raise InvalidTokenCacheError(path, "saved_at에는 시간대 정보가 포함되어야 합니다.")
        if mode not in ("real", "demo"):
            raise InvalidTokenCacheError(path, f"지원하지 않는 mode 값입니다: {mode}")

        profile = payload.get("profile")
        if profile is not None:
            try:
                profile = validate_profile_alias(profile)
            except ValueError as exc:
                raise InvalidTokenCacheError(path, f"profile 값이 올바르지 않습니다: {profile!r}") from exc

        return cls(
            access_token=access_token,
            token_type=token_type,
            expires_at=expires_at.astimezone(UTC),
            mode=mode,
            profile=profile,
            credential_fingerprint=payload.get("credential_fingerprint"),
            saved_at=saved_at.astimezone(UTC) if saved_at else None,
        )


class MemoryTokenStore:
    def __init__(self) -> None:
        self._records: dict[str, TokenRecord] = {}

    def load(self, mode: Mode, *, profile: str | None = None) -> TokenRecord | None:
        return self._records.get(self._key(mode, profile=profile))

    def save(self, record: TokenRecord) -> None:
        self._records[self._key(record.mode, profile=record.profile)] = record

    def clear(self, mode: Mode, *, profile: str | None = None) -> None:
        self._records.pop(self._key(mode, profile=profile), None)

    def peek(self, mode: Mode, *, profile: str | None = None) -> TokenRecord | None:
        return self.load(mode, profile=profile)

    @staticmethod
    def _key(mode: Mode, *, profile: str | None) -> str:
        return f"profile:{profile}" if profile else f"mode:{mode}"


class FileTokenStore:
    def __init__(self, *, strict_permissions: bool = True) -> None:
        self.strict_permissions = strict_permissions

    def load(self, mode: Mode, *, profile: str | None = None) -> TokenRecord | None:
        return self._read(mode, profile=profile, clear_on_error=True)

    def peek(self, mode: Mode, *, profile: str | None = None) -> TokenRecord | None:
        return self._read(mode, profile=profile, clear_on_error=False)

    def _read(self, mode: Mode, *, profile: str | None, clear_on_error: bool) -> TokenRecord | None:
        path = self._token_path(mode, profile=profile)
        if not path.exists():
            return None
        self._validate_permissions(path, clear_on_error=clear_on_error)

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            record = TokenRecord.from_json(payload, path=path)
        except json.JSONDecodeError as exc:
            if clear_on_error:
                self.clear(mode, profile=profile)
            raise InvalidTokenCacheError(path, f"JSON 파싱에 실패했습니다: {exc}") from exc
        except InvalidTokenCacheError:
            if clear_on_error:
                self.clear(mode, profile=profile)
            raise

        if record.mode != mode:
            if clear_on_error:
                self.clear(mode, profile=profile)
            raise InvalidTokenCacheError(path, "저장된 mode 값이 요청한 mode와 일치하지 않습니다.")

        return record

    def save(self, record: TokenRecord) -> None:
        directory = ensure_private_directory(self._token_directory(record.profile), strict=self.strict_permissions)
        path = self._token_path(record.mode, profile=record.profile)
        payload = json.dumps(record.to_json(), ensure_ascii=True, indent=2)

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=directory,
            delete=False,
        ) as tmp:
            tmp.write(payload)
            tmp.flush()
            os.fsync(tmp.fileno())
            temp_path = Path(tmp.name)

        protect_file(temp_path, strict=self.strict_permissions)
        temp_path.replace(path)
        protect_file(path, strict=self.strict_permissions)

    def clear(self, mode: Mode, *, profile: str | None = None) -> None:
        path = self._token_path(mode, profile=profile)
        path.unlink(missing_ok=True)

    @staticmethod
    def _token_directory(profile: str | None) -> Path:
        return cache_dir() / "profiles" if profile else cache_dir()

    @staticmethod
    def _token_path(mode: Mode, *, profile: str | None = None) -> Path:
        if profile:
            alias = validate_profile_alias(profile)
            digest = hashlib.sha256(alias.encode("utf-8")).hexdigest()[:16]
            return cache_dir() / "profiles" / f"profile-{digest}-token.json"
        return cache_dir() / f"{mode}-token.json"

    def _validate_permissions(self, path: Path, *, clear_on_error: bool) -> None:
        if os.name == "nt":
            return
        mode = S_IMODE(path.stat().st_mode)
        if mode & 0o077:
            if clear_on_error:
                path.unlink(missing_ok=True)
            raise InvalidTokenCacheError(path, "토큰 캐시 파일 권한이 너무 넓게 열려 있습니다.")
