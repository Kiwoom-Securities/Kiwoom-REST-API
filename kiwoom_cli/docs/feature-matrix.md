# Feature Matrix

This matrix follows the Upbit CLI model of plural resource groups plus
subcommands, while adapting names and safety rules to Kiwoom OpenAPI.

## Global Behavior

| Feature | Status | Notes |
| --- | --- | --- |
| Installed command | Implemented | The user command is `kiwoom`. |
| Profiles | Implemented | `kiwoom auth login/list/switch` manage profile aliases. |
| Mode selection | Implemented | Auth and implemented domain commands accept `--mode demo|real`; domain commands also accept `--profile`. |
| API discovery | Implemented | `kiwoom spec search/show/groups/apis` searches and displays local spec metadata. |
| Output formats | Implemented | Implemented domain commands support `--format pretty|json|jsonl|yaml`; spec commands support `pretty|json|yaml`. |
| Transform/filtering | Planned | Add `--transform <path>` only after choosing a parser/dependency and redaction policy. |
| Pagination limit | Planned | Add `--max-items N` and map it to `client.paginate(...)` where supported. |
| Debug mode | Planned | Add `--debug` with redacted request/response diagnostics. |

## Resource Groups

| Group | Status | Coverage | Purpose | Auth | Safety |
| --- | --- | --- | --- | --- | --- |
| `auth` | Implemented | `public` | Credential/profile/token administration. | Mixed | `token_admin` |
| `spec` | Implemented | `public` | Local API discovery for users and agents. | No | `read` |
| `stocks` | Implemented | `public` | Domestic stock identity, broker, fill, investor, program-trading, credit-loanable, and screener-style stock APIs. Overseas stock rows remain TODO until overseas runtime is verified. | Usually yes through shared runtime token | `read` |
| `quotes` | Implemented | `public` | Domestic current price, quote, investor, broker, and program-trading summaries. Overseas quote rows remain TODO until overseas runtime is verified. | Usually yes through shared runtime token | `read` |
| `orderbooks` | Partial | `public` | 호가/order book views. | Usually yes through shared runtime token | `read` |
| `candles` | Partial | `public` | Chart/candle data by interval. | Usually yes through shared runtime token | `read` |
| `accounts` | Implemented | `guarded` | Domestic account list, cash, assets, balances, PnL, settlement, and gold-account reads with account identifier redaction across all CLI output formats. Order numbers are shown when present so they can be reused for order management. Overseas account rows remain TODO until overseas runtime is verified. | Yes | `account_read` |
| `orders` | Implemented | `guarded` for inquiry and write APIs | Domestic order inquiry plus write-like stock/credit/gold orders. Write commands show 미전송 주문 확인 output when `--confirm` is omitted, and submit to the real endpoint with `--confirm`. Overseas order rows remain TODO until overseas runtime is verified. | Yes for guarded reads; writes submit only with `--confirm` | `account_read` or `order_write` |
| `streams` | Implemented | `public` for market/condition streams, `guarded` for account/order streams | WebSocket realtime subscriptions and condition search through the package WebSocket client. Foreground only; use `--output` plus OS backgrounding (nohup/tmux/systemd/작업 스케줄러) for long-running capture. | Yes | `read` / `account_read` |
| `rankings` | Implemented | `public` | Domestic ranking and screener-style APIs; overseas ranking rows remain TODO until overseas runtime is verified. | Mixed | `read` |
| `sectors` | Partial | `public` | Domestic sector APIs; overseas sector rows remain TODO until overseas runtime is verified. | Mixed | `read` |
| `etfs` | Implemented | `public` | Domestic ETF APIs. | Mixed | `read` |
| `elws` | Implemented | `public` | Domestic ELW APIs. | Mixed | `read` |
| `investors` | Implemented | `public` | Institution/foreign investor flow APIs. | Mixed | `read` |
| `short-selling` | Implemented | `public` | Short-selling trend APIs. | Mixed | `read` |
| `securities-lending` | Implemented | `public` | Securities lending APIs. | Mixed | `read` |
| `themes` | Implemented | `public` | Theme group and component APIs. | Mixed | `read` |
| `investment-info` | Planned | `public` | Overseas research/dividend/investment information APIs; TODO until overseas runtime is verified. | Mixed | `read` |
| `overseas stocks/rankings/sectors/quotes/orderbooks/candles` | Planned | `public` | Overseas public-read command candidates are mapped but not runtime-exposed. | Mixed | `read` |
| `overseas accounts` | Planned | `guarded` | Overseas account-read command candidates are mapped but not runtime-exposed. | Yes | `account_read` |
| `overseas orders` | Planned | `preview-only` | Overseas order command candidates are mapped but not runtime-exposed. | Yes | `order_write` |
| `overseas-review` | Review | `planned` or `preview-only` | Overseas miscellaneous APIs split by coverage status. | Mixed | `review_required` |
| `deposits` | Blocked | none | Deposit history/availability only if explicitly mapped. | Yes | `account_read` |
| `withdraws` | Blocked | none | Withdrawable inquiry only unless an execution API and safety policy are approved. | Yes | `account_read` or stronger |

## Command Matrix

| Command | Status | Candidate API ID(s) | Auth | Safety | Feature Notes |
| --- | --- | --- | --- | --- | --- |
| `kiwoom setup` | Implemented | `ka00001` verification call in setup flow | Yes | `token_admin` | Creates shared credentials/token setup used by CLI and generated examples. |
| `kiwoom auth login` | Implemented | `au10001` | Yes | `auth_write` | Registers or refreshes a profile alias. |
| `kiwoom auth list` | Implemented | Local profile/token state | No network by default | `token_admin` | Lists aliases and token/cache status. |
| `kiwoom auth switch <alias>` | Implemented | Local profile state | No | `token_admin` | Changes current profile. |
| `kiwoom auth status` | Implemented | Local auth/token state | No network by default | `token_admin` | Shows token reuse and next auth action. |
| `kiwoom auth refresh` | Implemented | OAuth token issue | Yes | `token_admin` | Refreshes local token cache. |
| `kiwoom auth revoke` | Implemented | `au10002` | Yes | `auth_write` | Revokes server token and clears local cache. |
| `kiwoom auth clear` | Implemented | Local token/credential store | No | `token_admin` | Clears token, optionally stored credentials. |
| `kiwoom spec search <query>` | Implemented | `kiwoom_api_spec.json` | No | `read` | Discovery/fallback; not the primary trading interface. |
| `kiwoom spec show <api-id>` | Implemented | `kiwoom_api_spec.json` | No | `read` | Shows request/response fields for one local API ID. |
| `kiwoom spec groups` | Implemented | `kiwoom_api_spec.json` | No | `read` | Lists local API groups and counts. |
| `kiwoom spec apis` | Implemented | `kiwoom_api_spec.json` | No | `read` | Lists local API summaries, optionally filtered by menu group. |
| `kiwoom stocks info --code <code>` | Implemented | `ka10001` | Yes | `read` | First read-only domain command through shared runtime facade. |
| `kiwoom stocks trend --code <code> --date <yyyymmdd> --kind financing\|loan` | Implemented | `ka10013` | Yes | `read` | 신용매매 동향 through shared runtime facade. |
| `kiwoom stocks realtime-rank --window 1m\|10m\|1h\|today\|30s` | Implemented | `ka00198` | Yes | `read` | 실시간 종목 조회 순위 through shared runtime facade. |
| `kiwoom stocks brokers --code <code>` | Implemented | `ka10002` | Yes | `read` | 주식 거래원 through shared runtime facade. |
| `kiwoom stocks fills --code <code>` | Implemented | `ka10003` | Yes | `read` | 체결 정보 through shared runtime facade. |
| `kiwoom stocks daily-trades --code <code> --from <yyyymmdd>` | Implemented | `ka10015` | Yes | `read` | 일별 거래 상세 through shared runtime facade. |
| `kiwoom stocks new-high-low --market all\|kospi\|kosdaq --kind new-high\|new-low --price-basis high-low\|close --stock-condition <value> --volume-condition <value> --credit-condition <value> --include-limit yes\|no --period-days 5\|10\|20\|60\|250 --exchange KRX\|NXT\|ALL` | Implemented | `ka10016` | Yes | `read` | 신고가/신저가 through shared runtime facade. |
| `kiwoom stocks limit-move --market all\|kospi\|kosdaq --direction upper\|rise\|flat\|lower\|fall\|prev-upper\|prev-lower --sort code\|count\|change-rate --stock-condition <value> --volume-condition <value> --credit-condition <value> --price-condition <value> --exchange KRX\|NXT\|ALL` | Implemented | `ka10017` | Yes | `read` | 상하한가/상승하락 종목 through shared runtime facade. |
| `kiwoom stocks high-low-near --kind high\|low --near-rate <value> --market all\|kospi\|kosdaq --volume-condition <value> --stock-condition <value> --credit-condition <value> --exchange KRX\|NXT\|ALL` | Implemented | `ka10018` | Yes | `read` | 고저가 근접 종목 through shared runtime facade. |
| `kiwoom stocks price-spike --market all\|kospi\|kosdaq\|kospi200 --direction rise\|fall --time-unit minute\|day --time <n> --volume-condition <value> --stock-condition <value> --credit-condition <value> --price-condition <value> --include-limit yes\|no --exchange KRX\|NXT\|ALL` | Implemented | `ka10019` | Yes | `read` | 가격 급등락 종목 through shared runtime facade. |
| `kiwoom stocks volume-renewal --market all\|kospi\|kosdaq --period-days 5\|10\|20\|60\|250 --volume-condition <value> --exchange KRX\|NXT\|ALL` | Implemented | `ka10024` | Yes | `read` | 거래량 갱신 종목 through shared runtime facade. |
| `kiwoom stocks volume-zone --market all\|kospi\|kosdaq --concentration-rate <value> --include-current yes\|no --zone-count <n> --period-days 50\|100\|150\|200\|250\|300 --exchange KRX\|NXT\|ALL` | Implemented | `ka10025` | Yes | `read` | 매물대 집중 종목 through shared runtime facade. |
| `kiwoom stocks valuation-rank --kind low-pbr\|high-pbr\|low-per\|high-per\|low-roe\|high-roe --exchange KRX\|NXT\|ALL` | Implemented | `ka10026` | Yes | `read` | 고저 PER/PBR/ROE 순위 through shared runtime facade. |
| `kiwoom stocks open-change --basis open\|high\|low\|base --volume-condition <value> --market all\|kospi\|kosdaq --include-limit yes\|no --stock-condition <value> --credit-condition <value> --amount-condition <value> --direction top\|bottom --exchange KRX\|NXT\|ALL` | Implemented | `ka10028` | Yes | `read` | 시가 대비 등락률 through shared runtime facade. |
| `kiwoom stocks broker-volume-zone --code <code> --from <yyyymmdd> --to <yyyymmdd> --date-mode period\|start-end --position today\|previous --period-days 5\|10\|20\|40\|60\|120 --sort close\|date --broker-code <value> --exchange KRX\|NXT\|ALL` | Implemented | `ka10043` | Yes | `read` | 거래원 매물대 분석 through shared runtime facade. |
| `kiwoom stocks broker-instant-volume --broker-code <value> [--code <code>] --market all\|kospi\|kosdaq\|stock --quantity-condition <value> --price-condition <value> --exchange KRX\|NXT\|ALL` | Implemented | `ka10052` | Yes | `read` | 거래원 순간 거래량 through shared runtime facade. |
| `kiwoom stocks vi-triggered --market all\|kospi\|kosdaq --session all\|regular\|after-hours [--code <code>] --vi-type all\|static\|dynamic\|both --skip-stocks <value> --use-volume yes\|no --min-volume <value> --max-volume <value> --use-amount yes\|no --min-amount <value> --max-amount <value> --direction all\|rise\|fall --exchange KRX\|NXT\|ALL` | Implemented | `ka10054` | Yes | `read` | 변동성완화장치 발동 종목 through shared runtime facade. |
| `kiwoom stocks today-previous-fills --code <code> --day today\|previous` | Implemented | `ka10055` | Yes | `read` | 당일/전일 체결량 through shared runtime facade. |
| `kiwoom stocks investor-daily --from <yyyymmdd> --to <yyyymmdd> --side net-sell\|net-buy --market kospi\|kosdaq --investor individual\|foreign\|financial-investment\|investment-trust\|private-fund\|other-financial\|bank\|insurance\|pension\|state\|other-corporate\|institution --exchange KRX\|NXT\|ALL` | Implemented | `ka10058` | Yes | `read` | 투자자별 일별 매매 종목 through shared runtime facade. |
| `kiwoom stocks investor-by-stock --date <yyyymmdd> --code <code> --basis amount\|quantity --side net-buy\|buy\|sell --unit thousand\|share` | Implemented | `ka10059` | Yes | `read` | 종목별 투자자/기관 매매 through shared runtime facade. |
| `kiwoom stocks investor-by-stock-total --code <code> --from <yyyymmdd> --to <yyyymmdd> --basis amount\|quantity --side net-buy --unit thousand\|share` | Implemented | `ka10061` | Yes | `read` | 종목별 투자자/기관 매매 합계 through shared runtime facade. |
| `kiwoom stocks today-previous-trades --code <code> --day today\|previous --interval-type tick\|minute [--time <value>]` | Implemented | `ka10084` | Yes | `read` | 당일/전일 체결 through shared runtime facade. |
| `kiwoom stocks watchlist-info --codes <value>` | Implemented | `ka10095` | Yes | `read` | 관심종목 정보 through shared runtime facade. |
| `kiwoom stocks info-list --market-type kospi\|kosdaq\|kotc\|konex\|etn\|loss-limit-etn\|gold\|volatility-etn\|infrastructure\|elw\|mutual-fund\|warrant\|reit\|warrant-certificate\|etf\|high-yield-fund` | Implemented | `ka10099` | Yes | `read` | 종목정보 리스트 through shared runtime facade. |
| `kiwoom stocks info-detail --code <code>` | Implemented | `ka10100` | Yes | `read` | 종목정보 조회 through shared runtime facade. |
| `kiwoom stocks sector-codes --market kospi\|kosdaq\|kospi200\|kospi100\|krx100` | Implemented | `ka10101` | Yes | `read` | 업종코드 리스트 through shared runtime facade. |
| `kiwoom stocks member-firms` | Implemented | `ka10102` | Yes | `read` | 회원사 리스트 through shared runtime facade. |
| `kiwoom stocks program-net-top --side net-sell\|net-buy --basis amount\|quantity --market-code <value> --exchange KRX\|NXT\|ALL` | Implemented | `ka90003` | Yes | `read` | 프로그램 순매수 상위 50 through shared runtime facade. |
| `kiwoom stocks program-by-stock --date <yyyymmdd> --market-code <value> --exchange KRX\|NXT\|ALL` | Implemented | `ka90004` | Yes | `read` | 종목별 프로그램매매 현황 through shared runtime facade. |
| `kiwoom stocks credit-loanable [--credit-grade all\|a\|b\|c\|d\|e] [--market all\|kospi\|kosdaq] [--code <code>]` | Implemented | `kt20016` | Yes | `read` | 신용융자 가능 종목 through shared runtime facade. |
| `kiwoom stocks credit-loanable-check --code <code>` | Implemented | `kt20017` | Yes | `read` | 신용융자 가능 문의 through shared runtime facade. |
| `kiwoom quotes price --code <code>` | Implemented | `ka10007` | Yes | `read` | Current price summary through shared runtime facade. |
| `kiwoom quotes balance --date <yyyymmdd> --exchange KRX\|NXT\|ALL` | Implemented | `ka90006` | Yes | `read` | Program trading arbitrage balance trend through shared runtime facade. |
| `kiwoom quotes by-stock --code <code> --from <yyyymmdd> --to <yyyymmdd>` | Implemented | `ka10045` | Yes | `read` | 종목별 기관 매매 추이 through shared runtime facade. |
| `kiwoom quotes list --kind all\|warrant-security\|warrant-certificate` | Implemented | `ka10011` | Yes | `read` | 신주인수권 전체 시세 through shared runtime facade. |
| `kiwoom quotes gold-price --code <gold-code>` | Implemented | `ka50100` | Yes | `read` | 금현물 시세정보 through shared runtime facade. |
| `kiwoom quotes gold-fills --code <gold-code>` | Implemented | `ka50010` | Yes | `read` | 금현물 체결추이 through shared runtime facade. |
| `kiwoom quotes gold-daily --code <gold-code> --date <yyyymmdd>` | Implemented | `ka50012` | Yes | `read` | 금현물 일별추이 through shared runtime facade. |
| `kiwoom quotes gold-expected --code <gold-code>` | Implemented | `ka50087` | Yes | `read` | 금현물 예상체결 through shared runtime facade. |
| `kiwoom quotes multi-period --code <code>` | Implemented | `ka10005` | Yes | `read` | 주식 일/주/월/시/분 요약 시세 through shared runtime facade. |
| `kiwoom quotes intraday-minute --code <code>` | Implemented | `ka10006` | Yes | `read` | 주식 시분 시세 through shared runtime facade. |
| `kiwoom quotes institution-daily --from <yyyymmdd> --to <yyyymmdd> --side net-sell\|net-buy --market kospi\|kosdaq --exchange KRX\|NXT\|ALL` | Implemented | `ka10044` | Yes | `read` | 일별 기관 매매 종목 through shared runtime facade. |
| `kiwoom quotes strength-time --code <code>` | Implemented | `ka10046` | Yes | `read` | 체결강도 시간별 추이 through shared runtime facade. |
| `kiwoom quotes strength-daily --code <code>` | Implemented | `ka10047` | Yes | `read` | 체결강도 일별 추이 through shared runtime facade. |
| `kiwoom quotes investor-intraday --market all\|kospi\|kosdaq --basis combined --investor foreign\|institution\|investment-trust\|insurance\|bank\|pension\|state\|other-corporate --foreign-all yes\|no --same-net-buy yes\|no --exchange KRX\|NXT\|ALL` | Implemented | `ka10063` | Yes | `read` | 장중 투자자별 매매 through shared runtime facade. |
| `kiwoom quotes investor-after-close --market all\|kospi\|kosdaq --basis amount\|quantity --side net-buy\|buy\|sell --exchange KRX\|NXT\|ALL` | Implemented | `ka10066` | Yes | `read` | 장마감 후 투자자별 매매 through shared runtime facade. |
| `kiwoom quotes broker-trend --broker-code <value> --code <code> --from <yyyymmdd> --to <yyyymmdd>` | Implemented | `ka10078` | Yes | `read` | 증권사별 종목 매매 동향 through shared runtime facade. |
| `kiwoom quotes daily-price --code <code> --date <yyyymmdd> --basis quantity\|amount` | Implemented | `ka10086` | Yes | `read` | 일별 주가 through shared runtime facade. |
| `kiwoom quotes after-hours --code <code>` | Implemented | `ka10087` | Yes | `read` | 시간외 단일가 through shared runtime facade. |
| `kiwoom quotes program-time --date <yyyymmdd> --basis amount\|quantity --market-code <value> --interval-type tick\|minute --exchange KRX\|NXT\|ALL` | Implemented | `ka90005` | Yes | `read` | 프로그램매매 시간대별 추이 through shared runtime facade. |
| `kiwoom quotes program-cumulative --date <yyyymmdd> --basis amount\|quantity --market kospi\|kosdaq --exchange KRX\|NXT\|ALL` | Implemented | `ka90007` | Yes | `read` | 프로그램매매 누적 추이 through shared runtime facade. |
| `kiwoom quotes program-by-stock --basis amount\|quantity --code <code> --date <yyyymmdd>` | Implemented | `ka90008` | Yes | `read` | 종목 시간별 프로그램매매 추이 through shared runtime facade. |
| `kiwoom quotes program-daily --date <yyyymmdd> --basis amount\|quantity --market-code <value> --interval-type tick\|minute --exchange KRX\|NXT\|ALL` | Implemented | `ka90010` | Yes | `read` | 프로그램매매 일자별 추이 through shared runtime facade. |
| `kiwoom quotes stock-program-daily [--basis amount\|quantity] --code <code> [--date <yyyymmdd>]` | Implemented | `ka90013` | Yes | `read` | 종목 일별 프로그램매매 추이 through shared runtime facade. |
| `kiwoom orderbooks list --code <code>` | Implemented | `ka10004` | Yes | `read` | 호가 조회 through shared runtime facade. |
| `kiwoom orderbooks gold --code <gold-code> --tick 1\|3\|5\|10\|30` | Implemented | `ka50101` | Yes | `read` | 금현물 호가 through shared runtime facade. |
| `kiwoom candles daily --code <code> --date <yyyymmdd>` | Implemented | `ka10081` | Yes | `read` | Daily chart/candle data through shared runtime facade. |
| `kiwoom candles by-stock --date <yyyymmdd> --code <code> --basis amount\|quantity --side net-buy\|buy\|sell --unit thousand\|share` | Implemented | `ka10060` | Yes | `read` | 종목별 투자자/기관 차트 through shared runtime facade. |
| `kiwoom candles lookup --market all\|kospi\|kosdaq --basis amount\|quantity --side net-buy\|buy\|sell --code <code>` | Implemented | `ka10064` | Yes | `read` | 장중 투자자별 매매 차트 through shared runtime facade. |
| `kiwoom candles stock-tick --code <code> --interval <n>` | Implemented | `ka10079` | Yes | `read` | 주식 틱 차트 through shared runtime facade. |
| `kiwoom candles stock-minute --code <code> --interval <n>` | Implemented | `ka10080` | Yes | `read` | 주식 분봉 차트 through shared runtime facade. |
| `kiwoom candles stock-weekly --code <code> --date <yyyymmdd>` | Implemented | `ka10082` | Yes | `read` | 주식 주봉 차트 through shared runtime facade. |
| `kiwoom candles stock-monthly --code <code> --date <yyyymmdd>` | Implemented | `ka10083` | Yes | `read` | 주식 월봉 차트 through shared runtime facade. |
| `kiwoom candles stock-yearly --code <code> --date <yyyymmdd>` | Implemented | `ka10094` | Yes | `read` | 주식 년봉 차트 through shared runtime facade. |
| `kiwoom candles sector-tick --code <sector-code> --interval <n>` | Implemented | `ka20004` | Yes | `read` | 업종 틱 차트 through shared runtime facade. |
| `kiwoom candles sector-minute --code <sector-code> --interval <n>` | Implemented | `ka20005` | Yes | `read` | 업종 분봉 차트 through shared runtime facade. |
| `kiwoom candles sector-daily --code <sector-code> --date <yyyymmdd>` | Implemented | `ka20006` | Yes | `read` | 업종 일봉 차트 through shared runtime facade. |
| `kiwoom candles sector-weekly --code <sector-code> --date <yyyymmdd>` | Implemented | `ka20007` | Yes | `read` | 업종 주봉 차트 through shared runtime facade. |
| `kiwoom candles sector-monthly --code <sector-code> --date <yyyymmdd>` | Implemented | `ka20008` | Yes | `read` | 업종 월봉 차트 through shared runtime facade. |
| `kiwoom candles sector-yearly --code <sector-code> --date <yyyymmdd>` | Implemented | `ka20019` | Yes | `read` | 업종 년봉 차트 through shared runtime facade. |
| `kiwoom candles gold-tick --code <gold-code> --interval <n>` | Implemented | `ka50079` | Yes | `read` | 금현물 틱 차트 through shared runtime facade. |
| `kiwoom candles gold-minute --code <gold-code> --interval <n>` | Implemented | `ka50080` | Yes | `read` | 금현물 분봉 차트 through shared runtime facade. |
| `kiwoom candles gold-daily --code <gold-code> --date <yyyymmdd>` | Implemented | `ka50081` | Yes | `read` | 금현물 일봉 차트 through shared runtime facade. |
| `kiwoom candles gold-weekly --code <gold-code> --date <yyyymmdd>` | Implemented | `ka50082` | Yes | `read` | 금현물 주봉 차트 through shared runtime facade. |
| `kiwoom candles gold-monthly --code <gold-code> --date <yyyymmdd>` | Implemented | `ka50083` | Yes | `read` | 금현물 월봉 차트 through shared runtime facade. |
| `kiwoom candles gold-today-tick --code <gold-code> --interval <n>` | Implemented | `ka50091` | Yes | `read` | 금현물 당일 틱 차트 through shared runtime facade. |
| `kiwoom candles gold-today-minute --code <gold-code> --interval <n>` | Implemented | `ka50092` | Yes | `read` | 금현물 당일 분봉 차트 through shared runtime facade. |
| `kiwoom rankings orderbook-balance --market kospi\|kosdaq --sort net-buy-balance\|net-sell-balance\|buy-ratio\|sell-ratio --volume preopen\|10k\|50k\|100k --stock-condition all\|exclude-managed\|exclude-margin-100\|only-margin-100\|only-margin-40\|only-margin-30\|only-margin-20 --credit-condition all\|a\|b\|c\|d\|e\|all-financing --exchange KRX\|NXT\|ALL` | Implemented | `ka10020` | Yes | `read` | 호가잔량 상위 through shared runtime facade. |
| `kiwoom rankings orderbook-balance-spike --market kospi\|kosdaq --side buy-balance\|sell-balance --sort spike-quantity\|spike-rate --interval <n> --volume 1k\|5k\|10k\|50k\|100k --stock-condition all\|exclude-managed\|exclude-margin-100\|only-margin-100\|only-margin-40\|only-margin-30\|only-margin-20 --exchange KRX\|NXT\|ALL` | Implemented | `ka10021` | Yes | `read` | 호가잔량 급증 through shared runtime facade. |
| `kiwoom rankings balance-rate-spike --market kospi\|kosdaq --ratio buy-to-sell\|sell-to-buy --interval <n> --volume 5k\|10k\|50k\|100k --stock-condition all\|exclude-managed\|exclude-margin-100\|only-margin-100\|only-margin-40\|only-margin-30\|only-margin-20 --exchange KRX\|NXT\|ALL` | Implemented | `ka10022` | Yes | `read` | 잔량율 급증 through shared runtime facade. |
| `kiwoom rankings volume-spike --market all\|kospi\|kosdaq --sort spike-quantity\|spike-rate\|drop-quantity\|drop-rate --time-unit minute\|previous-day --volume-condition <value> [--time <n>] --stock-condition <value> --price-condition <value> --exchange KRX\|NXT\|ALL` | Implemented | `ka10023` | Yes | `read` | 거래량 급증 through shared runtime facade. |
| `kiwoom rankings previous-change-rate --market all\|kospi\|kosdaq --sort rise-rate\|rise-price\|fall-rate\|fall-price\|flat --volume all\|10k\|50k\|100k\|150k\|200k\|300k\|500k\|1000k --stock-condition all\|exclude-managed\|exclude-preferred\|exclude-managed-preferred\|exclude-margin-100\|only-margin-100\|only-margin-40\|only-margin-30\|only-margin-20\|exclude-liquidation\|only-margin-50\|only-margin-60\|exclude-etf\|exclude-spac\|exclude-etf-etn --credit-condition all\|a\|b\|c\|d\|e\|all-financing --include-limit yes\|no --price-condition all\|under-1k\|1k-2k\|2k-5k\|5k-10k\|over-10k\|over-1k\|under-10k --amount-condition <value> --exchange KRX\|NXT\|ALL` | Implemented | `ka10027` | Yes | `read` | 전일대비 등락률 상위 through shared runtime facade. |
| `kiwoom rankings list-fills --market all\|kospi\|kosdaq --sort rise-rate\|rise-price\|flat\|fall-rate\|fall-price\|volume\|upper-limit\|lower-limit --volume all\|1k\|3k\|5k\|10k\|50k\|100k --stock-condition all\|exclude-managed\|exclude-preferred\|exclude-managed-preferred\|exclude-margin-100\|only-margin-100\|only-margin-40\|only-margin-30\|only-margin-20\|exclude-liquidation\|only-margin-50\|only-margin-60\|exclude-etf\|exclude-spac\|exclude-etf-etn --credit-condition all\|a\|b\|c\|d\|exclude-overlimit\|e\|short\|all-financing --price-condition all\|under-1k\|1k-2k\|2k-5k\|5k-10k\|over-10k\|over-1k\|under-10k --exchange KRX\|NXT\|ALL` | Implemented | `ka10029` | Yes | `read` | 예상체결 등락률 상위 through shared runtime facade. |
| `kiwoom rankings today-volume --market all\|kospi\|kosdaq --sort volume\|turnover\|amount --stock-condition <value> --credit-type all\|all-financing\|a\|b\|c\|d\|short --volume-condition <value> --price-condition <value> --amount-condition <value> --session all\|regular\|pre-open\|after-hours --exchange KRX\|NXT\|ALL` | Implemented | `ka10030` | Yes | `read` | 당일 거래량 상위 through shared runtime facade. |
| `kiwoom rankings previous-volume --market all\|kospi\|kosdaq --kind volume\|amount --rank-from <n> --rank-to <n> --exchange KRX\|NXT\|ALL` | Implemented | `ka10031` | Yes | `read` | 전일 거래량 상위 through shared runtime facade. |
| `kiwoom rankings amount --market all\|kospi\|kosdaq --include-managed yes\|no --exchange KRX\|NXT\|ALL` | Implemented | `ka10032` | Yes | `read` | 거래대금 상위 through shared runtime facade. |
| `kiwoom rankings credit-ratio --market all\|kospi\|kosdaq --volume-condition <value> --stock-condition all\|exclude-managed\|exclude-margin-100\|only-margin-100\|only-margin-40\|only-margin-30\|only-margin-20 --include-limit yes\|no --credit-condition all\|a\|b\|c\|d\|e\|all-financing --exchange KRX\|NXT\|ALL` | Implemented | `ka10033` | Yes | `read` | 신용비율 상위 through shared runtime facade. |
| `kiwoom rankings foreign-period-trades --market all\|kospi\|kosdaq --side net-sell\|net-buy\|net-trade --period today\|previous\|5d\|10d\|20d\|60d --exchange KRX\|NXT\|ALL` | Implemented | `ka10034` | Yes | `read` | 외인 기간별 매매 상위 through shared runtime facade. |
| `kiwoom rankings foreign-continuous-net --market all\|kospi\|kosdaq --side net-sell\|net-buy --base-date today\|previous --exchange KRX\|NXT\|ALL` | Implemented | `ka10035` | Yes | `read` | 외인 연속 순매매 상위 through shared runtime facade. |
| `kiwoom rankings foreign-limit-usage --market all\|kospi\|kosdaq --period today\|previous\|5d\|10d\|20d\|60d --exchange KRX\|NXT\|ALL` | Implemented | `ka10036` | Yes | `read` | 외인 한도소진율 증가 상위 through shared runtime facade. |
| `kiwoom rankings foreign-broker-trades --market all\|kospi\|kosdaq --period today\|previous\|5d\|10d\|20d\|60d --side net-buy\|net-sell\|buy\|sell --sort amount\|quantity --exchange KRX\|NXT\|ALL` | Implemented | `ka10037` | Yes | `read` | 외국계 창구 매매 상위 through shared runtime facade. |
| `kiwoom rankings broker-by-stock --code <code> --from <yyyymmdd> --to <yyyymmdd> --side net-sell\|net-buy [--period previous\|5d\|10d\|20d\|40d\|60d\|120d]` | Implemented | `ka10038` | Yes | `read` | 종목별 증권사 순위 through shared runtime facade. |
| `kiwoom rankings broker-trades --broker-code <value> --volume-condition <value> --side net-buy\|net-sell --period previous\|5d\|10d\|60d --exchange KRX\|NXT\|ALL` | Implemented | `ka10039` | Yes | `read` | 증권사별 매매 상위 through shared runtime facade. |
| `kiwoom rankings stock-main-brokers --code <code>` | Implemented | `ka10040` | Yes | `read` | 당일 주요 거래원 through shared runtime facade. |
| `kiwoom rankings net-buy-brokers --code <code> [--from <yyyymmdd>] [--to <yyyymmdd>] --date-mode period\|start-end --point today\|previous [--period 5d\|10d\|20d\|40d\|60d\|120d] --sort close\|date` | Implemented | `ka10042` | Yes | `read` | 순매수 거래원 순위 through shared runtime facade. |
| `kiwoom rankings top-exit-brokers --code <code>` | Implemented | `ka10053` | Yes | `read` | 당일 상위 이탈원 through shared runtime facade. |
| `kiwoom rankings same-net-trades --from <yyyymmdd> [--to <yyyymmdd>] --market all\|kospi\|kosdaq --side net-buy\|net-sell --basis quantity\|amount --unit share\|thousand --exchange KRX\|NXT\|ALL` | Implemented | `ka10062` | Yes | `read` | 동일 순매매 순위 through shared runtime facade. |
| `kiwoom rankings investor-intraday --side net-buy\|net-sell --market all\|kospi\|kosdaq --investor foreign\|foreign-broker\|financial-investment\|investment-trust\|other-financial\|bank\|insurance\|pension\|state\|other-corporate\|institution [--basis amount\|quantity]` | Implemented | `ka10065` | Yes | `read` | 장중 투자자별 매매 상위 through shared runtime facade. |
| `kiwoom rankings after-hours-change-rate --market all\|kospi\|kosdaq --sort rise-rate\|rise-price\|fall-rate\|fall-price\|flat --stock-condition <value> --volume <value> --credit-condition all\|a\|b\|c\|d\|exclude-overlimit\|e\|short\|all-financing --amount-condition <value>` | Implemented | `ka10098` | Yes | `read` | 시간외 단일가 등락율 순위 through shared runtime facade. |
| `kiwoom rankings foreign-institution-trades --market all\|kospi\|kosdaq --basis amount\|quantity --include-date yes\|no [--date <yyyymmdd>] --exchange KRX\|NXT\|ALL` | Implemented | `ka90009` | Yes | `read` | 외국인기관 매매 상위 through shared runtime facade. |
| `kiwoom sectors program --code <code>` | Implemented | `ka10010` | Yes | `read` | 종목 기준 업종 프로그램 매매 through shared runtime facade. |
| `kiwoom sectors investor-flows --market kospi\|kosdaq --basis amount\|quantity --exchange KRX\|NXT\|ALL` | Implemented | `ka10051` | Yes | `read` | 업종별 투자자 순매수 through shared runtime facade. |
| `kiwoom sectors price --market kospi\|kosdaq\|kospi200 --code <sector-code>` | Implemented | `ka20001` | Yes | `read` | 업종 현재가 through shared runtime facade. |
| `kiwoom sectors stocks --market kospi\|kosdaq\|kospi200 --code <sector-code> --exchange KRX\|NXT\|ALL` | Implemented | `ka20002` | Yes | `read` | 업종별 주가 through shared runtime facade. |
| `kiwoom sectors indices --code <sector-code>` | Implemented | `ka20003` | Yes | `read` | 전업종 지수 through shared runtime facade. |
| `kiwoom sectors daily --market kospi\|kosdaq\|kospi200 --code <sector-code>` | Implemented | `ka20009` | Yes | `read` | 업종 현재가 일별 데이터 through shared runtime facade. |
| `kiwoom etfs info --code <code>` | Implemented | `ka40002` | Yes | `read` | ETF 종목정보 through shared runtime facade. |
| `kiwoom etfs daily --code <code>` | Implemented | `ka40003` | Yes | `read` | ETF 일별추이 through shared runtime facade. |
| `kiwoom etfs profit --code <code> --index-code <code> --period week\|month\|six-months\|year` | Implemented | `ka40001` | Yes | `read` | ETF 수익률 through shared runtime facade. |
| `kiwoom etfs list --tax-type <type> --nav-compare <mode> --manager <code> --taxable <mode> --tracking-index <code> --exchange KRX\|NXT\|ALL` | Implemented | `ka40004` | Yes | `read` | ETF 전체 시세 through shared runtime facade. |
| `kiwoom etfs intraday-trend --code <code>` | Implemented | `ka40006` | Yes | `read` | ETF 시간대별 추이 through shared runtime facade. |
| `kiwoom etfs intraday-fills --code <code>` | Implemented | `ka40007` | Yes | `read` | ETF 시간대별 체결 through shared runtime facade. |
| `kiwoom etfs daily-fills --code <code>` | Implemented | `ka40008` | Yes | `read` | ETF 일자별 체결 through shared runtime facade. |
| `kiwoom etfs nav --code <code>` | Implemented | `ka40009` | Yes | `read` | ETF NAV 관련 정보 through shared runtime facade. |
| `kiwoom etfs foreign-trend --code <code>` | Implemented | `ka40010` | Yes | `read` | ETF 외국인 순매수 추이 through shared runtime facade. |
| `kiwoom elws daily --code <code>` | Implemented | `ka10048` | Yes | `read` | ELW 일별 민감도 지표 through shared runtime facade. |
| `kiwoom elws balance --code <code> --date <yyyymmdd>` | Implemented | `ka30003` | Yes | `read` | ELW LP 보유 일별 추이 through shared runtime facade. |
| `kiwoom elws conditions --issuer-code <code> --underlying-code <code> --right-type <kind> --lp-code <code> --sort <sort>` | Implemented | `ka30005` | Yes | `read` | ELW 조건검색 through shared runtime facade. |
| `kiwoom elws sensitivity --code <code>` | Implemented | `ka10050` | Yes | `read` | ELW 민감도 지표 through shared runtime facade. |
| `kiwoom elws price-move --direction rise\|fall --time-unit minute\|day --time <n>` | Implemented | `ka30001` | Yes | `read` | ELW 가격 급등락 through shared runtime facade. |
| `kiwoom elws broker-net --issuer-code <code> --side net-buy\|net-sell --period <period>` | Implemented | `ka30002` | Yes | `read` | 거래원별 ELW 순매매 상위 through shared runtime facade. |
| `kiwoom elws divergence --issuer-code <code> --underlying-code <code> --right-type <kind> --lp-code <code>` | Implemented | `ka30004` | Yes | `read` | ELW 괴리율 through shared runtime facade. |
| `kiwoom elws change-rank --sort <sort> --right-type <kind> --include-ended yes\|no` | Implemented | `ka30009` | Yes | `read` | ELW 등락율 순위 through shared runtime facade. |
| `kiwoom elws balance-rank --sort buy-balance\|sell-balance --right-type <kind> --include-ended yes\|no` | Implemented | `ka30010` | Yes | `read` | ELW 잔량 순위 through shared runtime facade. |
| `kiwoom elws proximity --code <code>` | Implemented | `ka30011` | Yes | `read` | ELW 근접율 through shared runtime facade. |
| `kiwoom elws details --code <code>` | Implemented | `ka30012` | Yes | `read` | ELW 종목 상세정보 through shared runtime facade. |
| `kiwoom investors by-stock --code <code>` | Implemented | `ka10008` | Yes | `read` | 종목별 외국인 매매동향 through shared runtime facade. |
| `kiwoom investors lookup --code <code>` | Implemented | `ka10009` | Yes | `read` | 종목별 기관 정보 through shared runtime facade. |
| `kiwoom investors trend --period <period> --market kospi\|kosdaq --side net-buy --target stock\|sector --basis amount\|quantity --exchange KRX\|NXT\|ALL` | Implemented | `ka10131` | Yes | `read` | 기관/외국인 연속매매 현황 through shared runtime facade. |
| `kiwoom investors gold-status` | Implemented | `ka52301` | Yes | `read` | 금현물 투자자 현황 through shared runtime facade. |
| `kiwoom short-selling trend --code <code> --from <yyyymmdd> --to <yyyymmdd>` | Implemented | `ka10014` | Yes | `read` | 종목별 공매도 추이 through shared runtime facade. |
| `kiwoom securities-lending by-stock --code <code>` | Implemented | `ka20068` | Yes | `read` | 종목별 대차거래 추이 through shared runtime facade. |
| `kiwoom securities-lending trend` | Implemented | `ka10068` | Yes | `read` | 대차거래 추이 through shared runtime facade. |
| `kiwoom securities-lending list --from <yyyymmdd> --market kospi\|kosdaq` | Implemented | `ka10069` | Yes | `read` | 대차거래 상위 10종목 through shared runtime facade. |
| `kiwoom securities-lending lookup --date <yyyymmdd> --market kospi\|kosdaq` | Implemented | `ka90012` | Yes | `read` | 대차거래 내역 through shared runtime facade. |
| `kiwoom themes lookup --kind all\|theme\|stock --days <n> --sort profit-top\|profit-bottom\|change-top\|change-bottom --exchange KRX\|NXT\|ALL` | Implemented | `ka90001` | Yes | `read` | 테마 그룹 조회 through shared runtime facade. |
| `kiwoom themes by-stock --code <code> --exchange KRX\|NXT\|ALL` | Implemented | `ka90002` | Yes | `read` | 테마 구성 종목 through shared runtime facade. |
| `kiwoom accounts balance` | Planned | `kt00005` | Yes | `account_read` | 체결잔고 / holdings. |
| `kiwoom accounts pnl` | Planned | `ka10072`, `ka10073`, `ka10074` | Yes | `account_read` | Realized PnL views. |
| `kiwoom accounts withdrawable` | Planned | `kt00010` or mapped response fields | Yes | `account_read` | Inquiry only; not a withdrawal execution command. |
| `kiwoom streams conditions-list` | Implemented | `ka10171` | Yes | `read` | 조건검색 목록조회 through shared WebSocket runtime facade. 조건검색식 생성/수정은 영웅문 HTS에서 수행; CLI는 저장식 조회/사용만 한다. |
| `kiwoom streams conditions-search [--seq <value>] --exchange KRX\|NXT\|ALL [--cont yes\|no] [--next-key <value>]` | Implemented | `ka10172` | Yes | `read` | 조건검색 요청 일반; command internally runs `CNSRLST` before `CNSRREQ`. 조건검색식 생성/수정은 영웅문 HTS에서 수행. |
| `kiwoom streams conditions-subscribe [--seq <value>] --exchange KRX\|NXT\|ALL [--count <n>] [--duration <seconds>] [--check]` | Implemented | `ka10173` | Yes | `read` | 조건검색 요청 실시간; command internally runs `CNSRLST`, `CNSRREQ`, realtime collection, and `CNSRCLR`. 조건검색식 생성/수정은 영웅문 HTS에서 수행. |
| `kiwoom streams conditions-unsubscribe [--seq <value>] [--exchange KRX\|NXT\|ALL]` | Implemented | `ka10174` | Yes | `read` | 조건검색 실시간 해제; one-shot CLI performs same-session register-and-clear proof. 조건검색식 생성/수정은 영웅문 HTS에서 수행. |
| `kiwoom streams order-fills [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] [--code <value>] [--codes <codes>] [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `00` | Yes | `account_read` | 주문체결 with bounded wait and account redaction; order numbers are shown. |
| `kiwoom streams balance [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] [--code <value>] [--codes <codes>] [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `04` | Yes | `account_read` | 잔고 with bounded wait and account redaction; order numbers are shown. |
| `kiwoom streams momentum [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0A` | Yes | `read` | 주식기세 through shared bounded WebSocket runtime facade. |
| `kiwoom streams trades [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0B` | Yes | `read` | 주식체결 through shared bounded WebSocket runtime facade. |
| `kiwoom streams best-quotes [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0C` | Yes | `read` | 주식우선호가 through shared bounded WebSocket runtime facade. |
| `kiwoom streams orderbook [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0D` | Yes | `read` | 주식호가잔량 through shared bounded WebSocket runtime facade. |
| `kiwoom streams after-hours-orderbook [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0E` | Yes | `read` | 주식시간외호가 through shared bounded WebSocket runtime facade. |
| `kiwoom streams brokers [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0F` | Yes | `read` | 주식당일거래원 through shared bounded WebSocket runtime facade. |
| `kiwoom streams etf-nav [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0G` | Yes | `read` | ETF NAV through shared bounded WebSocket runtime facade. |
| `kiwoom streams expected-fills [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0H` | Yes | `read` | 주식예상체결 through shared bounded WebSocket runtime facade. |
| `kiwoom streams gold-conversion [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0I` | Yes | `read` | 국제금환산가격 through shared bounded WebSocket runtime facade. |
| `kiwoom streams sector-index [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0J` | Yes | `read` | 업종지수 through shared bounded WebSocket runtime facade. |
| `kiwoom streams sector-change [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0U` | Yes | `read` | 업종등락 through shared bounded WebSocket runtime facade. |
| `kiwoom streams stock-info [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0g` | Yes | `read` | 주식종목정보 through shared bounded WebSocket runtime facade. |
| `kiwoom streams elw-theory [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0m` | Yes | `read` | ELW 이론가 through shared bounded WebSocket runtime facade. |
| `kiwoom streams market-open [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] [--code <value>] [--codes <codes>] [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0s` | Yes | `read` | 장시작시간 through shared bounded WebSocket runtime facade. |
| `kiwoom streams elw-indicator [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0u` | Yes | `read` | ELW 지표 through shared bounded WebSocket runtime facade. |
| `kiwoom streams program-trades [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] (--code <value> | --codes <codes>) [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `0w` | Yes | `read` | 종목프로그램매매 through shared bounded WebSocket runtime facade. |
| `kiwoom streams vi [--action subscribe\|unsubscribe] [--group <n>] [--refresh yes\|no] [--code <value>] [--codes <codes>] [--count <n>] [--duration <seconds>] [--watch] [--check] [--named] [--output <path>]` | Implemented | `1h` | Yes | `read` | VI발동/해제 through shared bounded WebSocket runtime facade. |
| `kiwoom accounts list` | Implemented | `ka00001` | Yes | `account_read` | 계좌번호조회 through shared runtime facade with account redaction. |
| `kiwoom accounts daily-balance-return --date <yyyymmdd>` | Implemented | `ka01690` | Yes | `account_read` | 일별잔고수익률 through shared runtime facade with account redaction. |
| `kiwoom accounts realized-profit-stock-daily [--code <code>] --date <yyyymmdd>` | Implemented | `ka10072` | Yes | `account_read` | 일자별 종목별 실현손익(일자) through shared runtime facade with account redaction. |
| `kiwoom accounts realized-profit-period-stock [--code <code>] --from <yyyymmdd> --to <yyyymmdd>` | Implemented | `ka10073` | Yes | `account_read` | 일자별 종목별 실현손익(기간) through shared runtime facade with account redaction. |
| `kiwoom accounts realized-profit-daily --from <yyyymmdd> --to <yyyymmdd>` | Implemented | `ka10074` | Yes | `account_read` | 일자별 실현손익 through shared runtime facade with account redaction. |
| `kiwoom accounts realized-profit-today-detail --code <code>` | Implemented | `ka10077` | Yes | `account_read` | 당일 실현손익 상세 through shared runtime facade with account redaction. |
| `kiwoom accounts return-rate --exchange ALL\|KRX\|NXT` | Implemented | `ka10085` | Yes | `account_read` | 계좌수익률 through shared runtime facade with account redaction. |
| `kiwoom accounts day-trading-log [--date <yyyymmdd>] --sell-scope same-day-buy-sell\|all-sells --cash-credit all\|cash\|credit` | Implemented | `ka10170` | Yes | `account_read` | 당일매매일지 through shared runtime facade with account redaction. |
| `kiwoom accounts cash --cash-basis estimated\|normal` | Implemented | `kt00001` | Yes | `account_read` | 예수금상세현황 through shared runtime facade with account redaction. |
| `kiwoom accounts estimated-assets-daily --from <yyyymmdd> --to <yyyymmdd>` | Implemented | `kt00002` | Yes | `account_read` | 일별 추정예탁자산 현황 through shared runtime facade with account redaction. |
| `kiwoom accounts assets --include-delisted yes\|no` | Implemented | `kt00003` | Yes | `account_read` | 추정자산조회 through shared runtime facade with account redaction. |
| `kiwoom accounts valuation --include-delisted yes\|no --exchange KRX\|NXT` | Implemented | `kt00004` | Yes | `account_read` | 계좌평가현황 through shared runtime facade with account redaction. |
| `kiwoom accounts fill-balance --exchange KRX\|NXT` | Implemented | `kt00005` | Yes | `account_read` | 체결잔고 through shared runtime facade with account redaction. |
| `kiwoom accounts order-fill-detail [--date <yyyymmdd>] (--order order\|reverse \| --fill-status open\|filled) --asset-kind all\|stock\|bond --side all\|sell\|buy [--code <code>] [--order-id <id>] --exchange ALL\|KRX\|NXT\|SOR` | Implemented | `kt00007` | Yes | `account_read` | 계좌별 주문체결내역 상세 through shared runtime facade with account redaction. |
| `kiwoom accounts next-settlement [--settlement-id <value>]` | Implemented | `kt00008` | Yes | `account_read` | 계좌별 익일결제 예정내역 through shared runtime facade with account redaction. |
| `kiwoom accounts order-fill-status [--date <yyyymmdd>] --asset-kind all\|stock\|bond --market all\|kospi\|kosdaq\|otcbb\|ecn --side all\|sell\|buy --fill-status all\|filled [--code <code>] [--order-id <id>] --exchange ALL\|KRX\|NXT\|SOR` | Implemented | `kt00009` | Yes | `account_read` | 계좌별 주문체결 현황 through shared runtime facade with account redaction. |
| `kiwoom accounts credit-margin --code <code> [--price <price>]` | Implemented | `kt00012` | Yes | `account_read` | 신용보증금율별 주문가능수량 through shared runtime facade with account redaction. |
| `kiwoom accounts margin-details` | Implemented | `kt00013` | Yes | `account_read` | 증거금 세부내역 through shared runtime facade with account redaction. |
| `kiwoom accounts transaction-history --from <yyyymmdd> --to <yyyymmdd> --kind <value> [--code <value>] [--currency <value>] --product all\|domestic-stock\|fund\|overseas-stock\|financial-product [--overseas-exchange <value>] --exchange ALL\|KRX\|NXT` | Implemented | `kt00015` | Yes | `account_read` | 위탁종합 거래내역 through shared runtime facade with account redaction. |
| `kiwoom accounts daily-return-detail --from <yyyymmdd> --to <yyyymmdd>` | Implemented | `kt00016` | Yes | `account_read` | 일별 계좌수익률 상세현황 through shared runtime facade with account redaction. |
| `kiwoom accounts today-status` | Implemented | `kt00017` | Yes | `account_read` | 계좌별 당일현황 through shared runtime facade with account redaction. |
| `kiwoom accounts holdings --basis total\|individual --exchange KRX\|NXT` | Implemented | `kt00018` | Yes | `account_read` | 계좌평가잔고내역 through shared runtime facade with account redaction. |
| `kiwoom accounts gold-balance` | Implemented | `kt50020` | Yes | `account_read` | 금현물 잔고확인 through shared runtime facade with account redaction. |
| `kiwoom accounts gold-cash` | Implemented | `kt50021` | Yes | `account_read` | 금현물 예수금 through shared runtime facade with account redaction. |
| `kiwoom accounts gold-all-order-fills --date <yyyymmdd> [--order order\|reverse] --market-deal <value> --asset-kind all\|stock\|bond --side all\|sell\|buy [--code <value>] [--order-id <id>] [--exchange ALL\|KRX\|NXT\|SOR]` | Implemented | `kt50030` | Yes | `account_read` | 금현물 주문체결 전체조회 through shared runtime facade with account redaction. |
| `kiwoom accounts gold-order-fills [--date <yyyymmdd>] (--order order\|reverse \| --fill-status open\|filled) --asset-kind all\|stock\|bond --side all\|sell\|buy [--code <value>] [--order-id <id>] --exchange ALL\|KRX\|NXT\|SOR` | Implemented | `kt50031` | Yes | `account_read` | 금현물 주문체결 조회 through shared runtime facade with account redaction. |
| `kiwoom accounts gold-transactions [--from <yyyymmdd>] [--to <yyyymmdd>] [--kind all\|deposit-withdrawal\|release\|trade\|buy\|sell\|deposit\|withdrawal] [--code <value>]` | Implemented | `kt50032` | Yes | `account_read` | 금현물 거래내역 through shared runtime facade with account redaction. |
| `kiwoom accounts gold-open-orders --date <yyyymmdd> [--order order\|reverse] --market-deal <value> --asset-kind all\|stock\|bond --side all\|sell\|buy [--code <value>] [--order-id <id>] [--exchange ALL\|KRX\|NXT\|SOR]` | Implemented | `kt50075` | Yes | `account_read` | 금현물 미체결 조회 through shared runtime facade with account redaction. |
| `kiwoom orders chance --code <code> --side sell\|buy --price <price>` | Implemented | `kt00010` | Yes | `account_read` | 주문/인출 가능금액 조회 through shared runtime facade and account redaction. |
| `kiwoom orders margin --code <code>` | Implemented | `kt00011` | Yes | `account_read` | 증거금율별 주문가능수량 조회 through shared runtime facade and account redaction. |
| `kiwoom orders list-open --stock-scope all\|stock --side all\|sell\|buy --exchange ALL\|KRX\|NXT` | Implemented | `ka10075` | Yes | `account_read` | 미체결 주문 조회 through shared runtime facade and account redaction; order numbers are shown. |
| `kiwoom orders list-fills --stock-scope all\|stock --side all\|sell\|buy --exchange ALL\|KRX\|NXT` | Implemented | `ka10076` | Yes | `account_read` | 체결 주문 조회 through shared runtime facade and account redaction; order numbers are shown. |
| `kiwoom orders open-detail --order-id <id>` | Implemented | `ka10088` | Yes | `account_read` | 미체결 분할주문 상세 조회 through shared runtime facade and account redaction; order numbers are shown. |
<!-- Superseded design note retained for history: `kiwoom streams order-events` became the implemented `kiwoom streams order-fills` guarded stream. -->
| `kiwoom orders buy [--exchange KRX\|NXT\|SOR] --code <code> --qty <n> [--price <price>] --order-type limit\|market [--confirm]` | Implemented | `kt10000` | Yes, submits only with --confirm | `order_write` | 주식 매수주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders sell [--exchange KRX\|NXT\|SOR] --code <code> --qty <n> [--price <price>] --order-type limit\|market [--confirm]` | Implemented | `kt10001` | Yes, submits only with --confirm | `order_write` | 주식 매도주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders modify [--exchange KRX\|NXT\|SOR] --order-id <id> --code <code> --qty <n> --price <price> [--confirm]` | Implemented | `kt10002` | Yes, submits only with --confirm | `order_write` | 주식 정정주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders cancel [--exchange KRX\|NXT\|SOR] --order-id <id> --code <code> --qty <n> [--confirm]` | Implemented | `kt10003` | Yes, submits only with --confirm | `order_write` | 주식 취소주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders credit-buy --exchange KRX\|NXT\|SOR --code <code> --qty <n> [--price <price>] --order-type limit\|market\|conditional-limit\|after-hours-close\|pre-open\|after-hours-single\|best-limit\|top-priority\|limit-ioc\|market-ioc\|best-ioc\|limit-fok\|market-fok\|best-fok\|stop-limit\|mid\|mid-ioc\|mid-fok [--condition-price <price>] [--confirm]` | Implemented | `kt10006` | Yes, submits only with --confirm | `order_write` | 신용 매수주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders credit-sell --exchange KRX\|NXT\|SOR --code <code> --qty <n> [--price <price>] --order-type limit\|market\|conditional-limit\|after-hours-close\|pre-open\|after-hours-single\|best-limit\|top-priority\|limit-ioc\|market-ioc\|best-ioc\|limit-fok\|market-fok\|best-fok\|stop-limit\|mid\|mid-ioc\|mid-fok --credit-deal financing\|financing-all [--loan-date <yyyymmdd>] [--condition-price <price>] [--confirm]` | Implemented | `kt10007` | Yes, submits only with --confirm | `order_write` | 신용 매도주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders credit-modify --exchange KRX\|NXT\|SOR --order-id <id> --code <code> --qty <n> --price <price> [--condition-price <price>] [--confirm]` | Implemented | `kt10008` | Yes, submits only with --confirm | `order_write` | 신용 정정주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders credit-cancel --exchange KRX\|NXT\|SOR --order-id <id> --code <code> --qty <n> [--confirm]` | Implemented | `kt10009` | Yes, submits only with --confirm | `order_write` | 신용 취소주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders gold-buy --code <value> --qty <n> [--price <price>] --order-type limit\|limit-ioc\|limit-fok [--confirm]` | Implemented | `kt50000` | Yes, submits only with --confirm | `order_write` | 금현물 매수주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders gold-sell --code <value> --qty <n> [--price <price>] --order-type limit\|limit-ioc\|limit-fok [--confirm]` | Implemented | `kt50001` | Yes, submits only with --confirm | `order_write` | 금현물 매도주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders gold-modify --code <value> --order-id <id> --qty <n> --price <price> [--confirm]` | Implemented | `kt50002` | Yes, submits only with --confirm | `order_write` | 금현물 정정주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| `kiwoom orders gold-cancel --order-id <id> --code <value> --qty <n> [--confirm]` | Implemented | `kt50003` | Yes, submits only with --confirm | `order_write` | 금현물 취소주문 request; submits to the real endpoint only with `--confirm`, otherwise shows 미전송 주문 확인 output. |
| 해외주식 기타 APIs | Planned/Preview-only | `ust30130` through `ust71920` family | Mixed | `review_required` | 조회성 rows remain planned; write-like rows start preview-only until semantics and safety are approved. |
| `kiwoom deposits list` | Blocked | Overseas/dividend candidates exist; domestic semantics TBD | Yes | `account_read` | Do not expose until mapped and reviewed. |
| `kiwoom withdraws create` | Blocked | None approved | Yes | Stronger than `order_write` | Do not expose without explicit supported API and safety policy. |

## Feature Principles

- Agent-default commands should be predictable resource commands, not API ID
  wrappers.
- `kiwoom spec search` is a discovery fallback, not the primary operation path.
- Read-only market data should be easy to call and easy to parse.
- Account output must redact account numbers in human/debug output modes
  (order numbers are shown as operational identifiers).
- Write commands must require explicit confirmation and must not be verified
  with mocks or simulated Kiwoom responses.
- Unsupported deposit/withdraw execution should be documented as blocked, not
  guessed.
