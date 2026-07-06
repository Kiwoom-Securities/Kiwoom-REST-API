# Positional Argument Policy

This document manages positional shorthand candidates for the installed
`kiwoomcli` CLI. The canonical command form remains explicit option flags. A
positional form is only a shorthand when the target operand is obvious and the
risk of accidental execution is low.

Runtime source of truth must be a mapping table, not this prose document. The
current positional policy table is `kiwoom_cli/maps/positional_arguments.csv`;
validators keep this document and the table synchronized.

## Rules

- Canonical examples keep the full option form.
- Positional shorthand must map to exactly one existing option/destination.
- `allow` rows may be implemented.
- `candidate` rows are documented for future UX review but are not implemented
  until promoted to `allow`.
- `defer` rows are intentionally not implemented yet.
- Order/write-like commands stay `defer` unless a later safety review approves
  the exact positional order.
- Docs are not parsed by runtime code.

## Status Meaning

| Status | Meaning |
| --- | --- |
| `allow` | Approved for implementation as a positional shorthand. |
| `candidate` | Plausible shorthand, but not approved for implementation yet. |
| `defer` | Keep option-only for now because ambiguity or safety risk is material. |
| `reject` | Do not support positional shorthand. |

## Managed Positional Shorthands

| Full command | Canonical full form | Allowed positional form | Positional mapping | Status | Reason |
| --- | --- | --- | --- | --- | --- |
| `kiwoomcli setup` | `kiwoomcli setup --alias <alias> --mode <mode>` | `kiwoomcli setup <alias> --mode <mode>` | `1 -> --alias` | `allow` | setup/login target alias is the primary operand |
| `kiwoomcli auth login` | `kiwoomcli auth login --alias <alias> --mode <mode>` | `kiwoomcli auth login <alias> --mode <mode>` | `1 -> --alias` | `allow` | auth login target alias is the primary operand |
| `kiwoomcli auth status` | `kiwoomcli auth status --profile <alias>` | `kiwoomcli auth status <alias>` | `1 -> --profile` | `allow` | profile status naturally targets one alias |
| `kiwoomcli auth refresh` | `kiwoomcli auth refresh --profile <alias>` | `kiwoomcli auth refresh <alias>` | `1 -> --profile` | `allow` | profile refresh naturally targets one alias |
| `kiwoomcli auth revoke` | `kiwoomcli auth revoke --profile <alias>` | `kiwoomcli auth revoke <alias>` | `1 -> --profile` | `allow` | profile token revoke naturally targets one alias |
| `kiwoomcli auth clear` | `kiwoomcli auth clear --profile <alias> --all` | `kiwoomcli auth clear <alias> --all` | `1 -> --profile` | `allow` | profile credential cleanup naturally targets one alias |
| `kiwoomcli domestic stocks info` | `kiwoomcli domestic stocks info --code <code>` | `kiwoomcli domestic stocks info <code>` | `1 -> --code` | `candidate` | common single-stock lookup shorthand |
| `kiwoomcli domestic quotes price` | `kiwoomcli domestic quotes price --code <code>` | `kiwoomcli domestic quotes price <code>` | `1 -> --code` | `candidate` | common single-stock quote shorthand |
| `kiwoomcli domestic orderbooks list` | `kiwoomcli domestic orderbooks list --code <code>` | `kiwoomcli domestic orderbooks list <code>` | `1 -> --code` | `candidate` | common single-stock orderbook shorthand |
| `kiwoomcli domestic candles daily` | `kiwoomcli domestic candles daily --code <code>` | `kiwoomcli domestic candles daily <code>` | `1 -> --code` | `candidate` | common single-stock chart shorthand |
| `kiwoomcli domestic streams trades` | `kiwoomcli domestic streams trades --code <code>` | `kiwoomcli domestic streams trades <code>` | `1 -> --code` | `candidate` | common single-stock realtime shorthand |
| `kiwoomcli domestic streams conditions-search` | `kiwoomcli domestic streams conditions-search [--seq <seq>] --exchange <exchange>` | `defer` | `1 -> --seq` | `defer` | seq is optional because the command internally loads saved conditions with `CNSRLST` |
| `kiwoomcli domestic streams conditions-subscribe` | `kiwoomcli domestic streams conditions-subscribe [--seq <seq>] --exchange <exchange>` | `defer` | `1 -> --seq` | `defer` | seq is optional because the command internally loads saved conditions with `CNSRLST` |
| `kiwoomcli domestic streams conditions-unsubscribe` | `kiwoomcli domestic streams conditions-unsubscribe [--seq <seq>]` | `defer` | `1 -> --seq` | `defer` | one-shot clear is same-session only; positional shorthand would hide that constraint |
| `kiwoomcli domestic orders buy` | `kiwoomcli domestic orders buy --code <code> --qty <qty> --price <price> --order-type <type>` | `defer` | `1 -> --code` | `defer` | write-like order shorthand is deferred for safety and ambiguity |
| `kiwoomcli domestic orders sell` | `kiwoomcli domestic orders sell --code <code> --qty <qty> --price <price> --order-type <type>` | `defer` | `1 -> --code` | `defer` | write-like order shorthand is deferred for safety and ambiguity |
| `kiwoomcli domestic orders modify` | `kiwoomcli domestic orders modify --code <code> --order-id <order-id> --qty <qty> --price <price>` | `defer` | `1 -> --code`; `2 -> --order-id` | `defer` | modify shorthand is deferred because order-id qty price order can be confused |
| `kiwoomcli domestic orders cancel` | `kiwoomcli domestic orders cancel --code <code> --order-id <order-id> --qty <qty>` | `defer` | `1 -> --code`; `2 -> --order-id` | `defer` | cancel shorthand is deferred because order-id and quantity mistakes are high impact |

## Implementation Notes

- The first implementation batch should handle only `allow` rows.
- Auth/setup profile names should keep a single documented option form; avoid
  adding duplicate old/new command shapes.
- Resource command shorthands require parser/help/reference updates and map
  validation before promotion from `candidate` to `allow`.
- Order shorthand promotion requires a separate safety decision.
