"""Shared auth-context composition for CLI status/doctor/error rendering.

This module does not redefine auth state. It composes the two existing
sources of truth:

- `kiwoom.core.runtime.describe_selection` — which input won target selection.
- `kiwoom.core.auth.AuthStatus` — credential/token health for that target.

`auth status`, `auth list`, `doctor`, and credential error messages all build
on `AuthContext` so they cannot disagree about "can I call now / later?".
"""

from __future__ import annotations

from dataclasses import dataclass

from kiwoom.core.auth import AuthStatus
from kiwoom.core.runtime import SelectionContext, describe_selection, get_auth


@dataclass(frozen=True)
class AuthContext:
    selection: SelectionContext
    status: AuthStatus

    @property
    def can_call_now(self) -> bool:
        """A request can be served right now."""
        # A reusable cached token works even without stored credentials;
        # otherwise credentials let auth issue/refresh before the request.
        return self.status.token_reusable or self.status.has_credentials

    @property
    def can_refresh(self) -> bool:
        """A fresh token can be issued/refreshed (needs credentials)."""
        return self.status.has_credentials

    def warnings(self) -> list[str]:
        messages: list[str] = []
        if self.status.token_warning:
            messages.append(self.status.token_warning)
        if self.status.token_reusable and not self.status.has_credentials:
            messages.append(
                "지금은 캐시 토큰으로 호출할 수 있지만, 토큰 만료 후에는 자동 재발급할 수 없습니다."
            )
        if not self.can_call_now:
            messages.append("현재 이 대상으로는 API를 호출할 수 없습니다.")
        return messages


def build_auth_context(
    mode: str | None = None,
    *,
    profile: str | None = None,
) -> AuthContext:
    """Resolve selection then snapshot auth health for that target.

    Raises `ModeNotConfiguredError` when nothing selects a target, matching
    `describe_selection`/`get_auth`.
    """

    selection = describe_selection(mode, profile=profile)
    auth = get_auth(mode, profile=profile)
    return AuthContext(selection=selection, status=auth.status())
