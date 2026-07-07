# Kiwoom CLI

This directory owns the installed customer-facing command:

```sh
kiwoom
```

Do not document `uv run kiwoom` as the customer-facing invocation.

The CLI is the natural operation surface for humans and AI agents that need to
inspect Kiwoom OpenAPI data, manage auth state, and eventually perform guarded
trading actions. Runtime/auth logic stays in `kiwoom/core/`; CLI use cases stay
under `kiwoom_cli/`; generated examples stay under `Examples/`; maintenance
generation utilities stay under `utils/`.

## Quickstart

The everyday flow for both humans and AI agents is discovery first, then a
single command. The exhaustive per-command reference lives in
[docs/command-contracts.md](docs/command-contracts.md); use `-h` on any command
for its live, mapped contract.

```sh
1. kiwoomcli setup                         # onboard: alias, demo/real, keys, verify
2. kiwoomcli spec search "<term>"          # find the API/command you need
3. kiwoom <group> <command> -h          # Summary/Behavior/Examples/OpenAPI map
4. kiwoom <group> <command> --format json
5. kiwoomcli domestic orders buy ...                # writes need --confirm; otherwise preview only
```

The full command inventory below is the audited reference surface. Day-to-day
use should go through `spec search` and `-h` rather than scanning the inventory.

## Usage Notes

- `kiwoomcli setup` is the onboarding bootstrap: it first runs an environment
  pre-flight (OS credential-store availability plus a PATH ambiguity warning),
  then creates an account alias, chooses demo/real, stores App Key / Secret,
  validates with a safe read-only call (re-prompting on validation failure in a
  terminal), sets the current profile, and prints a readiness summary. In a
  non-interactive shell it fails with guidance instead of hanging (pass
  `--mode`). `kiwoomcli doctor` is the read-only state
  diagnostic: it explains which auth context is selected now (priority of
  `--profile`/`KIWOOM_PROFILE` > `--mode`/`KIWOOM_MODE` > current profile),
  shows per-profile credential/token/refresh health, and recommends fixes (for
  example, it warns when `KIWOOM_MODE` overrides the current profile).
- `kiwoomcli auth clear` removes only the secret material for a target: by default
  the local token cache, and with `--all` also the OS credential-store App
  Key/Secret. It does NOT unregister the account, so the alias still appears in
  `kiwoomcli auth list` with `credentials=아니오`. To fully unregister an account,
  use `kiwoomcli auth remove <alias>`, which deletes the profile entry, its token
  cache, and its stored credentials in one step (and clears the current-profile
  selection if that alias was current).
- `kiwoomcli auth export [alias] [--dir FOLDER] [--yes]` writes the stored App
  Key/Secret to a `.env` file (mode-specific keys like `APP_KEY`/`APP_SECRET`);
  it never prints the secrets. Exporting plaintext credentials is guarded: it
  asks for confirmation (`--yes` skips; a non-interactive shell requires
  `--yes`), writes the file with `0600` permissions, and auto-registers the
  file in the enclosing repo's `.gitignore` to prevent accidental commits.
  Without `--dir` it saves to the current folder and says so before writing.
- If `kiwoomcli auth list` or `kiwoomcli doctor` shows a saved alias with
  `credentials=아니오`, an expired/non-reusable token, and `지금 호출=불가`, the
  alias was not necessarily deleted; the OS credential-store App Key/Secret is
  missing or unreadable. Re-login the same alias to restore credentials and a
  fresh token, for example:
  `kiwoomcli auth login --alias '실전계좌' --mode real`, then verify with
  `kiwoomcli auth status --profile '실전계좌'`.
- `--profile NAME` uses a stored account alias (App Key / Secret in the OS
  credential store). `--mode demo|real` does not use a stored alias; mode-only
  execution needs `APP_KEY` / `APP_SECRET` environment variables (or mode-level
  credentials). A missing-credentials error therefore differs by entry path,
  and the message names the matching fix.
- `kiwoomcli domestic stocks watchlist-info --codes` expects a pipe-delimited Kiwoom code
  list, for example `--codes '005930|000660'`. Comma-delimited input is not the
  documented API shape.
- `kiwoomcli domestic stocks credit-loanable-check` preserves the Kiwoom `crd_alow_yn`
  field and adds `loanable`: `true`, `false`, or `null` when the response text
  cannot be classified.
- Gold spot examples use `M04020000` (`금 99.99_1kg`) as the sample instrument
  code. Gold development-endpoint credentials, when needed, must remain outside
  command output and committed files.
- ELW sample parameters should come from current/proven ELW evidence. ELW
  instruments expire, so a previously valid `--code` can later return an empty
  list even when the command mapping is correct.
- Account/order history commands are account/date-state dependent. Realized PnL,
  return-rate, fill-history, and open-order queries can return an empty list
  when the selected account and date have no matching holdings, fills, or open
  orders. Treat this as an account-state-dependent zero-row result, not as a
  synthetic success proof or an automatic command mapping failure.
- Program-trading aggregate commands are market-time and condition dependent.
  Empty lists with `return_code=0` should be recorded as zero rows and not
  over-counted as investor-useful data evidence. For `--market-code`, use the
  program-trading market code family from the samplecode, such as `P00101` for
  KRX KOSPI or `P10102` for KRX KOSDAQ; ordinary market selectors like `000`
  are weak evidence for these APIs.

## Current Commands

Implemented:

```sh
kiwoomcli setup [NAME] [--alias NAME] [--mode demo|real]
kiwoomcli doctor
kiwoomcli auth login [NAME] [--alias NAME] [--mode demo|real]
kiwoomcli auth list
kiwoomcli auth switch <alias>
kiwoomcli auth status [NAME] [--profile NAME | --mode demo|real]
kiwoomcli auth refresh [NAME] [--profile NAME | --mode demo|real]
kiwoomcli auth revoke [NAME] [--profile NAME | --mode demo|real]
kiwoomcli auth clear [NAME] [--profile NAME | --mode demo|real] [--all]
kiwoomcli auth remove <alias>
kiwoomcli spec search <query> [--limit N]
kiwoomcli spec show <api-id> [--format pretty|json|yaml]
kiwoomcli spec groups [--format pretty|json|yaml]
kiwoomcli spec apis [--group <text>] [--limit N] [--format pretty|json|yaml]
kiwoomcli domestic stocks info --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks trend --code <code> --date <yyyymmdd> --kind financing|loan [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks realtime-rank --window 1m|10m|1h|today|30s [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks brokers --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks fills --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks daily-trades --code <code> --from <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks new-high-low --market all|kospi|kosdaq --kind new-high|new-low --price-basis high-low|close --stock-condition <value> --volume-condition <value> --credit-condition <value> --include-limit yes|no --period-days 5|10|20|60|250 --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks limit-move --market all|kospi|kosdaq --direction upper|rise|flat|lower|fall|prev-upper|prev-lower --sort code|count|change-rate --stock-condition <value> --volume-condition <value> --credit-condition <value> --price-condition <value> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks high-low-near --kind high|low --near-rate <value> --market all|kospi|kosdaq --volume-condition <value> --stock-condition <value> --credit-condition <value> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks price-spike --market all|kospi|kosdaq|kospi200 --direction rise|fall --time-unit minute|day --time <n> --volume-condition <value> --stock-condition <value> --credit-condition <value> --price-condition <value> --include-limit yes|no --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks volume-renewal --market all|kospi|kosdaq --period-days 5|10|20|60|250 --volume-condition <value> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks volume-zone --market all|kospi|kosdaq --concentration-rate <value> --include-current yes|no --zone-count <n> --period-days 50|100|150|200|250|300 --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks valuation-rank --kind low-pbr|high-pbr|low-per|high-per|low-roe|high-roe --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks open-change --basis open|high|low|base --volume-condition <value> --market all|kospi|kosdaq --include-limit yes|no --stock-condition <value> --credit-condition <value> --amount-condition <value> --direction top|bottom --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks broker-volume-zone --code <code> --from <yyyymmdd> --to <yyyymmdd> --date-mode period|start-end --position today|previous --period-days 5|10|20|40|60|120 --sort close|date --broker-code <value> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks broker-instant-volume --broker-code <value> [--code <code>] --market all|kospi|kosdaq|stock --quantity-condition <value> --price-condition <value> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks vi-triggered --market all|kospi|kosdaq --session all|regular|after-hours [--code <code>] --vi-type all|static|dynamic|both --skip-stocks <value> --use-volume yes|no --min-volume <value> --max-volume <value> --use-amount yes|no --min-amount <value> --max-amount <value> --direction all|rise|fall --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks today-previous-fills --code <code> --day today|previous [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks investor-daily --from <yyyymmdd> --to <yyyymmdd> --side net-sell|net-buy --market kospi|kosdaq --investor individual|foreign|financial-investment|investment-trust|private-fund|other-financial|bank|insurance|pension|state|other-corporate|institution --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks investor-by-stock --date <yyyymmdd> --code <code> --basis amount|quantity --side net-buy|buy|sell --unit thousand|share [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks investor-by-stock-total --code <code> --from <yyyymmdd> --to <yyyymmdd> --basis amount|quantity --side net-buy --unit thousand|share [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks today-previous-trades --code <code> --day today|previous --interval-type tick|minute [--time <value>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks watchlist-info --codes <value> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks info-list --market-type kospi|kosdaq|kotc|konex|etn|loss-limit-etn|gold|volatility-etn|infrastructure|elw|mutual-fund|warrant|reit|warrant-certificate|etf|high-yield-fund [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks info-detail --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks sector-codes --market kospi|kosdaq|kospi200|kospi100|krx100 [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks member-firms [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks program-net-top --side net-sell|net-buy --basis amount|quantity --market-code <value> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks program-by-stock --date <yyyymmdd> --market-code <value> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks credit-loanable [--credit-grade all|a|b|c|d|e] [--market all|kospi|kosdaq] [--code <code>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic stocks credit-loanable-check --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes price --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes balance --date <yyyymmdd> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes by-stock --code <code> --from <yyyymmdd> --to <yyyymmdd> --institution-price buy|sell --foreign-price buy|sell [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes list --kind all|warrant-security|warrant-certificate [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes gold-price --code <gold-code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes gold-fills --code <gold-code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes gold-daily --code <gold-code> --date <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes gold-expected --code <gold-code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes multi-period --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes intraday-minute --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes institution-daily --from <yyyymmdd> --to <yyyymmdd> --side net-sell|net-buy --market kospi|kosdaq --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes strength-time --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes strength-daily --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes investor-intraday --market all|kospi|kosdaq --basis combined --investor foreign|institution|investment-trust|insurance|bank|pension|state|other-corporate --foreign-all yes|no --same-net-buy yes|no --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes investor-after-close --market all|kospi|kosdaq --basis amount|quantity --side net-buy|buy|sell --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes broker-trend --broker-code <value> --code <code> --from <yyyymmdd> --to <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes daily-price --code <code> --date <yyyymmdd> --basis quantity|amount [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes after-hours --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes program-time --date <yyyymmdd> --basis amount|quantity --market-code <value> --interval-type tick|minute --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes program-cumulative --date <yyyymmdd> --basis amount|quantity --market kospi|kosdaq --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes program-by-stock --basis amount|quantity --code <code> --date <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes program-daily --date <yyyymmdd> --basis amount|quantity --market-code <value> --interval-type tick|minute --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic quotes stock-program-daily [--basis amount|quantity] --code <code> [--date <yyyymmdd>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orderbooks list --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orderbooks gold --code <gold-code> --tick 1|3|5|10|30 [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles daily --code <code> --date <yyyymmdd> [--adjusted 0|1] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles by-stock --date <yyyymmdd> --code <code> --basis amount|quantity --side net-buy|buy|sell --unit thousand|share [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles lookup --market all|kospi|kosdaq --basis amount|quantity --side net-buy|buy|sell --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles stock-tick --code <code> --interval <n> [--adjusted 0|1] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles stock-minute --code <code> --interval <n> [--adjusted 0|1] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles stock-weekly --code <code> --date <yyyymmdd> [--adjusted 0|1] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles stock-monthly --code <code> --date <yyyymmdd> [--adjusted 0|1] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles stock-yearly --code <code> --date <yyyymmdd> [--adjusted 0|1] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles sector-tick --code <sector-code> --interval <n> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles sector-minute --code <sector-code> --interval <n> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles sector-daily --code <sector-code> --date <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles sector-weekly --code <sector-code> --date <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles sector-monthly --code <sector-code> --date <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles sector-yearly --code <sector-code> --date <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles gold-tick --code <gold-code> --interval <n> [--adjusted 0|1] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles gold-minute --code <gold-code> --interval <n> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles gold-daily --code <gold-code> --date <yyyymmdd> [--adjusted 0|1] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles gold-weekly --code <gold-code> --date <yyyymmdd> [--adjusted 0|1] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles gold-monthly --code <gold-code> --date <yyyymmdd> [--adjusted 0|1] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles gold-today-tick --code <gold-code> --interval <n> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic candles gold-today-minute --code <gold-code> --interval <n> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings orderbook-balance --market kospi|kosdaq --sort net-buy-balance|net-sell-balance|buy-ratio|sell-ratio --volume preopen|10k|50k|100k --stock-condition all|exclude-managed|exclude-margin-100|only-margin-100|only-margin-40|only-margin-30|only-margin-20 --credit-condition all|a|b|c|d|e|all-financing --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings orderbook-balance-spike --market kospi|kosdaq --side buy-balance|sell-balance --sort spike-quantity|spike-rate --interval <n> --volume 1k|5k|10k|50k|100k --stock-condition all|exclude-managed|exclude-margin-100|only-margin-100|only-margin-40|only-margin-30|only-margin-20 --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings balance-rate-spike --market kospi|kosdaq --ratio buy-to-sell|sell-to-buy --interval <n> --volume 5k|10k|50k|100k --stock-condition all|exclude-managed|exclude-margin-100|only-margin-100|only-margin-40|only-margin-30|only-margin-20 --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings volume-spike --market all|kospi|kosdaq --sort spike-quantity|spike-rate|drop-quantity|drop-rate --time-unit minute|previous-day --volume-condition <value> [--time <n>] --stock-condition <value> --price-condition <value> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings previous-change-rate --market all|kospi|kosdaq --sort rise-rate|rise-price|fall-rate|fall-price|flat --volume all|10k|50k|100k|150k|200k|300k|500k|1000k --stock-condition all|exclude-managed|exclude-preferred|exclude-managed-preferred|exclude-margin-100|only-margin-100|only-margin-40|only-margin-30|only-margin-20|exclude-liquidation|only-margin-50|only-margin-60|exclude-etf|exclude-spac|exclude-etf-etn --credit-condition all|a|b|c|d|e|all-financing --include-limit yes|no --price-condition all|under-1k|1k-2k|2k-5k|5k-10k|over-10k|over-1k|under-10k --amount-condition <value> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings list-fills --market all|kospi|kosdaq --sort rise-rate|rise-price|flat|fall-rate|fall-price|volume|upper-limit|lower-limit --volume all|1k|3k|5k|10k|50k|100k --stock-condition all|exclude-managed|exclude-preferred|exclude-managed-preferred|exclude-margin-100|only-margin-100|only-margin-40|only-margin-30|only-margin-20|exclude-liquidation|only-margin-50|only-margin-60|exclude-etf|exclude-spac|exclude-etf-etn --credit-condition all|a|b|c|d|exclude-overlimit|e|short|all-financing --price-condition all|under-1k|1k-2k|2k-5k|5k-10k|over-10k|over-1k|under-10k --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings today-volume --market all|kospi|kosdaq --sort volume|turnover|amount --stock-condition <value> --credit-type all|all-financing|a|b|c|d|short --volume-condition <value> --price-condition <value> --amount-condition <value> --session all|regular|pre-open|after-hours --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings previous-volume --market all|kospi|kosdaq --kind volume|amount --rank-from <n> --rank-to <n> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings amount --market all|kospi|kosdaq --include-managed yes|no --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings credit-ratio --market all|kospi|kosdaq --volume-condition <value> --stock-condition all|exclude-managed|exclude-margin-100|only-margin-100|only-margin-40|only-margin-30|only-margin-20 --include-limit yes|no --credit-condition all|a|b|c|d|e|all-financing --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings foreign-period-trades --market all|kospi|kosdaq --side net-sell|net-buy|net-trade --period today|previous|5d|10d|20d|60d --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings foreign-continuous-net --market all|kospi|kosdaq --side net-sell|net-buy --base-date today|previous --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings foreign-limit-usage --market all|kospi|kosdaq --period today|previous|5d|10d|20d|60d --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings foreign-broker-trades --market all|kospi|kosdaq --period today|previous|5d|10d|20d|60d --side net-buy|net-sell|buy|sell --sort amount|quantity --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings broker-by-stock --code <code> --from <yyyymmdd> --to <yyyymmdd> --side net-sell|net-buy [--period previous|5d|10d|20d|40d|60d|120d] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings broker-trades --broker-code <value> --volume-condition <value> --side net-buy|net-sell --period previous|5d|10d|60d --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings stock-main-brokers --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings net-buy-brokers --code <code> [--from <yyyymmdd>] [--to <yyyymmdd>] --date-mode period|start-end --point today|previous [--period 5d|10d|20d|40d|60d|120d] --sort close|date [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings top-exit-brokers --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings same-net-trades --from <yyyymmdd> [--to <yyyymmdd>] --market all|kospi|kosdaq --side net-buy|net-sell --basis quantity|amount --unit share|thousand --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings investor-intraday --side net-buy|net-sell --market all|kospi|kosdaq --investor foreign|foreign-broker|financial-investment|investment-trust|other-financial|bank|insurance|pension|state|other-corporate|institution [--basis amount|quantity] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings after-hours-change-rate --market all|kospi|kosdaq --sort rise-rate|rise-price|fall-rate|fall-price|flat --stock-condition <value> --volume <value> --credit-condition all|a|b|c|d|exclude-overlimit|e|short|all-financing --amount-condition <value> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic rankings foreign-institution-trades --market all|kospi|kosdaq --basis amount|quantity --include-date yes|no [--date <yyyymmdd>] --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic sectors program --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic sectors investor-flows --market kospi|kosdaq --basis amount|quantity --exchange KRX|NXT|ALL [--date <yyyymmdd>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic sectors price --market kospi|kosdaq|kospi200 --code <sector-code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic sectors stocks --market kospi|kosdaq|kospi200 --code <sector-code> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic sectors indices --code <sector-code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic sectors daily --market kospi|kosdaq|kospi200 --code <sector-code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic etfs info --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic etfs daily --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic etfs profit --code <code> --index-code <code> --period week|month|six-months|year [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic etfs list --tax-type all|tax-free|holding-tax|company|foreign|foreign-tax-free --nav-compare all|nav-gt-close|nav-lt-close --manager <code> --taxable all|taxable|tax-free --tracking-index <code> --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic etfs intraday-trend --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic etfs intraday-fills --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic etfs daily-fills --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic etfs nav --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic etfs foreign-trend --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws daily --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws balance --code <code> --date <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws conditions --issuer-code <code> --underlying-code <code> --right-type all|call|put|dc|dp|ex|early-call|early-put --lp-code <code> --sort none|rise-rate|rise-price|fall-rate|fall-price|volume|amount|days-left [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws sensitivity --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws price-move --direction rise|fall --time-unit minute|day --time <n> --volume all|10k|50k|100k|300k|500k|1000k --issuer-code <code> --underlying-code <code> --right-type all|call|put|dc|dp|ex|early-call|early-put --lp-code <code> --include-ended yes|no [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws broker-net --issuer-code <code> --volume all|5k|10k|50k|100k|500k|1000k --side net-buy|net-sell --period previous|5d|10d|40d|60d --include-ended yes|no [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws divergence --issuer-code <code> --underlying-code <code> --right-type all|call|put|dc|dp|ex|early-call|early-put --lp-code <code> --include-ended yes|no [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws change-rank --sort rise-rate|rise-price|fall-rate|fall-price --right-type all|call|put|dc|dp|early-call|early-put --include-ended yes|no [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws balance-rank --sort buy-balance|sell-balance --right-type all|call|put|dc|dp|early-call|early-put --include-ended yes|no [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws proximity --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic elws details --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic investors by-stock --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic investors lookup --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic investors trend --period recent|3d|5d|10d|20d|120d|range [--from <yyyymmdd>] [--to <yyyymmdd>] --market kospi|kosdaq --side net-buy --target stock|sector --basis amount|quantity --exchange KRX|NXT|ALL [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic investors gold-status [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic short-selling trend --code <code> --from <yyyymmdd> --to <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic securities-lending by-stock --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic securities-lending trend [--from <yyyymmdd>] [--to <yyyymmdd>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic securities-lending list --from <yyyymmdd> --market kospi|kosdaq [--to <yyyymmdd>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic securities-lending lookup --date <yyyymmdd> --market kospi|kosdaq [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic themes lookup --kind all|theme|stock --days <n> --sort profit-top|profit-bottom|change-top|change-bottom --exchange KRX|NXT|ALL [--code <code>] [--name <text>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic themes by-stock --code <code> --exchange KRX|NXT|ALL [--days <n>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams conditions-list [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams conditions-search [--seq <value>] --exchange KRX|NXT|ALL [--cont yes|no] [--next-key <value>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams conditions-subscribe [--seq <value>] --exchange KRX|NXT|ALL [--count <n>] [--duration <seconds>] [--check] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams conditions-unsubscribe [--seq <value>] [--exchange KRX|NXT|ALL] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams order-fills [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] [--code <value>] [--codes <codes>] [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams balance [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] [--code <value>] [--codes <codes>] [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams momentum [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams trades [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams best-quotes [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams orderbook [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams after-hours-orderbook [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams brokers [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams etf-nav [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams expected-fills [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams gold-conversion [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams sector-index [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams sector-change [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams stock-info [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams elw-theory [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams market-open [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] [--code <value>] [--codes <codes>] [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams elw-indicator [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams program-trades [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic streams vi [--action subscribe|unsubscribe] [--group <n>] [--refresh yes|no] [--code <value>] [--codes <codes>] [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts list [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts daily-balance-return --date <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts realized-profit-stock-daily [--code <code>] --date <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts realized-profit-period-stock [--code <code>] --from <yyyymmdd> --to <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts realized-profit-daily --from <yyyymmdd> --to <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts realized-profit-today-detail --code <code> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts return-rate --exchange ALL|KRX|NXT [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts day-trading-log [--date <yyyymmdd>] --sell-scope same-day-buy-sell|all-sells --cash-credit all|cash|credit [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts cash --cash-basis estimated|normal [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts estimated-assets-daily --from <yyyymmdd> --to <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts assets --include-delisted yes|no [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts valuation --include-delisted yes|no --exchange KRX|NXT [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts fill-balance --exchange KRX|NXT [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts order-fill-detail [--date <yyyymmdd>] (--order order|reverse | --fill-status open|filled) --asset-kind all|stock|bond --side all|sell|buy [--code <code>] [--order-id <id>] --exchange ALL|KRX|NXT|SOR [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts next-settlement [--settlement-id <value>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts order-fill-status [--date <yyyymmdd>] --asset-kind all|stock|bond --market all|kospi|kosdaq|otcbb|ecn --side all|sell|buy --fill-status all|filled [--code <code>] [--order-id <id>] --exchange ALL|KRX|NXT|SOR [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts credit-margin --code <code> [--price <price>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts margin-details [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts transaction-history --from <yyyymmdd> --to <yyyymmdd> --kind <value> [--code <value>] [--currency <value>] --product all|domestic-stock|fund|overseas-stock|financial-product [--overseas-exchange <value>] --exchange ALL|KRX|NXT [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts daily-return-detail --from <yyyymmdd> --to <yyyymmdd> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts today-status [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts holdings --basis total|individual --exchange KRX|NXT [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts gold-balance [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts gold-cash [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts gold-all-order-fills --date <yyyymmdd> [--order order|reverse] --market-deal <value> --asset-kind all|stock|bond --side all|sell|buy [--code <value>] [--order-id <id>] [--exchange ALL|KRX|NXT|SOR] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts gold-order-fills [--date <yyyymmdd>] (--order order|reverse | --fill-status open|filled) --asset-kind all|stock|bond --side all|sell|buy [--code <value>] [--order-id <id>] --exchange ALL|KRX|NXT|SOR [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts gold-transactions [--from <yyyymmdd>] [--to <yyyymmdd>] [--kind all|deposit-withdrawal|release|trade|buy|sell|deposit|withdrawal] [--code <value>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic accounts gold-open-orders --date <yyyymmdd> [--order order|reverse] --market-deal <value> --asset-kind all|stock|bond --side all|sell|buy [--code <value>] [--order-id <id>] [--exchange ALL|KRX|NXT|SOR] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders chance --code <code> --side sell|buy --price <price> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders margin --code <code> [--price <price>] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders list-open --stock-scope all|stock --side all|sell|buy [--code <code>] --exchange ALL|KRX|NXT [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders list-fills --stock-scope all|stock --side all|sell|buy [--code <code>] [--order-id <id>] --exchange ALL|KRX|NXT [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders open-detail --order-id <id> [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders buy [--exchange KRX|NXT|SOR] --code <code> --qty <n> [--price <price>] --order-type limit|market [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders sell [--exchange KRX|NXT|SOR] --code <code> --qty <n> [--price <price>] --order-type limit|market [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders modify [--exchange KRX|NXT|SOR] --order-id <id> --code <code> --qty <n> --price <price> [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders cancel [--exchange KRX|NXT|SOR] --order-id <id> --code <code> --qty <n> [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders credit-buy --exchange KRX|NXT|SOR --code <code> --qty <n> [--price <price>] --order-type limit|market|conditional-limit|after-hours-close|pre-open|after-hours-single|best-limit|top-priority|limit-ioc|market-ioc|best-ioc|limit-fok|market-fok|best-fok|stop-limit|mid|mid-ioc|mid-fok [--condition-price <price>] [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders credit-sell --exchange KRX|NXT|SOR --code <code> --qty <n> [--price <price>] --order-type limit|market|conditional-limit|after-hours-close|pre-open|after-hours-single|best-limit|top-priority|limit-ioc|market-ioc|best-ioc|limit-fok|market-fok|best-fok|stop-limit|mid|mid-ioc|mid-fok --credit-deal financing|financing-all [--loan-date <yyyymmdd>] [--condition-price <price>] [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders credit-modify --exchange KRX|NXT|SOR --order-id <id> --code <code> --qty <n> --price <price> [--condition-price <price>] [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders credit-cancel --exchange KRX|NXT|SOR --order-id <id> --code <code> --qty <n> [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders gold-buy --code <value> --qty <n> [--price <price>] --order-type limit|limit-ioc|limit-fok [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders gold-sell --code <value> --qty <n> [--price <price>] --order-type limit|limit-ioc|limit-fok [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders gold-modify --code <value> --order-id <id> --qty <n> --price <price> [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
kiwoomcli domestic orders gold-cancel --order-id <id> --code <value> --qty <n> [--confirm] [--format pretty|json|jsonl|yaml] [--profile NAME | --mode demo|real]
```

Design backlog / TODO command candidates:

These lines are not `coverage_status=planned` by themselves. They are retained
as design notes or overseas TODO placeholders. Runtime-exposed commands are
listed in the implemented block above.

```sh
kiwoomcli domestic stocks search --query <text>
kiwoomcli domestic stocks financials --code <code>
kiwoomcli domestic stocks disclosures --code <code>

kiwoomcli domestic rankings list --kind <kind> --market <market>

kiwoomcli domestic etfs components --code <code>
kiwoomcli domestic etfs quotes --code <code>

kiwoomcli domestic investors by-market --market <market>

kiwoomcli domestic short-selling by-market --market <market>

kiwoom investment-info ...  # TODO: overseas APIs are mapped but not runtime-exposed yet
kiwoom overseas sectors ...  # TODO: overseas APIs are mapped but not runtime-exposed yet
kiwoom overseas quotes ...  # TODO: overseas APIs are mapped but not runtime-exposed yet
kiwoom overseas orderbooks ...  # TODO: overseas APIs are mapped but not runtime-exposed yet
kiwoom overseas candles ...  # TODO: overseas APIs are mapped but not runtime-exposed yet

kiwoomcli domestic accounts balance
kiwoomcli domestic accounts withdrawable
kiwoomcli domestic accounts profit
kiwoomcli domestic accounts positions
kiwoomcli domestic accounts executions

kiwoomcli domestic orders history --from <yyyymmdd> --to <yyyymmdd>

# Superseded by implemented stream commands above:
# kiwoomcli domestic streams quotes --code <code>
# kiwoomcli domestic streams orderbooks --code <code>
# kiwoomcli domestic streams order-events --account <alias>
# kiwoomcli domestic streams conditions

# TODO(overseas): keep all overseas command candidates mapped but not
# runtime-exposed until overseas Kiwoom API execution is verified.
# kiwoom overseas stocks search --query <text>
# kiwoom overseas stocks info --code <code>
# kiwoom overseas accounts balance --account <alias>
# kiwoom overseas accounts positions --account <alias>
# kiwoom overseas orders chance --account <alias> --code <code> --side buy|sell
# kiwoom overseas orders buy --account <alias> --code <code> --qty <n> --price <price> --order-type <type> --confirm
# kiwoom overseas orders sell --account <alias> --code <code> --qty <n> --price <price> --order-type <type> --confirm
```

WebSocket stream commands output Kiwoom server messages only. For bounded
`--format pretty`/`json`/`yaml` runs, stdout is one list of received server
messages; `--format jsonl` streams one server message per line. `REG`, `REMOVE`,
and `SYSTEM` are control messages and may appear in stdout, but `--count`
counts only `REAL` data messages. Foreground stream commands also accept repeated
`--code`, comma-separated `--codes`, `--count`, `--duration`, `--watch`, `--check`, and
`--named`; prefer `--count`/`--duration` for bounded stream runs. Use
`--check` for a finite registration/collection run that exits successfully even
if no `REAL` tick arrives. CLI timeout/error explanations are written to stderr
and are not injected as synthetic JSON payloads.
With `--named`, only `REAL` frames are converted: `data[*].values` FID keys are
emitted under `data[*].data` using the built-in schema derived from the packaged
Kiwoom spec. Control frames remain raw, unknown FIDs are preserved under
`unknown`, and values stay strings.

```bash
kiwoomcli domestic streams trades --code 005930 --count 1 --named --format json
```

Stream commands run in the foreground. To capture a long-running subscription
without keeping the terminal attached, redirect `--output` (or stdout) to a file
and background the process with your OS tools instead of a built-in job manager:

```bash
# 계속 수신하며 이벤트를 파일에 기록
kiwoomcli domestic streams trades --codes 005930,000660 --watch --format jsonl --output trades.jsonl

# Linux/macOS: 터미널을 닫아도 유지 (nohup / tmux / systemd --user 등)
nohup kiwoomcli domestic streams trades --codes 005930,000660 --watch --format jsonl --output trades.jsonl &

# Windows PowerShell: 별도 프로세스로 분리
Start-Process kiwoom -ArgumentList 'streams trades --codes 005930,000660 --watch --format jsonl --output trades.jsonl'
```

The OS (shell job control, `nohup`, `tmux`, `systemd --user`, Windows 작업
스케줄러/`Start-Process`) already provides process detachment, supervision, and
restart, so the CLI does not ship its own job manager.

Condition search formulas are created and changed in Kiwoom Hero Moon HTS
(영웅문 HTS). The CLI only lists, selects, requests, subscribes to, and clears
conditions already saved in HTS.

Account identifiers are redacted by the CLI output layer for guarded
account/order reads and account/order streams. Order numbers (`ord_no`,
`orig_ord_no`, …) are NOT redacted: they are operational identifiers the user
needs to read from a buy/list response and pass to `orders modify`/`cancel`.
Redaction applies consistently to `pretty`, `json`, `jsonl`, and `yaml` and does
not expose configured account identifier fields.
Domestic order write commands (`orders buy/sell/modify/cancel`, `credit-*`,
`gold-*`) are `guarded`/`order_write`: without `--confirm` they show a short
미전송 주문 확인 message plus order summary and never call the order API, and with
`--confirm` they submit to the real endpoint. Order-type price rules are validated before any
submission path from `kiwoom_cli/maps/order_price_policies.csv`; for example,
`--order-type limit` requires `--price`, while `--order-type market` must not
include `--price`. Invalid order identifiers are returned before any submission
path.
Order writes select their auth target with `--profile`/`--mode` like other
runtime commands; verify them against the demo (모의투자) server, using a
separate account/`.env` for 금현물 where the demo account differs. Order rows
that remain `preview-only` (overseas) never submit, even with `--confirm`.

See [docs/command-system.md](docs/command-system.md) for the CLI command-system
principles and [docs/feature-matrix.md](docs/feature-matrix.md) for the full
command matrix and implementation status.

Policy-design API families:

The local spec includes `해외주식 > 기타` APIs for won-order available amount,
won-order setting exchange, auto exchange cancellation, target-rate auto
exchange, foreign-currency exchange, and integrated margin details. These APIs
are recorded in `kiwoom_cli/maps/api_commands.csv`; 조회성 rows use `planned`
coverage status and write-like rows start as `preview-only` until command
semantics, account impact, and safety policy are explicitly approved.

## User-Facing Terminology

Keep CLI terms stable and hide Kiwoom source field names such as `stk_cd` in the
maps. Command context decides the concrete code type.

| Concept | Canonical option | Example | Notes |
| --- | --- | --- | --- |
| Stock, sector, theme, ETF, ELW, or overseas symbol code | `--code`, `-c` | `--code 005930` | Do not use `--sector-code`, `--theme-code`, or `--symbol` as canonical options. |
| Account selection | `--account` | `--account main` | Account/order commands should prefer a local alias over a raw account number. |
| Auth profile selection | `--profile` | `--profile demo-main` | Runtime/auth selection only; keep separate from `--account`. |
| Runtime mode | `--mode` | `--mode demo` | Choices: `demo`, `real`. |
| Market/exchange selector | `--market` | `--market kospi` | Choices come from maps/specs. |
| Search text | `--query` | `--query 삼성` | Search commands only. |
| Quantity | `--qty` | `--qty 10` | Accepted short form for order quantity. |
| Price | `--price` | `--price 70000` | Unit price or price condition. |
| Buy/sell side | `--side` | `--side buy` | Choices: `buy`, `sell`. |
| Order type | `--order-type` | `--order-type limit` | Choices must come from command maps. |
| Order identifier | `--order-id` | `--order-id 123` | Do not abbreviate safety-critical identifiers. |
| Original order identifier | `--orig-order-id` | `--orig-order-id 123` | Use for modify/cancel APIs when the spec requires an original order number. |
| Start date | `--from` | `--from 20250101` | Period queries. |
| End date | `--to` | `--to 20260528` | Period queries. |
| Single base date | `--date` | `--date 20260528` | Single-date queries. |
| Minute interval | `--interval` | `--interval 1` | Minute candles and similar interval queries. |
| Maximum result count | `--limit` | `--limit 200` | Prefer this over `--max-items` for new commands. |
| Output format | `--format` | `--format json` | Choices: `pretty`, `json`, `jsonl`, `yaml`. |
| Transform/extract path | `--transform` | `--transform data.items` | Add only after parser and redaction policy are approved. |
| Diagnostics | `--debug` | `--debug` | Must redact tokens and account numbers (order numbers are shown). |
| Condition search formula | `--seq` | `--seq 2` | Create or edit saved condition formulas in Kiwoom Hero Moon HTS; CLI uses saved formulas only. |
| Write confirmation | `--confirm` | `--confirm` | Candidate confirmation flag for order/transfer-like writes; final policy is decided per command group. |

Rules:

- Use `--code` whenever command context already identifies the code type.
- Keep Kiwoom source field names in `kiwoom_cli/maps/`, not in user help text.
- Abbreviate only common trading terms with low ambiguity, such as `--qty`.
- Do not abbreviate safety-critical terms such as `--account` or `--order-id`.
- Use the same date, output, pagination, mode, and profile options across all
  command groups.

## Spec-Driven Development Rules

The CLI is curated, not raw-spec generated.

Use `kiwoomcli spec search` for discovery and fallback, but expose stable
user-facing operations as resource commands such as `stocks info`,
`accounts balance`, or `orders list-open`.

Rules:

- API IDs, paths, methods, required fields, and response fields must be validated
  against `kiwoom_api_spec.json`.
- User-facing command names, friendly option names, output policy, pagination
  policy, and safety policy must come from editable maps or explicit docs.
- Do not hide command behavior in Python handlers when a spec, map, or explicit
  config can define it.
- Do not add or revive a broad public `kiwoom/apis/` wrapper layer.
- Do not import generated examples as stable public CLI APIs.
- Do not add example-local auth helpers such as `Examples/auth.py`,
  `examples/auth.py`, or `kis_auth.py`.
- New CLI behavior must acquire runtime objects through the package facade:
  `get_auth`, `get_client`, or `get_ws_client`.
- New implemented CLI behavior must update this README and the docs under
  `kiwoom_cli/docs/`.

Preferred runtime pattern:

```python
from kiwoom import get_client, get_ws_client

client = get_client(mode=args.mode, profile=args.profile)
response = client.fetch_page(api_id=api_id, path=path, body=body, method=method)
```

## Internal Layout

Current CLI implementation layout:

```text
kiwoom_cli/
  main.py            # router only: parse args, dispatch to args.handler, error funnel
  arguments.py
  executor.py
  output.py
  registry.py
  safety.py
  setup.py           # setup command parser/handler + onboarding logic
  doctor.py          # doctor command parser/handler
  order_confirmation.py
  README.md
  commands/          # one module per command group, each add_*_parser + handlers
    auth.py
    spec.py
    accounts.py
    candles.py
    elws.py
    etfs.py
    investors.py
    orderbooks.py
    orders.py
    quotes.py
    rankings.py
    securities_lending.py
    short_selling.py
    stocks.py
    streams.py
    themes.py
  docs/
  maps/
    api_commands.csv
    arguments.csv
    README.md
```

`api_commands.csv` must include every local API exactly once.
`coverage_status` records whether each row is `public`, `guarded`,
`preview-only`, or `planned`.

As additional domain commands are implemented, add small modules and maps:

```text
kiwoom_cli/
  registry.py
  arguments.py
  executor.py
  output.py
  safety.py
  commands/
    accounts.py
    stocks.py
    quotes.py
    orderbooks.py
    candles.py
    rankings.py
    etfs.py
    elws.py
    investors.py
    short_selling.py
    securities_lending.py
    themes.py
    orders.py
    streams.py
  maps/
    api_commands.csv
    arguments.csv
    output.csv
    safety.csv
```

Domain modules should register command groups and delegate to shared execution.
They should not call `requests` directly, issue tokens directly, construct
ad-hoc request bodies, or bypass common safety checks.

## Docs Contract

The `docs/` folder is intended to be good enough to publish as command
documentation or transform into an agent skill reference bundle.

Docs currently provided:

- [docs/README.md](docs/README.md): docs index and status labels.
- [docs/command-system.md](docs/command-system.md): the only maintained CLI
  command-system principles document.
- [docs/feature-matrix.md](docs/feature-matrix.md): resource groups, command
  status, API candidates, auth, safety, and feature notes.
- [docs/api-coverage.md](docs/api-coverage.md): local API counts and coverage
  evidence.
- [docs/command-contracts.md](docs/command-contracts.md): command-by-command
  argument contracts, Kiwoom field mappings, and examples.
- [docs/implementation-status.md](docs/implementation-status.md): current
  implementation evidence and blocked real-call items.
- [docs/types.md](docs/types.md): shared CLI types, validation rules, choices,
  redaction types, and safety policies.

When maps exist, docs should be generated from maps plus `kiwoom_api_spec.json`
and then reviewed. Do not let docs drift from parser behavior.

Every implemented command must satisfy:

- `kiwoom <resource> <command> --help` renders the documented flags.
- The command appears in the feature matrix with status `Implemented`.
- Required request fields are validated against the spec.
- Output and redaction behavior is documented.
- Safety policy is explicit.

## Agent Reference Direction

Upbit's CLI is useful to agents because it has both a resource-shaped CLI and
focused reference files that define flags, types, examples, safety rules, setup,
output, and terminology.

Kiwoom should follow that pattern after the first domain commands are stable:

```text
.agents/skills/kiwoom/kiwoom/
  SKILL.md
  references/
    setup.md
    accounts.md
    orders.md
    stocks.md
    quotes.md
    orderbooks.md
    candles.md
    streams.md
    output.md
    glossary.md
```

Those references should be derived from the same maps and specs as the CLI docs,
not maintained as unrelated prose.

## Safety Rules

Order and transfer-like commands have real account side effects.

- Prefer `demo` mode during development and verification.
- Write commands must support preview/check workflows before submission.
- Order write confirmation policy is not finalized; the current candidate is a
  single `--confirm` flag plus command-specific preview/check behavior.
- Deposit/withdraw execution commands are blocked until explicit spec support and
  safety policy are approved.
- Do not prove behavior with mocks, fake clients, fake transports, replay logs,
  cassettes, or simulated Kiwoom payloads.
- If credentials, network, or account-safety constraints block real
  verification, report it as blocked/not-run.
- Never log or commit credentials, tokens, account numbers, order IDs, or
  unsanitized real-call output.

## Verification

Static checks for CLI/doc changes:

```sh
.venv/bin/python -m compileall kiwoom kiwoom_cli Examples
kiwoomcli --help
kiwoomcli spec search ka10001 --limit 3
! rg -n "unittest\\.mock|MagicMock|\\bMock\\b|\\bpatch\\b|fake|stub|monkeypatch|cassette|replay" kiwoom kiwoom_cli Examples utils -g '!**/*.md' -g '!**/*.csv'
```

When command maps exist, add:

```sh
.venv/bin/python -m kiwoom_cli.validate_maps
```
