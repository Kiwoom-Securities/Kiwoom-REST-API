"""CLI-owned exception taxonomy.

Separates user-fixable input/policy violations from should-be-unreachable
internal assertions so ``main()`` can present each differently: input errors
get a single Korean line the user can act on, while internal errors surface as
"내부 오류" with a traceback instead of being mistaken for user mistakes.

API/server errors stay as ``kiwoom.core`` ``KiwoomError`` subclasses and are
passed through unchanged; they are intentionally NOT remapped here.
"""

from __future__ import annotations


class CliError(Exception):
    """Base class for errors owned by the CLI layer."""


class CliInputError(CliError):
    """User input or policy violation (a single Korean message the user can fix)."""


class CliInternalError(CliError):
    """Should-be-unreachable internal assertion (reported as 내부 오류)."""
