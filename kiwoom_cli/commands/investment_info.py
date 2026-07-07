"""TODO: overseas investment-info commands.

The local spec contains 12 `해외주식 > 투자정보` APIs and they remain mapped in
`kiwoom_cli/maps/api_commands.csv` as planned public coverage. Do not expose this
module from `kiwoom_cli.main` until the overseas Kiwoom runtime path is confirmed
to work.

Planned command candidates, intentionally disabled:

- `kiwoom investment-info research`
- `kiwoom investment-info valuation-change`
- `kiwoom investment-info dividend-search`
- `kiwoom investment-info dividend-search-category`
- `kiwoom investment-info dividend-rank`
- `kiwoom investment-info dividend-rank-category`
- `kiwoom investment-info best-dividends`
- `kiwoom investment-info dividend-annual`
- `kiwoom investment-info dividend-schedule`
- `kiwoom investment-info dividend-events`
- `kiwoom investment-info dividend-growth`
- `kiwoom investment-info dividend-summary`
"""

from __future__ import annotations


# NOTE:
# Keep this file as an implementation placeholder instead of deleting the
# overseas investment-info plan. When overseas APIs are verified, re-enable the
# parser by:
#
# 1. Changing the corresponding map rows from `planned` to `implemented`.
# 2. Adding explicit rows to `kiwoom_cli/maps/arguments.csv`.
# 3. Restoring `add_investment_info_parser(...)` and runtime handlers.
# 4. Updating README/docs/contracts and regenerating `.agents` references.
#
# Until then this module intentionally exports no parser hook.
