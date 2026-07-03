from pathlib import Path


class KiwoomError(Exception):
    """Base error for the Kiwoom helper package."""


class SetupError(KiwoomError):
    """Raised when setup onboarding cannot complete."""


class InvalidModeError(KiwoomError):
    def __init__(self, value: str):
        super().__init__(
            f"지원하지 않는 모드 값입니다: {value!r}. "
            "사용 가능한 값은 'real' 또는 'demo' 입니다."
        )
        self.value = value


class SettingsError(KiwoomError):
    """Raised when the local settings file is unreadable or invalid."""


class ModeNotConfiguredError(KiwoomError):
    def __init__(self):
        super().__init__(
            "사용할 계좌가 설정되어 있지 않습니다. "
            "`kiwoom setup`으로 계좌를 등록하거나, 이미 등록한 계좌가 있으면 "
            "`kiwoom auth switch <별칭>`으로 선택해 주세요."
        )


class CredentialsNotFoundError(KiwoomError):
    def __init__(self, mode: str):
        super().__init__(
            f"{mode!r} 모드 자격 증명을 찾을 수 없습니다. "
            "다음 명령으로 초기 설정을 진행하거나, 환경변수를 설정해 주세요: "
            "kiwoom setup"
        )
        self.mode = mode


class KeyringUnavailableError(KiwoomError):
    """Raised when the OS credential store is unavailable."""


class InvalidTokenCacheError(KiwoomError):
    def __init__(self, path: Path, reason: str):
        super().__init__(f"토큰 캐시 파일이 올바르지 않습니다: {path} ({reason})")
        self.path = path
        self.reason = reason


class HTTPRequestError(KiwoomError):
    def __init__(self, status_code: int, message: str):
        super().__init__(f"HTTP 요청 실패 ({status_code}): {message}")
        self.status_code = status_code
        self.message = message


class AuthenticationError(KiwoomError):
    """Raised when token issuance or auth recovery fails."""


class APIError(KiwoomError):
    def __init__(self, return_code: int, return_msg: str):
        super().__init__(f"키움 API 오류 ({return_code}): {return_msg}")
        self.return_code = return_code
        self.return_msg = return_msg


class InputValidationError(APIError):
    """Raised when required fields or formats are invalid."""


class RateLimitError(APIError):
    """Raised when the API request limit is exceeded."""

    def __init__(self, return_code: int, return_msg: str):
        super().__init__(return_code, f"요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요. ({return_msg})")


class SymbolNotFoundError(APIError):
    """Raised when a requested symbol or market code is invalid."""

    def __init__(self, return_code: int, return_msg: str):
        super().__init__(return_code, f"종목 코드 또는 시장 정보가 올바르지 않습니다. ({return_msg})")


class InvalidCredentialsError(AuthenticationError):
    def __init__(self, return_code: int, return_msg: str):
        super().__init__(f"앱키 또는 시크릿키가 올바르지 않습니다 ({return_code}): {return_msg}")
        self.return_code = return_code
        self.return_msg = return_msg


class InvalidTokenError(AuthenticationError):
    def __init__(self, return_code: int, return_msg: str):
        super().__init__(f"접근 토큰이 올바르지 않거나 만료되었습니다 ({return_code}): {return_msg}")
        self.return_code = return_code
        self.return_msg = return_msg


class ModeMismatchError(AuthenticationError):
    def __init__(self, return_code: int, return_msg: str):
        super().__init__(f"실전/모의 모드가 일치하지 않습니다 ({return_code}): {return_msg}")
        self.return_code = return_code
        self.return_msg = return_msg


class DeviceAuthenticationError(AuthenticationError):
    def __init__(self, return_code: int, return_msg: str):
        super().__init__(f"단말기 인증에 실패했습니다 ({return_code}): {return_msg}")
        self.return_code = return_code
        self.return_msg = return_msg


INPUT_VALIDATION_CODES = {
    1501,
    1504,
    1505,
    1511,
    1512,
    1513,
    1514,
    1515,
    1516,
    1517,
    1687,
    8020,
}
RATE_LIMIT_CODES = {1700}
SYMBOL_NOT_FOUND_CODES = {1901, 1902}
INVALID_CREDENTIAL_CODES = {8001, 8002, 8011, 8012}
INVALID_TOKEN_CODES = {8003, 8005, 8006, 8009, 8015, 8016}
MODE_MISMATCH_CODES = {8030, 8031}
DEVICE_AUTH_CODES = {8010, 8040, 8050, 8103}


def raise_for_error_code(return_code: int, return_msg: str) -> None:
    if return_code in INPUT_VALIDATION_CODES:
        raise InputValidationError(return_code, return_msg)
    if return_code in RATE_LIMIT_CODES:
        raise RateLimitError(return_code, return_msg)
    if return_code in SYMBOL_NOT_FOUND_CODES:
        raise SymbolNotFoundError(return_code, return_msg)
    if return_code in INVALID_CREDENTIAL_CODES:
        raise InvalidCredentialsError(return_code, return_msg)
    if return_code in INVALID_TOKEN_CODES:
        raise InvalidTokenError(return_code, return_msg)
    if return_code in MODE_MISMATCH_CODES:
        raise ModeMismatchError(return_code, return_msg)
    if return_code in DEVICE_AUTH_CODES:
        raise DeviceAuthenticationError(return_code, return_msg)
    raise APIError(return_code, return_msg)
