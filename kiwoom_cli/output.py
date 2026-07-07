"""Output formatting for CLI command results."""

from __future__ import annotations

import json
from typing import Any, Iterable

from kiwoom.core.types import KiwoomResponse
from kiwoom_cli.errors import CliInternalError


OUTPUT_FORMATS = ("pretty", "json", "jsonl", "yaml")
ACCOUNT_IDENTIFIER_FIELDS = frozenset(
    {
        "acctNo",
        "acctno",
        "acct_no",
        "account_no",
        "account_number",
        "acnt_no",
        "acntNo",
        "acntno",
        "acnt_num",
        "cano",
    }
)
# Order numbers are operational identifiers the user needs to manage their own
# orders (e.g. read an `ord_no` from a buy/list response and pass it to
# modify/cancel), so they are NOT redacted. Account numbers are sensitive PII
# and stay redacted.
ACCOUNT_REDACT_FIELDS = ACCOUNT_IDENTIFIER_FIELDS


def format_response(
    response: KiwoomResponse,
    *,
    output_format: str = "pretty",
    redact_fields: Iterable[str] = (),
) -> str:
    return format_payload(response.body, output_format=output_format, redact_fields=redact_fields)


def format_payload(
    payload: Any,
    *,
    output_format: str = "pretty",
    redact_fields: Iterable[str] = (),
) -> str:
    payload = _redact_payload(payload, set(redact_fields))

    if output_format == "pretty":
        return json.dumps(payload, ensure_ascii=False, indent=2)
    if output_format == "json":
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    if output_format == "jsonl":
        return _to_jsonl(payload)
    if output_format == "yaml":
        return _to_yaml(payload)
    raise CliInternalError(f"지원하지 않는 출력 형식입니다: {output_format}")


def _to_jsonl(payload: Any) -> str:
    rows = payload if isinstance(payload, list) else [payload]
    return "\n".join(
        json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows
    )


def _redact_payload(value: Any, redact_fields: set[str]) -> Any:
    if not redact_fields:
        return value
    if isinstance(value, dict):
        return {
            key: _redact_sensitive_value(item)
            if _should_redact_key(key, redact_fields)
            else _redact_payload(item, redact_fields)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact_payload(item, redact_fields) for item in value]
    return value


def _should_redact_key(key: Any, redact_fields: set[str]) -> bool:
    text = str(key)
    return text in redact_fields or text.lower() in redact_fields


def _redact_sensitive_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _redact_sensitive_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_sensitive_value(item) for item in value]
    return _redact_value(value)


def _redact_value(value: Any) -> Any:
    if value is None:
        return None
    text = str(value)
    if len(text) <= 4:
        return "****"
    return f"{'*' * (len(text) - 4)}{text[-4:]}"


def _to_yaml(value: Any, *, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(_to_yaml(item, indent=indent + 2))
            else:
                lines.append(f"{prefix}{key}: {_yaml_scalar(item)}")
        return "\n".join(lines)
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.append(_to_yaml(item, indent=indent + 2))
            else:
                lines.append(f"{prefix}- {_yaml_scalar(item)}")
        return "\n".join(lines)
    return f"{prefix}{_yaml_scalar(value)}"


def _yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)
