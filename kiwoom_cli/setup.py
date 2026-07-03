import argparse
from dataclasses import dataclass, replace
from datetime import timedelta, timezone
from getpass import getpass
import sys

from kiwoom import get_auth, get_client
from kiwoom.core.auth import AuthStatus
from kiwoom.core.errors import KiwoomError, SetupError
from kiwoom.core.profiles import (
    AuthProfile,
    get_current_profile,
    load_profiles,
    save_profile,
    set_current_profile,
    validate_profile_alias,
)
from kiwoom.core.secrets import (
    CredentialSet,
    EnvSecretProvider,
    default_secret_provider,
)
from kiwoom.core.settings import restore_settings, snapshot_settings
from kiwoom.core.token_store import TokenRecord
from kiwoom.core.types import Mode, VALID_MODES, normalize_mode
from kiwoom_cli.arguments import resolve_optional_alias
from kiwoom_cli.auth_context import build_auth_context
from kiwoom_cli.banner import print_banner
from kiwoom_cli.doctor import path_kiwoom_entries


KST = timezone(timedelta(hours=9))
TEST_STOCK_CODE = "005930"  # 조회 테스트용, 삼성전자


def add_setup_parser(subparsers: argparse._SubParsersAction) -> None:
    setup_parser = subparsers.add_parser(
        "setup", help="대화형 계좌 인증 초기 설정을 실행합니다."
    )
    setup_parser.add_argument("alias_arg", nargs="?", metavar="alias", help="저장할 계좌 별칭")
    setup_parser.add_argument("--alias", help="저장할 계좌 별칭")
    setup_parser.add_argument("--mode", choices=VALID_MODES, help="계좌 별칭의 Kiwoom 모드")
    setup_parser.set_defaults(handler=handle_setup)


def handle_setup(args: argparse.Namespace) -> None:
    run_setup(
        alias=resolve_optional_alias(args.alias_arg, args.alias, "--alias"),
        mode=args.mode,
    )


@dataclass
class _EphemeralSecretProvider:
    appkey: str
    secretkey: str

    def get_credentials(self, mode: Mode) -> CredentialSet | None:
        return CredentialSet(appkey=self.appkey, secretkey=self.secretkey, source="prompt")

    def set_credentials(self, mode: Mode, appkey: str, secretkey: str) -> None:
        raise RuntimeError("임시 자격 증명 공급자는 읽기 전용입니다.")

    def clear_credentials(self, mode: Mode) -> None:
        raise RuntimeError("임시 자격 증명 공급자는 읽기 전용입니다.")


def run_setup(*, alias: str | None = None, mode: str | None = None) -> None:
    print_banner()
    print("Kiwoom CLI 초기 설정을 시작합니다.")
    print("이 과정에서:")
    print("  1) 실행 환경을 점검하고")
    print("  2) 계좌 별칭을 만들고")
    print("  3) demo/real 서버를 선택하고")
    print("  4) App Key / Secret을 운영체제 자격 증명 저장소에 저장하고")
    print("  5) 안전한 조회 API로 연결을 검증합니다.")
    print()
    _run_preflight()
    run_login(alias=alias, mode=mode)
    _print_readiness_summary()


def _run_preflight() -> None:
    print("환경 점검")
    available, detail = _credential_store_status()
    if available:
        print(f"  운영체제 자격 증명 저장소: 사용 가능 ({detail})")
    else:
        print(f"  운영체제 자격 증명 저장소: 사용 불가 - {detail}")
        print("    App Key/Secret은 이 저장소에 저장됩니다. 저장 단계에서 실패할 수 있습니다.")
        print("    지원되는 keyring 백엔드를 설치하거나 환경변수(APP_KEY/APP_SECRET)를 사용하세요.")
    entries = path_kiwoom_entries()
    if len(entries) > 1:
        print(
            f"  주의: PATH에 kiwoom 실행 파일이 {len(entries)}개 있습니다. "
            "`which -a kiwoom`로 우선순위를 확인하세요."
        )
    print()


def _credential_store_status() -> tuple[bool, str]:
    try:
        import keyring

        backend = keyring.get_keyring()
    except Exception as exc:  # keyring import/백엔드 조회 자체 실패
        return False, str(exc)
    module = type(backend).__module__
    if module.endswith(".fail") or module.endswith(".null"):
        return False, "사용 가능한 keyring 백엔드가 없습니다"
    return True, type(backend).__name__


def _print_readiness_summary() -> None:
    current = get_current_profile()
    if current is None:
        return
    try:
        context = build_auth_context(profile=current.alias)
    except KiwoomError:
        return
    print()
    print("준비 상태")
    print(f"  현재 계좌: {current.alias} ({current.mode})")
    print(f"  지금 호출 가능: {'예' if context.can_call_now else '아니오'}")


def run_login(*, alias: str | None = None, mode: str | None = None) -> None:
    if alias is None:
        selected_mode = normalize_mode(mode) if mode is not None else _select_mode()
        profile_alias = _select_profile_alias(alias, mode=selected_mode)
        existing_profile = _maybe_get_profile(profile_alias)
        if existing_profile is not None and existing_profile.mode != selected_mode:
            raise SetupError("같은 계좌 별칭이 이미 다른 모드로 등록되어 있습니다. 다른 별칭을 입력해 주세요.")
    else:
        profile_alias = _select_profile_alias(alias, mode=normalize_mode(mode) if mode is not None else None)
        existing_profile = _maybe_get_profile(profile_alias)
        selected_mode = _resolve_login_mode(mode=mode, existing_profile=existing_profile)

    if existing_profile is not None:
        status = get_auth(profile=profile_alias).status()
        _print_existing_setup_summary(profile_alias, selected_mode, status)
        action = _prompt_existing_state_action(status)
        if action == "keep":
            set_current_profile(profile_alias)
            print()
            print("기존 계좌 별칭을 현재 계좌로 선택했습니다.")
            print(f"다음 단계: kiwoom auth status --profile {profile_alias}")
            return
        if action == "refresh":
            _refresh_token_only(profile_alias, selected_mode)
            return
        if action == "reset":
            _reset_profile(profile_alias, selected_mode)
        # reconfigure/reset both continue to credential collection.

    print()
    print(f"{profile_alias} ({_mode_label(selected_mode)}) 계좌 인증을 설정합니다.")
    appkey, secretkey, token_record, stock_name = _collect_and_validate(selected_mode)
    _persist_setup_result(profile_alias, selected_mode, appkey, secretkey, token_record)
    _print_success_message(
        profile_alias,
        selected_mode,
        stock_name,
        summary="계좌 인증 설정이 완료되었습니다.",
    )


def _select_profile_alias(alias: str | None = None, *, mode: Mode | None = None) -> str:
    if alias is not None:
        try:
            return validate_profile_alias(alias)
        except ValueError as exc:
            raise SetupError(str(exc)) from exc

    default_alias = _default_profile_alias(mode)
    if not sys.stdin.isatty():
        return default_alias

    print("계좌 별칭을 입력해 주세요.")
    print("예: 모의계좌, 실전계좌, 가족계좌-demo")
    print(f"그냥 Enter를 누르면 '{default_alias}'로 저장합니다.")
    while True:
        value = input(f"계좌 별칭 [{default_alias}]: ").strip()
        if not value:
            return default_alias
        try:
            return validate_profile_alias(value)
        except ValueError as exc:
            print(str(exc))


def _resolve_login_mode(*, mode: str | None, existing_profile: AuthProfile | None) -> Mode:
    if mode is not None:
        selected = normalize_mode(mode)
        if existing_profile is not None and selected != existing_profile.mode:
            raise SetupError("기존 계좌 별칭의 모드와 다른 모드로는 덮어쓸 수 없습니다. 새 계좌 별칭을 사용해 주세요.")
        return selected
    if existing_profile is not None:
        return existing_profile.mode
    return _select_mode()


def _maybe_get_profile(alias: str) -> AuthProfile | None:
    return load_profiles().get(alias)


def _default_profile_alias(mode: Mode | None) -> str:
    if mode == "real":
        return "실전계좌"
    return "모의계좌"


def _select_mode(default: Mode | None = None) -> Mode:
    # demo first and as the Enter default so a stray keystroke can't land on
    # the real (실전) server during the bootstrap wizard.
    enter_default = default if default is not None else "demo"
    if not sys.stdin.isatty():
        if default is not None:
            return default
        raise SetupError("비대화형 환경에서는 --mode demo|real 을 지정해 주세요.")
    while True:
        print("사용할 서버를 선택해 주세요.")
        print("[1] demo  (모의투자)")
        print("[2] real  (실전투자)")
        print(f"Enter: {_mode_label(enter_default)}")
        choice = input("> ").strip()
        if choice == "":
            return enter_default
        if choice == "1":
            return "demo"
        if choice == "2":
            return "real"
        print("1 또는 2를 입력해 주세요.")


def _collect_and_validate(mode: Mode) -> tuple[str, str, TokenRecord, str]:
    env_credentials = EnvSecretProvider().get_credentials(mode)
    if env_credentials is not None:
        print(f"환경변수에서 {_mode_label(mode)} App Key와 Secret Key를 읽었습니다.")
        token_record, stock_name = _validate_credentials(
            mode, env_credentials.appkey, env_credentials.secretkey
        )
        return env_credentials.appkey, env_credentials.secretkey, token_record, stock_name

    print(f"키움에서 발급받은 {_mode_label(mode)} App Key와 Secret Key를 붙여넣어 주세요.")
    while True:
        appkey, secretkey = _collect_from_prompt()
        try:
            token_record, stock_name = _validate_credentials(mode, appkey, secretkey)
        except KiwoomError as exc:
            print(f"검증 실패: {exc}", file=sys.stderr)
            print("App Key/Secret Key를 다시 확인해 주세요. (취소: Ctrl-C)")
            continue
        return appkey, secretkey, token_record, stock_name


def _collect_from_prompt() -> tuple[str, str]:
    if not sys.stdin.isatty():
        raise SetupError("setup에서 자격 증명 입력은 대화형 터미널에서만 지원합니다.")
    print("입력한 값은 화면에 표시되지 않습니다.")
    appkey = getpass("App Key: ").strip()
    secretkey = getpass("Secret Key: ").strip()
    if not appkey or not secretkey:
        raise SetupError("App Key와 Secret Key를 모두 입력해 주세요.")
    return appkey, secretkey


def _validate_credentials(mode: Mode, appkey: str, secretkey: str) -> tuple[TokenRecord, str]:
    print("입력한 자격 증명을 확인하는 중입니다...")
    auth = get_auth(
        mode=mode,
        secret_provider=_EphemeralSecretProvider(appkey=appkey, secretkey=secretkey),
        token_store_kind="memory",
    )
    client = get_client(auth=auth)
    response = client.fetch_page(
        api_url="/api/dostk/stkinfo/ka10001",
        body={"stk_cd": TEST_STOCK_CODE},
    )
    token_record = auth.token_store.load(mode)
    if token_record is None:
        raise SetupError("검증은 성공했지만 토큰이 저장되지 않았습니다.")
    payload = response.body
    return token_record, str(payload.get("stk_nm", TEST_STOCK_CODE))


def _refresh_token_only(alias: str, mode: Mode) -> None:
    credentials = default_secret_provider(profile=alias).get_credentials(mode)
    if credentials is None:
        raise SetupError(f"{alias} 계좌 별칭의 자격 증명이 없어 토큰을 다시 발급할 수 없습니다.")

    print()
    print("저장된 자격 증명으로 토큰을 다시 발급합니다.")
    token_record, stock_name = _validate_credentials(mode, credentials.appkey, credentials.secretkey)
    _persist_token_result(alias, mode, token_record)
    _print_success_message(
        alias,
        mode,
        stock_name,
        summary="토큰을 새로 발급했습니다.",
    )


def _reset_profile(alias: str, mode: Mode) -> None:
    provider = default_secret_provider(profile=alias)
    credentials = provider.get_credentials(mode)
    get_auth(profile=alias).clear_token()
    print()
    print(f"{alias} 계좌 별칭의 토큰 캐시를 삭제했습니다.")
    if credentials is None:
        print("삭제할 자격 증명이 없습니다.")
        return

    provider.clear_credentials(mode)
    print("운영체제 자격 증명 저장소의 값도 삭제했습니다.")


def _print_existing_setup_summary(alias: str, mode: Mode, status: AuthStatus) -> None:
    print()
    print("이미 저장된 계좌 별칭을 찾았습니다.")
    print(f"계좌 별칭: {alias}")
    print(f"모드: {mode}")
    print(f"자격 증명 존재 여부: {'예' if status.has_credentials else '아니오'}")
    print(f"자격 증명 출처: {_credential_source_label(status.credential_source)}")
    print(f"토큰 존재 여부: {'예' if status.has_token else '아니오'}")
    print(f"토큰 유효 여부: {'예' if status.token_valid else '아니오'}")
    print(f"토큰 재사용 가능 여부: {'예' if status.token_reusable else '아니오'}")
    print(f"토큰 저장 시각: {_format_token_saved_at(status)}")
    print(f"토큰 만료 시각: {_format_token_expires_at(status)}")
    print(f"다음 API 호출 인증 동작: {_next_auth_action_label(status.next_auth_action)}")
    if status.token_warning:
        print(f"토큰 경고: {status.token_warning}")


def _prompt_existing_state_action(status: AuthStatus) -> str:
    if not sys.stdin.isatty():
        raise SetupError(
            "비대화형 환경에서는 기존 계좌 처리를 선택할 수 없습니다. "
            "대화형 터미널에서 실행하거나 kiwoom auth 하위 명령을 사용하세요."
        )
    print()
    print("어떻게 할까요?")
    print("[1] 이 계좌 별칭으로 전환")
    if status.has_credentials:
        print("[2] 토큰만 다시 발급")
    else:
        # Refresh needs stored credentials; show it disabled instead of letting
        # the user pick an action that can only fail in _refresh_token_only.
        print("[2] 토큰만 다시 발급 - 사용할 수 없음: 키/시크릿이 없습니다.")
    print("[3] App Key / Secret Key 다시 입력")
    print("[4] 자격 증명과 토큰 삭제 후 다시 설정")
    while True:
        choice = input("> ").strip()
        if choice == "1":
            return "keep"
        if choice == "2":
            if not status.has_credentials:
                print("키/시크릿이 없어 토큰만 재발급할 수 없습니다. [3]으로 키/시크릿을 다시 입력해 주세요.")
                continue
            return "refresh"
        if choice == "3":
            return "reconfigure"
        if choice == "4":
            return "reset"
        print("1, 2, 3, 4 중 하나를 입력해 주세요.")


def _mode_label(mode: Mode) -> str:
    return "real(실전)" if mode == "real" else "demo(모의)"


def _server_label(mode: Mode) -> str:
    return "실전투자(real)" if mode == "real" else "모의투자(demo)"


def _credential_source_label(source: str | None) -> str:
    return {
        "env": "환경변수",
        "keyring": "운영체제 자격 증명 저장소",
        "prompt": "입력값",
        None: "없음",
    }.get(source, source or "없음")


def _format_token_expires_at(status: AuthStatus) -> str:
    return _format_kst_datetime(status.token_expires_at)


def _format_token_saved_at(status: AuthStatus) -> str:
    return _format_kst_datetime(status.token_saved_at)


def _format_kst_datetime(value) -> str:
    if value is None:
        return "없음"
    return f"{value.astimezone(KST).isoformat()} (KST)"


def _next_auth_action_label(action: str) -> str:
    return {
        "use_cached_token": "캐시 토큰 사용",
        "issue_before_request": "다음 API 호출 시 새 토큰 자동 발급",
        "refresh_before_request": "다음 API 호출 시 토큰 자동 재발급",
        "credentials_missing": "자격 증명 필요",
    }.get(action, action)


def _print_success_message(alias: str, mode: Mode, stock_name: str, *, summary: str) -> None:
    print()
    print(summary)
    print(f"  계좌 별칭: {alias}")
    print(f"  서버: {_server_label(mode)}")
    print("  키/시크릿: 저장됨")
    print("  토큰: 발급됨")
    print(f"  API 검증: 성공 ({stock_name} {TEST_STOCK_CODE} 조회)")
    print("다음 명령:")
    print(f"  kiwoom auth status --profile {alias}")
    print(f"  kiwoom stocks info --code {TEST_STOCK_CODE} --profile {alias}")


def _persist_token_result(alias: str, mode: Mode, token_record: TokenRecord) -> None:
    previous_settings = snapshot_settings()
    save_profile(alias, mode, make_current=True)
    token_store = get_auth(profile=alias).token_store
    previous_token = token_store.peek(mode, profile=alias)
    try:
        token_store.save(replace(token_record, mode=mode, profile=alias))
        set_current_profile(alias)
    except Exception:
        if previous_token is None:
            token_store.clear(mode, profile=alias)
        else:
            token_store.save(previous_token)
        restore_settings(previous_settings)
        raise


def _persist_setup_result(alias: str, mode: Mode, appkey: str, secretkey: str, token_record: TokenRecord) -> None:
    previous_settings = snapshot_settings()
    save_profile(alias, mode, make_current=True)
    provider = default_secret_provider(profile=alias)
    token_store = get_auth(profile=alias).token_store
    previous_credentials = provider.get_credentials(mode)
    previous_token = token_store.peek(mode, profile=alias)

    try:
        provider.set_credentials(mode, appkey, secretkey)
        print("자격 증명을 운영체제 자격 증명 저장소에 저장했습니다.")
        token_store.save(replace(token_record, mode=mode, profile=alias))
        set_current_profile(alias)
    except Exception:
        if previous_token is None:
            token_store.clear(mode, profile=alias)
        else:
            token_store.save(previous_token)

        try:
            if previous_credentials is None:
                provider.clear_credentials(mode)
            else:
                provider.set_credentials(
                    mode,
                    previous_credentials.appkey,
                    previous_credentials.secretkey,
                )
        except Exception:
            pass
        finally:
            restore_settings(previous_settings)
        raise
