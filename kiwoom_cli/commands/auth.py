"""Account alias, auth status, token, and credential commands."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import timedelta, timezone
from pathlib import Path

from kiwoom import SelectionContext, describe_selection, get_auth
from kiwoom.core.auth import (
    KiwoomAuth,
    endpoint_env_var_names,
    get_base_url,
    get_ws_base_url,
)
from kiwoom.core.platform_paths import protect_file
from kiwoom.core.profiles import (
    delete_profile,
    get_current_profile,
    get_profile,
    load_profiles,
    set_current_profile,
)
from kiwoom.core.secrets import env_var_names
from kiwoom.core.types import VALID_MODES
from kiwoom_cli.arguments import resolve_optional_alias
from kiwoom_cli.auth_context import AuthContext, build_auth_context
from kiwoom_cli.errors import CliInputError
from kiwoom_cli.setup import run_login


KST = timezone(timedelta(hours=9))


def add_auth_parser(subparsers: argparse._SubParsersAction) -> None:
    auth_parser = subparsers.add_parser(
        "auth",
        help="계좌 별칭 등록/전환, 인증 상태 조회, 토큰 재발급, 서버 토큰 폐기, 로컬 인증 정보 정리를 수행합니다.",
    )
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command", required=True)

    login_parser = auth_subparsers.add_parser("login", help="계좌 별칭을 등록하거나 다시 설정합니다.")
    login_parser.add_argument("alias_arg", nargs="?", metavar="alias", help="저장할 계좌 별칭")
    login_parser.add_argument("--alias", help="저장할 계좌 별칭")
    login_parser.add_argument("--mode", choices=VALID_MODES, help="계좌 별칭의 Kiwoom 모드")
    login_parser.set_defaults(handler=handle_auth_login)

    list_parser = auth_subparsers.add_parser(
        "list", help="저장된 계좌 별칭 목록과 현재 선택된 계좌를 보여줍니다."
    )
    list_parser.set_defaults(handler=handle_auth_list)

    switch_parser = auth_subparsers.add_parser("switch", help="현재 계좌 별칭을 전환합니다.")
    switch_parser.add_argument("alias", help="전환할 계좌 별칭")
    switch_parser.set_defaults(handler=handle_auth_switch)

    status_parser = auth_subparsers.add_parser("status", help="자격 증명과 토큰 상태를 확인합니다.")
    _add_auth_target_args(status_parser)
    status_parser.set_defaults(handler=handle_auth_status)

    refresh_parser = auth_subparsers.add_parser(
        "refresh",
        help="저장된 자격 증명으로 새 접근 토큰을 발급하고 로컬 캐시를 갱신합니다.",
    )
    _add_auth_target_args(refresh_parser)
    refresh_parser.set_defaults(handler=handle_auth_refresh)

    revoke_parser = auth_subparsers.add_parser(
        "revoke",
        help="로컬 토큰 캐시에 저장된 현재 토큰을 서버에서 폐기하고 로컬 캐시도 삭제합니다.",
    )
    _add_auth_target_args(revoke_parser)
    revoke_parser.set_defaults(handler=handle_auth_revoke)

    clear_parser = auth_subparsers.add_parser("clear", help="로컬 토큰 캐시를 삭제합니다.")
    _add_auth_target_args(clear_parser)
    clear_parser.add_argument(
        "--all",
        dest="clear_all",
        action="store_true",
        help="로컬 토큰 캐시와 운영체제 자격 증명 저장소의 값을 삭제합니다. 환경변수는 삭제하지 않습니다.",
    )
    clear_parser.add_argument(
        "--credentials",
        dest="clear_all",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    clear_parser.set_defaults(handler=handle_auth_clear)

    remove_parser = auth_subparsers.add_parser(
        "remove",
        help="계좌 별칭 등록을 삭제합니다(토큰 캐시와 자격 증명도 함께 삭제).",
    )
    remove_parser.add_argument("alias", help="삭제할 계좌 별칭")
    remove_parser.set_defaults(handler=handle_auth_remove)

    export_parser = auth_subparsers.add_parser(
        "export",
        help="저장된 App Key/Secret을 파일(.env)로 내보냅니다(화면에는 출력하지 않음).",
    )
    _add_auth_target_args(export_parser)
    export_parser.add_argument(
        "--dir", help="내보낼 폴더. 생략하면 현재 폴더에 저장하며 확인을 요청합니다."
    )
    export_parser.add_argument(
        "--yes", action="store_true", help="내보내기 확인 프롬프트를 생략합니다."
    )
    export_parser.set_defaults(handler=handle_auth_export)


def handle_auth_login(args: argparse.Namespace) -> None:
    run_login(
        alias=resolve_optional_alias(args.alias_arg, args.alias, "--alias"),
        mode=args.mode,
    )


def handle_auth_list(args: argparse.Namespace) -> None:
    _print_profile_list()


def handle_auth_switch(args: argparse.Namespace) -> None:
    profile = set_current_profile(args.alias)
    print(f"현재 계좌 별칭: {profile.alias} ({profile.mode})")
    print(f"다음 단계: kiwoom auth status --profile {profile.alias}")


def handle_auth_remove(args: argparse.Namespace) -> None:
    profile = get_profile(args.alias)
    was_current = bool(
        get_current_profile() and get_current_profile().alias == profile.alias
    )
    auth = get_auth(profile=profile.alias)
    auth.clear_token()
    auth.secret_provider.clear_credentials(profile.mode)
    delete_profile(profile.alias)
    print(f"계좌 별칭 {profile.alias} ({profile.mode})을(를) 삭제했습니다.")
    print("등록, 토큰 캐시, 운영체제 자격 증명 저장소의 값을 모두 제거했습니다.")
    if was_current:
        print("현재 선택된 계좌였으므로 현재 계좌 선택도 해제했습니다.")


def handle_auth_export(args: argparse.Namespace) -> None:
    auth, auth_label = _resolve_auth(args)
    credentials = auth.secret_provider.get_credentials(auth.mode)
    if credentials is None:
        raise CliInputError(
            f"{auth_label}: 내보낼 App Key/Secret이 없습니다. 먼저 kiwoom setup으로 저장하세요."
        )

    target = auth.profile or auth.mode
    used_default_dir = not args.dir
    dest_dir = Path(args.dir).expanduser() if args.dir else Path.cwd()
    dest_file = dest_dir / f"kiwoom_{target}.env"

    if used_default_dir:
        print(f"저장 위치를 지정하지 않아 현재 폴더에 저장합니다: {dest_file}")
    else:
        print(f"저장 위치: {dest_file}")

    if not _confirm_export(args):
        print("내보내기를 취소했습니다.")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    _write_credentials_file(dest_file, auth.mode, credentials, auth_label)
    gitignore_note = _register_gitignore(dest_file)

    permission_note = (
        "현재 사용자 전용 (Windows ACL)"
        if os.name == "nt"
        else "0600 (소유자 전용)"
    )

    print()
    print(f"{auth_label} App Key/Secret을 파일로 내보냈습니다.")
    print(f"  파일: {dest_file}")
    print(f"  권한: {permission_note}")
    print(f"  .gitignore: {gitignore_note}")
    print("주의: 평문 자격증명 파일입니다. 공유하거나 커밋하지 마세요.")


def _confirm_export(args: argparse.Namespace) -> bool:
    if getattr(args, "yes", False):
        return True
    if not sys.stdin.isatty():
        raise CliInputError(
            "비대화형 환경에서 자격증명 내보내기는 --yes 옵션이 필요합니다."
        )
    print("경고: App Key/Secret을 평문 파일로 저장합니다.")
    return input("정말 내보내시겠습니까? [y/N] ").strip().lower() in {"y", "yes"}


def _write_credentials_file(
    path: Path, mode: str, credentials, auth_label: str
) -> None:
    appkey_var, secretkey_var = env_var_names(mode)
    content = "\n".join(
        [
            f"# kiwoom-cli App Key/Secret export - {auth_label}",
            "# 평문 자격증명입니다. 절대 공유/커밋하지 마세요.",
            f"{appkey_var}={credentials.appkey}",
            f"{secretkey_var}={credentials.secretkey}",
            "",
        ]
    )
    # POSIX에서는 생성 순간부터 0600으로 열어 넓은 권한 노출 창을 없앤다.
    # (Windows에서는 mode 인자가 사실상 무시되므로 아래 protect_file이 실제 제한을 담당한다.)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        file.write(content)
    # 토큰/프로필 저장과 동일한 공용 보호를 적용한다.
    # POSIX: chmod 0600, Windows: icacls로 상속 제거 후 현재 사용자 전용.
    protect_file(path)


def _register_gitignore(file_path: Path) -> str:
    repo_root = _find_repo_root(file_path.parent.resolve())
    if repo_root is None:
        return "git 저장소가 아니라 등록을 건너뜁니다"
    gitignore = repo_root / ".gitignore"
    try:
        relative = file_path.resolve().relative_to(repo_root)
    except ValueError:
        entry = file_path.name
    else:
        entry = "/" + str(relative).replace(os.sep, "/")
    existing = (
        gitignore.read_text(encoding="utf-8").splitlines()
        if gitignore.exists()
        else []
    )
    if entry in existing or file_path.name in existing:
        return f"이미 등록됨 ({gitignore})"
    with gitignore.open("a", encoding="utf-8") as file:
        if existing and existing[-1].strip() != "":
            file.write("\n")
        file.write("# kiwoom-cli exported credentials (do not commit)\n")
        file.write(f"{entry}\n")
    return f"{entry} 등록됨 ({gitignore})"


def _find_repo_root(start: Path) -> Path | None:
    for parent in (start, *start.parents):
        if (parent / ".git").exists():
            return parent
    return None


def handle_auth_status(args: argparse.Namespace) -> None:
    auth, auth_label = _resolve_auth(args)
    selection = describe_selection(
        getattr(args, "mode", None), profile=getattr(args, "profile", None)
    )
    _print_auth_status(auth, auth_label, selection)


def handle_auth_refresh(args: argparse.Namespace) -> None:
    auth, auth_label = _resolve_auth(args)
    auth.refresh_access_token()
    status = auth.status()
    print(f"{auth_label} 새 접근 토큰을 발급했습니다.")
    print(f"토큰 저장 시각: {_format_kst_datetime(status.token_saved_at, none_label='알 수 없음')}")
    print(f"토큰 만료 시각: {_format_kst_datetime(status.token_expires_at, none_label='알 수 없음')}")
    print(f"다음 단계: kiwoom auth status{_auth_target_hint(auth)}")


def handle_auth_revoke(args: argparse.Namespace) -> None:
    auth, auth_label = _resolve_auth(args)
    auth.revoke_access_token()
    print(f"{auth_label} 로컬 토큰 캐시에 저장된 현재 토큰을 서버에서 폐기했습니다.")
    print("로컬 토큰 캐시도 삭제했습니다.")


def handle_auth_clear(args: argparse.Namespace) -> None:
    auth, auth_label = _resolve_auth(args)
    auth.clear_token()
    if args.clear_all:
        auth.secret_provider.clear_credentials(auth.mode)
    print(f"{auth_label} 토큰 캐시를 삭제했습니다.")
    if args.clear_all:
        print("운영체제 자격 증명 저장소의 값도 삭제했습니다.")
        if auth.profile is None:
            appkey_var, secretkey_var = env_var_names(auth.mode)
            remaining_env = [name for name in (appkey_var, secretkey_var) if os.getenv(name)]
            if remaining_env:
                print("다음 환경변수는 여전히 우선 적용됩니다.")
                for name in remaining_env:
                    print(f"- {name}")


def _resolve_auth(args: argparse.Namespace) -> tuple[KiwoomAuth, str]:
    if hasattr(args, "profile_arg"):
        args.profile = resolve_optional_alias(args.profile_arg, args.profile, "--profile")
    auth: KiwoomAuth = get_auth(
        mode=getattr(args, "mode", None), profile=getattr(args, "profile", None)
    )
    return auth, _auth_label(auth)


def _add_auth_target_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "profile_arg",
        nargs="?",
        metavar="alias",
        help="대상 계좌 별칭입니다. --profile 대신 사용할 수 있습니다.",
    )
    parser.add_argument(
        "--profile",
        help="사용할 계좌 별칭입니다. --mode/KIWOOM_MODE가 없을 때 생략하면 현재 계좌 별칭을 사용합니다.",
    )
    parser.add_argument("--mode", choices=VALID_MODES, help="계좌 별칭 대신 모드를 직접 지정합니다.")


def _print_profile_list() -> None:
    profiles = load_profiles()
    current = get_current_profile()
    if not profiles:
        print("저장된 계좌 별칭이 없습니다.")
        print("다음 단계: kiwoom auth login")
        return

    print("계좌 별칭 목록:")
    for alias in sorted(profiles):
        profile = profiles[alias]
        marker = "*" if current is not None and current.alias == alias else " "
        # Pass the profile's own mode so ambient KIWOOM_MODE can't trigger a
        # mode-mismatch while listing stored profiles.
        context = build_auth_context(mode=profile.mode, profile=alias)
        status = context.status
        credential_label = "credentials=예" if status.has_credentials else "credentials=아니오"
        token_label = "token=재사용 가능" if status.token_reusable else "token=재발급 필요" if status.has_token else "token=없음"
        call_label = "지금 호출=가능" if context.can_call_now else "지금 호출=불가"
        refresh_label = "재발급=가능" if context.can_refresh else "재발급=불가"
        print(
            f"{marker} {profile.alias}\tmode={profile.mode}\t{credential_label}\t"
            f"{token_label}\t{call_label}\t{refresh_label}"
        )


def _print_auth_status(auth: KiwoomAuth, auth_label: str, selection: SelectionContext) -> None:
    context = AuthContext(selection=selection, status=auth.status())
    status = context.status
    credential_source = {
        "env": "환경변수",
        "keyring": "운영체제 자격 증명 저장소",
        None: "없음",
    }.get(status.credential_source, status.credential_source or "없음")
    print(f"선택 방식: {selection.selection_source}")
    if status.profile:
        print(f"계좌 별칭: {status.profile}")
    print(f"모드: {status.mode}")
    print(f"대상: {auth_label}")
    _print_endpoint_status(status.mode)
    print(f"자격 증명 존재: {'예' if status.has_credentials else '아니오'}")
    print(f"자격 증명 출처: {credential_source}")
    print(f"토큰 존재: {'예' if status.has_token else '아니오'}")
    print(f"토큰 유효: {'예' if status.token_valid else '아니오'}")
    print(f"토큰 재사용 가능: {'예' if status.token_reusable else '아니오'}")
    print(f"토큰 저장 시각: {_format_kst_datetime(status.token_saved_at)}")
    print(f"토큰 만료 시각: {_format_kst_datetime(status.token_expires_at)}")
    print(f"다음 API 호출 인증 동작: {_next_auth_action_label(status.next_auth_action)}")
    print(f"지금 API 호출 가능: {'예' if context.can_call_now else '아니오'}")
    print(f"토큰 재발급 가능: {'예' if context.can_refresh else '아니오'}")
    for warning in context.warnings():
        print(f"주의: {warning}")


def _print_endpoint_status(mode: str) -> None:
    rest_var, ws_var = endpoint_env_var_names(mode)
    print(f"REST 주소: {get_base_url(mode)} ({rest_var}, {_endpoint_source_label(rest_var)})")
    print(f"WebSocket 주소: {get_ws_base_url(mode)} ({ws_var}, {_endpoint_source_label(ws_var)})")


def _endpoint_source_label(env_name: str) -> str:
    return "환경변수" if os.getenv(env_name) else "기본값"


def _auth_label(auth: KiwoomAuth) -> str:
    if auth.profile:
        return f"계좌 별칭 {auth.profile} ({auth.mode})"
    return f"{auth.mode} mode"


def _auth_target_hint(auth: KiwoomAuth) -> str:
    if auth.profile:
        return f" --profile {auth.profile}"
    return f" --mode {auth.mode}"


def _format_kst_datetime(value, *, none_label: str = "없음") -> str:
    if value is None:
        return none_label
    return f"{value.astimezone(KST).isoformat()} (KST)"


def _next_auth_action_label(action: str) -> str:
    return {
        "use_cached_token": "캐시 토큰 사용",
        "issue_before_request": "다음 API 호출 시 새 토큰 자동 발급",
        "refresh_before_request": "다음 API 호출 시 토큰 자동 재발급",
        "credentials_missing": "자격 증명 필요",
    }.get(action, action)
