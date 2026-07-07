# CLI Types

Types are part of the CLI contract. Argument parsing, command maps, generated
reference docs, validation, and examples should use the same names.

## Runtime Types

| Type | Format | Validation | Notes |
| --- | --- | --- | --- |
| `mode` | `demo` or `real` | Must be one of `VALID_MODES`. | Order write policy is decided separately from mode parsing. |
| `account_alias` | Profile alias string | Must exist when used. | Local profile alias, not a raw account number. |
| `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Must be one of the supported formats. | `json` is recommended for agents. |
| `positive_int` | integer string | Must be greater than 0. | Used by `--limit`, `--max-items`, counts. |

## Market/Data Types

| Type | Format | Validation | Notes |
| --- | --- | --- | --- |
| `stock_code` | Usually six digits, e.g. `005930` | Validate as six digits first. Any `A` prefix behavior must be API-specific and documented in maps. | Do not silently rewrite unless a map says to. |
| `exchange_stock_code` | Six digits with optional `_NX` or `_AL` suffix, e.g. `005930`, `039490_NX`, `039490_AL` | Validate as `^\d{6}(_NX\|_AL)?$`. | Used only when the Kiwoom spec says the request field accepts exchange-specific stock codes. |
| `date_yyyymmdd` | `YYYYMMDD` | Eight digits and a valid calendar date. | Used by chart/account date filters. |
| `time_hhmmss` | `HHMMSS` | Six digits and valid 24-hour time. | Use only when a mapped API requires it. |
| `market` | Kiwoom market/exchange selector | Choices must come from spec or command map. | Do not infer from stock code. |
| `sector_code` | Three digits, e.g. `001` | Validate as `^\d{3}$`. | Used by sector commands and mapped to `inds_cd`. |

## Stream Types

| Type | Format | Validation | Notes |
| --- | --- | --- | --- |
| `stream_action` | `subscribe` or `unsubscribe` | Mapped to Kiwoom `REG`/`REMOVE` in `arguments.csv`. | Used by realtime WebSocket commands. |
| `stream_group` | positive integer string | Defaults to `1` unless the command map says otherwise. | Kiwoom `grp_no`. |
| `stream_count` | positive integer string | Defaults to `1`; use `--watch` for an unbounded foreground stream. | Counts REAL data messages only; REG/REMOVE/SYSTEM control messages do not satisfy the limit. |

## Account Types

| Type | Format | Validation | Redaction |
| --- | --- | --- | --- |
| `account_number` | Kiwoom account number | Must come from API/auth runtime, not manual docs examples. | Redact by default. |
| `cash_amount` | decimal/integer string | Preserve as string unless formatting for display. | May be sensitive in account output. |
| `asset_value` | decimal/integer string | Preserve as string unless formatting for display. | May be sensitive in account output. |

## Order Types

| Type | Format | Validation | Notes |
| --- | --- | --- | --- |
| `order_side` | `buy` or `sell` | CLI-friendly side; mapped to Kiwoom request values by command map. | Write commands may fix this by subcommand. |
| `quantity` | positive integer string | Must be greater than 0. | Share/order quantity. |
| `cancel_quantity` | non-negative integer string | Must be zero or greater. | Cancel APIs may use `0` for full remaining quantity when the Kiwoom spec says so. |
| `price` | decimal/integer string | Must satisfy mapped API and order-type rules. | Do not coerce floats. |
| `order_type` | symbolic CLI value | Choices must come from `arguments.csv` and mapped Kiwoom API descriptions. | Example symbolic values may include `limit`, `market`, or Kiwoom-specific names after review. |
| `order_id` | order number/string | Required for modify/cancel. | Shown in output (not redacted) so it can be read from a buy/list response and reused; account numbers stay redacted. |
| `client_order_id` | user-supplied id if supported | Validate only when mapped API supports it. | Do not invent if spec has no field. |
| `credit_type` | mapped credit enum | Choices must come from credit-order spec. | Only for future credit order commands. |

## Safety Policies

| Policy | Network Write | Confirmation | Intended Use |
| --- | --- | --- | --- |
| `read` | No account side effect | None | Market data, spec search. |
| `account_read` | No trading side effect | None | Account, balance, order inquiry. |
| `order_preview` | No write submission | None | Build and show a request body. |
| `order_write` | Yes | `--confirm` | Domestic order writes submit only when explicitly confirmed; without `--confirm` they return a not-submitted preview. |
| `token_admin` | Token/credential state changes | Command-specific | Auth setup, refresh, revoke, clear. |

## Coverage Status Types

`coverage_status` is separate from implementation `status`. It describes the
intended user exposure and safety posture for each API row in
`kiwoom_cli/maps/api_commands.csv`.

| Coverage Status | Meaning | Typical Safety |
| --- | --- | --- |
| `public` | Ordinary read/query command surface. | `read` |
| `guarded` | Command surface exists, but output or account-sensitive data needs redaction/safety policy. | `account_read` |
| `preview-only` | Request generation/validation only; actual submission is blocked until safety policy is implemented. | `order_preview` or gated `order_write` |
| `planned` | API is mapped for full coverage, but final command UX or policy is not fixed yet. | `review_required` or future policy |

## Redaction Types

| Type | Redact By Default | Examples |
| --- | :---: | --- |
| `secret` | Yes | app key, secret key, token, authorization header. |
| `account_identifier` | Yes | account number. |
| `order_identifier` | Yes | order number, original order number. |
| `raw_payload` | Depends | Full API response in debug/raw modes. |
| `public_market_value` | No | stock code, price, candle rows. |

## Type Source Rules

- Required fields come from `kiwoom_api_spec.json` unless a command map marks a
  runtime source.
- Friendly option names come from `maps/arguments.csv`.
- Choices come from explicit maps or spec descriptions, not hidden Python logic.
- Redaction comes from `maps/output.csv` and safety policy.
- Docs must not define a type that the parser and maps do not recognize.
