import hashlib
import os
from dataclasses import dataclass
from typing import Protocol

import keyring
from keyring.errors import KeyringError, NoKeyringError

from kiwoom.core.errors import KeyringUnavailableError
from kiwoom.core.types import Mode


@dataclass(frozen=True)
class CredentialSet:
    appkey: str
    secretkey: str
    source: str


class SecretProvider(Protocol):
    def get_credentials(self, mode: Mode) -> CredentialSet | None: ...

    def set_credentials(self, mode: Mode, appkey: str, secretkey: str) -> None: ...

    def clear_credentials(self, mode: Mode) -> bool: ...


class EnvSecretProvider:
    def get_credentials(self, mode: Mode) -> CredentialSet | None:
        appkey_var, secretkey_var = env_var_names(mode)
        appkey = os.getenv(appkey_var)
        secretkey = os.getenv(secretkey_var)
        if not appkey or not secretkey:
            return None
        return CredentialSet(appkey=appkey, secretkey=secretkey, source="env")

    def set_credentials(self, mode: Mode, appkey: str, secretkey: str) -> None:
        raise RuntimeError("환경변수 공급자는 읽기 전용입니다.")

    def clear_credentials(self, mode: Mode) -> bool:
        raise RuntimeError("환경변수 공급자는 읽기 전용입니다.")


class KeyringSecretProvider:
    def get_credentials(self, mode: Mode) -> CredentialSet | None:
        try:
            appkey = keyring.get_password(self._service_name(mode), "appkey")
            secretkey = keyring.get_password(self._service_name(mode), "secretkey")
        except NoKeyringError as exc:
            raise KeyringUnavailableError(
                "사용 가능한 운영체제 자격 증명 저장소를 찾을 수 없습니다. "
                "환경변수를 사용하거나 지원되는 keyring 백엔드를 설치해 주세요."
            ) from exc
        except KeyringError as exc:
            raise KeyringUnavailableError(f"운영체제 자격 증명 저장소를 읽는 중 오류가 발생했습니다: {exc}") from exc

        if not appkey or not secretkey:
            return None

        return CredentialSet(appkey=appkey, secretkey=secretkey, source="keyring")

    def set_credentials(self, mode: Mode, appkey: str, secretkey: str) -> None:
        try:
            keyring.set_password(self._service_name(mode), "appkey", appkey)
            keyring.set_password(self._service_name(mode), "secretkey", secretkey)
        except NoKeyringError as exc:
            raise KeyringUnavailableError(
                "사용 가능한 운영체제 자격 증명 저장소를 찾을 수 없습니다. "
                "환경변수를 사용하거나 지원되는 keyring 백엔드를 설치해 주세요."
            ) from exc
        except KeyringError as exc:
            self._best_effort_clear(mode)
            raise KeyringUnavailableError(f"운영체제 자격 증명 저장소에 저장하는 중 오류가 발생했습니다: {exc}") from exc

    def clear_credentials(self, mode: Mode) -> bool:
        try:
            deleted = False
            for name in ("appkey", "secretkey"):
                try:
                    keyring.delete_password(self._service_name(mode), name)
                    deleted = True
                except keyring.errors.PasswordDeleteError:
                    continue
            return deleted
        except NoKeyringError as exc:
            raise KeyringUnavailableError(
                "사용 가능한 운영체제 자격 증명 저장소를 찾을 수 없습니다. "
                "환경변수를 사용하거나 지원되는 keyring 백엔드를 설치해 주세요."
            ) from exc
        except KeyringError as exc:
            raise KeyringUnavailableError(f"운영체제 자격 증명 저장소를 정리하는 중 오류가 발생했습니다: {exc}") from exc

    @staticmethod
    def _service_name(mode: Mode) -> str:
        return f"kiwoom-{mode}"

    def _best_effort_clear(self, mode: Mode) -> None:
        for name in ("appkey", "secretkey"):
            try:
                keyring.delete_password(self._service_name(mode), name)
            except Exception:
                continue


class ProfileKeyringSecretProvider:
    def __init__(self, profile_alias: str) -> None:
        self.profile_alias = profile_alias

    def get_credentials(self, mode: Mode) -> CredentialSet | None:
        try:
            appkey = keyring.get_password(self._service_name(), "appkey")
            secretkey = keyring.get_password(self._service_name(), "secretkey")
        except NoKeyringError as exc:
            raise KeyringUnavailableError(
                "사용 가능한 운영체제 자격 증명 저장소를 찾을 수 없습니다. "
                "환경변수를 사용하거나 지원되는 keyring 백엔드를 설치해 주세요."
            ) from exc
        except KeyringError as exc:
            raise KeyringUnavailableError(f"운영체제 자격 증명 저장소를 읽는 중 오류가 발생했습니다: {exc}") from exc

        if not appkey or not secretkey:
            return None
        return CredentialSet(appkey=appkey, secretkey=secretkey, source="keyring")

    def set_credentials(self, mode: Mode, appkey: str, secretkey: str) -> None:
        try:
            keyring.set_password(self._service_name(), "appkey", appkey)
            keyring.set_password(self._service_name(), "secretkey", secretkey)
        except NoKeyringError as exc:
            raise KeyringUnavailableError(
                "사용 가능한 운영체제 자격 증명 저장소를 찾을 수 없습니다. "
                "환경변수를 사용하거나 지원되는 keyring 백엔드를 설치해 주세요."
            ) from exc
        except KeyringError as exc:
            self._best_effort_clear()
            raise KeyringUnavailableError(f"운영체제 자격 증명 저장소에 저장하는 중 오류가 발생했습니다: {exc}") from exc

    def clear_credentials(self, mode: Mode) -> bool:
        try:
            deleted = False
            for name in ("appkey", "secretkey"):
                try:
                    keyring.delete_password(self._service_name(), name)
                    deleted = True
                except keyring.errors.PasswordDeleteError:
                    continue
            return deleted
        except NoKeyringError as exc:
            raise KeyringUnavailableError(
                "사용 가능한 운영체제 자격 증명 저장소를 찾을 수 없습니다. "
                "환경변수를 사용하거나 지원되는 keyring 백엔드를 설치해 주세요."
            ) from exc
        except KeyringError as exc:
            raise KeyringUnavailableError(f"운영체제 자격 증명 저장소를 정리하는 중 오류가 발생했습니다: {exc}") from exc

    def _service_name(self) -> str:
        digest = hashlib.sha256(self.profile_alias.encode("utf-8")).hexdigest()[:16]
        return f"kiwoom-profile-{digest}"

    def _best_effort_clear(self) -> None:
        for name in ("appkey", "secretkey"):
            try:
                keyring.delete_password(self._service_name(), name)
            except Exception:
                continue


class CompositeSecretProvider:
    def __init__(
        self,
        *providers: SecretProvider,
        writable_provider: SecretProvider | None = None,
        suppress_read_errors: tuple[type[Exception], ...] = (),
    ) -> None:
        self.providers = providers
        self.writable_provider = writable_provider
        self.suppress_read_errors = suppress_read_errors

    def get_credentials(self, mode: Mode) -> CredentialSet | None:
        for provider in self.providers:
            try:
                credentials = provider.get_credentials(mode)
            except self.suppress_read_errors:
                continue
            if credentials is not None:
                return credentials
        return None

    def set_credentials(self, mode: Mode, appkey: str, secretkey: str) -> None:
        if self.writable_provider is None:
            raise RuntimeError("이 자격 증명 공급자는 읽기 전용입니다.")
        self.writable_provider.set_credentials(mode, appkey, secretkey)

    def clear_credentials(self, mode: Mode) -> bool:
        if self.writable_provider is None:
            raise RuntimeError("이 자격 증명 공급자는 읽기 전용입니다.")
        return self.writable_provider.clear_credentials(mode)


def default_secret_provider(*, profile: str | None = None) -> CompositeSecretProvider:
    if profile is not None:
        profile_keyring_provider = ProfileKeyringSecretProvider(profile)
        return CompositeSecretProvider(
            profile_keyring_provider,
            writable_provider=profile_keyring_provider,
            suppress_read_errors=(KeyringUnavailableError,),
        )

    keyring_provider = KeyringSecretProvider()
    return CompositeSecretProvider(
        EnvSecretProvider(),
        keyring_provider,
        writable_provider=keyring_provider,
        suppress_read_errors=(KeyringUnavailableError,),
    )


def env_var_names(mode: Mode) -> tuple[str, str]:
    if mode == "real":
        return "APP_KEY", "APP_SECRET"
    if mode == "demo":
        return "APP_KEY_MOCK", "APP_SECRET_MOCK"
    raise ValueError(f"Unsupported mode: {mode!r}")
