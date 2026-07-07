# API Coverage Analysis

This document answers a specific coverage question: whether the current
high-level CLI resource plan covers the local Kiwoom OpenAPI inventory that the
`kiwoomcli` CLI ships. Overseas (해외주식/미장) APIs are out of scope for this
build and are not bundled in the spec or the command maps.

## Source Counts

Current local evidence:

| Source | Count | Meaning |
| --- | ---: | --- |
| `kiwoom_api_spec.json` | 207 | Parsed API specs (국내주식 205 + OAuth 인증 2). This is the authoritative API count for CLI coverage. |
| `api_commands.csv` | 207 | One command-map row per API. |

Conclusion: the CLI coverage target is **207 APIs** (domestic + OAuth). If a
future spec refresh changes `total_specs`, this document must be regenerated.

## Current Coverage Model

The internal CLI plan covers the full bundled API inventory through
`kiwoom_cli/maps/api_commands.csv`. Every one of the 207 API IDs appears exactly
once in the map. Coverage is tracked with two separate fields:

- `status`: implementation lifecycle (`implemented`, `planned`, `review`,
  `blocked`, `unsupported`).
- `coverage_status`: user exposure and safety posture (`public`, `guarded`,
  `preview-only`, `planned`).

Current coverage status counts:

| Coverage Status | Count | Meaning |
| --- | ---: | --- |
| `public` | 160 | Ordinary read/query command surface. |
| `guarded` | 47 | Account or sensitive read surface plus --confirm-gated order writes, with redaction/safety policy. |
| **Total** | **207** | Full bundled OpenAPI inventory (all `implemented`). |

## Full API Family Map

The 207 local APIs classify into these CLI resource families:

| CLI Resource Family | API Count | Source Categories |
| --- | ---: | --- |
| `stocks` | 31 | 국내주식 > 종목정보 (31) |
| `accounts` | 28 | 국내주식 > 계좌 (28) |
| `quotes` | 23 | 국내주식 > 시세 (23) |
| `rankings` | 23 | 국내주식 > 순위정보 (23) |
| `streams` | 23 | 국내주식 > 실시간시세 (19), 국내주식 > 조건검색 (4) |
| `candles` | 21 | 국내주식 > 차트 (21) |
| `orders` | 17 | 국내주식 > 주문 (8), 국내주식 > 계좌 (5), 국내주식 > 신용주문 (4) |
| `elws` | 11 | 국내주식 > ELW (11) |
| `etfs` | 9 | 국내주식 > ETF (9) |
| `sectors` | 6 | 국내주식 > 업종 (6) |
| `investors` | 4 | 국내주식 > 기관/외국인 (4) |
| `securities-lending` | 4 | 국내주식 > 대차거래 (4) |
| `auth` | 2 | OAuth 인증 (2) |
| `orderbooks` | 2 | 국내주식 > 시세 (2) |
| `themes` | 2 | 국내주식 > 테마 (2) |
| `short-selling` | 1 | 국내주식 > 공매도 (1) |

Total: 207 APIs.

## Coverage Verdict

The current command map covers **207 / 207** bundled APIs, all `implemented`.
The remaining work is not API discovery; it is policy execution by
`coverage_status`.

| Area | API Count | Coverage Position |
| --- | ---: | --- |
| Public read/query APIs | 160 | Ordinary resource commands. |
| Guarded account/sensitive APIs | 47 | Redaction and account-output policy; domestic order writes submit only with --confirm. |

This keeps raw API IDs out of the primary user surface while still making the
full inventory traceable and testable.

## Recommended Full-Coverage CLI Taxonomy

To cover all 207 APIs without exposing raw API-ID commands as the primary user
surface, use resource groups plus per-row coverage status:

```text
kiwoomcli auth ...
kiwoomcli spec search|show|groups|apis ...

kiwoomcli domestic stocks ...
kiwoomcli domestic quotes ...
kiwoomcli domestic orderbooks ...
kiwoomcli domestic candles ...
kiwoomcli domestic rankings ...
kiwoomcli domestic sectors ...
kiwoomcli domestic etfs ...
kiwoomcli domestic elws ...
kiwoomcli domestic investors ...
kiwoomcli domestic short-selling ...
kiwoomcli domestic securities-lending ...
kiwoomcli domestic themes ...

kiwoomcli domestic accounts ...
kiwoomcli domestic orders ...
kiwoomcli domestic streams ...
```

Do not create all 207 commands manually. Use curated maps:

- One command group per resource family.
- One map row per supported API command.
- Shared executor, output, pagination, and safety machinery.
- Generated docs/references from the maps plus `kiwoom_api_spec.json`.

## Validation Requirements

Full API coverage is not proven by having a group name. It is proven only when:

- Every API ID appears in exactly one curated command-map row or is explicitly
  marked unsupported/blocked with a reason.
- Every command-map row validates against `kiwoom_api_spec.json`.
- Every required request field is satisfied by an argument, default, or runtime
  source.
- Every side-effecting API has an explicit safety policy.
- Generated docs list each command's type contract and match parser help.
- Real-call verification is attempted only where safe and credentialed; blocked
  real-call checks are reported as blocked, not replaced with mocks.
