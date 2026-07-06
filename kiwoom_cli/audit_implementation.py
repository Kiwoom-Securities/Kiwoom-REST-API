"""Audit implemented CLI commands against maps, parser surface, and docs."""

from __future__ import annotations

import argparse
import re
import tomllib
from pathlib import Path
from types import SimpleNamespace

from kiwoom_cli.argument_maps import (
    build_body,
    get_argument_definitions,
    load_argument_definitions,
)
from kiwoom_cli.executor import preview_rest_command
from kiwoom_cli.order_confirmation import build_order_confirmation
from kiwoom_cli.generate_agent_reference import (
    render_all_references,
    render_command_options,
    render_implemented_commands,
)
from kiwoom_cli.main import build_parser
from kiwoom_cli.registry import CommandDefinition, load_command_definitions
from kiwoom_cli.errors import CliError
from kiwoom_cli.safety import enforce_before_request


README = Path(__file__).resolve().parent / "README.md"
COMMAND_SYSTEM = Path(__file__).resolve().parent / "docs" / "command-system.md"
FEATURE_MATRIX = Path(__file__).resolve().parent / "docs" / "feature-matrix.md"
COMMAND_CONTRACTS = Path(__file__).resolve().parent / "docs" / "command-contracts.md"
IMPLEMENTATION_STATUS = (
    Path(__file__).resolve().parent / "docs" / "implementation-status.md"
)
PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"
ROOT_SPEC = Path(__file__).resolve().parents[1] / "kiwoom" / "_data" / "kiwoom_api_spec.json"
ROOT_API_LIST = Path(__file__).resolve().parents[1] / "api_list.csv"
REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_REFERENCE_ROOT = (
    Path(__file__).resolve().parents[1] / ".agents" / "skills" / "kiwoom" / "kiwoom"
)
AGENT_IMPLEMENTED_COMMANDS = (
    AGENT_REFERENCE_ROOT / "references" / "implemented-commands.md"
)
AGENT_COMMAND_OPTIONS = AGENT_REFERENCE_ROOT / "references" / "command-options.md"
MAP_RESOURCES = (
    ROOT_SPEC,
    ROOT_API_LIST,
    Path(__file__).resolve().parent / "maps" / "api_commands.csv",
    Path(__file__).resolve().parent / "maps" / "arguments.csv",
    Path(__file__).resolve().parent / "maps" / "positional_arguments.csv",
    Path(__file__).resolve().parent / "maps" / "order_price_policies.csv",
    Path(__file__).resolve().parent / "maps" / "order_confirmation_commands.csv",
    Path(__file__).resolve().parent / "maps" / "order_confirmation_fields.csv",
    Path(__file__).resolve().parent / "maps" / "order_value_labels.csv",
    README,
    COMMAND_SYSTEM,
    FEATURE_MATRIX,
    COMMAND_CONTRACTS,
    Path(__file__).resolve().parent / "docs" / "positional-arguments.md",
    IMPLEMENTATION_STATUS,
    PYPROJECT,
)

VERIFICATION_COMMAND_DOCS = (
    Path(__file__).resolve().parent / "docs" / "README.md",
    IMPLEMENTATION_STATUS,
)

REQUIRED_VERIFICATION_COMMANDS = (
    ".venv/bin/python -m kiwoom_cli.validate_maps",
    ".venv/bin/python -m kiwoom_cli.audit_implementation",
    "env PYTHONPYCACHEPREFIX=.pycache-check .venv/bin/python -m compileall -q kiwoom kiwoom_cli Examples",
    "rg -n ",
    "git diff --check",
    "uv build",
    ".venv/bin/python -m kiwoom_cli.audit_wheel",
    ".venv/bin/python -m kiwoom_cli.verify_real_calls --mode demo || true",
)

OVERSEAS_TODO_GROUPS = {
    "investment-info",
    "overseas accounts",
    "overseas candles",
    "overseas orderbooks",
    "overseas orders",
    "overseas quotes",
    "overseas rankings",
    "overseas sectors",
    "overseas stocks",
}

OVERSEAS_PLACEHOLDERS = (
    Path(__file__).resolve().parent / "commands" / "investment_info.py",
    Path(__file__).resolve().parent / "commands" / "overseas.py",
)

STATIC_IMPLEMENTED_COMMANDS = (
    "kiwoomcli spec search",
    "kiwoomcli spec show",
    "kiwoomcli spec groups",
    "kiwoomcli spec apis",
)

CONTRACT_GROUPS = {
    "accounts",
    "candles",
    "elws",
    "etfs",
    "investors",
    "orderbooks",
    "orders",
    "quotes",
    "rankings",
    "sectors",
    "securities-lending",
    "short-selling",
    "stocks",
    "streams",
    "themes",
}

REQUIRED_MAPPED_HELP_SECTIONS = (
    "Summary:",
    "Behavior:",
    "Examples:",
    "OpenAPI mapping:",
)

REMOVED_OPTION_REPLACEMENTS_BY_COMMAND = {
    "kiwoomcli domestic accounts cash": {"--query": "--cash-basis"},
    "kiwoomcli domestic accounts assets": {"--delisted": "--include-delisted"},
    "kiwoomcli domestic accounts valuation": {"--delisted": "--include-delisted"},
    "kiwoomcli domestic accounts order-fill-detail": {
        "--asset": "--asset-kind",
        "--sort": "--order/--fill-status",
    },
    "kiwoomcli domestic accounts order-fill-status": {
        "--asset": "--asset-kind",
        "--scope": "--fill-status",
    },
    "kiwoomcli domestic accounts gold-all-order-fills": {
        "--asset": "--asset-kind",
        "--sort": "--order",
    },
    "kiwoomcli domestic accounts gold-order-fills": {
        "--asset": "--asset-kind",
        "--sort": "--order/--fill-status",
    },
    "kiwoomcli domestic accounts gold-open-orders": {
        "--asset": "--asset-kind",
        "--sort": "--order",
    },
    "kiwoomcli domestic elws balance-rank": {
        "--ended": "--include-ended",
        "--right": "--right-type",
    },
    "kiwoomcli domestic elws broker-net": {
        "--ended": "--include-ended",
        "--issuer": "--issuer-code",
    },
    "kiwoomcli domestic elws change-rank": {
        "--ended": "--include-ended",
        "--right": "--right-type",
    },
    "kiwoomcli domestic elws conditions": {
        "--asset": "--underlying-code",
        "--issuer": "--issuer-code",
        "--lp": "--lp-code",
        "--right": "--right-type",
    },
    "kiwoomcli domestic elws divergence": {
        "--asset": "--underlying-code",
        "--ended": "--include-ended",
        "--issuer": "--issuer-code",
        "--lp": "--lp-code",
        "--right": "--right-type",
    },
    "kiwoomcli domestic elws price-move": {
        "--asset": "--underlying-code",
        "--ended": "--include-ended",
        "--issuer": "--issuer-code",
        "--lp": "--lp-code",
        "--right": "--right-type",
    },
    "kiwoomcli domestic orders list-fills": {"--scope": "--stock-scope"},
    "kiwoomcli domestic orders list-open": {"--scope": "--stock-scope"},
    "kiwoomcli domestic rankings today-volume": {"--credit": "--credit-type"},
}


def audit() -> None:
    parser = build_parser()
    definitions = [
        definition
        for definition in load_command_definitions()
        if definition.status == "implemented"
    ]

    errors: list[str] = []
    _audit_packaged_resources(errors)
    _audit_verification_command_docs(errors)
    _audit_pyproject(errors)
    _audit_project_rules(errors)
    _audit_examples_compile_and_runtime(errors)
    _audit_overseas_todo(parser, errors)
    _audit_agent_reference(definitions, errors)
    for command_path in STATIC_IMPLEMENTED_COMMANDS:
        _audit_static_command(parser, command_path, errors)
    for definition in definitions:
        resolved = _audit_parser_path(parser, definition, errors)
        if resolved is not None:
            _audit_mapped_options(resolved, definition.command_path, errors)
            _audit_removed_options(resolved, definition.command_path, errors)
            _audit_help_contract(resolved, definition, errors)
        _audit_docs(definition, errors)

    order_write_count = 0
    preview_count = 0
    for definition in definitions:
        if definition.safety_policy == "order_preview":
            preview_count += 1
            _audit_preview(definition, errors)
        elif definition.safety_policy == "order_write":
            order_write_count += 1
            _audit_order_write(definition, errors)

    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise SystemExit(f"implementation audit failed:\n{joined}")

    print(
        "implementation audit passed: "
        f"{len(definitions) + len(STATIC_IMPLEMENTED_COMMANDS)} implemented commands, "
        f"{preview_count} preview-only commands, "
        f"{order_write_count} --confirm-gated order_write commands"
    )


def _audit_packaged_resources(errors: list[str]) -> None:
    for path in MAP_RESOURCES:
        if not path.is_file():
            errors.append(f"required CLI resource missing: {path}")
            continue
        if path.stat().st_size == 0:
            errors.append(f"required CLI resource is empty: {path}")


def _audit_verification_command_docs(errors: list[str]) -> None:
    for path in VERIFICATION_COMMAND_DOCS:
        if not path.is_file():
            errors.append(f"verification command document missing: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        for command in REQUIRED_VERIFICATION_COMMANDS:
            if command not in text:
                errors.append(
                    f"verification command document missing {command!r}: {path}"
                )


def _audit_pyproject(errors: list[str]) -> None:
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    scripts = pyproject.get("project", {}).get("scripts", {})
    if scripts.get("kiwoomcli") != "kiwoom_cli.main:main":
        errors.append(
            "pyproject.toml missing project script: kiwoomcli = kiwoom_cli.main:main"
        )

    wheel = (
        pyproject.get("tool", {})
        .get("hatch", {})
        .get("build", {})
        .get("targets", {})
        .get("wheel", {})
    )
    packages = set(wheel.get("packages", []))
    for package in ("kiwoom", "kiwoom_cli"):
        if package not in packages:
            errors.append(f"pyproject.toml wheel packages missing {package!r}")

    artifacts = set(wheel.get("artifacts", []))
    required_artifacts = {
        "kiwoom/_data/*.json",
        "kiwoom_cli/maps/*.csv",
        "kiwoom_cli/maps/*.md",
        "kiwoom_cli/docs/*.md",
        "kiwoom_cli/README.md",
    }
    missing_artifacts = sorted(required_artifacts - artifacts)
    if missing_artifacts:
        errors.append(f"pyproject.toml wheel artifacts missing: {missing_artifacts}")

    force_include = wheel.get("force-include", {})
    expected_force_include = {
        "api_list.csv": "api_list.csv",
    }
    for source, target in expected_force_include.items():
        if force_include.get(source) != target:
            errors.append(
                f"pyproject.toml wheel force-include missing {source!r} = {target!r}"
            )


def _audit_project_rules(errors: list[str]) -> None:
    _audit_no_public_api_layer(errors)
    _audit_no_example_auth_helpers(errors)
    _audit_no_customer_uv_run_invocation(errors)
    _audit_no_test_double_terms(errors)
    _audit_cli_runtime_boundary(errors)


def _audit_no_public_api_layer(errors: list[str]) -> None:
    public_api_layer = REPO_ROOT / "kiwoom" / "apis"
    if public_api_layer.exists():
        errors.append(f"broad public wrapper layer must not exist: {public_api_layer}")


def _audit_no_example_auth_helpers(errors: list[str]) -> None:
    forbidden_paths = (
        REPO_ROOT / "Examples" / "auth.py",
        REPO_ROOT / "examples" / "auth.py",
    )
    for path in forbidden_paths:
        if path.exists():
            errors.append(f"example-local auth helper must not exist: {path}")

    for root_name in ("Examples", "examples"):
        root = REPO_ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("kis_auth.py"):
            errors.append(f"KIS-style example auth helper must not exist: {path}")


def _audit_no_customer_uv_run_invocation(errors: list[str]) -> None:
    command_pattern = re.compile(r"^\s*(?:[$>]\s*)?uv\s+run\s+kiwoom\b")
    for path in _iter_text_files(
        (REPO_ROOT / "kiwoom_cli", AGENT_REFERENCE_ROOT),
        suffixes={".md"},
    ):
        for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        ):
            if command_pattern.search(line):
                errors.append(
                    "customer-facing docs must use `kiwoomcli`, not `uv run kiwoom`: "
                    f"{path}:{line_number}"
                )


def _audit_no_test_double_terms(errors: list[str]) -> None:
    terms = (
        "unittest" + r"\.mock",
        "Magic" + "Mo" + "ck",
        r"\b" + "Mo" + "ck" + r"\b",
        r"\b" + "pa" + "tch" + r"\b",
        "fa" + "ke",
        "stu" + "b",
        "monkey" + "pa" + "tch",
        "cass" + "ette",
        "re" + "play",
    )
    pattern = re.compile("|".join(terms))
    for path in _iter_text_files(
        (
            REPO_ROOT / "kiwoom",
            REPO_ROOT / "kiwoom_cli",
            REPO_ROOT / "Examples",
            REPO_ROOT / "utils",
        ),
        excluded_suffixes={".md", ".csv", ".pyc"},
    ):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for match in pattern.finditer(text):
            line_number = text.count("\n", 0, match.start()) + 1
            errors.append(
                "test double or response-recording term is not allowed in "
                f"implementation/test/example code: {path}:{line_number}"
            )


def _audit_cli_runtime_boundary(errors: list[str]) -> None:
    executor = Path(__file__).resolve().parent / "executor.py"
    executor_text = executor.read_text(encoding="utf-8")
    if "from kiwoom import get_client, get_ws_client" not in executor_text:
        errors.append(
            "kiwoom_cli/executor.py must acquire runtime through package facade"
        )

    forbidden_runtime_import = re.compile(
        r"\b(from\s+kiwoom\s+import\s+get_(?:client|ws_client)|"
        r"requests\.|httpx\.|urllib\.)"
    )
    commands_root = Path(__file__).resolve().parent / "commands"
    for path in _iter_text_files((commands_root,), suffixes={".py"}):
        text = path.read_text(encoding="utf-8", errors="ignore")
        match = forbidden_runtime_import.search(text)
        if match:
            line_number = text.count("\n", 0, match.start()) + 1
            errors.append(
                "resource command modules must use kiwoom_cli.executor rather than "
                f"direct runtime/network access: {path}:{line_number}"
            )


def _audit_examples_compile_and_runtime(errors: list[str]) -> None:
    examples_root = REPO_ROOT / "Examples"
    if not examples_root.is_dir():
        errors.append(f"generated examples root missing: {examples_root}")
        return

    example_files = sorted(examples_root.rglob("*.py"))
    if not example_files:
        errors.append(f"generated examples missing Python files: {examples_root}")
        return

    facade_pattern = re.compile(
        r"^from\s+kiwoom\s+import\s+.*\b(get_auth|get_client|get_ws_client)\b",
        flags=re.MULTILINE,
    )
    forbidden_runtime_pattern = re.compile(
        r"\b("
        r"requests\.|httpx\.|urllib\.|"
        r"from\s+requests\b|import\s+requests\b|"
        r"from\s+urllib\b|import\s+urllib\b|"
        r"from\s+kiwoom\.core\b|"
        r"KiwoomRestClient|KiwoomWebSocketClient"
        r")"
    )
    for path in example_files:
        text = path.read_text(encoding="utf-8")
        try:
            compile(text, str(path), "exec")
        except SyntaxError as exc:
            errors.append(f"generated example does not compile: {path}:{exc.lineno}")
            continue
        if not facade_pattern.search(text):
            errors.append(
                f"generated example must acquire runtime through package facade: {path}"
            )
        match = forbidden_runtime_pattern.search(text)
        if match:
            line_number = text.count("\n", 0, match.start()) + 1
            errors.append(
                "generated example must not use direct network/core runtime access: "
                f"{path}:{line_number}"
            )


def _iter_text_files(
    roots: tuple[Path, ...],
    *,
    suffixes: set[str] | None = None,
    excluded_suffixes: set[str] | None = None,
) -> list[Path]:
    excluded_dirs = {".git", ".venv", "dist", "__pycache__", ".pytest_cache"}
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            candidates = [root]
        else:
            candidates = [path for path in root.rglob("*") if path.is_file()]
        for path in candidates:
            if any(part in excluded_dirs for part in path.parts):
                continue
            if suffixes is not None and path.suffix not in suffixes:
                continue
            if excluded_suffixes is not None and path.suffix in excluded_suffixes:
                continue
            paths.append(path)
    return paths


def _audit_overseas_todo(
    parser: argparse.ArgumentParser,
    errors: list[str],
) -> None:
    root_subparsers = _subparser_action(parser)
    root_choices = set((root_subparsers.choices if root_subparsers else {}).keys())
    for command in ("investment-info", "overseas"):
        if command in root_choices:
            errors.append(f"overseas TODO command is runtime-exposed: kiwoom {command}")

    for path in OVERSEAS_PLACEHOLDERS:
        if not path.is_file():
            errors.append(f"overseas TODO placeholder missing: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if "TODO" not in text:
            errors.append(f"overseas placeholder missing TODO marker: {path}")
        if re.search(r"^def add_.*_parser", text, flags=re.MULTILINE):
            errors.append(f"overseas placeholder exports a parser hook: {path}")

    for definition in load_command_definitions():
        if (
            definition.cli_group in OVERSEAS_TODO_GROUPS
            and definition.status == "implemented"
        ):
            errors.append(
                "overseas TODO group must not be implemented before runtime "
                f"verification: {definition.command_path}"
            )


def _audit_agent_reference(
    definitions: list[CommandDefinition],
    errors: list[str],
) -> None:
    generated_references = render_all_references(
        definitions, load_argument_definitions()
    )
    for path, expected_text in generated_references.items():
        if not path.is_file():
            errors.append(f"agent reference missing: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if "uv run kiwoom" in text:
            errors.append(f"agent reference documents forbidden invocation: {path}")
        if text != expected_text:
            errors.append(f"agent reference is not generated from current maps: {path}")

    for path in AGENT_REFERENCE_ROOT.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if "uv run kiwoom" in text:
            errors.append(f"agent reference documents forbidden invocation: {path}")

    if not AGENT_IMPLEMENTED_COMMANDS.is_file():
        return
    command_inventory = AGENT_IMPLEMENTED_COMMANDS.read_text(encoding="utf-8")
    generated_inventory = render_implemented_commands(definitions)
    if command_inventory != generated_inventory:
        errors.append(
            "agent implemented command inventory is not generated from current maps"
        )
    inventory_rows = _agent_inventory_rows(command_inventory)
    expected_rows = {
        definition.command_path: (definition.api_id, definition.safety_policy)
        for definition in definitions
    }
    if inventory_rows != expected_rows:
        errors.append(
            "agent implemented command inventory mismatch: "
            f"doc_only={_mapping_diff(inventory_rows, expected_rows)} "
            f"map_only={_mapping_diff(expected_rows, inventory_rows)}"
        )
    for command_path in STATIC_IMPLEMENTED_COMMANDS:
        if command_path not in command_inventory:
            errors.append(
                f"agent implemented command inventory missing: {command_path}"
            )
    for command_path in ("kiwoomcli setup", "kiwoomcli auth list", "kiwoomcli auth switch"):
        if command_path not in command_inventory:
            errors.append(
                f"agent implemented command inventory missing: {command_path}"
            )
    for definition in definitions:
        if definition.command_path not in command_inventory:
            errors.append(
                f"agent implemented command inventory missing: {definition.command_path}"
            )
    if AGENT_COMMAND_OPTIONS.is_file():
        command_options = AGENT_COMMAND_OPTIONS.read_text(encoding="utf-8")
        generated_options = render_command_options(
            definitions,
            load_argument_definitions(),
        )
        if command_options != generated_options:
            errors.append(
                "agent command option reference is not generated from current maps"
            )


def _agent_inventory_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    pattern = re.compile(r"^\| `([^`]+)` \| `([^`]+)` \| `([^`]+)` \|$")
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        command_path, api_id, safety_policy = match.groups()
        rows[command_path] = (api_id, safety_policy)
    return rows


def _mapping_diff(
    left: dict[str, tuple[str, str]],
    right: dict[str, tuple[str, str]],
) -> dict[str, tuple[str, str]]:
    return {key: left[key] for key in sorted(left) if left[key] != right.get(key)}


def _audit_parser_path(
    parser: argparse.ArgumentParser,
    definition: CommandDefinition,
    errors: list[str],
) -> argparse.ArgumentParser | None:
    tokens = _command_tokens(definition.command_path)
    resolved = _resolve_parser(parser, tokens)
    if resolved is None:
        errors.append(f"parser missing command path: {definition.command_path}")
    return resolved


def _audit_mapped_options(
    parser: argparse.ArgumentParser,
    command_path: str,
    errors: list[str],
) -> None:
    option_strings = {
        option for action in parser._actions for option in action.option_strings
    }
    for argument in get_argument_definitions(command_path):
        if argument.option and argument.option not in option_strings:
            errors.append(
                f"parser missing mapped option {argument.option}: {command_path}"
            )


def _audit_removed_options(
    parser: argparse.ArgumentParser,
    command_path: str,
    errors: list[str],
) -> None:
    option_strings = {
        option for action in parser._actions for option in action.option_strings
    }
    for removed, replacement in REMOVED_OPTION_REPLACEMENTS_BY_COMMAND.get(
        command_path,
        {},
    ).items():
        if removed in option_strings:
            errors.append(
                f"parser exposes removed option {removed}: {command_path} "
                f"(use {replacement})"
            )


def _audit_help_contract(
    parser: argparse.ArgumentParser,
    definition: CommandDefinition,
    errors: list[str],
) -> None:
    if not get_argument_definitions(definition.command_path):
        return
    help_text = parser.format_help()
    for section in REQUIRED_MAPPED_HELP_SECTIONS:
        if section not in help_text:
            errors.append(
                f"help output missing {section} section: {definition.command_path}"
            )
    if definition.safety_policy == "order_write" and "--confirm" not in help_text:
        errors.append(
            f"order_write help missing --confirm: {definition.command_path}"
        )


def _audit_static_command(
    parser: argparse.ArgumentParser,
    command_path: str,
    errors: list[str],
) -> None:
    resolved = _resolve_parser(parser, _command_tokens(command_path))
    if resolved is None:
        errors.append(f"parser missing command path: {command_path}")
    _audit_doc_text(command_path, errors)
    _audit_contract(command_path, errors)


def _audit_docs(definition: CommandDefinition, errors: list[str]) -> None:
    _audit_doc_text(definition.command_path, errors)
    _audit_readme_options(definition, errors)
    _audit_feature_matrix_row(definition, errors)
    if definition.cli_group not in CONTRACT_GROUPS:
        return

    _audit_contract(definition.command_path, errors, definition)


def _audit_doc_text(command_path: str, errors: list[str]) -> None:
    readme = README.read_text(encoding="utf-8")
    feature_matrix = FEATURE_MATRIX.read_text(encoding="utf-8")

    if command_path not in readme:
        errors.append(f"README missing implemented command: {command_path}")

    if not _has_implemented_feature_row(feature_matrix, command_path):
        errors.append(f"feature matrix missing Implemented row: {command_path}")


def _audit_readme_options(definition: CommandDefinition, errors: list[str]) -> None:
    line = _readme_command_line(definition.command_path)
    if line is None:
        return
    _audit_removed_options_in_text(
        line,
        definition.command_path,
        errors,
        context="README command line",
    )
    for argument in get_argument_definitions(definition.command_path):
        if argument.option and argument.option not in line:
            errors.append(
                f"README command line missing mapped option {argument.option}: "
                f"{definition.command_path}"
            )


def _audit_feature_matrix_row(
    definition: CommandDefinition,
    errors: list[str],
) -> None:
    row = _feature_matrix_row(definition.command_path)
    if row is None:
        return
    if f"`{definition.api_id}`" not in row:
        errors.append(
            f"feature matrix row missing API ID {definition.api_id}: "
            f"{definition.command_path}"
        )
    if f"| `{definition.safety_policy}` |" not in row:
        errors.append(
            f"feature matrix row missing safety policy {definition.safety_policy}: "
            f"{definition.command_path}"
        )


def _audit_contract(
    command_path: str,
    errors: list[str],
    definition: CommandDefinition | None = None,
) -> None:
    contracts = COMMAND_CONTRACTS.read_text(encoding="utf-8")
    section = _contract_section(contracts, command_path)
    if section is None:
        errors.append(f"command contracts missing section: {command_path}")
        return
    if "Status: Implemented" not in section:
        errors.append(f"command contracts section is not Implemented: {command_path}")
    if definition is None:
        return
    _audit_removed_options_in_text(
        section,
        command_path,
        errors,
        context="command contracts section",
    )
    if f"Candidate API: `{definition.api_id}`" not in section:
        errors.append(
            f"command contracts section missing candidate API {definition.api_id}: "
            f"{command_path}"
        )
    if f"Safety: `{definition.safety_policy}`" not in section:
        errors.append(
            f"command contracts section missing safety policy {definition.safety_policy}: "
            f"{command_path}"
        )
    for argument in get_argument_definitions(command_path):
        if argument.option and f"`{argument.option}`" not in section:
            errors.append(
                f"command contracts section missing mapped option {argument.option}: "
                f"{command_path}"
            )
        if argument.kiwoom_field and f"`{argument.kiwoom_field}`" not in section:
            errors.append(
                f"command contracts section missing Kiwoom field {argument.kiwoom_field}: "
                f"{command_path}"
            )


def _audit_removed_options_in_text(
    text: str,
    command_path: str,
    errors: list[str],
    *,
    context: str,
) -> None:
    for removed, replacement in REMOVED_OPTION_REPLACEMENTS_BY_COMMAND.get(
        command_path,
        {},
    ).items():
        if _contains_option(text, removed):
            errors.append(
                f"{context} documents removed option {removed}: {command_path} "
                f"(use {replacement})"
            )


def _audit_preview(definition: CommandDefinition, errors: list[str]) -> None:
    args = SimpleNamespace(**_sample_values(definition.command_path))
    try:
        body = build_body(definition.command_path, args)
        payload = preview_rest_command(definition, body=body)
    except CliError as exc:
        errors.append(f"preview build failed for {definition.command_path}: {exc}")
        return

    if payload.get("network") != "not-submitted":
        errors.append(
            f"preview command allows network submission: {definition.command_path}"
        )


def _audit_order_write(definition: CommandDefinition, errors: list[str]) -> None:
    """order_write commands must preview without --confirm and be gated by it."""
    args = SimpleNamespace(**_sample_values(definition.command_path))
    try:
        body = build_body(definition.command_path, args)
        payload = preview_rest_command(definition, body=body)
    except CliError as exc:
        errors.append(
            f"order_write preview build failed for {definition.command_path}: {exc}"
        )
        return

    if payload.get("network") != "not-submitted":
        errors.append(
            f"order_write command submits without --confirm: {definition.command_path}"
        )
    if any(
        field in body for field in ("orig_ord_no", "ord_no", "fr_ord_no", "rsrv_ord_no")
    ):
        invalid_body = dict(body)
        for field in ("orig_ord_no", "ord_no", "fr_ord_no", "rsrv_ord_no"):
            if field in invalid_body:
                invalid_body[field] = "0000000000"
        invalid_payload = preview_rest_command(definition, body=invalid_body)
        validation = invalid_payload.get("validation", {})
        if validation.get("status") != "invalid":
            errors.append(
                f"order_write preview does not report invalid order id: {definition.command_path}"
            )

    try:
        enforce_before_request(definition, confirm=False)
    except CliError:
        pass
    else:
        errors.append(
            f"order_write command is not gated by --confirm: {definition.command_path}"
        )

    try:
        enforce_before_request(definition, confirm=True)
    except CliError as exc:
        errors.append(
            f"order_write command stays blocked even with --confirm: {definition.command_path} ({exc})"
        )

    _audit_order_price_policy(definition, errors)
    _audit_order_confirmation(definition, errors)


def _audit_order_price_policy(definition: CommandDefinition, errors: list[str]) -> None:
    arguments = get_argument_definitions(definition.command_path)
    order_type_argument = next(
        (argument for argument in arguments if argument.option == "--order-type"),
        None,
    )
    price_argument = next(
        (argument for argument in arguments if argument.option == "--price"),
        None,
    )
    if order_type_argument is None or price_argument is None:
        return

    if "limit" in order_type_argument.choices:
        values = _sample_values(definition.command_path)
        values[order_type_argument.dest] = "limit"
        values.pop(price_argument.dest, None)
        try:
            build_body(definition.command_path, SimpleNamespace(**values))
        except CliError as exc:
            message = str(exc)
            if "--price" not in message or "필요" not in message:
                errors.append(
                    "order_write limit price validation returned unexpected error "
                    f"for {definition.command_path}: {exc}"
                )
        else:
            errors.append(
                "order_write limit order does not require --price: "
                f"{definition.command_path}"
            )

    if "market" in order_type_argument.choices:
        values = _sample_values(definition.command_path)
        values[order_type_argument.dest] = "market"
        values[price_argument.dest] = "70000"
        try:
            build_body(definition.command_path, SimpleNamespace(**values))
        except CliError as exc:
            message = str(exc)
            if "--price" not in message or "넣지 마세요" not in message:
                errors.append(
                    "order_write market price validation returned unexpected error "
                    f"for {definition.command_path}: {exc}"
                )
        else:
            errors.append(
                "order_write market order allows --price despite policy: "
                f"{definition.command_path}"
            )


def _audit_order_confirmation(definition: CommandDefinition, errors: list[str]) -> None:
    args = SimpleNamespace(**_sample_values(definition.command_path))
    try:
        payload = build_order_confirmation(definition, args)
    except CliError as exc:
        errors.append(
            f"order_write confirmation build failed for {definition.command_path}: {exc}"
        )
        return
    if "--confirm" not in payload.get("message", ""):
        errors.append(
            "order_write confirmation message does not guide --confirm: "
            f"{definition.command_path}"
        )
    order = payload.get("order", {})
    if not isinstance(order, dict) or not order.get("kind"):
        errors.append(
            f"order_write confirmation missing order kind: {definition.command_path}"
        )
    for internal_key in ("body", "network", "api_id", "path", "method"):
        if internal_key in payload:
            errors.append(
                "order_write confirmation exposes raw request metadata: "
                f"{definition.command_path} key={internal_key}"
            )


def _sample_values(command_path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    sampled_required_fields: set[str] = set()
    for argument in get_argument_definitions(command_path):
        if not argument.dest:
            continue
        if (
            argument.required
            and argument.kiwoom_field
            and argument.kiwoom_field in sampled_required_fields
        ):
            continue
        if argument.required and argument.kiwoom_field:
            sampled_required_fields.add(argument.kiwoom_field)
        if argument.default:
            values[argument.dest] = argument.default
            continue
        if argument.choices:
            values[argument.dest] = argument.choices[0]
            continue
        values[argument.dest] = _sample_value(argument.type_name)
    return values


def _sample_value(type_name: str) -> str:
    samples = {
        "stock_code": "005930",
        "instrument_code": "57JBHH",
        "sector_code": "001",
        "date_yyyymmdd": "20260529",
        "adjusted_price_flag": "1",
        "quantity": "1",
        "cancel_quantity": "0",
        "price": "70000",
        "order_id": "0000140",
        "order_type": "limit",
        "market": "KRX",
    }
    return samples.get(type_name, "value")


def _resolve_parser(
    parser: argparse.ArgumentParser,
    tokens: list[str],
) -> argparse.ArgumentParser | None:
    current = parser
    for token in tokens:
        subparsers = _subparser_action(current)
        if subparsers is None:
            return None
        current = subparsers.choices.get(token)
        if current is None:
            return None
    return current


def _subparser_action(
    parser: argparse.ArgumentParser,
) -> argparse._SubParsersAction | None:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action
    return None


def _command_tokens(command_path: str) -> list[str]:
    tokens = command_path.split()
    if not tokens or tokens[0] != "kiwoomcli":
        raise ValueError(f"command_path must start with kiwoomcli: {command_path}")
    return tokens[1:]


def _contract_section(text: str, command_path: str) -> str | None:
    heading = f"### `{command_path}`"
    start = text.find(heading)
    if start < 0:
        return None
    next_heading = _find_next_heading(text, start + len(heading))
    return text[start:next_heading]


def _has_implemented_feature_row(text: str, command_path: str) -> bool:
    row = _feature_matrix_row(command_path)
    return row is not None and "| Implemented |" in row


def _readme_command_line(command_path: str) -> str | None:
    for line in README.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith(command_path):
            return stripped
    return None


def _feature_matrix_row(command_path: str) -> str | None:
    prefix = f"| `{command_path}"
    for line in FEATURE_MATRIX.read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line
    return None


def _contains_option(text: str, option: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(option)}(?![\w-])", text) is not None


def _find_next_heading(text: str, start: int) -> int:
    candidates = [
        index
        for marker in ("\n### ", "\n## ")
        for index in [text.find(marker, start)]
        if index >= 0
    ]
    if not candidates:
        return len(text)
    return min(candidates)


if __name__ == "__main__":
    audit()
