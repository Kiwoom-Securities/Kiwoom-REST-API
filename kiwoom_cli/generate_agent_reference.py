"""Generate agent-facing Kiwoom CLI reference fragments from maps."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from kiwoom_cli.argument_maps import ArgumentDefinition, load_argument_definitions
from kiwoom_cli.registry import CommandDefinition, load_command_definitions


FOUNDATION_COMMANDS = (
    "kiwoomcli setup",
    "kiwoomcli auth login [--alias NAME] [--mode demo|real]",
    "kiwoomcli auth list",
    "kiwoomcli auth switch <alias>",
    "kiwoomcli auth status [--profile NAME | --mode demo|real]",
    "kiwoomcli auth refresh [--profile NAME | --mode demo|real]",
    "kiwoomcli auth revoke [--profile NAME | --mode demo|real]",
    "kiwoomcli auth clear [--profile NAME | --mode demo|real] [--all]",
    "kiwoomcli auth remove <alias>",
    "kiwoomcli spec search <query> [--limit N]",
    "kiwoomcli spec show <api-id> [--format pretty|json|yaml]",
    "kiwoomcli spec groups [--format pretty|json|yaml]",
    "kiwoomcli spec apis [--group <text>] [--limit N] [--format pretty|json|yaml]",
)

STATIC_REFERENCE_NAMES = (
    "setup",
    "output",
    "glossary",
)

ROOT = Path(__file__).resolve().parents[1]
AGENT_REFERENCE_ROOT = ROOT / ".agents" / "skills" / "kiwoom" / "kiwoom"
REFERENCE_ROOT = AGENT_REFERENCE_ROOT / "references"
CONDITION_HTS_NOTE = (
    "조건검색식 생성/수정은 영웅문 HTS에서 해야 합니다. "
    "CLI는 HTS에 저장된 조건식을 목록 조회, 선택, 조회, 구독, 해제만 합니다."
)
WATCHLIST_CODES_NOTE = (
    "`kiwoomcli domestic stocks watchlist-info --codes` uses pipe-delimited codes such as "
    "`005930|000660`; comma-delimited input is not the documented API shape."
)
CREDIT_LOANABLE_NOTE = (
    "`kiwoomcli domestic stocks credit-loanable-check` preserves `crd_alow_yn` and adds "
    "`loanable` as `true`, `false`, or `null`."
)
GOLD_CODE_NOTE = (
    "Use `M04020000` (`금 99.99_1kg`) as the gold spot sample code unless a "
    "specific live gold instrument is required."
)
ELW_SAMPLE_NOTE = (
    "ELW instruments expire; choose sample parameters from current/proven ELW "
    "evidence, not stale placeholder codes."
)
ACCOUNT_EMPTY_NOTE = (
    "Account/order history commands are account-state dependent: realized PnL, "
    "return-rate, order/fill, and open-order queries may return empty lists when "
    "the selected account and date have no matching holdings, fills, or open "
    "orders."
)
PROGRAM_EMPTY_NOTE = (
    "Program-trading aggregate commands are market-time and condition dependent; "
    "empty lists with `return_code=0` are valid zero-row results, not positive "
    "investor-useful data evidence by themselves. Use the samplecode-backed "
    "program market-code family for `--market-code`, such as `P00101`/`P10102` "
    "for KRX KOSPI/KOSDAQ and the `P001_NX01`/`P101_NX02` or "
    "`P001_AL01`/`P101_AL02` variants for NXT/integrated markets."
)
ACCOUNT_STATE_DEPENDENT_COMMANDS = {
    "kiwoomcli domestic accounts realized-profit-stock-daily",
    "kiwoomcli domestic accounts realized-profit-period-stock",
    "kiwoomcli domestic accounts return-rate",
    "kiwoomcli domestic accounts order-fill-detail",
    "kiwoomcli domestic accounts order-fill-status",
    "kiwoomcli domestic accounts gold-all-order-fills",
    "kiwoomcli domestic accounts gold-order-fills",
    "kiwoomcli domestic accounts gold-open-orders",
    "kiwoomcli domestic orders list-open",
    "kiwoomcli domestic orders list-fills",
    "kiwoomcli domestic orders open-detail",
}


def render_all_references(
    definitions: list[CommandDefinition] | None = None,
    arguments: list[ArgumentDefinition] | None = None,
) -> dict[Path, str]:
    resolved_definitions = definitions or load_command_definitions()
    resolved_arguments = arguments or load_argument_definitions()
    references: dict[Path, str] = {
        AGENT_REFERENCE_ROOT / "SKILL.md": render_skill(resolved_definitions),
        REFERENCE_ROOT / "setup.md": render_setup_reference(resolved_definitions),
        REFERENCE_ROOT / "output.md": render_output_reference(),
        REFERENCE_ROOT / "glossary.md": render_glossary_reference(resolved_arguments),
        REFERENCE_ROOT / "implemented-commands.md": render_implemented_commands(
            resolved_definitions,
        ),
        REFERENCE_ROOT / "command-options.md": render_command_options(
            resolved_definitions,
            resolved_arguments,
        ),
    }
    for group in _implemented_resource_groups(resolved_definitions):
        references[REFERENCE_ROOT / f"{group}.md"] = render_group_reference(
            group,
            resolved_definitions,
            resolved_arguments,
        )
    return references


def render_skill(definitions: list[CommandDefinition] | None = None) -> str:
    resolved_definitions = definitions or load_command_definitions()
    reference_names = [
        *STATIC_REFERENCE_NAMES,
        *_implemented_resource_groups(resolved_definitions),
        "implemented-commands",
        "command-options",
    ]
    lines = [
        "# Kiwoom CLI Skill",
        "",
        "Use this skill when an agent needs to inspect or operate the Kiwoom CLI from",
        "this repository.",
        "",
        "<!-- generated from kiwoom_cli/maps/*.csv; do not edit by hand -->",
        "",
        "## Rules",
        "",
        "- Use the installed command name `kiwoomcli`.",
        "- Do not use a development runner as the customer-facing invocation.",
        "- Treat `kiwoom_api_spec.json`, `api_list.csv`, and `kiwoom_cli/maps/*.csv` as",
        "  the source of truth.",
        "- Use `kiwoomcli spec search/show/groups/apis` for discovery and debugging, not as",
        "  the primary trading surface.",
        "- Prefer implemented resource commands listed in the generated references over",
        "  raw API IDs.",
        "- Overseas commands are TODO/planned unless they appear in the implemented",
        "  command inventory generated from maps.",
        f"- {CONDITION_HTS_NOTE}",
        f"- {WATCHLIST_CODES_NOTE}",
        f"- {CREDIT_LOANABLE_NOTE}",
        f"- {GOLD_CODE_NOTE}",
        f"- {ELW_SAMPLE_NOTE}",
        f"- {ACCOUNT_EMPTY_NOTE}",
        f"- {PROGRAM_EMPTY_NOTE}",
        "- Do not use test doubles or recorded payloads as behavioral proof.",
        "- If credentials are unavailable, report real-call verification as",
        "  blocked/not-run.",
        "",
        "## References",
        "",
    ]
    lines.extend(f"- [{name}](references/{name}.md)" for name in reference_names)
    return "\n".join(lines) + "\n"


def render_setup_reference(definitions: list[CommandDefinition] | None = None) -> str:
    auth_definitions = sorted(
        [
            definition
            for definition in (definitions or load_command_definitions())
            if definition.cli_group == "auth" and definition.status == "implemented"
        ],
        key=lambda definition: definition.command_path,
    )
    lines = [
        "# Setup And Discovery",
        "",
        "<!-- generated from kiwoom_cli/maps/*.csv; do not edit by hand -->",
        "",
        "## Commands",
        "",
        "```sh",
        *FOUNDATION_COMMANDS,
        "```",
        "",
        "## Auth API mappings",
        "",
        "| Command | API ID | API name | Safety |",
        "| --- | --- | --- | --- |",
    ]
    for definition in auth_definitions:
        lines.append(
            f"| `{definition.command_path}` | `{definition.api_id}` | "
            f"{definition.api_name} | `{definition.safety_policy}` |"
        )
    lines.extend(
        [
            "",
            "## Spec Discovery",
            "",
            "`kiwoomcli spec` reads the packaged local spec. It is a discovery fallback;",
            "prefer mapped resource commands when an implemented command exists.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_output_reference() -> str:
    return (
        "\n".join(
            [
                "# Output",
                "",
                "<!-- generated from kiwoom_cli/maps/*.csv; do not edit by hand -->",
                "",
                "Implemented domain commands accept:",
                "",
                "```sh",
                "--format pretty|json|jsonl|yaml",
                "--profile NAME",
                "--mode demo|real",
                "```",
                "",
                "Output rules:",
                "",
                "- `pretty` is the default, human-readable view (indented JSON).",
                "- Use `json` for compact single-line agent parsing.",
                "- Use `jsonl` for one JSON record per line (list rows and streams).",
                "- Use `yaml` for a YAML rendering.",
                "- Token-like values and account identifiers are redacted by the CLI output",
                "  layer where the safety policy requires it.",
                "- Order numbers are shown because users need them for modify/cancel flows.",
            ]
        )
        + "\n"
    )


def render_glossary_reference(arguments: list[ArgumentDefinition] | None = None) -> str:
    resolved_arguments = arguments or load_argument_definitions()
    common_options = _common_options(resolved_arguments)
    lines = [
        "# Glossary",
        "",
        "<!-- generated from kiwoom_cli/maps/*.csv; do not edit by hand -->",
        "",
        "| CLI term | Kiwoom meaning |",
        "| --- | --- |",
        "| `--code` | Instrument, stock, theme, ETF, ELW, sector, gold, or symbol code as defined by the command contract. |",
        "| `--qty` | Order quantity. |",
        "| `--price` | Order unit price. |",
        "| `--order-id` | Original order number used by modify/cancel or inquiry commands. |",
        "| `--profile` | Local credential/profile alias. |",
        "| `--mode` | Direct runtime mode: `demo` or `real`. |",
        "| `KRX` | Korea Exchange. |",
        "| `NXT` | Alternative domestic trading venue selector when supported by the API. |",
        "| `SOR` | Smart order routing selector when supported by the API. |",
        "| `ALL` | Integrated exchange selector when supported by the API. |",
        "| `preview-only` | Request can be built and validated, but network submission is blocked. |",
        "| `guarded` | Command may expose account-sensitive data and must apply redaction policy. |",
        "",
        "## Common mapped options",
        "",
        "| Option | Mapped command count |",
        "| --- | ---: |",
    ]
    for option, count in common_options:
        lines.append(f"| `{option}` | {count} |")
    return "\n".join(lines) + "\n"


def render_implemented_commands(
    definitions: list[CommandDefinition] | None = None,
) -> str:
    implemented = _implemented_definitions(definitions or load_command_definitions())
    lines = [
        "# Implemented Commands",
        "",
        "This file lists the currently implemented customer-facing `kiwoomcli` commands",
        "that the agent reference may use.",
        "",
        "<!-- generated from kiwoom_cli/maps/api_commands.csv; do not edit by hand -->",
        "",
        "## Foundation",
        "",
        "```sh",
        *FOUNDATION_COMMANDS,
        "```",
        "",
        "## Mapped Resource Commands",
        "",
        "| Command | API ID | Safety |",
        "| --- | --- | --- |",
    ]
    for definition in implemented:
        lines.append(
            f"| `{definition.command_path}` | `{definition.api_id}` | "
            f"`{definition.safety_policy}` |"
        )
    return "\n".join(lines) + "\n"


def render_command_options(
    definitions: list[CommandDefinition] | None = None,
    arguments: list[ArgumentDefinition] | None = None,
) -> str:
    implemented = _implemented_definitions(definitions or load_command_definitions())
    arguments_by_command = _arguments_by_command(
        arguments or load_argument_definitions()
    )
    lines = [
        "# Command Options",
        "",
        "This file lists implemented command options generated from",
        "`kiwoom_cli/maps/arguments.csv` and `kiwoom_cli/maps/api_commands.csv`.",
        "",
        "<!-- generated from kiwoom_cli/maps/*.csv; do not edit by hand -->",
        "",
    ]
    for definition in implemented:
        lines.extend(
            [
                f"## `{definition.command_path}`",
                "",
                f"- API ID: `{definition.api_id}`",
                f"- Safety: `{definition.safety_policy}`",
                f"- Coverage: `{definition.coverage_status}`",
                "",
            ]
        )
        lines.extend(_command_domain_notes(definition))
        command_arguments = arguments_by_command.get(definition.command_path, [])
        lines.extend(_argument_table(command_arguments, definition))
    return "\n".join(lines)


def render_group_reference(
    group: str,
    definitions: list[CommandDefinition] | None = None,
    arguments: list[ArgumentDefinition] | None = None,
) -> str:
    resolved_definitions = definitions or load_command_definitions()
    resolved_arguments = arguments or load_argument_definitions()
    group_definitions = [
        definition
        for definition in _implemented_definitions(resolved_definitions)
        if definition.cli_group == group
    ]
    arguments_by_command = _arguments_by_command(resolved_arguments)
    lines = [
        f"# {_title(group)}",
        "",
        "<!-- generated from kiwoom_cli/maps/*.csv; do not edit by hand -->",
        "",
        "## Commands",
        "",
        "```sh",
    ]
    for definition in group_definitions:
        lines.append(
            _usage_line(
                definition, arguments_by_command.get(definition.command_path, [])
            )
        )
    lines.extend(
        [
            "```",
            "",
            "## Mappings",
            "",
            "| Command | API ID | API name | Coverage | Safety |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for definition in group_definitions:
        lines.append(
            f"| `{definition.command_path}` | `{definition.api_id}` | {definition.api_name} | "
            f"`{definition.coverage_status}` | `{definition.safety_policy}` |"
        )
    lines.extend(_group_safety_notes(group_definitions))
    lines.extend(_group_domain_notes(group_definitions))
    lines.append("\n## Options\n")
    for definition in group_definitions:
        lines.extend(
            [
                f"### `{definition.command_path}`",
                "",
                f"Candidate API: `{definition.api_id}`",
                "",
            ]
        )
        lines.extend(_command_domain_notes(definition))
        lines.extend(
            _argument_table(arguments_by_command.get(definition.command_path, []), definition)
        )
    return "\n".join(lines) + "\n"


def _implemented_resource_groups(definitions: list[CommandDefinition]) -> list[str]:
    return sorted(
        {
            definition.cli_group
            for definition in definitions
            if definition.status == "implemented" and definition.cli_group != "auth"
        }
    )


def _implemented_definitions(
    definitions: list[CommandDefinition],
) -> list[CommandDefinition]:
    return sorted(
        [
            definition
            for definition in definitions
            if definition.status == "implemented"
        ],
        key=lambda definition: definition.command_path,
    )


def _arguments_by_command(
    arguments: list[ArgumentDefinition],
) -> dict[str, list[ArgumentDefinition]]:
    by_command: dict[str, list[ArgumentDefinition]] = {}
    for argument in arguments:
        by_command.setdefault(argument.command_path, []).append(argument)
    return by_command


def _argument_table(
    arguments: list[ArgumentDefinition],
    definition: CommandDefinition | None = None,
) -> list[str]:
    resolved_arguments = list(arguments)
    if definition is not None:
        resolved_arguments.extend(_cli_only_stream_arguments(definition, arguments))
    if not resolved_arguments:
        return [
            "No mapped request-body options. Runtime/auth values are supplied by the CLI.",
            "",
        ]
    lines = [
        "| Option | Required | Kiwoom field | Type | Choices | Default |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for argument in resolved_arguments:
        lines.append(
            "| "
            f"`{argument.option}` | "
            f"{'yes' if argument.required else 'no'} | "
            f"`{argument.kiwoom_field}` | "
            f"`{argument.type_name}` | "
            f"{_format_values(argument.choices)} | "
            f"{_format_value(argument.default)} |"
        )
    lines.append("")
    return lines


def _cli_only_stream_arguments(
    definition: CommandDefinition,
    arguments: list[ArgumentDefinition],
) -> list[ArgumentDefinition]:
    if _is_condition_subscribe_command(definition):
        return [
            _cli_only_argument(definition, "--count", "count", "positive integer", "1"),
            _cli_only_argument(definition, "--duration", "duration", "positive seconds", "15"),
            _cli_only_argument(definition, "--check", "check", "flag", ""),
        ]
    if not _is_foreground_stream_command(definition):
        return []
    extras = [
        _cli_only_argument(definition, "--count", "count", "positive integer", "1"),
        _cli_only_argument(definition, "--duration", "duration", "non-negative seconds", "15"),
        _cli_only_argument(definition, "--watch", "watch", "flag", ""),
        _cli_only_argument(definition, "--check", "check", "flag", ""),
        _cli_only_argument(definition, "--named", "named", "flag", ""),
        _cli_only_argument(definition, "--output", "output", "path", ""),
    ]
    if any(argument.dest == "code" for argument in arguments):
        extras.insert(0, _cli_only_argument(definition, "--codes", "codes", "comma list", ""))
    return extras


def _cli_only_argument(
    definition: CommandDefinition,
    option: str,
    dest: str,
    type_name: str,
    default: str,
) -> ArgumentDefinition:
    return ArgumentDefinition(
        command_path=definition.command_path,
        option=option,
        dest=dest,
        kiwoom_field="CLI only",
        required=False,
        type_name=type_name,
        choices=(),
        value_map={},
        default=default,
        description="",
    )


def _usage_line(
    definition: CommandDefinition,
    arguments: list[ArgumentDefinition],
) -> str:
    parts = [definition.command_path]
    for argument in arguments:
        if not argument.option:
            continue
        if _is_foreground_stream_command(definition) and argument.dest == "code":
            placeholder = _placeholder(argument)
            if argument.required and not argument.default:
                parts.append(f"(--code {placeholder} | --codes <codes>)")
            else:
                parts.append(f"[--code {placeholder}] [--codes <codes>]")
            continue
        placeholder = _placeholder(argument)
        token = f"{argument.option} {placeholder}"
        if argument.required and not argument.default:
            parts.append(token)
        else:
            parts.append(f"[{token}]")
    if _is_foreground_stream_command(definition):
        parts.append(
            "[--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]"
        )
    if _is_condition_subscribe_command(definition):
        parts.append("[--count <n>] [--duration <seconds>] [--check]")
    if definition.safety_policy in {"order_preview", "order_write"}:
        parts.append("[--confirm]")
    if definition.cli_group != "auth":
        parts.append("[--format pretty|json|jsonl|yaml]")
        parts.append("[--profile NAME | --mode demo|real]")
    return " ".join(parts)


def _placeholder(argument: ArgumentDefinition) -> str:
    if argument.choices:
        return "|".join(argument.choices)
    placeholders = {
        "stock_code": "<code>",
        "exchange_stock_code": "<code>",
        "instrument_code": "<code>",
        "sector_code": "<code>",
        "date_yyyymmdd": "<yyyymmdd>",
        "adjusted_price_flag": "0|1",
        "quantity": "<n>",
        "cancel_quantity": "<n>",
        "price": "<price>",
        "order_id": "<id>",
        "preview_order_id": "<id>",
        "order_type": "<type>",
        "market": "<value>",
    }
    return placeholders.get(argument.type_name, "<value>")


def _group_safety_notes(definitions: list[CommandDefinition]) -> list[str]:
    policies = {definition.safety_policy for definition in definitions}
    lines: list[str] = []
    if "account_read" in policies:
        lines.extend(
            [
                "",
                "Account identifiers must not be exposed in human/debug output.",
                "Order numbers are shown because users need them for modify/cancel flows.",
            ]
        )
    if "order_preview" in policies:
        lines.extend(
            [
                "",
                "Preview-only order commands build and validate a request but must report",
                "`network: not-submitted`; `--confirm` does not submit while the map row stays",
                "`preview-only` with `order_preview` safety.",
                "Invalid preview order identifiers are reported in structured output before",
                "any network submission path is considered.",
            ]
        )
    if "order_write" in policies:
        lines.extend(
            [
                "",
                "Order write commands submit to the real endpoint only when `--confirm`",
                "is supplied. Without `--confirm`, the command prints a short unsubmitted",
                "order confirmation and never calls the order API. Invalid order",
                "identifiers are reported before any network submission path is considered.",
            ]
        )
    if policies:
        lines.extend(
            [
                "",
                "Credentialed verification must use real Kiwoom credentials. Do not use",
                "test doubles or recorded payloads.",
            ]
        )
    return lines


def _group_domain_notes(definitions: list[CommandDefinition]) -> list[str]:
    notes: list[str] = []
    if any(_is_condition_command(definition) for definition in definitions):
        notes.extend(
            [
                "",
                "Condition search note: " + CONDITION_HTS_NOTE,
            ]
        )
    if any(
        definition.command_path == "kiwoomcli domestic stocks watchlist-info"
        for definition in definitions
    ):
        notes.extend(
            [
                "",
                "Watchlist note: " + WATCHLIST_CODES_NOTE,
            ]
        )
    if any(
        definition.command_path == "kiwoomcli domestic stocks credit-loanable-check"
        for definition in definitions
    ):
        notes.extend(
            [
                "",
                "Credit loanable note: " + CREDIT_LOANABLE_NOTE,
            ]
        )
    if any("gold" in definition.command_path for definition in definitions):
        notes.extend(
            [
                "",
                "Gold spot note: " + GOLD_CODE_NOTE,
            ]
        )
    if any(definition.cli_group == "elws" for definition in definitions):
        notes.extend(
            [
                "",
                "ELW sample note: " + ELW_SAMPLE_NOTE,
            ]
        )
    if any(
        _is_account_state_dependent_command(definition) for definition in definitions
    ):
        notes.extend(
            [
                "",
                "Account empty-result note: " + ACCOUNT_EMPTY_NOTE,
            ]
        )
    if any(_is_program_trading_command(definition) for definition in definitions):
        notes.extend(
            [
                "",
                "Program-trading empty-result note: " + PROGRAM_EMPTY_NOTE,
            ]
        )
    return notes


def _command_domain_notes(definition: CommandDefinition) -> list[str]:
    notes: list[str] = []
    if _is_condition_command(definition):
        notes.extend(
            [
                "Note: " + CONDITION_HTS_NOTE,
                "",
            ]
        )
    if _is_foreground_stream_command(definition):
        notes.extend(
            [
                "Note: foreground stream commands support repeated `--code`, comma "
                "`--codes`, `--count`, `--duration`, `--watch`, `--check`, "
                "`--named`, and `--output` (write events to a JSONL file). Prefer "
                "`--count`/`--duration` for bounded stream runs.",
                "",
                "Note: streams run in the foreground and there is no built-in job "
                "manager. For unattended long-running capture, use `--watch "
                "--output <file>` and background the process with OS tools "
                "(`nohup`/`tmux`/`systemd --user` on Linux/macOS, `Start-Process` "
                "or 작업 스케줄러 on Windows).",
                "",
            ]
        )
    if definition.command_path == "kiwoomcli domestic stocks watchlist-info":
        notes.extend(
            [
                "Note: " + WATCHLIST_CODES_NOTE,
                "",
            ]
        )
    if definition.command_path == "kiwoomcli domestic stocks credit-loanable-check":
        notes.extend(
            [
                "Note: " + CREDIT_LOANABLE_NOTE,
                "",
            ]
        )
    if "gold" in definition.command_path:
        notes.extend(
            [
                "Note: " + GOLD_CODE_NOTE,
                "",
            ]
        )
    if definition.cli_group == "elws":
        notes.extend(
            [
                "Note: " + ELW_SAMPLE_NOTE,
                "",
            ]
        )
    if _is_account_state_dependent_command(definition):
        notes.extend(
            [
                "Note: " + ACCOUNT_EMPTY_NOTE,
                "",
            ]
        )
    if _is_program_trading_command(definition):
        notes.extend(
            [
                "Note: " + PROGRAM_EMPTY_NOTE,
                "",
            ]
        )
    return notes



def _is_foreground_stream_command(definition: CommandDefinition) -> bool:
    return definition.cli_group == "streams" and not definition.cli_command.startswith("conditions-")

def _is_condition_command(definition: CommandDefinition) -> bool:
    return definition.command_path.startswith("kiwoomcli domestic streams conditions-")


def _is_condition_subscribe_command(definition: CommandDefinition) -> bool:
    return definition.command_path == "kiwoomcli domestic streams conditions-subscribe"


def _is_program_trading_command(definition: CommandDefinition) -> bool:
    return definition.command_path in {
        "kiwoomcli domestic stocks program-net-top",
        "kiwoomcli domestic quotes program-time",
        "kiwoomcli domestic quotes program-daily",
    }


def _is_account_state_dependent_command(definition: CommandDefinition) -> bool:
    return definition.command_path in ACCOUNT_STATE_DEPENDENT_COMMANDS


def _common_options(arguments: list[ArgumentDefinition]) -> list[tuple[str, int]]:
    commands_by_option: dict[str, set[str]] = defaultdict(set)
    for argument in arguments:
        if argument.option:
            commands_by_option[argument.option].add(argument.command_path)
    return sorted(
        ((option, len(commands)) for option, commands in commands_by_option.items()),
        key=lambda item: (-item[1], item[0]),
    )[:20]


def _format_values(values: tuple[str, ...]) -> str:
    if not values:
        return ""
    return ", ".join(f"`{value}`" for value in values)


def _format_value(value: str) -> str:
    if not value:
        return ""
    return f"`{value}`"


def _title(group: str) -> str:
    return group.replace("-", " ").title()


def write_references() -> None:
    references = render_all_references()
    for path, content in references.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=(
            "all",
            "skill",
            "setup",
            "output",
            "glossary",
            "implemented-commands",
            "command-options",
            "group",
        ),
        default="implemented-commands",
    )
    parser.add_argument("--group", help="Group name for --target group")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    if args.write:
        write_references()
        return 0

    definitions = load_command_definitions()
    arguments = load_argument_definitions()
    if args.target == "all":
        for path, content in render_all_references(definitions, arguments).items():
            print(f"# {path.relative_to(ROOT)}")
            print(content, end="")
        return 0
    if args.target == "skill":
        print(render_skill(definitions), end="")
        return 0
    if args.target == "setup":
        print(render_setup_reference(definitions), end="")
        return 0
    if args.target == "output":
        print(render_output_reference(), end="")
        return 0
    if args.target == "glossary":
        print(render_glossary_reference(arguments), end="")
        return 0
    if args.target == "command-options":
        print(render_command_options(definitions, arguments), end="")
        return 0
    if args.target == "group":
        if not args.group:
            parser.error("--group is required with --target group")
        print(render_group_reference(args.group, definitions, arguments), end="")
        return 0
    print(render_implemented_commands(definitions), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
