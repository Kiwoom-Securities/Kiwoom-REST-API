# Kiwoom CLI Command System

This document is the canonical command-system guide for the installed
customer-facing command:

```sh
kiwoom
```

It defines the command tree, naming rules, safety posture, and documentation
roles used when changing the CLI. It is not a runtime source of truth. Runtime
behavior must still come from `kiwoom_cli/` code, `kiwoom_api_spec.json`, and the
editable mapping tables under `kiwoom_cli/maps/`.

Detailed parameter-naming evidence is kept in
`kiwoom_cli/docs/parameter-naming-audit.md`. That file is evidence, not policy.
If it differs from this document, this document wins.

## 1. Current Verdict

The repository already has many CLI documents, but they do not form one clean
command-system document:

| Document | Role | Boundary |
| --- | --- | --- |
| `kiwoom_cli/README.md` | User-facing command inventory and usage notes. | Too broad for design decisions; mixes usage notes, full command list, rules, and current caveats. |
| `kiwoom_cli/docs/feature-matrix.md` | Status matrix by resource group and command. | Status reference only; design rules stay here. |
| `kiwoom_cli/docs/command-contracts.md` | Command-by-command contract reference. | Exhaustive reference only; top-level policy stays here. |
| `kiwoom_cli/docs/api-coverage.md` | API inventory and coverage accounting. | Coverage evidence only; taxonomy policy stays here. |
| `kiwoom_cli/docs/parameter-naming-audit.md` | Argument naming audit and rename candidates. | Argument-specific audit artifact; accepted rules are copied here. |
| `kiwoom_cli/docs/implementation-status.md` | Current implementation evidence. | Status and verification evidence only; design rules stay here. |
| `.agents/skills/kiwoom/kiwoom/**` | Generated agent reference. | Generated output; should follow maps and command policy, not drive them. |

Therefore CLI reform should use this document as the top-level command-system
guide, and use the other documents as supporting references.

## 2. Source Of Truth

Implementation must not depend on prose docs. The authoritative files are:

| Concern | Source |
| --- | --- |
| API existence, method, path, request/response fields | `kiwoom_api_spec.json` |
| API inventory cross-check | `api_list.csv` |
| CLI command path, lifecycle status, coverage status, safety policy | `kiwoom_cli/maps/api_commands.csv` |
| CLI option to Kiwoom request-field mapping | `kiwoom_cli/maps/arguments.csv` |
| Positional shorthand policy | `kiwoom_cli/maps/positional_arguments.csv` |
| Order price validation | `kiwoom_cli/maps/order_price_policies.csv` |
| Order confirmation text and labels | `kiwoom_cli/maps/order_confirmation_*.csv` |
| User docs and agent references | Generated or checked from maps plus spec |

Design rule: if behavior can be described in a mapping table, put it in a
mapping table instead of hardcoding it in a parser, formatter, or document.

## 3. User Flow

The primary human and agent flow is:

```sh
kiwoom spec search "<term>"
kiwoom <group> <command> -h
kiwoom <group> <command> [options]
```

`kiwoom spec search` is the raw OpenAPI discovery tool. It should help users find
the curated command and then point them to command help. It should not be
replaced by a second `find` command.

Command help is the executable contract for a single command. New JSON metadata
commands such as `commands --json` or `help --json` are not part of the first
reform scope. JSON remains a data output format through the existing output
format option.

## 4. Command Tree

The CLI uses plural resource groups plus task-oriented subcommands:

```text
kiwoom <group> <command> [options]
```

Raw API IDs are traceable through maps and docs, but they are not the primary
user-facing command surface.

| Group | Role | Runtime position |
| --- | --- | --- |
| `auth` | Credential, profile, token administration. | Implemented. |
| `spec` | Local API discovery and raw spec inspection. | Implemented. |
| `stocks` | Domestic stock identity, broker, fill, investor, program, credit-loanable, and screener-style APIs. | Implemented for domestic rows; overseas rows remain planned. |
| `quotes` | Current price, quote, investor, broker, program, and gold quote reads. | Implemented for domestic/gold rows; overseas rows remain planned. |
| `orderbooks` | Stock and gold order book views. | Implemented for current mapped domestic/gold rows. |
| `candles` | Stock, sector, and gold chart/candle data. | Implemented for domestic/gold rows; overseas rows remain planned. |
| `rankings` | Domestic ranking and screener-style APIs. | Implemented for domestic rows; overseas rows remain planned. |
| `sectors` | Domestic sector APIs. | Implemented for domestic rows; overseas rows remain planned. |
| `etfs` | Domestic ETF APIs. | Implemented. |
| `elws` | Domestic ELW APIs. | Implemented. |
| `investors` | Institution/foreign investor flow APIs. | Implemented. |
| `short-selling` | Short-selling trend APIs. | Implemented. |
| `securities-lending` | Securities lending APIs. | Implemented. |
| `themes` | Theme group and component APIs. | Implemented. |
| `accounts` | Account, cash, asset, balance, PnL, settlement, and gold-account reads. | Guarded domestic reads implemented; overseas rows remain planned. |
| `orders` | Domestic order inquiry plus stock, credit, and gold order writes. | Guarded domestic commands implemented; overseas rows remain planned/preview-only. |
| `streams` | WebSocket realtime subscriptions and condition search (foreground; `--output` + OS backgrounding for long runs). | Implemented. |
| `investment-info` | Overseas research/dividend/investment information APIs. | Planned until overseas runtime verification. |
| `overseas ...` | Overseas public/account/order families. | Mapped for coverage, not runtime-exposed until verified. |
| `overseas-review` | Overseas miscellaneous APIs with unclear UX or write-like impact. | Review/preview-only. |

Command renames are not the first reform target. Keep the existing command tree
stable unless a command name itself blocks clear usage or safety. Argument names
are the first cleanup surface.

## 5. Argument Naming Rules

CLI option names follow user intent and domain meaning, not raw Kiwoom request
field names.

Rules:

- Use `--code` for the ordinary target code of the command: stock, sector, theme,
  ETF, ELW issue, gold item, or similar command target.
- Use qualified code names when `--code` would hide a distinct role:
  `--underlying-code`, `--issuer-code`, `--lp-code`, `--broker-code`,
  `--market-code`, `--sector-code`, `--index-code`.
- Use `--date` for a single 기준/조회 일자 and `--from` / `--to` for periods.
- Use `--side` for buy/sell/net-buy/net-sell direction.
- Use `--sort` only for the criterion used to rank or order output.
- Use `--order` for normal/reverse traversal when it is not a ranking criterion.
- Use `--fill-status` for open/filled/all order-state filters.
- Use `--*-basis` for 조회 기준, 금액/수량 기준, 평가 기준, or similar basis
  choices.
- Use `--*-type` or `--*-kind` only when the domain noun is explicit enough:
  `--right-type`, `--asset-kind`, `--order-type`.
- Use `--include-* yes|no` for inclusion/exclusion flags from the user's point
  of view. Do not expose skip/exclude-oriented raw fields directly.
- Use `--price` only for an actual order price or clear price input. Use
  `--price-condition` for price filters.
- Use `--amount-condition`, `--volume-condition`, and `--stock-condition` for
  high-cardinality condition code filters, and supply choices/value maps in
  `arguments.csv` when possible.

Do not mechanically map every Kiwoom `*_tp` field to `--type`. `*_tp` often
means "구분", but the user-facing meaning differs by command.

No legacy command surfaces are allowed. When an option is renamed, replace the
old option instead of keeping a compatibility alias.
Argparse abbreviation is disabled for the installed CLI, so removed options are
not accepted as prefixes of the new option names.

## 6. Applied Argument Reform Scope

Argument reform is mapping-table driven and limited to confusing option names
that already have clear replacements.

Applied first-stage replacements:

| Current | Replacement | Reason |
| --- | --- | --- |
| ELW `--issuer` | `--issuer-code` | It is a 발행사 code and should follow qualified code naming. |
| ELW `--lp` | `--lp-code` | It is an LP code and should follow qualified code naming. |
| ELW `--asset` for `bsis_aset_cd` | `--underlying-code` | It is a 기초자산 code, not an asset kind. |
| ELW `--right` | `--right-type` | It is 권리구분. |
| ELW `--ended include|exclude` | `--include-ended yes|no` | User intent is whether ended ELWs are included. |
| `accounts cash --query` | `--cash-basis` | It is 예수금 조회 기준, not a search query. |
| account asset/valuation `--delisted all|exclude` | `--include-delisted yes|no` | User intent is inclusion of delisted stocks. |
| account/gold order-fill `--asset` | `--asset-kind` | It means stock/bond kind and conflicts with ELW underlying asset usage. |

Applied second-stage replacements:

| Current | Replacement | Reason |
| --- | --- | --- |
| account/gold `--sort order|reverse` for `qry_tp` traversal | `--order order|reverse` | This is traversal order, not a ranking criterion. |
| account/gold `--sort open|filled` for `qry_tp` status filters | `--fill-status open|filled` | This is an order fill-state filter. |
| `accounts order-fill-status --scope all|filled` | `--fill-status all|filled` | This is a fill-state filter. |
| `orders list-open/list-fills --scope all|stock` | `--stock-scope all|stock` | This chooses all stocks versus one stock. |
| `securities-lending trend --scope all` | fixed internal `all_tp=1` | The only supported value is `all`, so it is not useful CLI surface. |
| `--credit` for `crd_cnd` | `--credit-condition` | This is a credit condition filter. |
| `--credit` for `crd_tp` | `--credit-type` | This is a credit type selector. |
| ranking `--price` for `pric_cnd` | `--price-condition` | This is a price filter, not an order/input price. |

Condition choice-map completion has been applied for the current
`--stock-condition`, `--volume-condition`, `--price-condition`, and
`--amount-condition` rows in `arguments.csv`. Future work in this area should
focus on checking value-map accuracy against the upstream spec and keeping
generated docs from falling back to vague `<value>` placeholders.

## 7. Output And Help

The current CLI output option is `--format`, not `--output`.

Current domain command formats include:

```text
auto, json, jsonl, pretty, raw, yaml
```

Spec commands use their own smaller format set. Do not rename `--format` as part
of the first argument cleanup unless the whole output contract is intentionally
changed.

For machine-readable output, stdout should contain only the selected data format.
Diagnostics, warnings, and safety notes should go to stderr when they are not
part of the chosen output payload.

Command help should be good enough for both humans and agents. The target shape
is:

```text
Usage
Summary / description
Options with required/default/choices
Behavior and safety notes
Examples
OpenAPI mapping or API ID trace
```

This does not require a separate JSON help interface.

## 8. Safety Policy

Safety is part of the command contract and must be explicit in
`api_commands.csv`.

| Safety posture | Rule |
| --- | --- |
| `read` | Ordinary read/query command. |
| `account_read` | Account-sensitive read; output must apply the shared redaction policy. |
| `order_write` | Side-effecting domestic order command; actual submission requires `--confirm`. |
| `preview-only` | Request generation/validation only; no real write submission. |
| `review_required` | Do not runtime-expose until UX and safety policy are reviewed. |

Domestic order write commands must validate the request before deciding whether
to submit. Without `--confirm`, they show 미전송 주문 확인 output and must not call
the real order endpoint. With `--confirm`, they may submit through the shared
runtime client when credentials and policy allow it.

Do not introduce `--yes` or `--dry-run` for order safety unless the order policy
is deliberately redesigned. The existing safety switch is `--confirm`.

## 9. Change Process

Use this process for CLI reform:

1. Decide whether the change is command-tree, argument-name, output, help, or
   safety policy work.
2. Update the relevant mapping table first when the behavior is data-driven.
3. Update parser/runtime code only when maps cannot express the behavior.
4. Regenerate or update user docs and agent references from maps/spec.
5. Run static validation and drift checks.
6. Run real Kiwoom verification only in a credentialed safe environment; report
   blocked/not-run if credentials or safety constraints prevent it.

Minimum static checks for command-system changes:

```sh
.venv/bin/python -m kiwoom_cli.validate_maps
.venv/bin/python -m kiwoom_cli.audit_implementation
env PYTHONPYCACHEPREFIX=.pycache-check .venv/bin/python -m compileall -q kiwoom kiwoom_cli Examples
git diff --check
```

Do not replace real behavior checks with mocks, fake clients, monkeypatching,
recorded responses, or simulated Kiwoom payloads.
