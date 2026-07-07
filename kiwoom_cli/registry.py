"""Load curated CLI command mappings."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from kiwoom_cli.errors import CliInternalError


MAP_PATH = Path(__file__).resolve().parent / "maps" / "api_commands.csv"


@dataclass(frozen=True)
class CommandDefinition:
    api_id: str
    api_name: str
    cli_group: str
    cli_command: str
    command_path: str
    status: str
    coverage_status: str
    safety_policy: str
    method: str
    path: str
    required_body_fields: tuple[str, ...]


def load_command_definitions(map_path: Path | None = None) -> list[CommandDefinition]:
    resolved_path = map_path or MAP_PATH
    if map_path is None:
        return list(_load_default_command_definitions())
    return _load_command_definitions_from_path(resolved_path)


@lru_cache(maxsize=1)
def _load_default_command_definitions() -> tuple[CommandDefinition, ...]:
    return tuple(_load_command_definitions_from_path(MAP_PATH))


def _load_command_definitions_from_path(resolved_path: Path) -> list[CommandDefinition]:
    with resolved_path.open(encoding="utf-8", newline="") as file:
        return [_definition_from_row(row) for row in csv.DictReader(file)]


def get_implemented_command(group: str, command: str) -> CommandDefinition:
    matches = [
        definition
        for definition in load_command_definitions()
        if definition.cli_group == group
        and definition.cli_command == command
        and definition.status == "implemented"
    ]
    if not matches:
        raise CliInternalError(f"구현된 명령을 찾을 수 없습니다: kiwoom {group} {command}")
    if len(matches) > 1:
        api_ids = ", ".join(definition.api_id for definition in matches)
        raise CliInternalError(f"구현된 명령 매핑이 중복됩니다: kiwoom {group} {command} ({api_ids})")
    return matches[0]


def get_command_by_path(command_path: str) -> CommandDefinition:
    matches = [
        definition
        for definition in load_command_definitions()
        if definition.command_path == command_path
    ]
    if not matches:
        raise CliInternalError(f"명령 매핑을 찾을 수 없습니다: {command_path}")
    if len(matches) > 1:
        api_ids = ", ".join(definition.api_id for definition in matches)
        raise CliInternalError(f"명령 경로 매핑이 중복됩니다: {command_path} ({api_ids})")
    return matches[0]


def _definition_from_row(row: dict[str, str]) -> CommandDefinition:
    return CommandDefinition(
        api_id=row["api_id"],
        api_name=row["api_name"],
        cli_group=row["cli_group"],
        cli_command=row["cli_command"],
        command_path=row["command_path"],
        status=row["status"],
        coverage_status=row["coverage_status"],
        safety_policy=row["safety_policy"],
        method=row["method"],
        path=row["path"],
        required_body_fields=_split_fields(row["required_body_fields"]),
    )


def _split_fields(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split(";") if part.strip())
