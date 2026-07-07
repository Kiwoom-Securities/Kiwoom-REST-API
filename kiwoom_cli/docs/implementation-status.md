# Kiwoom CLI Implementation Status

This status document records current implementation evidence. Design principles
live in `kiwoom_cli/docs/command-system.md`; maps and local specs remain the
runtime source of truth.

## Current Baseline

| Item | Current Evidence | Status |
| --- | --- | --- |
| Total local API inventory | `kiwoom_cli.validate_maps` reports 207 mapped APIs and 207 spec APIs (국내주식 205 + OAuth 인증 2; 해외주식 is out of scope for this build). | Complete |
| Coverage taxonomy | `kiwoom_cli.validate_maps` checks that `api_commands.csv`, `maps/README.md`, `docs/api-coverage.md`, and this status document agree on `public` 160 and `guarded` 47. | Complete |
| CLI argument mappings | `arguments.csv` has 729 rows and every implemented non-auth command satisfies required body fields through explicit mappings. | Complete |
| Installed command | `pyproject.toml` and built wheel metadata expose `kiwoomcli = kiwoom_cli.main:main`. | Complete |
| Packaged resources | `kiwoom_cli.audit_wheel` verifies the latest wheel includes CLI modules, maps, docs, `kiwoom_api_spec.json`, and `api_list.csv`. | Complete |
| Agent reference generation | `.agents/skills/kiwoom/kiwoom` references are generated from current `api_commands.csv` and `arguments.csv`; `kiwoom_cli.audit_implementation` compares rendered output to checked files. | Complete |
| Project boundary audit | `kiwoom_cli.audit_implementation` verifies no broad `kiwoom/apis/` layer, no example-local auth helpers, no customer-facing `uv run kiwoom` invocation, shared executor/runtime facade usage for resource command modules, and no test-double/response-recording terms in implementation/test/example code. | Complete |
| Generated examples | `kiwoom_cli.audit_implementation` statically compiles every `Examples/**/*.py` file and verifies each generated example acquires runtime through the package facade (`get_auth`, `get_client`, or `get_ws_client`) without direct network/core runtime access. | Complete |
| Real Kiwoom calls | `kiwoom_cli.verify_real_calls` attempts the safe read-only demo check, auto-selects the current saved demo profile when available, and currently passes against `ka10001`; see Real-Call Evidence below. | Complete |

## Implementation Milestones

| Milestone | Current Status | Evidence |
| --- | --- | --- |
| Phase 1. 검증 기준선 고정 | Complete | `kiwoom_cli.validate_maps` checks API ID coverage, spec/list/map drift, required fields, status/coverage/safety combinations, argument mappings, and count tables. |
| Phase 2. CLI 공통 런타임 골격 | Complete | `registry.py`, `arguments.py`, `argument_maps.py`, `executor.py`, `output.py`, `safety.py`, and resource command modules are present and audited. |
| Phase 3. 첫 public read 명령 | Complete | `kiwoomcli domestic stocks info` is mapped to `ka10001`; parser/docs/contracts are audited; the safe demo real-call checker passed against `ka10001`. |
| Phase 4. public 조회군 확장 | Complete | 158 non-auth public read API rows are implemented: domestic `stocks`, `quotes`, `rankings`, `candles`, `sectors`, `investors`, `etfs`, and `elws` APIs are fully implemented, 금현물 quote/orderbook reads are implemented, and 21 public stream rows are implemented. All bundled `public` rows are implemented (해외주식 is out of scope for this build). |
| Phase 5. guarded 계좌/민감 조회 | Complete | 47 guarded rows are implemented: 28 domestic `accounts` reads, 5 guarded order inquiry rows, 2 guarded account/order streams, and 12 domestic order-write rows (stock/credit/gold), all with shared account-number redaction across CLI output formats (order numbers are shown so orders can be managed). |
| Phase 6. 주문/write-like 명령 | Complete | Domestic stock, credit, and gold `orders` write-like rows are promoted to `guarded`/`order_write`: without `--confirm` they show a 미전송 주문 확인 message and order summary and never call the order API, and with `--confirm` they submit to the real endpoint. |
| Phase 7. planned/review 정책 확정 | Complete | Domestic streams are implemented; every bundled row is mapped to an implemented command. |
| Phase 8. Agent reference 생성 | Complete | `.agents/skills/kiwoom/kiwoom` now contains generated `SKILL.md`, setup/output/glossary references, per-resource references for every implemented CLI group, implemented command inventory, and command option reference. `kiwoom_cli.audit_implementation` compares all generated reference files against current maps. |

## Implemented Command Counts

| Category | Count | Evidence |
| --- | ---: | --- |
| Implemented command audit total | 211 | `kiwoom_cli.audit_implementation` includes static spec commands plus mapped implemented commands. |
| Order write commands (--confirm-gated) | 12 | Stock, credit, and gold `orders buy/sell/modify/cancel` variants; 미전송 주문 확인 without `--confirm`, submit with `--confirm`; order-type price rules validated from `maps/order_price_policies.csv`. |
| Mapped argument rows | 729 | `kiwoom_cli.validate_maps` summary. |

## Verification Commands

Run these before claiming implementation progress:

```bash
.venv/bin/python -m kiwoom_cli.validate_maps
.venv/bin/python -m kiwoom_cli.audit_implementation
env PYTHONPYCACHEPREFIX=.pycache-check .venv/bin/python -m compileall -q kiwoom kiwoom_cli Examples
! rg -n "unittest\\.mock|MagicMock|\\bMock\\b|\\bpatch\\b|fake|stub|monkeypatch|cassette|replay" kiwoom kiwoom_cli Examples utils -g '!**/*.md' -g '!**/*.csv'
git diff --check
uv build
.venv/bin/python -m kiwoom_cli.audit_wheel
.venv/bin/python -m kiwoom_cli.verify_real_calls --mode demo || true
```

Real API verification must use credentials and safe read-only/demo calls. If
credentials are unavailable, rejected by Kiwoom, or otherwise unsafe to use,
record the result as blocked/not-run rather than using mocks or recorded
responses.

## Real-Call Evidence

Current environment evidence:

| Check | Command | API / endpoint | Result |
| --- | --- | --- | --- |
| Safe public read checker, demo mode | `.venv/bin/python -m kiwoom_cli.verify_real_calls --mode demo` | `ka10001`, `POST /api/dostk/stkinfo` | Passed with sanitized JSON evidence after selecting current profile `demo`: `status=passed`, `response_keys` include `return_code`, `return_msg`, `stk_cd`, `stk_nm`, `cur_prc`; `row_count=null`, `secret_values=not-recorded`. |
| Order write path is wired (no submission) | `kiwoomcli domestic orders buy --code 005930 --qty 1 --price 70000 --order-type limit --format json` (no `--confirm`) | `kt10000`, `POST /api/dostk/ordr` | Static, no network: without `--confirm` the command prints the unsubmitted order confirmation (`message` + `order`) and never calls the order API. Confirms no submission by default. |
| Order write real demo submission | `kiwoomcli domestic orders buy ... --confirm --profile demo` (국내), `--env-file .env.gold ... --confirm` (금현물) | `kt10000`/`kt50000`, `POST /api/dostk/ordr` | Blocked/not-run: with `--confirm` the command reaches the live Kiwoom endpoint (network path confirmed), but the stored `demo`/ambient credentials in this environment return `인증 실패 [8001]` for both order and safe-read calls, so a `return_code=0` submission could not be captured. Re-run with valid demo (모의투자) credentials; 금현물 needs its own demo account/`.env`. CLI output shows order numbers (`ord_no` etc.) so buy/list responses can feed modify/cancel flows; account numbers remain redacted. |

No account identifiers, tokens, secrets, or unsanitized payload values were produced.
