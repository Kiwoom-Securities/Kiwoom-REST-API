"""Load explicit CLI argument-to-Kiwoom-field mappings."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable

from kiwoom_cli.errors import CliInputError, CliInternalError

from kiwoom_cli.arguments import (
    adjusted_price_flag,
    date_yyyymmdd,
    exchange_stock_code,
    instrument_code,
    nonnegative_int_string,
    order_id,
    preview_order_id,
    positive_int_string,
    price_string,
    sector_code,
    stock_code,
)


MAP_PATH = Path(__file__).resolve().parent / "maps" / "arguments.csv"
ORDER_PRICE_POLICY_PATH = (
    Path(__file__).resolve().parent / "maps" / "order_price_policies.csv"
)
ALLOWED_ORDER_PRICE_POLICIES = {"required", "optional", "forbidden"}


TYPE_PARSERS: dict[str, Callable[[str], str]] = {
    "stock_code": stock_code,
    "exchange_stock_code": exchange_stock_code,
    "instrument_code": instrument_code,
    "sector_code": sector_code,
    "date_yyyymmdd": date_yyyymmdd,
    "adjusted_price_flag": adjusted_price_flag,
    "quantity": positive_int_string,
    "cancel_quantity": nonnegative_int_string,
    "price": price_string,
    "order_id": order_id,
    "preview_order_id": preview_order_id,
    "order_type": str,
    "market": str,
}


@dataclass(frozen=True)
class OrderPricePolicy:
    command_path: str
    order_type: str
    price_option: str
    price_policy: str
    condition_price_option: str
    condition_price_policy: str
    description: str


@dataclass(frozen=True)
class ArgumentDefinition:
    command_path: str
    option: str
    dest: str
    kiwoom_field: str
    required: bool
    type_name: str
    choices: tuple[str, ...]
    value_map: dict[str, str]
    default: str
    description: str


def load_argument_definitions(map_path: Path | None = None) -> list[ArgumentDefinition]:
    resolved_path = map_path or MAP_PATH
    if map_path is None:
        return list(_load_default_argument_definitions())
    return _load_argument_definitions_from_path(resolved_path)


@lru_cache(maxsize=1)
def _load_default_argument_definitions() -> tuple[ArgumentDefinition, ...]:
    return tuple(_load_argument_definitions_from_path(MAP_PATH))


def _load_argument_definitions_from_path(resolved_path: Path) -> list[ArgumentDefinition]:
    with resolved_path.open(encoding="utf-8", newline="") as file:
        return [_definition_from_row(row) for row in csv.DictReader(file)]


def get_argument_definitions(command_path: str) -> list[ArgumentDefinition]:
    return [
        definition
        for definition in load_argument_definitions()
        if definition.command_path == command_path
    ]


def load_order_price_policies(
    map_path: Path | None = None,
) -> list[OrderPricePolicy]:
    resolved_path = map_path or ORDER_PRICE_POLICY_PATH
    if not resolved_path.exists():
        return []
    with resolved_path.open(encoding="utf-8", newline="") as file:
        return [_order_price_policy_from_row(row) for row in csv.DictReader(file)]


def get_order_price_policy(
    command_path: str, order_type: str
) -> OrderPricePolicy | None:
    for policy in load_order_price_policies():
        if policy.command_path == command_path and policy.order_type == order_type:
            return policy
    return None


def add_mapped_arguments(
    parser: argparse.ArgumentParser,
    command_path: str,
    *,
    required_overrides: dict[str, bool] | None = None,
    action_overrides: dict[str, str] | None = None,
) -> None:
    required_overrides = required_overrides or {}
    action_overrides = action_overrides or {}
    definitions = get_argument_definitions(command_path)
    alternative_fields = _alternative_required_fields(definitions)
    for definition in definitions:
        if not definition.option:
            continue
        required = required_overrides.get(
            definition.dest, definition.required and definition.default == ""
        )
        if definition.kiwoom_field in alternative_fields:
            required = False
        kwargs: dict[str, object] = {
            "dest": definition.dest,
            "required": required,
            "help": definition.description,
        }
        action = action_overrides.get(definition.dest)
        if action:
            kwargs["action"] = action
        type_parser = TYPE_PARSERS.get(definition.type_name)
        if type_parser is not None:
            kwargs["type"] = type_parser
        if definition.choices:
            kwargs["choices"] = definition.choices
        if definition.default and not action:
            kwargs["default"] = definition.default
        parser.add_argument(definition.option, **kwargs)
    attach_mapped_help_epilog(parser, command_path, definitions)


def attach_mapped_help_epilog(
    parser: argparse.ArgumentParser,
    command_path: str,
    definitions: list[ArgumentDefinition] | None = None,
) -> None:
    definitions = definitions if definitions is not None else get_argument_definitions(command_path)
    try:
        from kiwoom_cli.registry import get_command_by_path

        command = get_command_by_path(command_path)
    except ValueError:
        command = None

    sections: list[str] = []
    if command is not None:
        sections.extend(
            [
                "Summary:",
                f"  {command.api_name}.",
                "",
                "Behavior:",
                f"  {_behavior_text(command.command_path, command.safety_policy, command.coverage_status)}",
                "",
                "Examples:",
                f"  {_example_command(command_path, definitions)}",
                "",
                "OpenAPI mapping:",
                f"  API ID: {command.api_id}",
                f"  Request: {command.method} {command.path}",
            ]
        )
    else:
        sections.extend(
            [
                "Examples:",
                f"  {_example_command(command_path, definitions)}",
                "",
                "OpenAPI mapping:",
            ]
        )

    for line in _mapping_lines(definitions):
        sections.append(f"  {line}")

    extra = "\n".join(sections).rstrip()
    if parser.epilog:
        parser.epilog = f"{parser.epilog.rstrip()}\n\n{extra}"
    else:
        parser.epilog = extra


def _behavior_text(command_path: str, safety_policy: str, coverage_status: str) -> str:
    if _is_stream_subscription_command(command_path):
        return (
            "WebSocket stream 구독 명령입니다. foreground에서 실시간 이벤트를 수신하며, "
            "--count/--duration/--check로 종료 조건을 주거나 --watch로 계속 수신합니다. "
            "--output으로 이벤트를 JSONL 파일에 기록할 수 있습니다."
        )
    if safety_policy == "read":
        return "조회 전용 명령입니다. 계좌/주문 상태를 변경하지 않습니다."
    if safety_policy == "account_read":
        return "계좌 조회 명령입니다. 출력에는 공통 계좌번호 redaction 정책이 적용됩니다."
    if safety_policy == "order_write":
        return "--confirm 없이는 실제 주문 API를 호출하지 않고 미전송 주문 확인만 출력합니다."
    if safety_policy == "order_preview" or coverage_status == "preview-only":
        return "요청 생성/검증 전용 명령입니다. 실제 쓰기 요청은 전송하지 않습니다."
    if safety_policy in {"review_required", "blocked_review"}:
        return "실행 전 정책 검토가 필요한 명령입니다."
    if safety_policy == "auth_write":
        return "인증/토큰 상태를 변경할 수 있는 명령입니다."
    return f"안전 정책: {safety_policy}, 적용 상태: {coverage_status}."


def _is_stream_subscription_command(command_path: str) -> bool:
    if not command_path.startswith("kiwoomcli domestic streams "):
        return False
    command = command_path.removeprefix("kiwoomcli domestic streams ")
    return not command.startswith("conditions-")


def _example_command(command_path: str, definitions: list[ArgumentDefinition]) -> str:
    parts = [command_path]
    included_options: set[str] = set()
    for definition in definitions:
        if not definition.option:
            continue
        if not definition.required or definition.default:
            continue
        parts.extend([definition.option, _example_value(definition)])
        included_options.add(definition.option)
    _append_order_policy_example_options(parts, included_options, command_path, definitions)
    return " ".join(parts)


def _append_order_policy_example_options(
    parts: list[str],
    included_options: set[str],
    command_path: str,
    definitions: list[ArgumentDefinition],
) -> None:
    order_type = next(
        (
            definition.choices[0]
            for definition in definitions
            if definition.dest == "order_type" and definition.choices
        ),
        "",
    )
    if not order_type:
        return
    policy = get_order_price_policy(command_path, order_type)
    if policy is None:
        return
    definitions_by_option = {
        definition.option: definition for definition in definitions if definition.option
    }
    for option, option_policy in (
        (policy.price_option, policy.price_policy),
        (policy.condition_price_option, policy.condition_price_policy),
    ):
        if option_policy != "required" or not option or option in included_options:
            continue
        definition = definitions_by_option.get(option)
        if definition is None:
            continue
        parts.extend([option, _example_value(definition)])
        included_options.add(option)


def _example_value(definition: ArgumentDefinition) -> str:
    if definition.choices:
        return definition.choices[0]
    if definition.type_name in {"stock_code", "exchange_stock_code"}:
        return "005930"
    if definition.type_name == "sector_code":
        return "001"
    if definition.type_name == "instrument_code":
        return "M04020"
    if definition.type_name == "date_yyyymmdd":
        return "20260626"
    if definition.type_name in {"quantity", "cancel_quantity"}:
        return "10"
    if definition.type_name == "price":
        return "70000"
    if definition.type_name in {"order_id", "preview_order_id"}:
        return "1234567"
    return f"<{definition.dest or 'value'}>"


def _mapping_lines(definitions: list[ArgumentDefinition]) -> list[str]:
    lines: list[str] = []
    for definition in definitions:
        if not definition.kiwoom_field:
            continue
        option = definition.option or "(internal)"
        status = "required" if definition.required and not definition.default else "optional"
        suffix = f", default: {definition.default}" if definition.default else ""
        lines.append(f"{option} -> {definition.kiwoom_field} ({status}{suffix})")
        if definition.value_map:
            for choice, raw_value in definition.value_map.items():
                lines.append(f"    {choice} = {raw_value}")
    return lines


def build_body(command_path: str, args: argparse.Namespace) -> dict[str, str]:
    definitions = get_argument_definitions(command_path)
    validate_order_price_policy(command_path, args, definitions)
    body: dict[str, str] = {}
    definitions_by_field = _definitions_by_field(definitions)
    handled_fields: set[str] = set()
    for definition in definitions:
        field = definition.kiwoom_field
        if not field or field in handled_fields:
            continue
        handled_fields.add(field)
        field_definitions = definitions_by_field[field]
        if len(field_definitions) == 1:
            resolved = _resolve_definition_value(command_path, field_definitions[0], args)
        else:
            resolved = _resolve_alternative_value(command_path, field, field_definitions, args)
        if resolved is None:
            continue
        selected_definition, value = resolved
        if isinstance(value, list):
            body[field] = ",".join(
                _map_value(selected_definition, str(item)) for item in value
            )
        else:
            body[field] = _map_value(selected_definition, str(value))
    return body


def _definitions_by_field(
    definitions: list[ArgumentDefinition],
) -> dict[str, list[ArgumentDefinition]]:
    grouped: dict[str, list[ArgumentDefinition]] = {}
    for definition in definitions:
        if definition.kiwoom_field:
            grouped.setdefault(definition.kiwoom_field, []).append(definition)
    return grouped


def _alternative_required_fields(definitions: list[ArgumentDefinition]) -> set[str]:
    return {
        field
        for field, field_definitions in _definitions_by_field(definitions).items()
        if len(field_definitions) > 1
        and any(definition.required for definition in field_definitions)
    }


def _resolve_definition_value(
    command_path: str,
    definition: ArgumentDefinition,
    args: argparse.Namespace,
) -> tuple[ArgumentDefinition, object] | None:
    value: object = definition.default
    if definition.dest:
        arg_value = getattr(args, definition.dest, None)
        if arg_value not in (None, ""):
            value = arg_value
    if value == "":
        if definition.required:
            raise CliInputError(
                f"{command_path}: 필수 옵션이 빠졌습니다: {definition.option}"
            )
        return None
    return definition, value


def _resolve_alternative_value(
    command_path: str,
    field: str,
    definitions: list[ArgumentDefinition],
    args: argparse.Namespace,
) -> tuple[ArgumentDefinition, object] | None:
    provided: list[tuple[ArgumentDefinition, object]] = []
    defaults: list[tuple[ArgumentDefinition, object]] = []
    for definition in definitions:
        value: object = definition.default
        if definition.dest:
            arg_value = getattr(args, definition.dest, None)
            if arg_value not in (None, ""):
                provided.append((definition, arg_value))
                continue
        if value != "":
            defaults.append((definition, value))

    if len(provided) > 1:
        options = ", ".join(definition.option for definition in definitions)
        raise CliInputError(
            f"{command_path}: {options} 옵션은 함께 사용할 수 없습니다."
        )
    if provided:
        return provided[0]
    if defaults:
        return defaults[0]
    if any(definition.required for definition in definitions):
        options = ", ".join(definition.option for definition in definitions)
        raise CliInputError(f"{command_path}: 다음 옵션 중 하나가 필요합니다: {options}")
    return None


def _definition_from_row(row: dict[str, str]) -> ArgumentDefinition:
    return ArgumentDefinition(
        command_path=row["command_path"],
        option=row["option"],
        dest=row["dest"],
        kiwoom_field=row["kiwoom_field"],
        required=row["required"] == "Y",
        type_name=row["type"],
        choices=_split_choices(row["choices"]),
        value_map=_split_value_map(row["value_map"]),
        default=row["default"],
        description=row["description"],
    )


def _split_choices(value: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in value.split("|") if part.strip())


def _split_value_map(value: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for part in value.split(";"):
        if not part.strip():
            continue
        key, mapped_value = part.split("=", 1)
        mapping[key.strip()] = mapped_value.strip()
    return mapping


def _map_value(definition: ArgumentDefinition, value: str) -> str:
    if not definition.value_map:
        return value
    try:
        return definition.value_map[value]
    except KeyError as exc:
        allowed = ", ".join(sorted(definition.value_map))
        raise CliInputError(
            f"{definition.command_path}: {definition.option} 값은 다음 중 하나여야 합니다: {allowed}"
        ) from exc


def _order_price_policy_from_row(row: dict[str, str]) -> OrderPricePolicy:
    price_policy = row["price_policy"]
    condition_price_policy = row.get("condition_price_policy", "")
    for field_name, policy in (
        ("price_policy", price_policy),
        ("condition_price_policy", condition_price_policy),
    ):
        if policy and policy not in ALLOWED_ORDER_PRICE_POLICIES:
            raise CliInternalError(
                f"order_price_policies.csv {field_name} 값은 다음 중 하나여야 합니다: "
                f"{sorted(ALLOWED_ORDER_PRICE_POLICIES)}: {policy!r}"
            )
    return OrderPricePolicy(
        command_path=row["command_path"],
        order_type=row["order_type"],
        price_option=row["price_option"],
        price_policy=price_policy,
        condition_price_option=row.get("condition_price_option", ""),
        condition_price_policy=condition_price_policy,
        description=row.get("description", ""),
    )


def validate_order_price_policy(
    command_path: str,
    args: argparse.Namespace,
    definitions: list[ArgumentDefinition] | None = None,
) -> None:
    order_type = getattr(args, "order_type", None)
    if order_type in (None, ""):
        return
    policy = get_order_price_policy(command_path, str(order_type))
    if policy is None:
        return
    argument_definitions = (
        definitions
        if definitions is not None
        else get_argument_definitions(command_path)
    )
    definitions_by_option = {
        definition.option: definition for definition in argument_definitions
    }
    _validate_policy_option(
        command_path=command_path,
        order_type=str(order_type),
        option=policy.price_option,
        policy=policy.price_policy,
        description=policy.description,
        definitions_by_option=definitions_by_option,
        args=args,
    )
    if policy.condition_price_option or policy.condition_price_policy:
        _validate_policy_option(
            command_path=command_path,
            order_type=str(order_type),
            option=policy.condition_price_option,
            policy=policy.condition_price_policy,
            description=policy.description,
            definitions_by_option=definitions_by_option,
            args=args,
        )


def _validate_policy_option(
    *,
    command_path: str,
    order_type: str,
    option: str,
    policy: str,
    description: str,
    definitions_by_option: dict[str, ArgumentDefinition],
    args: argparse.Namespace,
) -> None:
    if policy == "optional" or not policy:
        return
    definition = definitions_by_option.get(option)
    if definition is None:
        raise CliInternalError(
            f"{command_path}: 주문 가격 정책이 알 수 없는 옵션을 참조합니다: {option}"
        )
    value = getattr(args, definition.dest, None)
    has_value = value not in (None, "")
    if policy == "required" and not has_value:
        raise CliInputError(
            f"{command_path}: {description or f'{option} 값이 필요합니다.'}\n"
            f"hint: --order-type {order_type}에는 {option} 옵션이 필요합니다."
        )
    if policy == "forbidden" and has_value:
        raise CliInputError(
            f"{command_path}: {description or f'{option} 값을 넣을 수 없습니다.'}\n"
            f"hint: --order-type {order_type}에는 {option} 옵션을 넣지 마세요."
        )
