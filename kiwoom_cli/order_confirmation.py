"""Order confirmation output for confirm-gated domestic order commands."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kiwoom_cli.errors import CliInternalError
from kiwoom_cli.output import format_payload
from kiwoom_cli.registry import CommandDefinition

MAP_ROOT = Path(__file__).resolve().parent / "maps"
COMMANDS_PATH = MAP_ROOT / "order_confirmation_commands.csv"
FIELDS_PATH = MAP_ROOT / "order_confirmation_fields.csv"
VALUE_LABELS_PATH = MAP_ROOT / "order_value_labels.csv"


@dataclass(frozen=True)
class OrderConfirmationCommand:
    command_path: str
    kind: str
    message: str


@dataclass(frozen=True)
class OrderConfirmationField:
    command_path: str
    output_key: str
    label: str
    arg_name: str
    value_label_group: str
    include_if_empty: bool
    empty_display: str


def build_order_confirmation(
    definition: CommandDefinition,
    args: argparse.Namespace,
) -> dict[str, Any]:
    command = get_order_confirmation_command(definition.command_path)
    if command is None:
        raise CliInternalError(
            f"{definition.command_path}: 주문 확인 출력 매핑이 없습니다."
        )
    fields = get_order_confirmation_fields(definition.command_path)
    value_labels = load_value_labels()
    order: dict[str, str] = {}
    display_rows: list[dict[str, str]] = []
    for field in fields:
        value = _field_value(
            field, command=command, args=args, value_labels=value_labels
        )
        if value == "" and not field.include_if_empty:
            continue
        display_value = field.empty_display if value == "" else value
        order[field.output_key] = display_value
        display_rows.append(
            {
                "key": field.output_key,
                "label": field.label,
                "value": display_value,
            }
        )
    return {
        "message": command.message,
        "order": order,
        "_display_rows": display_rows,
    }


def format_order_confirmation(payload: dict[str, Any], *, output_format: str) -> str:
    if output_format == "pretty":
        return _format_order_confirmation_pretty(payload)
    machine_payload = {
        "message": payload["message"],
        "order": payload["order"],
    }
    return format_payload(machine_payload, output_format=output_format)


def load_order_confirmation_commands(
    map_path: Path | None = None,
) -> list[OrderConfirmationCommand]:
    resolved_path = map_path or COMMANDS_PATH
    with resolved_path.open(encoding="utf-8", newline="") as file:
        return [
            OrderConfirmationCommand(
                command_path=row["command_path"],
                kind=row["kind"],
                message=row["message"],
            )
            for row in csv.DictReader(file)
        ]


def get_order_confirmation_command(
    command_path: str,
) -> OrderConfirmationCommand | None:
    for row in load_order_confirmation_commands():
        if row.command_path == command_path:
            return row
    return None


def load_order_confirmation_fields(
    map_path: Path | None = None,
) -> list[OrderConfirmationField]:
    resolved_path = map_path or FIELDS_PATH
    with resolved_path.open(encoding="utf-8", newline="") as file:
        return [_field_from_row(row) for row in csv.DictReader(file)]


def get_order_confirmation_fields(command_path: str) -> list[OrderConfirmationField]:
    return [
        field
        for field in load_order_confirmation_fields()
        if field.command_path == command_path
    ]


def load_value_labels(map_path: Path | None = None) -> dict[tuple[str, str], str]:
    resolved_path = map_path or VALUE_LABELS_PATH
    with resolved_path.open(encoding="utf-8", newline="") as file:
        return {
            (row["group"], row["value"]): row["label"] for row in csv.DictReader(file)
        }


def _field_from_row(row: dict[str, str]) -> OrderConfirmationField:
    return OrderConfirmationField(
        command_path=row["command_path"],
        output_key=row["output_key"],
        label=row["label"],
        arg_name=row["arg_name"],
        value_label_group=row["value_label_group"],
        include_if_empty=row["include_if_empty"] == "Y",
        empty_display=row["empty_display"],
    )


def _field_value(
    field: OrderConfirmationField,
    *,
    command: OrderConfirmationCommand,
    args: argparse.Namespace,
    value_labels: dict[tuple[str, str], str],
) -> str:
    if field.arg_name == "__kind__":
        value = command.kind
    else:
        value = getattr(args, field.arg_name, "")
        if value is None:
            value = ""
        value = str(value)
    if value and field.value_label_group:
        return value_labels.get((field.value_label_group, value), value)
    return value


def _format_order_confirmation_pretty(payload: dict[str, Any]) -> str:
    lines = [payload["message"], "", "주문 확인:"]
    for row in payload["_display_rows"]:
        lines.append(f"- {row['label']}: {row['value']}")
    return "\n".join(lines)
