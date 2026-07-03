from __future__ import annotations

import argparse
import os
import shlex
import shutil
import stat
import sys
from dataclasses import dataclass, field
from pathlib import Path

from kiwoom.core.errors import KiwoomError, ModeNotConfiguredError
from kiwoom.core.platform_paths import cache_dir
from kiwoom.core.profiles import get_current_profile, load_profiles
from kiwoom.core.runtime import describe_selection
from kiwoom.core.secrets import env_var_names
from kiwoom.core.settings import get_mode_from_env, get_profile_from_env, settings_path
from kiwoom_cli.auth_context import build_auth_context


def add_doctor_parser(subparsers: argparse._SubParsersAction) -> None:
    doctor_parser = subparsers.add_parser(
        "doctor", help="설치/인증 컨텍스트 현재 상태를 진단합니다."
    )
    doctor_parser.set_defaults(handler=handle_doctor)


def handle_doctor(args: argparse.Namespace) -> None:
    print_doctor()


def command_path() -> str:
    return shutil.which("kiwoom") or "없음"


def current_executable() -> str:
    raw = sys.argv[0] or ""
    if not raw:
        return "알 수 없음"
    path = Path(raw)
    if not path.is_absolute():
        path = Path.cwd() / path
    return str(path)


def resolved_current_executable() -> str:
    raw = current_executable()
    if raw in {"", "알 수 없음"}:
        return raw
    return str(Path(raw).resolve())


def path_kiwoom_entries() -> list[str]:
    entries: list[str] = []
    seen: set[str] = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory:
            continue
        candidate = Path(directory) / "kiwoom"
        try:
            candidate_stat = candidate.stat()
        except OSError:
            continue
        if not stat.S_ISREG(candidate_stat.st_mode):
            continue
        if not os.access(candidate, os.X_OK):
            continue
        rendered = str(candidate)
        if rendered not in seen:
            entries.append(rendered)
            seen.add(rendered)
    return entries


@dataclass
class _Finding:
    """A diagnosed problem: symptom plus the exact command(s) to fix it."""

    symptom: str
    fixes: list[str] = field(default_factory=list)


def print_doctor() -> None:
    """Diagnose the current auth context. Verdict-first and never crashes.

    Every gathering step is defensive: a broken settings file or a conflicting
    environment becomes a reported finding, not a traceback — because doctor is
    exactly the command a user runs when those things are wrong.
    """
    print("Kiwoom CLI 진단")
    print()

    findings: list[_Finding] = []
    target_label, can_call_now, cause = _diagnose_target(findings)
    _diagnose_install(findings)

    _print_verdict(target_label, can_call_now, cause)
    print()
    _print_findings(findings)
    print()
    _print_detail()
    print()
    _print_environment_summary()


def _print_verdict(target_label: str, can_call_now: bool | None, cause: str | None) -> None:
    print("판정")
    print(f"  유효 대상: {target_label}")
    if can_call_now is None:
        print("  지금 호출 가능: 알 수 없음")
    else:
        print(f"  지금 호출 가능: {'예' if can_call_now else '아니오'}")
    if cause:
        print(f"  원인: {cause}")


def _print_findings(findings: list[_Finding]) -> None:
    print("발견된 문제")
    if not findings:
        print("  특이 사항이 없습니다.")
        return
    for finding in findings:
        print(f"  • {finding.symptom}")
        for fix in finding.fixes:
            print(f"    고치려면: {fix}")


def _diagnose_target(findings: list[_Finding]) -> tuple[str, bool | None, str | None]:
    """Resolve the default target and judge whether it can call now.

    Returns (target_label, can_call_now, cause). can_call_now is None when the
    target cannot be resolved (not configured / conflicting / unreadable).
    """
    current = _safe_current_profile(findings)

    try:
        selection = describe_selection()
    except ModeNotConfiguredError:
        findings.append(_Finding("기본 실행 대상이 설정되지 않았습니다.", ["kiwoom setup"]))
        return ("없음", None, "설정된 계좌 별칭 또는 모드가 없습니다")
    except ValueError as exc:
        # KIWOOM_PROFILE + KIWOOM_MODE point at conflicting modes.
        findings.append(
            _Finding(
                f"환경변수 충돌: {exc}",
                ["KIWOOM_MODE 또는 KIWOOM_PROFILE 중 하나를 unset 하세요"],
            )
        )
        return ("알 수 없음", None, "KIWOOM_PROFILE 과 KIWOOM_MODE 가 충돌합니다")
    except KiwoomError as exc:
        # e.g. KIWOOM_PROFILE names a missing profile, or settings unreadable.
        findings.append(_Finding(f"실행 대상을 해석할 수 없습니다: {exc}", ["kiwoom setup", "또는 KIWOOM_PROFILE 값 확인"]))
        return ("알 수 없음", None, str(exc))

    _append_override_finding(findings, current, selection)

    try:
        context = build_auth_context()
    except KiwoomError as exc:
        return (selection.target_label, None, f"상태 확인 실패: {exc}")

    if context.can_call_now:
        return (selection.target_label, True, None)

    status = context.status
    cause = "키/시크릿이 없고 사용 가능한 토큰도 없습니다"
    if selection.uses_profile:
        alias_arg = shlex.quote(str(selection.profile))
        fixes = [
            f"kiwoom auth login --alias {alias_arg} --mode {selection.mode}",
            f"kiwoom auth status --profile {alias_arg}",
        ]
        if status.has_token and not status.token_reusable and not status.has_credentials:
            symptom = (
                f"계좌 별칭 '{selection.profile}' 은 남아 있지만 저장된 키/시크릿을 "
                "읽을 수 없고 토큰도 재사용할 수 없습니다."
            )
        else:
            symptom = f"유효 대상 '{selection.profile}' 으로 지금 호출할 수 없습니다."
        findings.append(
            _Finding(
                symptom,
                fixes,
            )
        )
    else:
        appkey_var, secretkey_var = env_var_names(selection.mode)
        findings.append(
            _Finding(
                f"유효 대상 {selection.mode} mode 로 지금 호출할 수 없습니다 (키/시크릿 없음).",
                ["kiwoom setup", f"{appkey_var} / {secretkey_var} 환경변수 설정"],
            )
        )
    return (selection.target_label, False, cause)


def _append_override_finding(findings: list[_Finding], current, selection) -> None:
    """Flag when an environment variable overrides the configured current profile.

    This is the "demo인데 왜 real?" surprise: a stored current_profile is
    silently bypassed because KIWOOM_MODE / KIWOOM_PROFILE wins the precedence.
    """
    if current is None:
        return
    if selection.selection_source not in {"KIWOOM_MODE", "KIWOOM_PROFILE"}:
        return
    if selection.uses_profile and selection.profile == current.alias:
        return
    findings.append(
        _Finding(
            f"{selection.selection_source} 가 current_profile {current.alias}({current.mode})"
            f" 보다 우선 적용되어 유효 대상이 {selection.target_label} 입니다.",
            [
                f"unset {selection.selection_source}  (current_profile {current.alias} 사용)",
                f"kiwoom auth switch {current.alias}  (현재 유효 대상을 기본값으로 굳히기)",
            ],
        )
    )


def _diagnose_install(findings: list[_Finding]) -> None:
    entries = path_kiwoom_entries()
    if len(entries) > 1:
        finding = _Finding(
            f"PATH 에 kiwoom 실행 파일이 {len(entries)}개 있어 어떤 것이 실행될지 모호합니다.",
            ["which -a kiwoom 로 우선순위를 확인하세요"],
        )
        finding.fixes.extend(f"- {entry}" for entry in entries)
        findings.append(finding)


def _print_detail() -> None:
    current = _safe_current_profile(None)
    print("상세(근거)")
    print("  선택 규칙 입력")
    print(f"    current_profile: {current.alias if current else '없음'}")
    print(f"    KIWOOM_MODE: {get_mode_from_env() or '없음'}")
    print(f"    KIWOOM_PROFILE: {get_profile_from_env() or '없음'}")
    print("  저장된 프로필")
    try:
        profiles = load_profiles()
    except KiwoomError as exc:
        print(f"    프로필을 읽을 수 없습니다: {exc}")
        return
    if not profiles:
        print("    저장된 계좌 별칭이 없습니다.")
        return
    for alias in sorted(profiles):
        try:
            # Pass the profile's own mode so ambient KIWOOM_MODE can't trigger
            # a mode-mismatch while enumerating stored profiles.
            context = build_auth_context(mode=profiles[alias].mode, profile=alias)
        except KiwoomError as exc:
            print(f"    {alias}: 상태 확인 실패 ({exc})")
            continue
        status = context.status
        token_label = "사용 가능" if status.token_reusable else ("있음" if status.has_token else "없음")
        marker = " (current)" if current is not None and current.alias == alias else ""
        print(f"    {alias}{marker}: 서버={status.mode} 키/시크릿={'있음' if status.has_credentials else '없음'} "
              f"토큰={token_label} 호출={'가능' if context.can_call_now else '불가'} "
              f"재발급={'가능' if context.can_refresh else '불가'}")


def _print_environment_summary() -> None:
    print("실행 환경")
    print(f"  실행 대상: {resolved_current_executable()}")
    print(f"  설정 파일: {settings_path()}")
    print(f"  토큰 캐시: {cache_dir()}")
    # Detailed PATH/package listing only matters when there is an anomaly; the
    # multiple-kiwoom case is already surfaced as a finding above.
    entries = path_kiwoom_entries()
    if len(entries) > 1:
        print(f"  PATH 의 kiwoom: {len(entries)}개")
        for entry in entries:
            print(f"  - {entry}")


def _safe_current_profile(findings: list[_Finding] | None):
    try:
        return get_current_profile()
    except KiwoomError as exc:
        if findings is not None:
            findings.append(
                _Finding(f"current_profile 을 읽을 수 없습니다: {exc}", ["settings.json 확인 또는 kiwoom setup"])
            )
        return None
