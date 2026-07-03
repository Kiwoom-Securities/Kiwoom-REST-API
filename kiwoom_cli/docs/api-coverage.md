# API Coverage Analysis

This document answers a specific coverage question: whether the current
high-level CLI resource plan covers the full local Kiwoom OpenAPI inventory.

## Source Counts

Current local evidence:

| Source | Count | Meaning |
| --- | ---: | --- |
| `kiwoom_api_spec.json` | 352 | Parsed API specs. This is the authoritative API count for CLI coverage. |
| `api_list.csv` | 352 real API rows | One row per API after excluding the CSV header. |
| `utils/generation_report.json` `written_files` | 372 | Generated example files, not API count. Some APIs produce more than one runnable file/name variant. |

Conclusion: the CLI coverage target is **352 APIs**, not 372 APIs. If a future
spec refresh changes `total_specs`, this document must be regenerated.

## Current Coverage Model

The internal CLI plan covers the full local API inventory through
`kiwoom_cli/maps/api_commands.csv`. Every one of the 352 API IDs appears exactly
once in the map. Coverage is tracked with two separate fields:

- `status`: implementation lifecycle (`implemented`, `planned`, `review`,
  `blocked`, `unsupported`).
- `coverage_status`: user exposure and safety posture (`public`, `guarded`,
  `preview-only`, `planned`).

Current coverage status counts:

| Coverage Status | Count | Meaning |
| --- | ---: | --- |
| `public` | 241 | Ordinary read/query command surface. |
| `guarded` | 85 | Account or sensitive read surface plus --confirm-gated order writes, with redaction/safety policy. |
| `preview-only` | 21 | Request generation/validation only until write safety is implemented. |
| `planned` | 5 | Mapped for full coverage, but command UX or policy is not fixed yet. |
| **Total** | **352** | Full local OpenAPI inventory. |

## Full API Family Map

The 352 local APIs classify into these CLI resource families:

| CLI Resource Family | API Count | Source Categories |
| --- | ---: | --- |
| `accounts` | 71 | 해외주식 > 계좌 (38), 국내주식 > 계좌 (33) |
| `stocks` | 54 | 국내주식 > 종목정보 (31), 해외주식 > 종목정보 (23) |
| `rankings` | 44 | 국내주식 > 순위정보 (23), 해외주식 > 순위정보 (21) |
| `candles` | 36 | 국내주식 > 차트 (21), 해외주식 > 차트 (15) |
| `quotes` | 30 | 국내주식 > 시세 (25), 해외주식 > 시세 (5) |
| `streams` | 23 | 국내주식 > 실시간시세 (19), 국내주식 > 조건검색 websocket APIs (4) |
| `orders` | 22 | 해외주식 > 주문 (10), 국내주식 > 주문 (8), 국내주식 > 신용주문 (4) |
| `overseas-review` | 16 | 해외주식 > 기타 (16). Covered in maps with `planned` or `preview-only` coverage status. |
| `investment-info` | 12 | 해외주식 > 투자정보 (12) |
| `elws` | 11 | 국내주식 > ELW (11) |
| `sectors` | 11 | 국내주식 > 업종 (6), 해외주식 > 업종 (5) |
| `etfs` | 9 | 국내주식 > ETF (9) |
| `investors` | 4 | 국내주식 > 기관/외국인 (4) |
| `securities-lending` | 4 | 국내주식 > 대차거래 (4) |
| `auth` | 2 | OAuth 인증 (2) |
| `themes` | 2 | 국내주식 > 테마 (2) |
| `short-selling` | 1 | 국내주식 > 공매도 (1) |

Total: 352 APIs.

## Coverage Verdict

The current command map covers **352 / 352** local APIs. The work remaining is
not API discovery; it is implementation and policy execution by
`coverage_status`.

| Area | API Count | Coverage Position |
| --- | ---: | --- |
| Public read/query APIs | 241 | Implement as ordinary resource commands. |
| Guarded account/sensitive APIs | 85 | Implement with redaction and account-output policy; domestic order writes submit only with --confirm. |
| Preview-only write-like APIs | 21 | Implement request construction/validation first; block actual submission until safety policy is active. |
| Planned UX/policy APIs | 5 | Keep mapped and documented; decide final command UX or policy before runtime exposure. |

This keeps raw API IDs out of the primary user surface while still making the
full inventory traceable and testable.

## Recommended Full-Coverage CLI Taxonomy

To cover all 352 APIs without exposing raw API-ID commands as the primary user
surface, use resource groups plus per-row coverage status:

```text
kiwoom auth ...
kiwoom spec search|show|groups|apis ...

kiwoom stocks ...
kiwoom quotes ...
kiwoom orderbooks ...
kiwoom candles ...
kiwoom rankings ...
kiwoom sectors ...
kiwoom etfs ...
kiwoom elws ...
kiwoom investors ...
kiwoom short-selling ...
kiwoom securities-lending ...
kiwoom themes ...

kiwoom accounts ...
kiwoom orders ...
kiwoom streams ...

# TODO(overseas): keep overseas command candidates mapped, but do not expose
# runtime parsers until overseas Kiwoom API execution is verified.
# kiwoom investment-info ...
# kiwoom overseas stocks|rankings|sectors|quotes|orderbooks|candles ...
# kiwoom overseas accounts|orders ...
```

`해외주식 > 기타` remains in the coverage maps as `overseas-review`; 조회성
rows can remain `planned`, while write-like rows start as `preview-only`.
All overseas groups remain in maps for 352-API coverage, but runtime commands
stay TODO until real credentialed overseas calls are verified.

Do not create all 352 commands manually. Use curated maps:

- One command group per resource family.
- One map row per supported API command.
- Shared executor, output, pagination, and safety machinery.
- Generated docs/references from the maps plus `kiwoom_api_spec.json`.

## Coverage Strategy By Phase

| Phase | Scope | Target Coverage |
| --- | --- | ---: |
| Phase 1 | Maps, validators, and docs | 352 mapped APIs, status/coverage validation |
| Phase 2 | Public read/query command runtime | 241 `public` APIs: implemented domestic/auth/streams rows plus overseas/investment-info TODO rows |
| Phase 3 | Guarded account/sensitive read runtime | 85 `guarded` APIs: implemented domestic/account-stream rows, domestic --confirm-gated order writes, plus overseas account TODO rows |
| Phase 4 | Order/write-like runtime | 21 `preview-only` APIs (request preview before submission) plus domestic order writes promoted to `guarded`/`order_write`; overseas rows remain mapped but not runtime-exposed |
| Phase 5 | Planned/review UX/policy resolution | 5 `planned` APIs plus `overseas-review` review rows; streams are already implemented |
| Phase 6 | Agent skill references generated from maps | Documentation coverage for all mapped APIs |

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
