from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

Mode = Literal["real", "demo"]

VALID_MODES = ("real", "demo")

TokenStoreKind = Literal["file", "memory"]

VALID_TOKEN_STORE_KINDS = ("file", "memory")


def normalize_mode(value: str) -> Mode:
    if value not in VALID_MODES:
        raise ValueError(f"Unsupported mode: {value!r}. Expected one of {VALID_MODES}.")
    return value  # type: ignore[return-value]


def normalize_token_store_kind(value: str) -> TokenStoreKind:
    if value not in VALID_TOKEN_STORE_KINDS:
        raise ValueError(
            f"Unsupported token store kind: {value!r}. Expected one of {VALID_TOKEN_STORE_KINDS}."
        )
    return value  # type: ignore[return-value]


@dataclass(frozen=True)
class Continuation:
    has_next: bool
    next_key: str | None
    cont_yn: str | None


@dataclass(frozen=True)
class KiwoomResponse:
    body: dict[str, Any]
    continuation: Continuation
    headers: dict[str, str]
