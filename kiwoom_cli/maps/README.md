# Kiwoom CLI Maps

This folder contains editable, spec-driven mapping tables for the installed `kiwoomcli` CLI.

## Files

- `api_commands.csv`: one row per local Kiwoom API from `api_list.csv` / `kiwoom_api_spec.json`.
- `arguments.csv`: explicit CLI option to Kiwoom request-field mappings for implemented commands.
- `positional_arguments.csv`: explicit positional shorthand policy by command path.
- `order_price_policies.csv`: explicit order-type to price/condition-price validation policy for implemented order-write commands.
- `order_confirmation_commands.csv`, `order_confirmation_fields.csv`, and `order_value_labels.csv`: editable 미전송 주문 확인 messages, fields, and labels for domestic order-write commands.

The table is intentionally explicit. Full CLI coverage means every API ID appears exactly once with an implemented, planned, review, blocked, or unsupported implementation status and a separate coverage status.

## Current Counts

| CLI Group | Implementation Status | Coverage Status | Count |
| --- | --- | --- | ---: |
| `accounts` | `implemented` | `guarded` | 28 |
| `auth` | `implemented` | `public` | 2 |
| `candles` | `implemented` | `public` | 21 |
| `elws` | `implemented` | `public` | 11 |
| `etfs` | `implemented` | `public` | 9 |
| `investors` | `implemented` | `public` | 4 |
| `orderbooks` | `implemented` | `public` | 2 |
| `orders` | `implemented` | `guarded` | 17 |
| `quotes` | `implemented` | `public` | 23 |
| `rankings` | `implemented` | `public` | 23 |
| `sectors` | `implemented` | `public` | 6 |
| `securities-lending` | `implemented` | `public` | 4 |
| `short-selling` | `implemented` | `public` | 1 |
| `stocks` | `implemented` | `public` | 31 |
| `streams` | `implemented` | `guarded` | 2 |
| `streams` | `implemented` | `public` | 21 |
| `themes` | `implemented` | `public` | 2 |

## Implementation Status Meaning

- `implemented`: parser/runtime behavior exists now.
- `planned`: part of the intended CLI implementation backlog.
- `review`: covered in maps/docs, but command semantics or safety policy still need review.
- `blocked`: intentionally withheld until a specific blocker is removed.
- `unsupported`: no CLI support intended unless policy changes.

## Coverage Status Meaning

- `public`: ordinary read/query command surface.
- `guarded`: command is exposed, but output/redaction/account-safety policy applies.
- `preview-only`: request generation/validation is allowed first; real write submission is blocked until explicit safety policy is implemented.
- `planned`: mapped for full coverage, but command UX or policy is not fixed yet.

## Column Notes

- `cli_group` and `cli_command` are user-facing command taxonomy candidates.
- `command_path` is the public invocation prefix when a command path is approved, not a raw API-ID command.
- `status` tracks implementation lifecycle; `coverage_status` tracks exposure/safety posture.
- `required_body_fields` and `required_header_fields` come from `kiwoom_api_spec.json`.
- Implemented command request bodies are assembled from `arguments.csv`, not hidden field rewrites.
- Order price validation is assembled from `order_price_policies.csv`; e.g. `limit` requires `--price`, while `market` forbids it.
- 미전송 주문 확인 output is assembled from `order_confirmation_*.csv`; without `--confirm` the order API is never called.
- `canonical_code_option` records the CLI naming rule: prefer `--code` for instrument/sector/theme/symbol-like values and map it internally to Kiwoom field names.

## Validation Scope

`.venv/bin/python -m kiwoom_cli.validate_maps` verifies that `api_commands.csv`
is in sync with `api_list.csv`, `kiwoom_api_spec.json`, and `arguments.csv`: API
IDs, API names, categories, method/path, required body fields, required header
fields, implementation status, coverage status, safety policy, implemented
command argument coverage, argument Kiwoom fields, positional shorthand policy,
order price policies, and documented count tables are checked directly from the
source files.
Count-table drift is checked across `maps/README.md`,
`docs/api-coverage.md`, and `docs/implementation-status.md`.

`.venv/bin/python -m kiwoom_cli.audit_implementation` verifies that implemented
map rows exist in the argparse command surface, appear in the user-facing docs,
and that implemented `preview-only`/`order_write` commands do not submit
unless `--confirm` is supplied for domestic order writes. Domestic order writes
show 미전송 주문 확인 output without `--confirm` and never call the order API. It also checks the project boundary rules that
matter to the CLI surface: no broad `kiwoom/apis/` wrapper layer, no
example-local auth helpers, no customer-facing `uv run kiwoom` invocation, no
test-double/response-recording terms in implementation/test/example code, and
resource command modules using the shared executor/runtime facade instead of
direct network access. Generated `Examples/` files are also compiled
statically and checked for package-facade runtime acquisition
(`get_auth`, `get_client`, or `get_ws_client`) rather than direct network/core
runtime access.

`.venv/bin/python -m kiwoom_cli.verify_real_calls --mode demo` is the
credentialed-environment smoke checker for sanitized safe-read evidence. Without
credentials it reports a blocked status before network submission instead of
using any substitute response.
