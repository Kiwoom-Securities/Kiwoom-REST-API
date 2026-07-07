"""TODO: overseas market commands.

The local spec contains overseas stocks, quotes, orderbooks, candles, sectors,
rankings, accounts, and orders. These rows stay in
`kiwoom_cli/maps/api_commands.csv` for full 352-API coverage, but the runtime
command surface is intentionally disabled because overseas Kiwoom API execution
is not currently working.

Do not expose this module from `kiwoom_cli.main` until the overseas runtime path
is confirmed with real credentials.
"""

from __future__ import annotations


# Planned public-read command candidates, intentionally disabled:
#
# - `kiwoom overseas sectors price`
# - `kiwoom overseas sectors price-daily`
# - `kiwoom overseas sectors summary`
# - `kiwoom overseas sectors summary-rank`
# - `kiwoom overseas sectors stocks`
# - `kiwoom overseas quotes info`
# - `kiwoom overseas quotes daily-fills`
# - `kiwoom overseas quotes daily-fills-from`
# - `kiwoom overseas quotes daily-price`
# - `kiwoom overseas orderbooks list`
# - `kiwoom overseas candles stock-tick`
# - `kiwoom overseas candles stock-minute`
# - `kiwoom overseas candles stock-daily`
# - `kiwoom overseas candles stock-weekly`
# - `kiwoom overseas candles stock-monthly`
# - `kiwoom overseas candles stock-yearly`
# - `kiwoom overseas candles stock-quarterly`
# - `kiwoom overseas candles sector-tick`
# - `kiwoom overseas candles sector-minute`
# - `kiwoom overseas candles sector-daily`
# - `kiwoom overseas candles sector-weekly`
# - `kiwoom overseas candles sector-monthly`
# - `kiwoom overseas candles sector-yearly`
# - `kiwoom overseas candles financial-annual`
# - `kiwoom overseas candles financial-quarterly`
#
# When overseas APIs are verified, re-enable incrementally by:
#
# 1. Promoting only verified API rows from `planned` to `implemented`.
# 2. Adding explicit argument mappings for those command paths.
# 3. Reintroducing parser/runtime handlers.
# 4. Updating README/docs/contracts and regenerating `.agents` references.
#
# Until then this module intentionally exports no parser hook.
