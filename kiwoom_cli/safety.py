"""Safety policy checks for CLI command execution."""

from __future__ import annotations

from kiwoom_cli.errors import CliInputError, CliInternalError
from kiwoom_cli.registry import CommandDefinition


def enforce_before_request(definition: CommandDefinition, *, confirm: bool = False) -> None:
    if definition.coverage_status == "planned":
        raise CliInternalError(f"{definition.command_path}: 아직 실행 정책과 명령 UX가 확정되지 않은 명령입니다.")

    if definition.safety_policy in {"read", "account_read", "auth_write"}:
        return

    if definition.coverage_status == "preview-only":
        raise CliInternalError(f"{definition.command_path}: 미리보기 전용 명령이라 실제 쓰기 요청을 전송할 수 없습니다.")

    if definition.safety_policy == "order_write" and not confirm:
        raise CliInputError(f"{definition.command_path}: 실제 주문 전송에는 --confirm 옵션이 필요합니다.")

    if definition.safety_policy in {"review_required", "blocked_review"}:
        raise CliInternalError(f"{definition.command_path}: 실행 전에 정책 검토가 필요한 명령입니다.")


def enforce_before_preview(definition: CommandDefinition) -> None:
    if definition.safety_policy not in {"order_preview", "order_write"}:
        raise CliInternalError(f"{definition.command_path}: 요청 미리보기를 지원하지 않는 명령입니다.")
    if definition.coverage_status not in {"preview-only", "guarded"}:
        raise CliInternalError(f"{definition.command_path}: 현재 적용 상태에서는 요청 미리보기를 사용할 수 없습니다.")
