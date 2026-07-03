"""Validate Kiwoom CLI mapping tables against the local API spec."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
API_LIST = ROOT / "api_list.csv"
API_SPEC = ROOT / "kiwoom" / "_data" / "kiwoom_api_spec.json"
API_COMMANDS = Path(__file__).resolve().parent / "maps" / "api_commands.csv"
ARGUMENTS = Path(__file__).resolve().parent / "maps" / "arguments.csv"
POSITIONAL_ARGUMENTS = (
    Path(__file__).resolve().parent / "maps" / "positional_arguments.csv"
)
ORDER_PRICE_POLICIES = (
    Path(__file__).resolve().parent / "maps" / "order_price_policies.csv"
)
ORDER_CONFIRMATION_COMMANDS = (
    Path(__file__).resolve().parent / "maps" / "order_confirmation_commands.csv"
)
ORDER_CONFIRMATION_FIELDS = (
    Path(__file__).resolve().parent / "maps" / "order_confirmation_fields.csv"
)
ORDER_VALUE_LABELS = Path(__file__).resolve().parent / "maps" / "order_value_labels.csv"
MAP_README = Path(__file__).resolve().parent / "maps" / "README.md"
API_COVERAGE_DOC = Path(__file__).resolve().parent / "docs" / "api-coverage.md"
POSITIONAL_ARGUMENTS_DOC = (
    Path(__file__).resolve().parent / "docs" / "positional-arguments.md"
)
IMPLEMENTATION_STATUS_DOC = (
    Path(__file__).resolve().parent / "docs" / "implementation-status.md"
)

ALLOWED_STATUSES = {"implemented", "planned", "review", "blocked", "unsupported"}
ALLOWED_COVERAGE_STATUSES = {"public", "guarded", "preview-only", "planned"}
ALLOWED_SAFETY_POLICIES = {
    "read",
    "account_read",
    "auth_write",
    "order_preview",
    "order_write",
    "review_required",
    "blocked_review",
}
ALLOWED_POSITIONAL_STATUSES = {"allow", "candidate", "defer", "reject"}
ALLOWED_ORDER_PRICE_POLICIES = {"required", "optional", "forbidden"}
STATIC_COMMAND_OPTIONS = {
    "kiwoom setup": {"--alias", "--mode"},
    "kiwoom auth login": {"--alias", "--mode"},
    "kiwoom auth status": {"--profile", "--mode"},
    "kiwoom auth refresh": {"--profile", "--mode"},
    "kiwoom auth revoke": {"--profile", "--mode"},
    "kiwoom auth clear": {"--profile", "--mode", "--all", "--credentials"},
    "kiwoom auth switch": set(),
}


def _read_api_list_rows() -> dict[str, dict[str, str]]:
    with API_LIST.open(encoding="utf-8-sig", newline="") as file:
        return {row["API ID"]: row for row in csv.DictReader(file)}


def _read_specs() -> dict[str, dict]:
    raw = json.loads(API_SPEC.read_text(encoding="utf-8"))
    return {
        api["meta"]["API ID"]: api
        for api in raw["apis"].values()
        if api.get("meta", {}).get("API ID")
    }


def _read_command_rows() -> list[dict[str, str]]:
    with API_COMMANDS.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _read_argument_rows() -> list[dict[str, str]]:
    with ARGUMENTS.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _read_positional_argument_rows() -> list[dict[str, str]]:
    with POSITIONAL_ARGUMENTS.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _read_order_price_policy_rows() -> list[dict[str, str]]:
    with ORDER_PRICE_POLICIES.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _read_order_confirmation_command_rows() -> list[dict[str, str]]:
    with ORDER_CONFIRMATION_COMMANDS.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _read_order_confirmation_field_rows() -> list[dict[str, str]]:
    with ORDER_CONFIRMATION_FIELDS.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _read_order_value_label_rows() -> list[dict[str, str]]:
    with ORDER_VALUE_LABELS.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def _split_fields(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def _required_elements(items: list[dict] | None) -> list[str]:
    return [
        item["element"]
        for item in items or []
        if item.get("required") == "Y" and item.get("element")
    ]


def _request_elements(items: list[dict] | None) -> set[str]:
    return {item["element"] for item in items or [] if item.get("element")}


def validate() -> None:
    api_list_rows = _read_api_list_rows()
    api_list_ids = set(api_list_rows)
    specs = _read_specs()
    spec_ids = set(specs)
    rows = _read_command_rows()
    argument_rows = _read_argument_rows()
    positional_rows = _read_positional_argument_rows()
    order_price_policy_rows = _read_order_price_policy_rows()
    order_confirmation_command_rows = _read_order_confirmation_command_rows()
    order_confirmation_field_rows = _read_order_confirmation_field_rows()
    order_value_label_rows = _read_order_value_label_rows()
    mapped_ids = [row["api_id"] for row in rows]
    mapped_id_set = set(mapped_ids)
    implemented_commands: dict[tuple[str, str], list[str]] = {}
    command_rows_by_path: dict[str, dict[str, str]] = {}
    arguments_by_command_path: dict[str, list[dict[str, str]]] = {}
    argument_options_by_command_path: dict[str, set[str]] = {}

    errors: list[str] = []

    if api_list_ids != spec_ids:
        errors.append(
            "api_list.csv and kiwoom_api_spec.json disagree: "
            f"api_list_only={sorted(api_list_ids - spec_ids)} "
            f"spec_only={sorted(spec_ids - api_list_ids)}"
        )

    if len(mapped_ids) != len(mapped_id_set):
        seen: set[str] = set()
        duplicates = sorted(
            api_id for api_id in mapped_ids if api_id in seen or seen.add(api_id)
        )
        errors.append(f"duplicate api_commands rows: {duplicates}")

    missing = sorted(spec_ids - mapped_id_set)
    extra = sorted(mapped_id_set - spec_ids)
    if missing:
        errors.append(f"missing api_commands rows: {missing}")
    if extra:
        errors.append(f"unknown api_commands rows: {extra}")

    for index, row in enumerate(rows, start=2):
        prefix = f"api_commands.csv:{index} api_id={row.get('api_id', '')}"
        if row.get("status") not in ALLOWED_STATUSES:
            errors.append(f"{prefix} invalid status={row.get('status', '')!r}")
        if row.get("coverage_status") not in ALLOWED_COVERAGE_STATUSES:
            errors.append(
                f"{prefix} invalid coverage_status={row.get('coverage_status', '')!r}"
            )
        if row.get("safety_policy") not in ALLOWED_SAFETY_POLICIES:
            errors.append(
                f"{prefix} invalid safety_policy={row.get('safety_policy', '')!r}"
            )
        if row.get("safety_policy") == "order_write" and row.get(
            "coverage_status"
        ) not in {"preview-only", "guarded"}:
            errors.append(f"{prefix} order_write must be preview-only or guarded")
        if (
            row.get("safety_policy") == "order_preview"
            and row.get("coverage_status") != "preview-only"
        ):
            errors.append(f"{prefix} order_preview must be preview-only")
        if row.get("status") == "review" and row.get("coverage_status") == "public":
            errors.append(f"{prefix} review rows cannot be public")
        if row.get("status") in {"implemented", "planned"} and not row.get(
            "command_path"
        ):
            errors.append(f"{prefix} missing command_path")
        if row.get("status") in {"implemented", "planned"} and row.get(
            "command_path", ""
        ).startswith("kiwoom spec "):
            errors.append(f"{prefix} command_path must not use raw spec commands")
        if row.get("status") == "implemented":
            key = (row.get("cli_group", ""), row.get("cli_command", ""))
            implemented_commands.setdefault(key, []).append(row.get("api_id", ""))
            command_rows_by_path[row.get("command_path", "")] = row

        api_id = row.get("api_id", "")
        spec = specs.get(api_id)
        api_list_row = api_list_rows.get(api_id)
        if not spec or not api_list_row:
            continue

        meta = spec.get("meta", {})
        request = spec.get("request", {})

        if row.get("api_name") != meta.get("API 명"):
            errors.append(
                f"{prefix} api_name mismatch: "
                f"map={row.get('api_name', '')!r} spec={meta.get('API 명', '')!r}"
            )
        if row.get("api_name") != api_list_row.get("API 명"):
            errors.append(
                f"{prefix} api_name mismatch: "
                f"map={row.get('api_name', '')!r} api_list={api_list_row.get('API 명', '')!r}"
            )
        if row.get("major_category") != api_list_row.get("대분류"):
            errors.append(
                f"{prefix} major_category mismatch: "
                f"map={row.get('major_category', '')!r} api_list={api_list_row.get('대분류', '')!r}"
            )
        if row.get("subcategory") != api_list_row.get("중분류"):
            errors.append(
                f"{prefix} subcategory mismatch: "
                f"map={row.get('subcategory', '')!r} api_list={api_list_row.get('중분류', '')!r}"
            )
        if row.get("method") != meta.get("Method"):
            errors.append(
                f"{prefix} method mismatch: "
                f"map={row.get('method', '')!r} spec={meta.get('Method', '')!r}"
            )
        if row.get("path") != meta.get("URL"):
            errors.append(
                f"{prefix} path mismatch: "
                f"map={row.get('path', '')!r} spec={meta.get('URL', '')!r}"
            )
        if row.get("path") != api_list_row.get("URL"):
            errors.append(
                f"{prefix} path mismatch: "
                f"map={row.get('path', '')!r} api_list={api_list_row.get('URL', '')!r}"
            )

        spec_required_body = _required_elements(request.get("body"))
        map_required_body = _split_fields(row.get("required_body_fields", ""))
        if map_required_body != spec_required_body:
            errors.append(
                f"{prefix} required_body_fields mismatch: "
                f"map={map_required_body!r} spec={spec_required_body!r}"
            )

        spec_required_header = _required_elements(request.get("header"))
        map_required_header = _split_fields(row.get("required_header_fields", ""))
        if map_required_header != spec_required_header:
            errors.append(
                f"{prefix} required_header_fields mismatch: "
                f"map={map_required_header!r} spec={spec_required_header!r}"
            )

        body_elements = _request_elements(request.get("body"))
        unknown_body_fields = sorted(set(map_required_body) - body_elements)
        if unknown_body_fields:
            errors.append(
                f"{prefix} required_body_fields not in spec request body: "
                f"{unknown_body_fields}"
            )

        header_elements = _request_elements(request.get("header"))
        unknown_header_fields = sorted(set(map_required_header) - header_elements)
        if unknown_header_fields:
            errors.append(
                f"{prefix} required_header_fields not in spec request header: "
                f"{unknown_header_fields}"
            )

    for (group, command), api_ids in sorted(implemented_commands.items()):
        if len(api_ids) > 1:
            errors.append(
                f"implemented command must be unique: kiwoom {group} {command} "
                f"api_ids={api_ids}"
            )

    for index, row in enumerate(argument_rows, start=2):
        prefix = f"arguments.csv:{index} command_path={row.get('command_path', '')!r}"
        command_path = row.get("command_path", "")
        arguments_by_command_path.setdefault(command_path, []).append(row)
        if row.get("option"):
            argument_options_by_command_path.setdefault(command_path, set()).add(
                row["option"]
            )
        command_row = command_rows_by_path.get(command_path)
        if command_row is None:
            errors.append(f"{prefix} has no implemented api_commands row")
            continue
        api_id = command_row.get("api_id", "")
        spec = specs.get(api_id)
        request_body_fields = _request_elements(
            (spec or {}).get("request", {}).get("body")
        )
        kiwoom_field = row.get("kiwoom_field", "")
        if kiwoom_field and kiwoom_field not in request_body_fields:
            errors.append(
                f"{prefix} kiwoom_field={kiwoom_field!r} is not in spec request body for {api_id}"
            )
        if row.get("required") not in {"Y", "N"}:
            errors.append(f"{prefix} invalid required={row.get('required', '')!r}")
        choices = set(_split_choices(row.get("choices", "")))
        value_map_keys = set(_split_value_map(row.get("value_map", "")).keys())
        if value_map_keys and choices and value_map_keys != choices:
            errors.append(
                f"{prefix} value_map keys must match choices: choices={sorted(choices)} "
                f"value_map={sorted(value_map_keys)}"
            )

    for command_path, command_row in sorted(command_rows_by_path.items()):
        if command_row.get("safety_policy") == "auth_write":
            continue
        required_body = set(_split_fields(command_row.get("required_body_fields", "")))
        mapped_fields = {
            row.get("kiwoom_field", "")
            for row in arguments_by_command_path.get(command_path, [])
            if row.get("kiwoom_field", "")
        }
        missing_fields = sorted(required_body - mapped_fields)
        if missing_fields:
            errors.append(
                f"{command_path} missing arguments.csv mappings for required fields: {missing_fields}"
            )

    _validate_maps_readme_counts(rows, errors)
    _validate_positional_arguments(
        positional_rows=positional_rows,
        implemented_command_paths=set(command_rows_by_path),
        argument_options_by_command_path=argument_options_by_command_path,
        errors=errors,
    )
    _validate_order_price_policies(
        policy_rows=order_price_policy_rows,
        command_rows_by_path=command_rows_by_path,
        arguments_by_command_path=arguments_by_command_path,
        argument_options_by_command_path=argument_options_by_command_path,
        errors=errors,
    )
    _validate_order_confirmations(
        command_rows=order_confirmation_command_rows,
        field_rows=order_confirmation_field_rows,
        value_label_rows=order_value_label_rows,
        command_rows_by_path=command_rows_by_path,
        arguments_by_command_path=arguments_by_command_path,
        errors=errors,
    )
    _validate_api_coverage_counts(rows, errors)
    _validate_implementation_status_counts(rows, errors)

    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise SystemExit(f"map validation failed:\n{joined}")

    print(
        "map validation passed: "
        f"{len(rows)} mapped APIs, {len(spec_ids)} spec APIs, "
        f"{len(api_list_ids)} api_list rows, {len(argument_rows)} argument rows"
    )


def _split_choices(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def _split_value_map(value: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for part in value.split(";"):
        if not part.strip():
            continue
        if "=" not in part:
            mapping[part.strip()] = ""
            continue
        key, mapped_value = part.split("=", 1)
        mapping[key.strip()] = mapped_value.strip()
    return mapping


def _validate_order_price_policies(
    *,
    policy_rows: list[dict[str, str]],
    command_rows_by_path: dict[str, dict[str, str]],
    arguments_by_command_path: dict[str, list[dict[str, str]]],
    argument_options_by_command_path: dict[str, set[str]],
    errors: list[str],
) -> None:
    required_columns = {
        "command_path",
        "order_type",
        "price_option",
        "price_policy",
        "condition_price_option",
        "condition_price_policy",
        "description",
    }
    if policy_rows:
        missing_columns = sorted(required_columns - set(policy_rows[0]))
        if missing_columns:
            errors.append(
                f"order_price_policies.csv missing columns: {missing_columns}"
            )
            return

    order_type_choices_by_command: dict[str, set[str]] = {}
    seen: set[tuple[str, str]] = set()
    for command_path, argument_rows in arguments_by_command_path.items():
        for row in argument_rows:
            if row.get("option") == "--order-type":
                order_type_choices_by_command[command_path] = set(
                    _split_choices(row.get("choices", ""))
                )

    for index, row in enumerate(policy_rows, start=2):
        command_path = row.get("command_path", "")
        order_type = row.get("order_type", "")
        prefix = (
            f"order_price_policies.csv:{index} "
            f"command_path={command_path!r} order_type={order_type!r}"
        )
        command_row = command_rows_by_path.get(command_path)
        if command_row is None:
            errors.append(f"{prefix} has no implemented api_commands row")
            continue
        if command_row.get("safety_policy") != "order_write":
            errors.append(f"{prefix} must reference an order_write command")
        if order_type not in order_type_choices_by_command.get(command_path, set()):
            errors.append(f"{prefix} order_type is not a mapped --order-type choice")
        key = (command_path, order_type)
        if key in seen:
            errors.append(f"{prefix} duplicate command_path/order_type")
        seen.add(key)

        known_options = argument_options_by_command_path.get(command_path, set())
        for option_field, policy_field in (
            ("price_option", "price_policy"),
            ("condition_price_option", "condition_price_policy"),
        ):
            option = row.get(option_field, "")
            policy = row.get(policy_field, "")
            if policy and policy not in ALLOWED_ORDER_PRICE_POLICIES:
                errors.append(f"{prefix} invalid {policy_field}={policy!r}")
            if option and option not in known_options:
                errors.append(
                    f"{prefix} {option_field} {option!r} is not known for command"
                )
            if option and not policy:
                errors.append(f"{prefix} {option_field} requires {policy_field}")
            if policy and not option:
                errors.append(f"{prefix} {policy_field} requires {option_field}")
        if not row.get("description", ""):
            errors.append(f"{prefix} missing description")

    for command_path, command_row in sorted(command_rows_by_path.items()):
        if command_row.get("safety_policy") != "order_write":
            continue
        choices = order_type_choices_by_command.get(command_path)
        if not choices:
            continue
        missing = sorted(
            choices
            - {
                row.get("order_type", "")
                for row in policy_rows
                if row.get("command_path", "") == command_path
            }
        )
        if missing:
            errors.append(
                f"order_price_policies.csv missing policies for {command_path}: {missing}"
            )


def _validate_order_confirmations(
    *,
    command_rows: list[dict[str, str]],
    field_rows: list[dict[str, str]],
    value_label_rows: list[dict[str, str]],
    command_rows_by_path: dict[str, dict[str, str]],
    arguments_by_command_path: dict[str, list[dict[str, str]]],
    errors: list[str],
) -> None:
    _validate_required_columns(
        rows=command_rows,
        columns={"command_path", "kind", "message"},
        path="order_confirmation_commands.csv",
        errors=errors,
    )
    _validate_required_columns(
        rows=field_rows,
        columns={
            "command_path",
            "output_key",
            "label",
            "arg_name",
            "value_label_group",
            "include_if_empty",
            "empty_display",
        },
        path="order_confirmation_fields.csv",
        errors=errors,
    )
    _validate_required_columns(
        rows=value_label_rows,
        columns={"group", "value", "label"},
        path="order_value_labels.csv",
        errors=errors,
    )

    implemented_order_write_paths = {
        command_path
        for command_path, command_row in command_rows_by_path.items()
        if command_row.get("status") == "implemented"
        and command_row.get("safety_policy") == "order_write"
    }
    confirmation_paths = {row.get("command_path", "") for row in command_rows}
    missing_confirmation_paths = sorted(
        implemented_order_write_paths - confirmation_paths
    )
    extra_confirmation_paths = sorted(
        confirmation_paths - implemented_order_write_paths
    )
    if missing_confirmation_paths:
        errors.append(
            "order_confirmation_commands.csv missing implemented order_write commands: "
            f"{missing_confirmation_paths}"
        )
    if extra_confirmation_paths:
        errors.append(
            "order_confirmation_commands.csv contains non-implemented order_write commands: "
            f"{extra_confirmation_paths}"
        )

    seen_commands: set[str] = set()
    for index, row in enumerate(command_rows, start=2):
        command_path = row.get("command_path", "")
        prefix = (
            f"order_confirmation_commands.csv:{index} command_path={command_path!r}"
        )
        if command_path in seen_commands:
            errors.append(f"{prefix} duplicate command_path")
        seen_commands.add(command_path)
        if not row.get("kind", ""):
            errors.append(f"{prefix} missing kind")
        if "--confirm" not in row.get("message", ""):
            errors.append(f"{prefix} message must mention --confirm")

    known_label_groups = {row.get("group", "") for row in value_label_rows}
    seen_value_labels: set[tuple[str, str]] = set()
    for index, row in enumerate(value_label_rows, start=2):
        key = (row.get("group", ""), row.get("value", ""))
        prefix = f"order_value_labels.csv:{index} group={key[0]!r} value={key[1]!r}"
        if key in seen_value_labels:
            errors.append(f"{prefix} duplicate group/value")
        seen_value_labels.add(key)
        if not row.get("label", ""):
            errors.append(f"{prefix} missing label")

    fields_by_command: dict[str, list[dict[str, str]]] = defaultdict(list)
    seen_fields: set[tuple[str, str]] = set()
    for index, row in enumerate(field_rows, start=2):
        command_path = row.get("command_path", "")
        output_key = row.get("output_key", "")
        prefix = (
            f"order_confirmation_fields.csv:{index} "
            f"command_path={command_path!r} output_key={output_key!r}"
        )
        fields_by_command[command_path].append(row)
        key = (command_path, output_key)
        if key in seen_fields:
            errors.append(f"{prefix} duplicate command_path/output_key")
        seen_fields.add(key)
        if command_path not in implemented_order_write_paths:
            errors.append(
                f"{prefix} command_path is not an implemented order_write command"
            )
        if not output_key:
            errors.append(f"{prefix} missing output_key")
        if not row.get("label", ""):
            errors.append(f"{prefix} missing label")
        if row.get("include_if_empty") not in {"Y", "N"}:
            errors.append(f"{prefix} include_if_empty must be Y or N")
        label_group = row.get("value_label_group", "")
        if label_group and label_group not in known_label_groups:
            errors.append(f"{prefix} unknown value_label_group={label_group!r}")
        known_destinations = {
            argument.get("dest", "")
            for argument in arguments_by_command_path.get(command_path, [])
            if argument.get("dest", "")
        }
        arg_name = row.get("arg_name", "")
        if arg_name != "__kind__" and arg_name not in known_destinations:
            errors.append(f"{prefix} unknown arg_name={arg_name!r}")

    missing_field_paths = sorted(implemented_order_write_paths - set(fields_by_command))
    if missing_field_paths:
        errors.append(
            "order_confirmation_fields.csv missing implemented order_write commands: "
            f"{missing_field_paths}"
        )
    for command_path, fields in fields_by_command.items():
        if command_path not in implemented_order_write_paths:
            continue
        if not any(row.get("output_key") == "kind" for row in fields):
            errors.append(
                f"order_confirmation_fields.csv missing kind field: {command_path}"
            )


def _validate_required_columns(
    *,
    rows: list[dict[str, str]],
    columns: set[str],
    path: str,
    errors: list[str],
) -> None:
    if not rows:
        errors.append(f"{path} is empty")
        return
    missing_columns = sorted(columns - set(rows[0]))
    if missing_columns:
        errors.append(f"{path} missing columns: {missing_columns}")


def _validate_positional_arguments(
    *,
    positional_rows: list[dict[str, str]],
    implemented_command_paths: set[str],
    argument_options_by_command_path: dict[str, set[str]],
    errors: list[str],
) -> None:
    required_columns = {
        "command_path",
        "canonical_form",
        "positional_form",
        "position",
        "name",
        "dest",
        "option",
        "status",
        "reason",
    }
    if positional_rows:
        missing_columns = sorted(required_columns - set(positional_rows[0]))
        if missing_columns:
            errors.append(
                f"positional_arguments.csv missing columns: {missing_columns}"
            )
            return

    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(positional_rows, start=2):
        command_path = row.get("command_path", "")
        option = row.get("option", "")
        prefix = f"positional_arguments.csv:{index} command_path={command_path!r}"

        if not command_path.startswith("kiwoom "):
            errors.append(f"{prefix} command_path must start with 'kiwoom '")
        if row.get("status") not in ALLOWED_POSITIONAL_STATUSES:
            errors.append(f"{prefix} invalid status={row.get('status', '')!r}")
        try:
            position = int(row.get("position", ""))
        except ValueError:
            errors.append(f"{prefix} position must be an integer")
            position = 0
        if position < 1:
            errors.append(f"{prefix} position must be greater than zero")
        if not option.startswith("--"):
            errors.append(f"{prefix} option must be a long option")
        if not row.get("dest"):
            errors.append(f"{prefix} missing dest")
        if not row.get("name"):
            errors.append(f"{prefix} missing name")
        if not row.get("canonical_form"):
            errors.append(f"{prefix} missing canonical_form")
        if not row.get("positional_form"):
            errors.append(f"{prefix} missing positional_form")
        if not row.get("reason"):
            errors.append(f"{prefix} missing reason")

        key = (command_path, str(position))
        if key in seen:
            errors.append(f"{prefix} duplicate command_path/position: {key}")
        seen.add(key)

        known_options = set(STATIC_COMMAND_OPTIONS.get(command_path, set()))
        known_options.update(argument_options_by_command_path.get(command_path, set()))
        if (
            command_path not in implemented_command_paths
            and command_path not in STATIC_COMMAND_OPTIONS
        ):
            errors.append(f"{prefix} command_path is not an implemented/static command")
        if option not in known_options:
            errors.append(
                f"{prefix} option {option!r} is not known for command; "
                f"known={sorted(known_options)}"
            )

        expected_mapping = f"`{position} -> {option}`"
        text = POSITIONAL_ARGUMENTS_DOC.read_text(encoding="utf-8")
        if f"`{command_path}`" not in text:
            errors.append(
                "kiwoom_cli/docs/positional-arguments.md missing command: "
                f"{command_path}"
            )
        if f"`{row.get('canonical_form', '')}`" not in text:
            errors.append(
                "kiwoom_cli/docs/positional-arguments.md missing canonical form: "
                f"{row.get('canonical_form', '')}"
            )
        if (
            row.get("status") != "defer"
            and f"`{row.get('positional_form', '')}`" not in text
        ):
            errors.append(
                "kiwoom_cli/docs/positional-arguments.md missing positional form: "
                f"{row.get('positional_form', '')}"
            )
        if expected_mapping not in text:
            errors.append(
                "kiwoom_cli/docs/positional-arguments.md missing positional mapping: "
                f"{command_path} {expected_mapping}"
            )


def _validate_maps_readme_counts(rows: list[dict[str, str]], errors: list[str]) -> None:
    expected = Counter(
        (row["cli_group"], row["status"], row["coverage_status"]) for row in rows
    )
    actual = _read_maps_readme_counts()
    if actual != expected:
        errors.append(
            "kiwoom_cli/maps/README.md Current Counts mismatch: "
            f"doc_only={_counter_diff(actual, expected)} "
            f"map_only={_counter_diff(expected, actual)}"
        )


def _read_maps_readme_counts() -> Counter[tuple[str, str, str]]:
    counts: Counter[tuple[str, str, str]] = Counter()
    pattern = re.compile(r"^\| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \| (\d+) \|$")
    for line in MAP_README.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        group, status, coverage_status, count = match.groups()
        counts[(group, status, coverage_status)] = int(count)
    return counts


def _validate_api_coverage_counts(
    rows: list[dict[str, str]], errors: list[str]
) -> None:
    expected = Counter(row["coverage_status"] for row in rows)
    actual = _read_api_coverage_status_counts()
    if actual != expected:
        errors.append(
            "kiwoom_cli/docs/api-coverage.md coverage status counts mismatch: "
            f"doc_only={_counter_diff(actual, expected)} "
            f"map_only={_counter_diff(expected, actual)}"
        )


def _read_api_coverage_status_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    pattern = re.compile(r"^\| `([^`]+)` \| (\d+) \|")
    for line in API_COVERAGE_DOC.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        coverage_status, count = match.groups()
        if coverage_status in ALLOWED_COVERAGE_STATUSES:
            counts[coverage_status] = int(count)
    return counts


def _validate_implementation_status_counts(
    rows: list[dict[str, str]],
    errors: list[str],
) -> None:
    expected = Counter(row["coverage_status"] for row in rows)
    actual = _read_inline_coverage_status_counts(
        IMPLEMENTATION_STATUS_DOC.read_text(encoding="utf-8")
    )
    if actual != expected:
        errors.append(
            "kiwoom_cli/docs/implementation-status.md coverage status counts mismatch: "
            f"doc_only={_counter_diff(actual, expected)} "
            f"map_only={_counter_diff(expected, actual)}"
        )


def _read_inline_coverage_status_counts(text: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    pattern = re.compile(r"`([^`]+)`\s+(\d+)")
    for coverage_status, count in pattern.findall(text):
        if coverage_status in ALLOWED_COVERAGE_STATUSES:
            counts[coverage_status] = int(count)
    return counts


def _counter_diff(left: Counter, right: Counter) -> dict:
    return {
        key: left[key]
        for key in sorted(left, key=str)
        if left[key] != right.get(key, 0)
    }


if __name__ == "__main__":
    validate()
