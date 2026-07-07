# Command Contracts

This document describes the intended command contracts for `kiwoom_cli/`. It is
written in the same shape as agent-facing reference files: each command lists
auth, safety, API candidate, arguments, and example usage.

Implemented commands reflect current CLI behavior. Planned commands define the
target contract and must be backed by curated maps before implementation.

## Foundation

### `kiwoomcli setup`

Status: Implemented

Purpose: Run interactive credential/profile setup and verify shared runtime
access.

Example:

```sh
kiwoomcli setup
kiwoomcli setup --alias demo-main --mode demo
```

### `kiwoomcli auth status`

Status: Implemented

Purpose: Show credential source, token cache state, token expiry, and next auth
action.

| Option | Required | Type | Description |
| --- | :---: | --- | --- |
| `--profile` | No | `account_alias` | Profile alias to inspect. |
| `--mode` | No | `mode` | Direct mode when profile is not used. |

Example:

```sh
kiwoomcli auth status --profile demo-main
kiwoomcli auth status --mode demo
```

Recovery note: if a saved alias still appears in `kiwoomcli auth list` but shows
missing credentials, an expired/non-reusable token, and cannot call now, restore
the same alias with `kiwoomcli auth login --alias '<alias>' --mode demo|real`, then
verify with `kiwoomcli auth status --profile '<alias>'`.

### `kiwoomcli spec search`

Status: Implemented

Purpose: Find raw Kiwoom API specs by API ID, API name, request field, response
field, menu path, or URL.

| Argument | Required | Type | Description |
| --- | :---: | --- | --- |
| `query` | Yes | `text` | Search term. |
| `--limit` | No | `positive_int` | Maximum number of results. |

Example:

```sh
kiwoomcli spec search ka10001 --limit 3
kiwoomcli spec search 예수금 --limit 5
```

### `kiwoomcli spec show`

Status: Implemented

Auth required: no
Safety: `read`
Source: `kiwoom_api_spec.json`

| Option | Required | Source field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `<api-id>` | Yes | `meta.API ID` | `api_id` | | Local Kiwoom API ID. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `yaml` | Output format. |

Example:

```sh
kiwoomcli spec show ka10001
```

### `kiwoomcli spec groups`

Status: Implemented

Auth required: no
Safety: `read`
Source: `kiwoom_api_spec.json`

| Option | Required | Source field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `yaml` | Output format. |

### `kiwoomcli spec apis`

Status: Implemented

Auth required: no
Safety: `read`
Source: `kiwoom_api_spec.json`

| Option | Required | Source field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--group` | No | `meta.메뉴 위치` | `text` | | Filter APIs whose menu path contains this text. |
| `--limit` | No | output limit | `positive_int` | | Maximum API summaries. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `yaml` | Output format. |

## Market Data

### `kiwoomcli domestic stocks info`

Status: Implemented

Auth required: no network in preview-only mode
Safety: `read`
Candidate API: `ka10001`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks info --code 005930 --format json
```

### `kiwoomcli domestic stocks trend`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10013`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--date` | Yes | `dt` | `date_yyyymmdd` | | Query date. |
| `--kind` | Yes | `qry_tp` | `market` | `financing`, `loan` | Query kind mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks trend --code 005930 --date 20241104 --kind financing --format json
```

### `kiwoomcli domestic stocks realtime-rank`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka00198`

Purpose: 실시간 종목 조회 순위.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--window` | Yes | `qry_tp` | `market` | `1m`, `10m`, `1h`, `today`, `30s` | 조회 기간. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks realtime-rank --window 1m --format json
```

### `kiwoomcli domestic stocks brokers`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10002`

Purpose: 주식 거래원.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks brokers --code 005930 --format json
```

### `kiwoomcli domestic stocks fills`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10003`

Purpose: 체결 정보.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks fills --code 005930 --format json
```

### `kiwoomcli domestic stocks daily-trades`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10015`

Purpose: 일별 거래 상세.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks daily-trades --code 005930 --from 20260529 --format json
```

### `kiwoomcli domestic stocks new-high-low`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10016`

Purpose: 신고가/신저가.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분. |
| `--kind` | Yes | `ntl_tp` | `market` | `new-high`, `new-low` | 신고/신저 구분. |
| `--price-basis` | Yes | `high_low_close_tp` | `market` | `high-low`, `close` | 고저/종가 기준. |
| `--stock-condition` | Yes | `stk_cnd` | `market` |  | 종목조건 코드. |
| `--volume-condition` | Yes | `trde_qty_tp` | `market` |  | 거래량조건 코드. |
| `--credit-condition` | Yes | `crd_cnd` | `market` |  | 신용조건 코드. |
| `--include-limit` | Yes | `updown_incls` | `market` | `yes`, `no` | 상하한 포함 여부. |
| `--period-days` | Yes | `dt` | `market` | `5`, `10`, `20`, `60`, `250` | 기간. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks new-high-low --market all --kind new-high --price-basis high-low --stock-condition value --volume-condition value --credit-condition value --include-limit yes --period-days 5 --exchange KRX --format json
```

### `kiwoomcli domestic stocks limit-move`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10017`

Purpose: 상하한가/상승하락 종목.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분. |
| `--direction` | Yes | `updown_tp` | `market` | `upper`, `rise`, `flat`, `lower`, `fall`, `prev-upper`, `prev-lower` | 상하한/등락 구분. |
| `--sort` | Yes | `sort_tp` | `market` | `code`, `count`, `change-rate` | 정렬구분. |
| `--stock-condition` | Yes | `stk_cnd` | `market` |  | 종목조건 코드. |
| `--volume-condition` | Yes | `trde_qty_tp` | `market` |  | 거래량조건 코드. |
| `--credit-condition` | Yes | `crd_cnd` | `market` |  | 신용조건 코드. |
| `--price-condition` | Yes | `trde_gold_tp` | `market` |  | 가격조건 코드. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks limit-move --market all --direction upper --sort code --stock-condition value --volume-condition value --credit-condition value --price-condition value --exchange KRX --format json
```

### `kiwoomcli domestic stocks high-low-near`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10018`

Purpose: 고저가 근접 종목.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--kind` | Yes | `high_low_tp` | `market` | `high`, `low` | 고가/저가 구분. |
| `--near-rate` | Yes | `alacc_rt` | `market` |  | 근접률 코드. |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분. |
| `--volume-condition` | Yes | `trde_qty_tp` | `market` |  | 거래량조건 코드. |
| `--stock-condition` | Yes | `stk_cnd` | `market` |  | 종목조건 코드. |
| `--credit-condition` | Yes | `crd_cnd` | `market` |  | 신용조건 코드. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks high-low-near --kind high --near-rate value --market all --volume-condition value --stock-condition value --credit-condition value --exchange KRX --format json
```

### `kiwoomcli domestic stocks price-spike`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10019`

Purpose: 가격 급등락 종목.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq`, `kospi200` | 시장구분. |
| `--direction` | Yes | `flu_tp` | `market` | `rise`, `fall` | 급등/급락 구분. |
| `--time-unit` | Yes | `tm_tp` | `market` | `minute`, `day` | 분전/일전 구분. |
| `--time` | Yes | `tm` | `quantity` |  | 분 또는 일 값. |
| `--volume-condition` | Yes | `trde_qty_tp` | `market` |  | 거래량조건 코드. |
| `--stock-condition` | Yes | `stk_cnd` | `market` |  | 종목조건 코드. |
| `--credit-condition` | Yes | `crd_cnd` | `market` |  | 신용조건 코드. |
| `--price-condition` | Yes | `pric_cnd` | `market` |  | 가격조건 코드. |
| `--include-limit` | Yes | `updown_incls` | `market` | `yes`, `no` | 상하한 포함 여부. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks price-spike --market all --direction rise --time-unit minute --time 1 --volume-condition value --stock-condition value --credit-condition value --price-condition value --include-limit yes --exchange KRX --format json
```

### `kiwoomcli domestic stocks volume-renewal`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10024`

Purpose: 거래량 갱신 종목.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분. |
| `--period-days` | Yes | `cycle_tp` | `market` | `5`, `10`, `20`, `60`, `250` | 기간. |
| `--volume-condition` | Yes | `trde_qty_tp` | `market` |  | 거래량조건 코드. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks volume-renewal --market all --period-days 5 --volume-condition value --exchange KRX --format json
```

### `kiwoomcli domestic stocks volume-zone`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10025`

Purpose: 매물대 집중 종목.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분. |
| `--concentration-rate` | Yes | `prps_cnctr_rt` | `market` |  | 매물집중비율. |
| `--include-current` | Yes | `cur_prc_entry` | `market` | `yes`, `no` | 현재가 매물대 포함 여부. |
| `--zone-count` | Yes | `prpscnt` | `quantity` |  | 매물대 수. |
| `--period-days` | Yes | `cycle_tp` | `market` | `50`, `100`, `150`, `200`, `250`, `300` | 기간. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks volume-zone --market all --concentration-rate value --include-current yes --zone-count 1 --period-days 50 --exchange KRX --format json
```

### `kiwoomcli domestic stocks valuation-rank`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10026`

Purpose: 고저 PER/PBR/ROE 순위.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--kind` | Yes | `pertp` | `market` | `low-pbr`, `high-pbr`, `low-per`, `high-per`, `low-roe`, `high-roe` | 지표구분. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks valuation-rank --kind low-pbr --exchange KRX --format json
```

### `kiwoomcli domestic stocks open-change`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10028`

Purpose: 시가 대비 등락률.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--basis` | Yes | `sort_tp` | `market` | `open`, `high`, `low`, `base` | 기준가 구분. |
| `--volume-condition` | Yes | `trde_qty_cnd` | `market` |  | 거래량조건 코드. |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분. |
| `--include-limit` | Yes | `updown_incls` | `market` | `yes`, `no` | 상하한 포함 여부. |
| `--stock-condition` | Yes | `stk_cnd` | `market` |  | 종목조건 코드. |
| `--credit-condition` | Yes | `crd_cnd` | `market` |  | 신용조건 코드. |
| `--amount-condition` | Yes | `trde_prica_cnd` | `market` |  | 거래대금조건 코드. |
| `--direction` | Yes | `flu_cnd` | `market` | `top`, `bottom` | 상위/하위 구분. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks open-change --basis open --volume-condition value --market all --include-limit yes --stock-condition value --credit-condition value --amount-condition value --direction top --exchange KRX --format json
```

### `kiwoomcli domestic stocks broker-volume-zone`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10043`

Purpose: 거래원 매물대 분석.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD. |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD. |
| `--date-mode` | Yes | `qry_dt_tp` | `market` | `period`, `start-end` | 조회일자 구분. |
| `--position` | Yes | `pot_tp` | `market` | `today`, `previous` | 당일/전일 구분. |
| `--period-days` | Yes | `dt` | `market` | `5`, `10`, `20`, `40`, `60`, `120` | 기간. |
| `--sort` | Yes | `sort_base` | `market` | `close`, `date` | 정렬기준. |
| `--broker-code` | Yes | `mmcm_cd` | `market` |  | 회원사 코드. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks broker-volume-zone --code 005930 --from 20260529 --to 20260529 --date-mode period --position today --period-days 5 --sort close --broker-code value --exchange KRX --format json
```

### `kiwoomcli domestic stocks broker-instant-volume`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10052`

Purpose: 거래원 순간 거래량.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--broker-code` | Yes | `mmcm_cd` | `market` |  | 회원사 코드. |
| `--code` | No | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq`, `stock` | 시장구분. |
| `--quantity-condition` | Yes | `qty_tp` | `market` |  | 수량조건 코드. |
| `--price-condition` | Yes | `pric_tp` | `market` |  | 가격조건 코드. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks broker-instant-volume --broker-code value --market all --quantity-condition value --price-condition value --exchange KRX --format json
```

### `kiwoomcli domestic stocks vi-triggered`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10054`

Purpose: 변동성완화장치 발동 종목.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분. |
| `--session` | Yes | `bf_mkrt_tp` | `market` | `all`, `regular`, `after-hours` | 시장시간 구분. |
| `--code` | No | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--vi-type` | Yes | `motn_tp` | `market` | `all`, `static`, `dynamic`, `both` | VI 구분. |
| `--skip-stocks` | Yes | `skip_stk` | `market` |  | 9자리 종목 제외 플래그. |
| `--use-volume` | Yes | `trde_qty_tp` | `market` | `yes`, `no` | 거래량 필터 사용 여부. |
| `--min-volume` | Yes | `min_trde_qty` | `market` |  | 최소 거래량. |
| `--max-volume` | Yes | `max_trde_qty` | `market` |  | 최대 거래량. |
| `--use-amount` | Yes | `trde_prica_tp` | `market` | `yes`, `no` | 거래대금 필터 사용 여부. |
| `--min-amount` | Yes | `min_trde_prica` | `market` |  | 최소 거래대금. |
| `--max-amount` | Yes | `max_trde_prica` | `market` |  | 최대 거래대금. |
| `--direction` | Yes | `motn_drc` | `market` | `all`, `rise`, `fall` | 발동 방향. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks vi-triggered --market all --session all --vi-type all --skip-stocks value --use-volume yes --min-volume value --max-volume value --use-amount yes --min-amount value --max-amount value --direction all --exchange KRX --format json
```

### `kiwoomcli domestic stocks today-previous-fills`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10055`

Purpose: 당일/전일 체결량.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--day` | Yes | `tdy_pred` | `market` | `today`, `previous` | 당일/전일 구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks today-previous-fills --code 005930 --day today --format json
```

### `kiwoomcli domestic stocks investor-daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10058`

Purpose: 투자자별 일별 매매 종목.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD. |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD. |
| `--side` | Yes | `trde_tp` | `market` | `net-sell`, `net-buy` | 순매매구분. |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq` | 시장구분. |
| `--investor` | Yes | `invsr_tp` | `market` | `individual`, `foreign`, `financial-investment`, `investment-trust`, `private-fund`, `other-financial`, `bank`, `insurance`, `pension`, `state`, `other-corporate`, `institution` | 투자자구분. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks investor-daily --from 20260529 --to 20260529 --side net-sell --market kospi --investor individual --exchange KRX --format json
```

### `kiwoomcli domestic stocks investor-by-stock`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10059`

Purpose: 종목별 투자자/기관 매매.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `dt` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD. |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액/수량 구분. |
| `--side` | Yes | `trde_tp` | `market` | `net-buy`, `buy`, `sell` | 매매구분. |
| `--unit` | Yes | `unit_tp` | `market` | `thousand`, `share` | 단위구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks investor-by-stock --date 20260529 --code 005930 --basis amount --side net-buy --unit thousand --format json
```

### `kiwoomcli domestic stocks investor-by-stock-total`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10061`

Purpose: 종목별 투자자/기관 매매 합계.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD. |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액/수량 구분. |
| `--side` | Yes | `trde_tp` | `market` | `net-buy` | 매매구분. |
| `--unit` | Yes | `unit_tp` | `market` | `thousand`, `share` | 단위구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks investor-by-stock-total --code 005930 --from 20260529 --to 20260529 --basis amount --side net-buy --unit thousand --format json
```

### `kiwoomcli domestic stocks today-previous-trades`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10084`

Purpose: 당일/전일 체결.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--day` | Yes | `tdy_pred` | `market` | `today`, `previous` | 당일/전일 구분. |
| `--interval-type` | Yes | `tic_min` | `market` | `tick`, `minute` | 틱/분 구분. |
| `--time` | No | `tm` | `market` |  | 조회시간 HHMM. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks today-previous-trades --code 005930 --day today --interval-type tick --format json
```

### `kiwoomcli domestic stocks watchlist-info`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10095`

Purpose: 관심종목 정보.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--codes` | Yes | `stk_cd` | `market` |  | 파이프(`\|`)로 구분한 거래소별 종목코드 목록. 쉼표 구분자는 문서화된 API 계약이 아니다. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks watchlist-info --codes '005930|000660' --format json
```

### `kiwoomcli domestic stocks info-list`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10099`

Purpose: 종목정보 리스트.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market-type` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq`, `kotc`, `konex`, `etn`, `loss-limit-etn`, `gold`, `volatility-etn`, `infrastructure`, `elw`, `mutual-fund`, `warrant`, `reit`, `warrant-certificate`, `etf`, `high-yield-fund` | 종목정보 시장구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks info-list --market-type kospi --format json
```

### `kiwoomcli domestic stocks info-detail`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10100`

Purpose: 종목정보 조회.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks info-detail --code 005930 --format json
```

### `kiwoomcli domestic stocks sector-codes`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10101`

Purpose: 업종코드 리스트.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq`, `kospi200`, `kospi100`, `krx100` | 업종 시장구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks sector-codes --market kospi --format json
```

### `kiwoomcli domestic stocks member-firms`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10102`

Purpose: 회원사 리스트.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks member-firms --format json
```

### `kiwoomcli domestic stocks program-net-top`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90003`

Purpose: 프로그램 순매수 상위 50.

Output note: Program-trading aggregates are market-time and condition dependent.
`return_code=0` with an empty list is a valid zero-row result, not positive
investor-useful data evidence by itself. `--market-code` uses the program
market-code family from samplecode, for example `P00101` KRX KOSPI, `P10102`
KRX KOSDAQ, `P001_NX01` NXT KOSPI, `P101_NX02` NXT KOSDAQ, `P001_AL01`
integrated KOSPI, and `P101_AL02` integrated KOSDAQ. Ordinary market selectors
such as `000` are weak evidence for this API and may produce zero rows.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--side` | Yes | `trde_upper_tp` | `market` | `net-sell`, `net-buy` | 순매매 상위 구분. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액/수량 구분. |
| `--market-code` | Yes | `mrkt_tp` | `market` |  | 프로그램 시장코드. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks program-net-top --side net-sell --basis amount --market-code P00101 --exchange KRX --format json
```

### `kiwoomcli domestic stocks program-by-stock`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90004`

Purpose: 종목별 프로그램매매 현황.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `dt` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD. |
| `--market-code` | Yes | `mrkt_tp` | `market` |  | 프로그램 시장코드. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks program-by-stock --date 20260529 --market-code value --exchange KRX --format json
```

### `kiwoomcli domestic stocks credit-loanable`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `kt20016`

Purpose: 신용융자 가능 종목.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--credit-grade` | No | `crd_stk_grde_tp` | `market` | `all`, `a`, `b`, `c`, `d`, `e` | 신용융자 등급. |
| `--market` | No | `mrkt_deal_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분. |
| `--code` | No | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks credit-loanable --format json
```

### `kiwoomcli domestic stocks credit-loanable-check`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `kt20017`

Purpose: 신용융자 가능 문의.

Output note: 원문 `crd_alow_yn`을 유지하고, CLI가 `loanable` 파생 필드를 추가한다. `crd_alow_yn`에 `불가능`이 있으면 `false`, `가능`이 있으면 `true`, 판정할 수 없으면 `null`이다.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic stocks credit-loanable-check --code 005930 --format json
```

### `kiwoomcli domestic quotes price`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10007`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Feature note: `ka10007` is selected because its spec requires `stk_cd` and its
response includes current-price-oriented fields such as `cur_prc`.

### `kiwoomcli domestic quotes balance`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90006`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `date` | `date_yyyymmdd` | | Query date. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | Exchange selector mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes balance --date 20260528 --exchange KRX --format json
```

### `kiwoomcli domestic quotes by-stock`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10045`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` | | Start date. |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` | | End date. |
| `--institution-price` | Yes | `orgn_prsm_unp_tp` | `market` | `buy`, `sell` | Institution estimated price side mapped by `maps/arguments.csv`. |
| `--foreign-price` | Yes | `for_prsm_unp_tp` | `market` | `buy`, `sell` | Foreign estimated price side mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes by-stock --code 005930 --from 20241007 --to 20241107 --institution-price buy --foreign-price buy --format json
```

### `kiwoomcli domestic quotes list`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10011`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--kind` | Yes | `newstk_recvrht_tp` | `market` | `all`, `warrant-security`, `warrant-certificate` | Warrant quote kind mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes list --kind all --format json
```

### `kiwoomcli domestic quotes gold-price`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50100`

Purpose: Query gold spot quote summary.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic quotes gold-fills`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50010`

Purpose: Query gold spot fill trend.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic quotes gold-daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50012`

Purpose: Query gold spot daily trend.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic quotes gold-expected`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50087`

Purpose: Query gold spot expected fills.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic quotes multi-period`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10005`

Purpose: 주식 일/주/월/시/분 요약 시세.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes multi-period --code 005930 --format json
```

### `kiwoomcli domestic quotes intraday-minute`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10006`

Purpose: 주식 시분 시세.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes intraday-minute --code 005930 --format json
```

### `kiwoomcli domestic quotes institution-daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10044`

Purpose: 일별 기관 매매 종목.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD. |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD. |
| `--side` | Yes | `trde_tp` | `market` | `net-sell`, `net-buy` | 순매매구분. |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq` | 시장구분. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes institution-daily --from 20260529 --to 20260529 --side net-sell --market kospi --exchange KRX --format json
```

### `kiwoomcli domestic quotes strength-time`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10046`

Purpose: 체결강도 시간별 추이.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes strength-time --code 005930 --format json
```

### `kiwoomcli domestic quotes strength-daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10047`

Purpose: 체결강도 일별 추이.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes strength-daily --code 005930 --format json
```

### `kiwoomcli domestic quotes investor-intraday`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10063`

Purpose: 장중 투자자별 매매.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `combined` | 금액/수량 동시 조회. |
| `--investor` | Yes | `invsr` | `market` | `foreign`, `institution`, `investment-trust`, `insurance`, `bank`, `pension`, `state`, `other-corporate` | 투자자구분. |
| `--foreign-all` | Yes | `frgn_all` | `market` | `yes`, `no` | 외국인 전체 포함 여부. |
| `--same-net-buy` | Yes | `smtm_netprps_tp` | `market` | `yes`, `no` | 동시 순매수 구분. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes investor-intraday --market all --basis combined --investor foreign --foreign-all yes --same-net-buy yes --exchange KRX --format json
```

### `kiwoomcli domestic quotes investor-after-close`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10066`

Purpose: 장마감 후 투자자별 매매.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액/수량 구분. |
| `--side` | Yes | `trde_tp` | `market` | `net-buy`, `buy`, `sell` | 매매구분. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes investor-after-close --market all --basis amount --side net-buy --exchange KRX --format json
```

### `kiwoomcli domestic quotes broker-trend`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10078`

Purpose: 증권사별 종목 매매 동향.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--broker-code` | Yes | `mmcm_cd` | `market` |  | 회원사 코드. |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD. |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes broker-trend --broker-code value --code 005930 --from 20260529 --to 20260529 --format json
```

### `kiwoomcli domestic quotes daily-price`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10086`

Purpose: 일별 주가.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--date` | Yes | `qry_dt` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD. |
| `--basis` | Yes | `indc_tp` | `market` | `quantity`, `amount` | 표시구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes daily-price --code 005930 --date 20260529 --basis quantity --format json
```

### `kiwoomcli domestic quotes after-hours`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10087`

Purpose: 시간외 단일가.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes after-hours --code 005930 --format json
```

### `kiwoomcli domestic quotes program-time`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90005`

Purpose: 프로그램매매 시간대별 추이.

Output note: Program-trading aggregates are market-time and condition dependent.
`return_code=0` with an empty list is a valid zero-row result, not positive
investor-useful data evidence by itself. `--market-code` uses the program
market-code family from samplecode, for example `P00101` KRX KOSPI, `P10102`
KRX KOSDAQ, `P001_NX01` NXT KOSPI, `P101_NX02` NXT KOSDAQ, `P001_AL01`
integrated KOSPI, and `P101_AL02` integrated KOSDAQ. Ordinary market selectors
such as `000` are weak evidence for this API and may produce zero rows.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `date` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액/수량 구분. |
| `--market-code` | Yes | `mrkt_tp` | `market` |  | 프로그램 시장코드. |
| `--interval-type` | Yes | `min_tic_tp` | `market` | `tick`, `minute` | 틱/분 구분. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes program-time --date 20241101 --basis amount --market-code P00101 --interval-type minute --exchange KRX --format json
```

### `kiwoomcli domestic quotes program-cumulative`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90007`

Purpose: 프로그램매매 누적 추이.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `date` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액/수량 구분. |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq` | 시장구분. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes program-cumulative --date 20260529 --basis amount --market kospi --exchange KRX --format json
```

### `kiwoomcli domestic quotes program-by-stock`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90008`

Purpose: 종목 시간별 프로그램매매 추이.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액/수량 구분. |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--date` | Yes | `date` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes program-by-stock --basis amount --code 005930 --date 20260529 --format json
```

### `kiwoomcli domestic quotes program-daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90010`

Purpose: 프로그램매매 일자별 추이.

Output note: Program-trading aggregates are market-time and condition dependent.
`return_code=0` with an empty list is a valid zero-row result, not positive
investor-useful data evidence by itself. `--market-code` uses the program
market-code family from samplecode, for example `P00101` KRX KOSPI, `P10102`
KRX KOSDAQ, `P001_NX01` NXT KOSPI, `P101_NX02` NXT KOSDAQ, `P001_AL01`
integrated KOSPI, and `P101_AL02` integrated KOSDAQ. Ordinary market selectors
such as `000` are weak evidence for this API and may produce zero rows.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `date` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액/수량 구분. |
| `--market-code` | Yes | `mrkt_tp` | `market` |  | 프로그램 시장코드. |
| `--interval-type` | Yes | `min_tic_tp` | `market` | `tick`, `minute` | 틱/분 구분. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes program-daily --date 20241125 --basis amount --market-code P00101 --interval-type tick --exchange KRX --format json
```

### `kiwoomcli domestic quotes stock-program-daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90013`

Purpose: 종목 일별 프로그램매매 추이.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--basis` | No | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액/수량 구분. |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드. |
| `--date` | No | `date` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic quotes stock-program-daily --code 005930 --format json
```

### `kiwoomcli domestic orderbooks list`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10004`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` or mapped field | `stock_code` | | Domestic stock code. |
| `--format` | No | output only | `output_format` | `auto`, `json`, `pretty`, `raw`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orderbooks list --code 005930 --format json
```

### `kiwoomcli domestic orderbooks gold`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50101`

Purpose: Query gold spot orderbook.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--tick` | Yes | `tic_scope` | `market` | `1`, `3`, `5`, `10`, `30` | Tick scope. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10081`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--adjusted` | No | `upd_stkpc_tp` | `bool_or_code` | `0`, `1`, `true`, `false`, `adjusted`, `raw` | Adjusted price option. Defaults to `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic candles daily --code 005930 --date 20260528 --adjusted 1 --format json
```

### `kiwoomcli domestic candles by-stock`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10060`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `dt` | `date_yyyymmdd` | | Query date. |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | Amount or quantity basis mapped by `maps/arguments.csv`. |
| `--side` | Yes | `trde_tp` | `market` | `net-buy`, `buy`, `sell` | Trade side mapped by `maps/arguments.csv`. |
| `--unit` | Yes | `unit_tp` | `market` | `thousand`, `share` | Unit mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic candles by-stock --date 20241107 --code 005930 --basis amount --side net-buy --unit thousand --format json
```

### `kiwoomcli domestic candles lookup`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10064`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | Market selector mapped by `maps/arguments.csv`. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | Amount or quantity basis mapped by `maps/arguments.csv`. |
| `--side` | Yes | `trde_tp` | `market` | `net-buy`, `buy`, `sell` | Trade side mapped by `maps/arguments.csv`. |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic candles lookup --market all --basis amount --side net-buy --code 005930 --format json
```

### `kiwoomcli domestic candles stock-tick`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10079`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--interval` | Yes | `tic_scope` | `market` | | Tick scope. |
| `--adjusted` | No | `upd_stkpc_tp` | `adjusted_price_flag` | `0`, `1`, `true`, `false`, `adjusted`, `raw` | Adjusted price option. Defaults to `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles stock-minute`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10080`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--interval` | Yes | `tic_scope` | `market` | | Minute scope. |
| `--adjusted` | No | `upd_stkpc_tp` | `adjusted_price_flag` | `0`, `1`, `true`, `false`, `adjusted`, `raw` | Adjusted price option. Defaults to `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles stock-weekly`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10082`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--adjusted` | No | `upd_stkpc_tp` | `adjusted_price_flag` | `0`, `1`, `true`, `false`, `adjusted`, `raw` | Adjusted price option. Defaults to `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles stock-monthly`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10083`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--adjusted` | No | `upd_stkpc_tp` | `adjusted_price_flag` | `0`, `1`, `true`, `false`, `adjusted`, `raw` | Adjusted price option. Defaults to `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles stock-yearly`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10094`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--adjusted` | No | `upd_stkpc_tp` | `adjusted_price_flag` | `0`, `1`, `true`, `false`, `adjusted`, `raw` | Adjusted price option. Defaults to `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles sector-tick`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20004`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `inds_cd` | `sector_code` | | Sector code. |
| `--interval` | Yes | `tic_scope` | `market` | | Tick scope. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles sector-minute`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20005`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `inds_cd` | `sector_code` | | Sector code. |
| `--interval` | Yes | `tic_scope` | `market` | | Minute scope. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles sector-daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20006`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `inds_cd` | `sector_code` | | Sector code. |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles sector-weekly`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20007`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `inds_cd` | `sector_code` | | Sector code. |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles sector-monthly`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20008`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `inds_cd` | `sector_code` | | Sector code. |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles sector-yearly`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20019`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `inds_cd` | `sector_code` | | Sector code. |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles gold-tick`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50079`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--interval` | Yes | `tic_scope` | `market` | | Tick scope. |
| `--adjusted` | No | `upd_stkpc_tp` | `adjusted_price_flag` | `0`, `1`, `true`, `false`, `adjusted`, `raw` | Adjusted price option. Defaults to `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles gold-minute`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50080`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--interval` | Yes | `tic_scope` | `market` | | Minute scope. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles gold-daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50081`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--adjusted` | No | `upd_stkpc_tp` | `adjusted_price_flag` | `0`, `1`, `true`, `false`, `adjusted`, `raw` | Adjusted price option. Defaults to `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles gold-weekly`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50082`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--adjusted` | No | `upd_stkpc_tp` | `adjusted_price_flag` | `0`, `1`, `true`, `false`, `adjusted`, `raw` | Adjusted price option. Defaults to `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles gold-monthly`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50083`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--adjusted` | No | `upd_stkpc_tp` | `adjusted_price_flag` | `0`, `1`, `true`, `false`, `adjusted`, `raw` | Adjusted price option. Defaults to `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles gold-today-tick`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50091`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--interval` | Yes | `tic_scope` | `market` | | Tick scope. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic candles gold-today-minute`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka50092`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` | | Gold spot instrument code, for example `M04020000` (gold 99.99_1kg). |
| `--interval` | Yes | `tic_scope` | `market` | | Minute scope. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic rankings orderbook-balance`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10020`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq` | 시장구분 |
| `--sort` | Yes | `sort_tp` | `market` | `net-buy-balance`, `net-sell-balance`, `buy-ratio`, `sell-ratio` | 정렬구분 |
| `--volume` | Yes | `trde_qty_tp` | `market` | `preopen`, `10k`, `50k`, `100k` | 거래량구분 |
| `--stock-condition` | Yes | `stk_cnd` | `market` | `all`, `exclude-managed`, `exclude-margin-100`, `only-margin-100`, `only-margin-40`, `only-margin-30`, `only-margin-20` | 종목조건 |
| `--credit-condition` | Yes | `crd_cnd` | `market` | `all`, `a`, `b`, `c`, `d`, `e`, `all-financing` | 신용조건 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings orderbook-balance --market kospi --sort net-buy-balance --volume preopen --stock-condition all --credit-condition all --exchange KRX --format json
```

### `kiwoomcli domestic rankings orderbook-balance-spike`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10021`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq` | 시장구분 |
| `--side` | Yes | `trde_tp` | `market` | `buy-balance`, `sell-balance` | 매매구분 |
| `--sort` | Yes | `sort_tp` | `market` | `spike-quantity`, `spike-rate` | 정렬구분 |
| `--interval` | Yes | `tm_tp` | `quantity` |  | 분 입력 |
| `--volume` | Yes | `trde_qty_tp` | `market` | `1k`, `5k`, `10k`, `50k`, `100k` | 거래량구분 |
| `--stock-condition` | Yes | `stk_cnd` | `market` | `all`, `exclude-managed`, `exclude-margin-100`, `only-margin-100`, `only-margin-40`, `only-margin-30`, `only-margin-20` | 종목조건 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings orderbook-balance-spike --market kospi --side buy-balance --sort spike-quantity --interval 1 --volume 1k --stock-condition all --exchange KRX --format json
```

### `kiwoomcli domestic rankings balance-rate-spike`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10022`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq` | 시장구분 |
| `--ratio` | Yes | `rt_tp` | `market` | `buy-to-sell`, `sell-to-buy` | 비율구분 |
| `--interval` | Yes | `tm_tp` | `quantity` |  | 분 입력 |
| `--volume` | Yes | `trde_qty_tp` | `market` | `5k`, `10k`, `50k`, `100k` | 거래량구분 |
| `--stock-condition` | Yes | `stk_cnd` | `market` | `all`, `exclude-managed`, `exclude-margin-100`, `only-margin-100`, `only-margin-40`, `only-margin-30`, `only-margin-20` | 종목조건 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings balance-rate-spike --market kospi --ratio buy-to-sell --interval 1 --volume 5k --stock-condition all --exchange KRX --format json
```

### `kiwoomcli domestic rankings volume-spike`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10023`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--sort` | Yes | `sort_tp` | `market` | `spike-quantity`, `spike-rate`, `drop-quantity`, `drop-rate` | 정렬구분 |
| `--time-unit` | Yes | `tm_tp` | `market` | `minute`, `previous-day` | 시간구분 |
| `--volume-condition` | Yes | `trde_qty_tp` | `market` |  | 거래량조건 코드 |
| `--time` | No | `tm` | `quantity` |  | 분 입력 |
| `--stock-condition` | Yes | `stk_cnd` | `market` |  | 종목조건 코드 |
| `--price-condition` | Yes | `pric_tp` | `market` |  | 가격조건 코드 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings volume-spike --market all --sort spike-quantity --time-unit minute --volume-condition value --stock-condition value --price-condition value --exchange KRX --format json
```

### `kiwoomcli domestic rankings previous-change-rate`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10027`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--sort` | Yes | `sort_tp` | `market` | `rise-rate`, `rise-price`, `fall-rate`, `fall-price`, `flat` | 정렬구분 |
| `--volume` | Yes | `trde_qty_cnd` | `market` | `all`, `10k`, `50k`, `100k`, `150k`, `200k`, `300k`, `500k`, `1000k` | 거래량조건 |
| `--stock-condition` | Yes | `stk_cnd` | `market` | `all`, `exclude-managed`, `exclude-preferred`, `exclude-managed-preferred`, `exclude-margin-100`, `only-margin-100`, `only-margin-40`, `only-margin-30`, `only-margin-20`, `exclude-liquidation`, `only-margin-50`, `only-margin-60`, `exclude-etf`, `exclude-spac`, `exclude-etf-etn` | 종목조건 |
| `--credit-condition` | Yes | `crd_cnd` | `market` | `all`, `a`, `b`, `c`, `d`, `e`, `all-financing` | 신용조건 |
| `--include-limit` | Yes | `updown_incls` | `market` | `yes`, `no` | 상하한 포함 여부 |
| `--price-condition` | Yes | `pric_cnd` | `market` | `all`, `under-1k`, `1k-2k`, `2k-5k`, `5k-10k`, `over-10k`, `over-1k`, `under-10k` | 가격조건 |
| `--amount-condition` | Yes | `trde_prica_cnd` | `market` |  | 거래대금조건 코드 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings previous-change-rate --market all --sort rise-rate --volume all --stock-condition all --credit-condition all --include-limit yes --price-condition all --amount-condition value --exchange KRX --format json
```

### `kiwoomcli domestic rankings list-fills`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10029`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--sort` | Yes | `sort_tp` | `market` | `rise-rate`, `rise-price`, `flat`, `fall-rate`, `fall-price`, `volume`, `upper-limit`, `lower-limit` | 정렬구분 |
| `--volume` | Yes | `trde_qty_cnd` | `market` | `all`, `1k`, `3k`, `5k`, `10k`, `50k`, `100k` | 거래량조건 |
| `--stock-condition` | Yes | `stk_cnd` | `market` | `all`, `exclude-managed`, `exclude-preferred`, `exclude-managed-preferred`, `exclude-margin-100`, `only-margin-100`, `only-margin-40`, `only-margin-30`, `only-margin-20`, `exclude-liquidation`, `only-margin-50`, `only-margin-60`, `exclude-etf`, `exclude-spac`, `exclude-etf-etn` | 종목조건 |
| `--credit-condition` | Yes | `crd_cnd` | `market` | `all`, `a`, `b`, `c`, `d`, `exclude-overlimit`, `e`, `short`, `all-financing` | 신용조건 |
| `--price-condition` | Yes | `pric_cnd` | `market` | `all`, `under-1k`, `1k-2k`, `2k-5k`, `5k-10k`, `over-10k`, `over-1k`, `under-10k` | 가격조건 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings list-fills --market all --sort rise-rate --volume all --stock-condition all --credit-condition all --price-condition all --exchange KRX --format json
```

### `kiwoomcli domestic rankings today-volume`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10030`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--sort` | Yes | `sort_tp` | `market` | `volume`, `turnover`, `amount` | 정렬구분 |
| `--stock-condition` | Yes | `mang_stk_incls` | `market` |  | 종목조건 코드 |
| `--credit-type` | Yes | `crd_tp` | `market` | `all`, `all-financing`, `a`, `b`, `c`, `d`, `short` | 신용구분 |
| `--volume-condition` | Yes | `trde_qty_tp` | `market` |  | 거래량조건 코드 |
| `--price-condition` | Yes | `pric_tp` | `market` |  | 가격조건 코드 |
| `--amount-condition` | Yes | `trde_prica_tp` | `market` |  | 거래대금조건 코드 |
| `--session` | Yes | `mrkt_open_tp` | `market` | `all`, `regular`, `pre-open`, `after-hours` | 장운영구분 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings today-volume --market all --sort volume --stock-condition value --credit-type all --volume-condition value --price-condition value --amount-condition value --session all --exchange KRX --format json
```

### `kiwoomcli domestic rankings previous-volume`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10031`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--kind` | Yes | `qry_tp` | `market` | `volume`, `amount` | 조회구분 |
| `--rank-from` | Yes | `rank_strt` | `quantity` |  | 순위시작 |
| `--rank-to` | Yes | `rank_end` | `quantity` |  | 순위끝 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings previous-volume --market all --kind volume --rank-from 1 --rank-to 1 --exchange KRX --format json
```

### `kiwoomcli domestic rankings amount`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10032`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--include-managed` | Yes | `mang_stk_incls` | `market` | `yes`, `no` | 관리종목 포함 여부 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings amount --market all --include-managed yes --exchange KRX --format json
```

### `kiwoomcli domestic rankings credit-ratio`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10033`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--volume-condition` | Yes | `trde_qty_tp` | `market` |  | 거래량조건 코드 |
| `--stock-condition` | Yes | `stk_cnd` | `market` | `all`, `exclude-managed`, `exclude-margin-100`, `only-margin-100`, `only-margin-40`, `only-margin-30`, `only-margin-20` | 종목조건 |
| `--include-limit` | Yes | `updown_incls` | `market` | `yes`, `no` | 상하한 포함 여부 |
| `--credit-condition` | Yes | `crd_cnd` | `market` | `all`, `a`, `b`, `c`, `d`, `e`, `all-financing` | 신용조건 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings credit-ratio --market all --volume-condition value --stock-condition all --include-limit yes --credit-condition all --exchange KRX --format json
```

### `kiwoomcli domestic rankings foreign-period-trades`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10034`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--side` | Yes | `trde_tp` | `market` | `net-sell`, `net-buy`, `net-trade` | 매매구분 |
| `--period` | Yes | `dt` | `market` | `today`, `previous`, `5d`, `10d`, `20d`, `60d` | 기간 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings foreign-period-trades --market all --side net-sell --period today --exchange KRX --format json
```

### `kiwoomcli domestic rankings foreign-continuous-net`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10035`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--side` | Yes | `trde_tp` | `market` | `net-sell`, `net-buy` | 매매구분 |
| `--base-date` | Yes | `base_dt_tp` | `market` | `today`, `previous` | 기준일구분 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings foreign-continuous-net --market all --side net-sell --base-date today --exchange KRX --format json
```

### `kiwoomcli domestic rankings foreign-limit-usage`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10036`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--period` | Yes | `dt` | `market` | `today`, `previous`, `5d`, `10d`, `20d`, `60d` | 기간 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings foreign-limit-usage --market all --period today --exchange KRX --format json
```

### `kiwoomcli domestic rankings foreign-broker-trades`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10037`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--period` | Yes | `dt` | `market` | `today`, `previous`, `5d`, `10d`, `20d`, `60d` | 기간 |
| `--side` | Yes | `trde_tp` | `market` | `net-buy`, `net-sell`, `buy`, `sell` | 매매구분 |
| `--sort` | Yes | `sort_tp` | `market` | `amount`, `quantity` | 정렬구분 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings foreign-broker-trades --market all --period today --side net-buy --sort amount --exchange KRX --format json
```

### `kiwoomcli domestic rankings broker-by-stock`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10038`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드 |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD |
| `--side` | Yes | `qry_tp` | `market` | `net-sell`, `net-buy` | 조회구분 |
| `--period` | No | `dt` | `market` | `previous`, `5d`, `10d`, `20d`, `40d`, `60d`, `120d` | 기간 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings broker-by-stock --code 005930 --from 20260529 --to 20260529 --side net-sell --format json
```

### `kiwoomcli domestic rankings broker-trades`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10039`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--broker-code` | Yes | `mmcm_cd` | `market` |  | 회원사코드 |
| `--volume-condition` | Yes | `trde_qty_tp` | `market` |  | 거래량조건 코드 |
| `--side` | Yes | `trde_tp` | `market` | `net-buy`, `net-sell` | 매매구분 |
| `--period` | Yes | `dt` | `market` | `previous`, `5d`, `10d`, `60d` | 기간 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings broker-trades --broker-code value --volume-condition value --side net-buy --period previous --exchange KRX --format json
```

### `kiwoomcli domestic rankings stock-main-brokers`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10040`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings stock-main-brokers --code 005930 --format json
```

### `kiwoomcli domestic rankings net-buy-brokers`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10042`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드 |
| `--from` | No | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD |
| `--to` | No | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD |
| `--date-mode` | Yes | `qry_dt_tp` | `market` | `period`, `start-end` | 조회기간구분 |
| `--point` | Yes | `pot_tp` | `market` | `today`, `previous` | 시점구분 |
| `--period` | No | `dt` | `market` | `5d`, `10d`, `20d`, `40d`, `60d`, `120d` | 기간 |
| `--sort` | Yes | `sort_base` | `market` | `close`, `date` | 정렬기준 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings net-buy-brokers --code 005930 --date-mode period --point today --sort close --format json
```

### `kiwoomcli domestic rankings top-exit-brokers`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10053`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings top-exit-brokers --code 005930 --format json
```

### `kiwoomcli domestic rankings same-net-trades`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10062`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD |
| `--to` | No | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--side` | Yes | `trde_tp` | `market` | `net-buy`, `net-sell` | 매매구분 |
| `--basis` | Yes | `sort_cnd` | `market` | `quantity`, `amount` | 정렬조건 |
| `--unit` | Yes | `unit_tp` | `market` | `share`, `thousand` | 단위구분 |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings same-net-trades --from 20260529 --market all --side net-buy --basis quantity --unit share --exchange KRX --format json
```

### `kiwoomcli domestic rankings investor-intraday`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10065`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--side` | Yes | `trde_tp` | `market` | `net-buy`, `net-sell` | 매매구분 |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--investor` | Yes | `orgn_tp` | `market` | `foreign`, `foreign-broker`, `financial-investment`, `investment-trust`, `other-financial`, `bank`, `insurance`, `pension`, `state`, `other-corporate`, `institution` | 기관구분 |
| `--basis` | No | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액수량구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings investor-intraday --side net-buy --market all --investor foreign --format json
```

### `kiwoomcli domestic rankings after-hours-change-rate`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10098`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--sort` | Yes | `sort_base` | `market` | `rise-rate`, `rise-price`, `fall-rate`, `fall-price`, `flat` | 정렬기준 |
| `--stock-condition` | Yes | `stk_cnd` | `market` |  | 종목조건 코드 |
| `--volume` | Yes | `trde_qty_cnd` | `market` |  | 거래량조건 코드 |
| `--credit-condition` | Yes | `crd_cnd` | `market` | `all`, `a`, `b`, `c`, `d`, `exclude-overlimit`, `e`, `short`, `all-financing` | 신용조건 |
| `--amount-condition` | Yes | `trde_prica` | `market` |  | 거래대금조건 코드 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings after-hours-change-rate --market all --sort rise-rate --stock-condition value --volume value --credit-condition all --amount-condition value --format json
```

### `kiwoomcli domestic rankings foreign-institution-trades`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90009`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq` | 시장구분 |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | 금액수량구분 |
| `--include-date` | Yes | `qry_dt_tp` | `market` | `yes`, `no` | 조회일자 포함 여부 |
| `--date` | No | `date` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic rankings foreign-institution-trades --market all --basis amount --include-date yes --exchange KRX --format json
```
### `kiwoomcli domestic sectors program`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10010`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic sectors program --code 005930 --format json
```

### `kiwoomcli domestic sectors investor-flows`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10051`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq` | Market selector mapped by `maps/arguments.csv`. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | Amount/quantity selector mapped by `maps/arguments.csv`. |
| `--date` | No | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | Exchange selector mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic sectors investor-flows --market kospi --basis amount --exchange ALL --format json
```

### `kiwoomcli domestic sectors price`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20001`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq`, `kospi200` | Market selector mapped by `maps/arguments.csv`. |
| `--code` | Yes | `inds_cd` | `sector_code` | | Kiwoom sector code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic sectors price --market kospi --code 001 --format json
```

### `kiwoomcli domestic sectors stocks`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20002`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq`, `kospi200` | Market selector mapped by `maps/arguments.csv`. |
| `--code` | Yes | `inds_cd` | `sector_code` | | Kiwoom sector code. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | Exchange selector mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic sectors stocks --market kospi --code 001 --exchange ALL --format json
```

### `kiwoomcli domestic sectors indices`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20003`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `inds_cd` | `sector_code` | | Kiwoom sector code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic sectors indices --code 001 --format json
```

### `kiwoomcli domestic sectors daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20009`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq`, `kospi200` | Market selector mapped by `maps/arguments.csv`. |
| `--code` | Yes | `inds_cd` | `sector_code` | | Kiwoom sector code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic sectors daily --market kospi --code 001 --format json
```

### `kiwoomcli domestic etfs info`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka40002`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic ETF code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic etfs info --code 069500 --format json
```

### `kiwoomcli domestic etfs daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka40003`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic ETF code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic etfs daily --code 069500 --format json
```

### `kiwoomcli domestic etfs profit`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka40001`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic ETF code. |
| `--index-code` | Yes | `etfobjt_idex_cd` | `market` | | ETF target index code. |
| `--period` | Yes | `dt` | `market` | `week`, `month`, `six-months`, `year` | Period mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic etfs profit --code 069500 --index-code 207 --period year --format json
```

### `kiwoomcli domestic etfs list`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka40004`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--tax-type` | Yes | `txon_type` | `market` | `all`, `tax-free`, `holding-tax`, `company`, `foreign`, `foreign-tax-free` | Tax type mapped by `maps/arguments.csv`. |
| `--nav-compare` | Yes | `navpre` | `market` | `all`, `nav-gt-close`, `nav-lt-close` | NAV comparison mapped by `maps/arguments.csv`. |
| `--manager` | Yes | `mngmcomp` | `market` | | Management company code. |
| `--taxable` | Yes | `txon_yn` | `market` | `all`, `taxable`, `tax-free` | Taxability mapped by `maps/arguments.csv`. |
| `--tracking-index` | Yes | `trace_idex` | `market` | | Tracking index code. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | Exchange selector mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic etfs list --tax-type all --nav-compare all --manager 0000 --taxable all --tracking-index 0 --exchange KRX --format json
```

### `kiwoomcli domestic etfs intraday-trend`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka40006`

Purpose: Query ETF intraday trend.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic ETF code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic etfs intraday-fills`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka40007`

Purpose: Query ETF intraday fills.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic ETF code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic etfs daily-fills`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka40008`

Purpose: Query ETF daily fills.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic ETF code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic etfs nav`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka40009`

Purpose: Query ETF NAV related information.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic ETF code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic etfs foreign-trend`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka40010`

Purpose: Query ETF foreign investor trend.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic ETF code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic elws daily`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10048`

Sample note: ELW instruments expire. Use current/proven ELW evidence for
examples; an expired or inactive ELW code can return an empty list even when
the command mapping is correct.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `instrument_code` | | Domestic ELW code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic elws daily --code 57M747 --format json
```

### `kiwoomcli domestic elws balance`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka30003`

Sample note: This command's `--code` maps to Kiwoom `bsis_aset_cd`. The latest
real-call evidence used `57M747` with `20260616`; generic codes such as `001`
are not useful evidence for this endpoint.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `bsis_aset_cd` | `market` | | Base asset code. |
| `--date` | Yes | `base_dt` | `date_yyyymmdd` | | Base date. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic elws balance --code 57M747 --date 20260616 --format json
```

### `kiwoomcli domestic elws conditions`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka30005`

Sample note: Prove evidence used issuer `000000000017`, underlying code `201`,
right type `call`, LP `000000000000`, and sort `none`. ELW universes change
with listing and expiry, so keep sample parameters tied to current/proven
evidence.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--issuer-code` | Yes | `isscomp_cd` | `market` | | Issuer code. |
| `--underlying-code` | Yes | `bsis_aset_cd` | `market` | | Base asset code. |
| `--right-type` | Yes | `rght_tp` | `market` | `all`, `call`, `put`, `dc`, `dp`, `ex`, `early-call`, `early-put` | Right type mapped by `maps/arguments.csv`. |
| `--lp-code` | Yes | `lpcd` | `market` | | LP code. |
| `--sort` | Yes | `sort_tp` | `market` | `none`, `rise-rate`, `rise-price`, `fall-rate`, `fall-price`, `volume`, `amount`, `days-left` | Sort rule mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic elws conditions --issuer-code 000000000017 --underlying-code 201 --right-type call --lp-code 000000000000 --sort none --format json
```

### `kiwoomcli domestic elws sensitivity`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10050`

Sample note: ELW instruments expire. Use current/proven ELW evidence for
examples; an expired or inactive ELW code can return an empty list even when
the command mapping is correct.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `instrument_code` | | ELW code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic elws sensitivity --code 57M747 --format json
```

### `kiwoomcli domestic elws price-move`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka30001`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--direction` | Yes | `flu_tp` | `market` | `rise`, `fall` | Price move direction. |
| `--time-unit` | Yes | `tm_tp` | `market` | `minute`, `day` | Time unit. |
| `--time` | Yes | `tm` | `quantity` | | Time value. |
| `--volume` | Yes | `trde_qty_tp` | `market` | `all`, `10k`, `50k`, `100k`, `300k`, `500k`, `1000k` | Volume threshold. |
| `--issuer-code` | Yes | `isscomp_cd` | `market` | | Issuer code. |
| `--underlying-code` | Yes | `bsis_aset_cd` | `market` | | Base asset code. |
| `--right-type` | Yes | `rght_tp` | `market` | `all`, `call`, `put`, `dc`, `dp`, `ex`, `early-call`, `early-put` | Right type. |
| `--lp-code` | Yes | `lpcd` | `market` | | LP code. |
| `--include-ended` | Yes | `trde_end_elwskip` | `market` | `yes`, `no` | Include ended ELWs. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic elws broker-net`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka30002`

Sample note: Prove evidence used issuer `003`, volume `all`, side `net-sell`,
period `60d`, and include-ended `yes`, returning 100 rows.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--issuer-code` | Yes | `isscomp_cd` | `market` | | Issuer code. |
| `--volume` | Yes | `trde_qty_tp` | `market` | `all`, `5k`, `10k`, `50k`, `100k`, `500k`, `1000k` | Volume threshold. |
| `--side` | Yes | `trde_tp` | `market` | `net-buy`, `net-sell` | Net trade side. |
| `--period` | Yes | `dt` | `market` | `previous`, `5d`, `10d`, `40d`, `60d` | Query period. |
| `--include-ended` | Yes | `trde_end_elwskip` | `market` | `yes`, `no` | Include ended ELWs. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic elws broker-net --issuer-code 003 --volume all --side net-sell --period 60d --include-ended yes --format json
```

### `kiwoomcli domestic elws divergence`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka30004`

Sample note: Prove evidence used all-issuer/all-underlying/all-LP 12-digit
codes (`000000000000`) with right type `all` and include-ended `yes`, returning
1000 rows.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--issuer-code` | Yes | `isscomp_cd` | `market` | | Issuer code. |
| `--underlying-code` | Yes | `bsis_aset_cd` | `market` | | Base asset code. |
| `--right-type` | Yes | `rght_tp` | `market` | `all`, `call`, `put`, `dc`, `dp`, `ex`, `early-call`, `early-put` | Right type. |
| `--lp-code` | Yes | `lpcd` | `market` | | LP code. |
| `--include-ended` | Yes | `trde_end_elwskip` | `market` | `yes`, `no` | Include ended ELWs. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic elws divergence --issuer-code 000000000000 --underlying-code 000000000000 --right-type all --lp-code 000000000000 --include-ended yes --format json
```

### `kiwoomcli domestic elws change-rank`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka30009`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--sort` | Yes | `sort_tp` | `market` | `rise-rate`, `rise-price`, `fall-rate`, `fall-price` | Sort selector. |
| `--right-type` | Yes | `rght_tp` | `market` | `all`, `call`, `put`, `dc`, `dp`, `early-call`, `early-put` | Right type. |
| `--include-ended` | Yes | `trde_end_skip` | `market` | `yes`, `no` | Include ended ELWs. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic elws balance-rank`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka30010`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--sort` | Yes | `sort_tp` | `market` | `buy-balance`, `sell-balance` | Sort selector. |
| `--right-type` | Yes | `rght_tp` | `market` | `all`, `call`, `put`, `dc`, `dp`, `early-call`, `early-put` | Right type. |
| `--include-ended` | Yes | `trde_end_skip` | `market` | `yes`, `no` | Include ended ELWs. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic elws proximity`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka30011`

Sample note: ELW instruments expire. Use current/proven ELW evidence for
examples; an expired or inactive ELW code can return an empty list even when
the command mapping is correct.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `instrument_code` | | ELW code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic elws proximity --code 57M747 --format json
```

### `kiwoomcli domestic elws details`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka30012`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `instrument_code` | | ELW code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic investors by-stock`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10008`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic investors by-stock --code 005930 --format json
```

### `kiwoomcli domestic investors lookup`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10009`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic investors lookup --code 005930 --format json
```

### `kiwoomcli domestic investors trend`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10131`

Purpose: Query continuous institutional/foreign investor trading status.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--period` | Yes | `dt` | `market` | `recent`, `3d`, `5d`, `10d`, `20d`, `120d`, `range` | Query period. Use `range` with `--from` and `--to`. |
| `--from` | No | `strt_dt` | `date_yyyymmdd` | | Start date. |
| `--to` | No | `end_dt` | `date_yyyymmdd` | | End date. |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq` | Market selector. |
| `--side` | Yes | `netslmt_tp` | `market` | `net-buy` | Net trade side fixed by the Kiwoom spec. |
| `--target` | Yes | `stk_inds_tp` | `market` | `stock`, `sector` | Stock or sector view. |
| `--basis` | Yes | `amt_qty_tp` | `market` | `amount`, `quantity` | Amount or quantity basis. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | Exchange selector. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic investors gold-status`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka52301`

Purpose: Query gold spot investor status.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

### `kiwoomcli domestic short-selling trend`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10014`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` | | Start date. |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` | | End date. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic short-selling trend --code 005930 --from 20250101 --to 20250131 --format json
```

### `kiwoomcli domestic securities-lending by-stock`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka20068`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic securities-lending by-stock --code 005930 --format json
```

### `kiwoomcli domestic securities-lending trend`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10068`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--from` | No | `strt_dt` | `date_yyyymmdd` | | Start date. |
| `--to` | No | `end_dt` | `date_yyyymmdd` | | End date. |
| `(fixed)` | Yes | `all_tp` | `market` |  | 전체표시 고정값 `1`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic securities-lending trend --from 20250401 --to 20250430 --format json
```

### `kiwoomcli domestic securities-lending list`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka10069`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` | | Start date. |
| `--to` | No | `end_dt` | `date_yyyymmdd` | | End date. |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq` | Market selector mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic securities-lending list --from 20250401 --to 20250430 --market kospi --format json
```

### `kiwoomcli domestic securities-lending lookup`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90012`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `dt` | `date_yyyymmdd` | | Query date. |
| `--market` | Yes | `mrkt_tp` | `market` | `kospi`, `kosdaq` | Market selector mapped by `maps/arguments.csv`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic securities-lending lookup --date 20250430 --market kospi --format json
```

### `kiwoomcli domestic themes lookup`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90001`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--kind` | Yes | `qry_tp` | `market` | `all`, `theme`, `stock` | Search kind mapped by `maps/arguments.csv`. |
| `--days` | Yes | `date_tp` | `market` | | Period in days. |
| `--sort` | Yes | `flu_pl_amt_tp` | `market` | `profit-top`, `profit-bottom`, `change-top`, `change-bottom` | Sort rule mapped by `maps/arguments.csv`. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | Exchange selector mapped by `maps/arguments.csv`. |
| `--code` | No | `stk_cd` | `stock_code` | | Stock code when `--kind stock` is used. |
| `--name` | No | `thema_nm` | `market` | | Theme name when `--kind theme` is used. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic themes lookup --kind all --days 10 --sort profit-top --exchange KRX --format json
```

### `kiwoomcli domestic themes by-stock`

Status: Implemented

Auth required: yes
Safety: `read`
Candidate API: `ka90002`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `thema_grp_cd` | `market` | | Theme group code. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | Exchange selector mapped by `maps/arguments.csv`. |
| `--days` | No | `date_tp` | `market` | | Period in days. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic themes by-stock --code 100 --exchange KRX --days 2 --format json
```

## Overseas TODO

Overseas investment-info, sectors, quotes, orderbooks, and candles APIs are kept
in `kiwoom_cli/maps/api_commands.csv` as planned public coverage. They are not
runtime-exposed because overseas Kiwoom API execution is not currently working.
Promote these commands only after real credentialed overseas calls are verified,
then add explicit `arguments.csv` rows and implemented command contracts.

## Accounts

### `kiwoomcli domestic accounts balance`

Status: Planned

Auth required: yes
Safety: `account_read`
Candidate API: `kt00005`

Feature: 체결잔고. Output should support table and JSON modes. Stock code,
stock name, quantity, purchase amount, current value, PnL, and withdrawable-like
fields should be reviewed from response metadata before table columns are fixed.

### `kiwoomcli domestic accounts withdrawable`

Status: Planned

Auth required: yes
Safety: `account_read`
Candidate API: `kt00010`

Feature: inquiry only. This is not a withdrawal execution command.

## Orders

### `kiwoomcli domestic accounts list`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka00001`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts list --format json
```

### `kiwoomcli domestic accounts daily-balance-return`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka01690`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `qry_dt` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts daily-balance-return --date 20260529 --format json
```

### `kiwoomcli domestic accounts realized-profit-stock-daily`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka10072`

Output note: This is account/date-state dependent. It returns rows only when
the selected account has realized stock PnL on `--date`; an empty list with a
normal Kiwoom return code is a zero-row account state, not a mapping failure.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | No | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--date` | Yes | `strt_dt` | `date_yyyymmdd` |  | 조회일자 YYYYMMDD |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts realized-profit-stock-daily --date 20260522 --format json
```

### `kiwoomcli domestic accounts realized-profit-period-stock`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka10073`

Output note: This is account/date-state dependent. It returns rows only when
the selected account has realized stock PnL inside the requested period; an
empty list with a normal Kiwoom return code is a zero-row account state, not a
mapping failure.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | No | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts realized-profit-period-stock --from 20260522 --to 20260522 --format json
```

### `kiwoomcli domestic accounts realized-profit-daily`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka10074`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts realized-profit-daily --from 20260529 --to 20260529 --format json
```

### `kiwoomcli domestic accounts realized-profit-today-detail`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka10077`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts realized-profit-today-detail --code 005930 --format json
```

### `kiwoomcli domestic accounts return-rate`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka10085`

Output note: This is account-state dependent. It returns rows only when the
selected account has matching holdings/return-rate rows for the exchange
filter; an empty list with a normal Kiwoom return code is a zero-row account
state, not a mapping failure.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--exchange` | Yes | `stex_tp` | `market` | `ALL`, `KRX`, `NXT` | 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts return-rate --exchange ALL --format json
```

### `kiwoomcli domestic accounts day-trading-log`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka10170`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | No | `base_dt` | `date_yyyymmdd` |  | 기준일자 YYYYMMDD |
| `--sell-scope` | Yes | `ottks_tp` | `market` | `same-day-buy-sell`, `all-sells` | 단주구분 |
| `--cash-credit` | Yes | `ch_crd_tp` | `market` | `all`, `cash`, `credit` | 현금신용구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts day-trading-log --sell-scope same-day-buy-sell --cash-credit all --format json
```

### `kiwoomcli domestic accounts cash`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00001`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--cash-basis` | Yes | `qry_tp` | `market` | `estimated`, `normal` | 조회구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts cash --cash-basis estimated --format json
```

### `kiwoomcli domestic accounts estimated-assets-daily`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00002`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--from` | Yes | `start_dt` | `date_yyyymmdd` |  | 시작조회기간 YYYYMMDD |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` |  | 종료조회기간 YYYYMMDD |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts estimated-assets-daily --from 20260529 --to 20260529 --format json
```

### `kiwoomcli domestic accounts assets`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00003`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--include-delisted` | Yes | `qry_tp` | `market` | `yes`, `no` | 상장폐지조회구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts assets --include-delisted yes --format json
```

### `kiwoomcli domestic accounts valuation`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00004`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--include-delisted` | Yes | `qry_tp` | `market` | `yes`, `no` | 상장폐지조회구분 |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `KRX`, `NXT` | 국내거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts valuation --include-delisted yes --exchange KRX --format json
```

### `kiwoomcli domestic accounts fill-balance`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00005`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `KRX`, `NXT` | 국내거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts fill-balance --exchange KRX --format json
```

### `kiwoomcli domestic accounts order-fill-detail`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00007`

Output note: This is account/date-state dependent. It returns rows only when
the selected account has matching order/fill history for the filters; an empty
list with a normal Kiwoom return code is a zero-row account state, not a mapping
failure.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | No | `ord_dt` | `date_yyyymmdd` |  | 주문일자 YYYYMMDD |
| `--order` | Either | `qry_tp` | `market` | `order`, `reverse` | 조회 순서 |
| `--fill-status` | Either | `qry_tp` | `market` | `open`, `filled` | 체결 상태 필터 |
| `--asset-kind` | Yes | `stk_bond_tp` | `market` | `all`, `stock`, `bond` | 주식채권구분 |
| `--side` | Yes | `sell_tp` | `market` | `all`, `sell`, `buy` | 매도수구분 |
| `--code` | No | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드 |
| `--order-id` | No | `fr_ord_no` | `order_id` |  | 시작주문번호 |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `ALL`, `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts order-fill-detail --date 20260522 --order order --asset-kind all --side all --exchange ALL --format json
```

### `kiwoomcli domestic accounts next-settlement`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00008`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--settlement-id` | No | `strt_dcd_seq` | `market` |  | 시작결제번호 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts next-settlement --format json
```

### `kiwoomcli domestic accounts order-fill-status`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00009`

Output note: This is account/date-state dependent. It returns rows only when
the selected account has matching order/fill status for the filters; an empty
list with a normal Kiwoom return code is a zero-row account state, not a mapping
failure. Some Kiwoom environments may also return metadata-only/non-zero
responses when the account/date combination is not queryable.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | No | `ord_dt` | `date_yyyymmdd` |  | 주문일자 YYYYMMDD |
| `--asset-kind` | Yes | `stk_bond_tp` | `market` | `all`, `stock`, `bond` | 주식채권구분 |
| `--market` | Yes | `mrkt_tp` | `market` | `all`, `kospi`, `kosdaq`, `otcbb`, `ecn` | 시장구분 |
| `--side` | Yes | `sell_tp` | `market` | `all`, `sell`, `buy` | 매도수구분 |
| `--fill-status` | Yes | `qry_tp` | `market` | `all`, `filled` | 체결 상태 필터 |
| `--code` | No | `stk_cd` | `exchange_stock_code` |  | 거래소별 종목코드 |
| `--order-id` | No | `fr_ord_no` | `order_id` |  | 시작주문번호 |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `ALL`, `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts order-fill-status --date 20260522 --asset-kind all --market all --side all --fill-status all --exchange ALL --format json
```

### `kiwoomcli domestic accounts credit-margin`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00012`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--price` | No | `uv` | `price` |  | 매수가격 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts credit-margin --code 005930 --format json
```

### `kiwoomcli domestic accounts margin-details`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00013`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts margin-details --format json
```

### `kiwoomcli domestic accounts transaction-history`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00015`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--from` | Yes | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD |
| `--to` | Yes | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD |
| `--kind` | Yes | `tp` | `market` |  | 거래내역 구분 코드 |
| `--code` | No | `stk_cd` | `market` |  | 종목코드 |
| `--currency` | No | `crnc_cd` | `market` |  | 통화코드 |
| `--product` | Yes | `gds_tp` | `market` | `all`, `domestic-stock`, `fund`, `overseas-stock`, `financial-product` | 상품구분 |
| `--overseas-exchange` | No | `frgn_stex_code` | `market` |  | 해외거래소코드 |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `ALL`, `KRX`, `NXT` | 국내거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts transaction-history --from 20260529 --to 20260529 --kind value --product all --exchange ALL --format json
```

### `kiwoomcli domestic accounts daily-return-detail`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00016`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--from` | Yes | `fr_dt` | `date_yyyymmdd` |  | 평가시작일 YYYYMMDD |
| `--to` | Yes | `to_dt` | `date_yyyymmdd` |  | 평가종료일 YYYYMMDD |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts daily-return-detail --from 20260529 --to 20260529 --format json
```

### `kiwoomcli domestic accounts today-status`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00017`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts today-status --format json
```

### `kiwoomcli domestic accounts holdings`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00018`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--basis` | Yes | `qry_tp` | `market` | `total`, `individual` | 조회구분 |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `KRX`, `NXT` | 국내거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts holdings --basis total --exchange KRX --format json
```

### `kiwoomcli domestic accounts gold-balance`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt50020`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts gold-balance --format json
```

### `kiwoomcli domestic accounts gold-cash`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt50021`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts gold-cash --format json
```

### `kiwoomcli domestic accounts gold-all-order-fills`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt50030`

Output note: This is gold-account/date-state dependent. It returns rows only
when the selected gold profile/account has matching gold order/fill history on
`--date`; an empty list with a normal Kiwoom return code is a zero-row account
state, not a mapping failure.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `ord_dt` | `date_yyyymmdd` |  | 주문일자 YYYYMMDD |
| `--order` | No | `qry_tp` | `market` | `order`, `reverse` | 조회 순서 |
| `--market-deal` | Yes | `mrkt_deal_tp` | `market` |  | 시장구분 코드 |
| `--asset-kind` | Yes | `stk_bond_tp` | `market` | `all`, `stock`, `bond` | 주식채권구분 |
| `--side` | Yes | `slby_tp` | `market` | `all`, `sell`, `buy` | 매도수구분 |
| `--code` | No | `stk_cd` | `market` |  | 금현물 종목코드(예: M04020000 금 99.99_1kg) |
| `--order-id` | No | `fr_ord_no` | `order_id` |  | 시작주문번호 |
| `--exchange` | No | `dmst_stex_tp` | `market` | `ALL`, `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts gold-all-order-fills --date 20260522 --market-deal 1 --asset-kind all --side all --format json
```

### `kiwoomcli domestic accounts gold-order-fills`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt50031`

Output note: This is gold-account/date-state dependent. It returns rows only
when the selected gold profile/account has matching gold order/fill history; an
empty list with a normal Kiwoom return code is a zero-row account state, not a
mapping failure.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | No | `ord_dt` | `date_yyyymmdd` |  | 주문일자 YYYYMMDD |
| `--order` | Either | `qry_tp` | `market` | `order`, `reverse` | 조회 순서 |
| `--fill-status` | Either | `qry_tp` | `market` | `open`, `filled` | 체결 상태 필터 |
| `--asset-kind` | Yes | `stk_bond_tp` | `market` | `all`, `stock`, `bond` | 주식채권구분 |
| `--side` | Yes | `sell_tp` | `market` | `all`, `sell`, `buy` | 매도수구분 |
| `--code` | No | `stk_cd` | `market` |  | 금현물 종목코드(예: M04020000 금 99.99_1kg) |
| `--order-id` | No | `fr_ord_no` | `order_id` |  | 시작주문번호 |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `ALL`, `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts gold-order-fills --date 20260522 --order order --asset-kind all --side all --exchange ALL --format json
```

### `kiwoomcli domestic accounts gold-transactions`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt50032`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--from` | No | `strt_dt` | `date_yyyymmdd` |  | 시작일자 YYYYMMDD |
| `--to` | No | `end_dt` | `date_yyyymmdd` |  | 종료일자 YYYYMMDD |
| `--kind` | No | `tp` | `market` | `all`, `deposit-withdrawal`, `release`, `trade`, `buy`, `sell`, `deposit`, `withdrawal` | 거래내역 구분 |
| `--code` | No | `stk_cd` | `market` |  | 금현물 종목코드(예: M04020000 금 99.99_1kg) |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts gold-transactions --format json
```

### `kiwoomcli domestic accounts gold-open-orders`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt50075`

Output note: This is gold-account/date-state dependent. It returns rows only
when the selected gold profile/account has matching open gold orders on
`--date`; an empty list with a normal Kiwoom return code is a zero-row account
state, not a mapping failure.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--date` | Yes | `ord_dt` | `date_yyyymmdd` |  | 주문일자 YYYYMMDD |
| `--order` | No | `qry_tp` | `market` | `order`, `reverse` | 조회 순서 |
| `--market-deal` | Yes | `mrkt_deal_tp` | `market` |  | 시장구분 코드 |
| `--asset-kind` | Yes | `stk_bond_tp` | `market` | `all`, `stock`, `bond` | 주식채권구분 |
| `--side` | Yes | `sell_tp` | `market` | `all`, `sell`, `buy` | 매도수구분 |
| `--code` | No | `stk_cd` | `market` |  | 금현물 종목코드(예: M04020000 금 99.99_1kg) |
| `--order-id` | No | `fr_ord_no` | `order_id` |  | 시작주문번호 |
| `--exchange` | No | `dmst_stex_tp` | `market` | `ALL`, `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic accounts gold-open-orders --date 20260522 --market-deal 1 --asset-kind all --side all --format json
```
### `kiwoomcli domestic orders chance`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00010`

Purpose: Check orderable/withdrawable cash before a write command.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--side` | Yes | `trde_tp` | `market` | `sell`, `buy` | Intended side mapped by `maps/arguments.csv`. |
| `--price` | Yes | `uv` | `price` | | Candidate buy price. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Output rule: apply account identifier redaction in CLI output.

Example:

```sh
kiwoomcli domestic orders chance --code 005930 --side buy --price 70000
```

### `kiwoomcli domestic orders margin`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `kt00011`

Purpose: Check orderable quantity by margin rate before a write command.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--price` | No | `uv` | `price` | | Candidate buy price. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Output rule: apply account identifier redaction in CLI output.

Example:

```sh
kiwoomcli domestic orders margin --code 005930 --price 70000
```

### `kiwoomcli domestic orders list-open`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka10075`

Purpose: Query open domestic orders.

Output note: This is account-state dependent. It returns rows only when the
selected account currently has open orders for the filters; an empty list with a
normal Kiwoom return code is a zero-row account state, not a mapping failure.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--stock-scope` | Yes | `all_stk_tp` | `market` | `all`, `stock` | All stocks or single stock query. |
| `--side` | Yes | `trde_tp` | `market` | `all`, `sell`, `buy` | Order side filter. |
| `--code` | No | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--exchange` | Yes | `stex_tp` | `market` | `ALL`, `KRX`, `NXT` | Exchange filter. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Output rule: redact account identifiers in CLI output; order numbers are shown.

### `kiwoomcli domestic orders list-fills`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka10076`

Purpose: Query filled orders/executions.

Output note: This is account-state dependent. It returns rows only when the
selected account has fills matching the filters; an empty list with a normal
Kiwoom return code is a zero-row account state, not a mapping failure.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--stock-scope` | Yes | `qry_tp` | `market` | `all`, `stock` | All stocks or single stock query. |
| `--side` | Yes | `sell_tp` | `market` | `all`, `sell`, `buy` | Order side filter. |
| `--code` | No | `stk_cd` | `stock_code` | | Domestic stock code. |
| `--order-id` | No | `ord_no` | `market` | | Query after the given order number. |
| `--exchange` | Yes | `stex_tp` | `market` | `ALL`, `KRX`, `NXT` | Exchange filter. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Output rule: redact account identifiers in CLI output; order numbers are shown.

### `kiwoomcli domestic orders open-detail`

Status: Implemented

Auth required: yes
Safety: `account_read`
Candidate API: `ka10088`

Purpose: Query open split-order details.

Output note: This is order/account-state dependent. The `--order-id` must refer
to a currently queryable split/open order in the selected account; otherwise an
empty result is expected and is not by itself a mapping failure.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--order-id` | Yes | `ord_no` | `market` | | Order number. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Output rule: redact account identifiers in CLI output; order numbers are shown.

Order write commands submit a network request only when `--confirm` is
present. Without `--confirm`, output shows a short 미전송 주문 확인 message
plus order summary and never calls the order API. Order-type price rules are validated from
`kiwoom_cli/maps/order_price_policies.csv` before request-body construction;
for example, `--order-type limit` requires `--price`, while `--order-type
market` must not include `--price`. Invalid order identifiers are reported
before any network submission path is considered.
Account identifiers are redacted in every formatted output mode, including
`json`, `pretty`, `yaml`, `jsonl`, and `raw`. Order numbers are not redacted so
they can be read from a buy/list response and passed to `orders modify`/`cancel`.

### `kiwoomcli domestic orders buy`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt10000`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--exchange` | No | `dmst_stex_tp` | `market` | `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--qty` | Yes | `ord_qty` | `quantity` |  | 주문수량 |
| `--price` | No | `ord_uv` | `price` |  | 주문단가 |
| `--order-type` | Yes | `trde_tp` | `order_type` | `limit`, `market` | 매매구분 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders buy --code 005930 --qty 1 --order-type limit --price 70000 --format json
kiwoomcli domestic orders buy --code 005930 --qty 1 --order-type limit --price 70000 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders sell`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt10001`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--exchange` | No | `dmst_stex_tp` | `market` | `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--qty` | Yes | `ord_qty` | `quantity` |  | 주문수량 |
| `--price` | No | `ord_uv` | `price` |  | 주문단가 |
| `--order-type` | Yes | `trde_tp` | `order_type` | `limit`, `market` | 매매구분 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders sell --code 005930 --qty 1 --order-type limit --price 70000 --format json
kiwoomcli domestic orders sell --code 005930 --qty 1 --order-type limit --price 70000 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders modify`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt10002`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--exchange` | No | `dmst_stex_tp` | `market` | `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--order-id` | Yes | `orig_ord_no` | `preview_order_id` |  | 원주문번호 |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--qty` | Yes | `mdfy_qty` | `quantity` |  | 정정수량 |
| `--price` | Yes | `mdfy_uv` | `price` |  | 정정단가 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders modify --order-id 0000140 --code 005930 --qty 1 --price 70000 --format json
kiwoomcli domestic orders modify --order-id 0000140 --code 005930 --qty 1 --price 70000 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders cancel`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt10003`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--exchange` | No | `dmst_stex_tp` | `market` | `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--order-id` | Yes | `orig_ord_no` | `preview_order_id` |  | 원주문번호 |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--qty` | Yes | `cncl_qty` | `quantity` |  | 취소수량 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders cancel --order-id 0000140 --code 005930 --qty 1 --format json
kiwoomcli domestic orders cancel --order-id 0000140 --code 005930 --qty 1 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders credit-buy`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt10006`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--qty` | Yes | `ord_qty` | `quantity` |  | 주문수량 |
| `--price` | No | `ord_uv` | `price` |  | 주문단가 |
| `--order-type` | Yes | `trde_tp` | `order_type` | `limit`, `market`, `conditional-limit`, `after-hours-close`, `pre-open`, `after-hours-single`, `best-limit`, `top-priority`, `limit-ioc`, `market-ioc`, `best-ioc`, `limit-fok`, `market-fok`, `best-fok`, `stop-limit`, `mid`, `mid-ioc`, `mid-fok` | 매매구분 |
| `--condition-price` | No | `cond_uv` | `price` |  | 조건단가 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders credit-buy --exchange KRX --code 005930 --qty 1 --order-type limit --price 70000 --format json
kiwoomcli domestic orders credit-buy --exchange KRX --code 005930 --qty 1 --order-type limit --price 70000 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders credit-sell`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt10007`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--qty` | Yes | `ord_qty` | `quantity` |  | 주문수량 |
| `--price` | No | `ord_uv` | `price` |  | 주문단가 |
| `--order-type` | Yes | `trde_tp` | `order_type` | `limit`, `market`, `conditional-limit`, `after-hours-close`, `pre-open`, `after-hours-single`, `best-limit`, `top-priority`, `limit-ioc`, `market-ioc`, `best-ioc`, `limit-fok`, `market-fok`, `best-fok`, `stop-limit`, `mid`, `mid-ioc`, `mid-fok` | 매매구분 |
| `--credit-deal` | Yes | `crd_deal_tp` | `market` | `financing`, `financing-all` | 신용거래구분 |
| `--loan-date` | No | `crd_loan_dt` | `date_yyyymmdd` |  | 대출일 YYYYMMDD |
| `--condition-price` | No | `cond_uv` | `price` |  | 조건단가 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders credit-sell --exchange KRX --code 005930 --qty 1 --order-type limit --price 70000 --credit-deal financing --format json
kiwoomcli domestic orders credit-sell --exchange KRX --code 005930 --qty 1 --order-type limit --price 70000 --credit-deal financing --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders credit-modify`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt10008`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--order-id` | Yes | `orig_ord_no` | `preview_order_id` |  | 원주문번호 |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--qty` | Yes | `mdfy_qty` | `quantity` |  | 정정수량 |
| `--price` | Yes | `mdfy_uv` | `price` |  | 정정단가 |
| `--condition-price` | No | `mdfy_cond_uv` | `price` |  | 정정조건단가 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders credit-modify --exchange KRX --order-id 0000140 --code 005930 --qty 1 --price 70000 --format json
kiwoomcli domestic orders credit-modify --exchange KRX --order-id 0000140 --code 005930 --qty 1 --price 70000 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders credit-cancel`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt10009`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--exchange` | Yes | `dmst_stex_tp` | `market` | `KRX`, `NXT`, `SOR` | 국내거래소구분 |
| `--order-id` | Yes | `orig_ord_no` | `preview_order_id` |  | 원주문번호 |
| `--code` | Yes | `stk_cd` | `stock_code` |  | 6자리 국내 종목코드 |
| `--qty` | Yes | `cncl_qty` | `cancel_quantity` |  | 취소수량; 0이면 잔량 전부 취소 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders credit-cancel --exchange KRX --order-id 0000140 --code 005930 --qty 0 --format json
kiwoomcli domestic orders credit-cancel --exchange KRX --order-id 0000140 --code 005930 --qty 0 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders gold-buy`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt50000`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` |  | 금현물 종목코드(예: M04020000 금 99.99_1kg) |
| `--qty` | Yes | `ord_qty` | `quantity` |  | 주문수량 |
| `--price` | No | `ord_uv` | `price` |  | 주문단가 |
| `--order-type` | Yes | `trde_tp` | `order_type` | `limit`, `limit-ioc`, `limit-fok` | 매매구분 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders gold-buy --code M04020000 --qty 1 --order-type limit --price 70000 --format json
kiwoomcli domestic orders gold-buy --code M04020000 --qty 1 --order-type limit --price 70000 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders gold-sell`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt50001`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` |  | 금현물 종목코드(예: M04020000 금 99.99_1kg) |
| `--qty` | Yes | `ord_qty` | `quantity` |  | 주문수량 |
| `--price` | No | `ord_uv` | `price` |  | 주문단가 |
| `--order-type` | Yes | `trde_tp` | `order_type` | `limit`, `limit-ioc`, `limit-fok` | 매매구분 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders gold-sell --code M04020000 --qty 1 --order-type limit --price 70000 --format json
kiwoomcli domestic orders gold-sell --code M04020000 --qty 1 --order-type limit --price 70000 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders gold-modify`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt50002`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--code` | Yes | `stk_cd` | `market` |  | 금현물 종목코드(예: M04020000 금 99.99_1kg) |
| `--order-id` | Yes | `orig_ord_no` | `preview_order_id` |  | 원주문번호 |
| `--qty` | Yes | `mdfy_qty` | `quantity` |  | 정정수량 |
| `--price` | Yes | `mdfy_uv` | `price` |  | 정정단가 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders gold-modify --code M04020000 --order-id 0000140 --qty 1 --price 70000 --format json
kiwoomcli domestic orders gold-modify --code M04020000 --order-id 0000140 --qty 1 --price 70000 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.

### `kiwoomcli domestic orders gold-cancel`

Status: Implemented

Auth required: yes; submits to the real endpoint only with --confirm
Safety: `order_write`
Candidate API: `kt50003`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--order-id` | Yes | `orig_ord_no` | `preview_order_id` |  | 원주문번호 |
| `--code` | Yes | `stk_cd` | `market` |  | 금현물 종목코드(예: M04020000 금 99.99_1kg) |
| `--qty` | Yes | `cncl_qty` | `cancel_quantity` |  | 취소수량; 0이면 잔량 전부 취소 |
| `--confirm` | No | safety gate | `flag` | | Submits to the real endpoint when present; otherwise shows 미전송 주문 확인 output. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |

Example:

```sh
kiwoomcli domestic orders gold-cancel --order-id 0000140 --code M04020000 --qty 0 --format json
kiwoomcli domestic orders gold-cancel --order-id 0000140 --code M04020000 --qty 0 --format json --confirm
```

Without `--confirm`, the command exits before network submission; with `--confirm`, it submits to the real endpoint.
## Streams

## WebSocket stream output contract

WebSocket stream commands output Kiwoom server messages only. For bounded
`--format json`/`pretty`/`yaml`/`raw` runs, stdout is one list of received server
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

```sh
kiwoomcli domestic streams trades --code 005930 --count 1 --named --format json
```

### Long-running stream capture (OS backgrounding)

Status: Foreground only; no built-in job manager.

Contract:

- Stream commands run in the foreground. Events go to stdout (or the `--output`
  JSONL file); logs/errors go to stderr.
- To keep a subscription running unattended, use `--watch --output <file>` and
  background the process with OS-native tools instead of a CLI job manager:
  `nohup`/`tmux`/`systemd --user` on Linux/macOS, `Start-Process` or 작업
  스케줄러 on Windows.
- The CLI intentionally ships no detached-subprocess job manager, pid files, or
  `streams jobs` subcommands. Process supervision, detachment, and restart are
  delegated to the OS.

Deferred (would require a supervised worker, not a thin pid layer): reconnect
policy, `--until`, `--max-runtime`, daemon/supervisor mode, database/message-queue
sinks, and alert hooks.

### `kiwoomcli domestic streams conditions-list`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `ka10171`

Condition search formulas are created and changed in Kiwoom Hero Moon HTS
(영웅문 HTS). This CLI command only lists formulas already saved in HTS.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `(fixed)` | Yes | `trnm` | `market` |  | TR명 Fixed value: `CNSRLST`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams conditions-list --format json
```

### `kiwoomcli domestic streams conditions-search`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `ka10172`

This command first loads saved conditions with `CNSRLST` in the same WebSocket
session, then sends `CNSRREQ`. If `--seq` is omitted, the first saved condition
from `CNSRLST` is selected.

Condition search formulas are created and changed in Kiwoom Hero Moon HTS
(영웅문 HTS). This CLI command only selects and requests a formula already saved
in HTS.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `(fixed)` | Yes | `trnm` | `market` |  | 서비스명 Fixed value: `CNSRREQ`. |
| `--seq` | No | `seq` | `market` |  | 조건검색식 일련번호; 생략 시 저장 조건검색식 목록의 첫 번째 조건식을 사용 |
| `(fixed)` | Yes | `search_type` | `market` |  | 조회타입 Fixed value: `0`. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--cont` | No | `cont_yn` | `market` | `yes`, `no` | 연속조회 여부 |
| `--next-key` | No | `next_key` | `market` |  | 연속조회키 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams conditions-search --exchange KRX --format json
```

### `kiwoomcli domestic streams conditions-subscribe`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `ka10173`

This command first loads saved conditions with `CNSRLST` in the same WebSocket
session, sends `CNSRREQ(search_type=1)`, collects realtime messages within the
configured bounds, then clears the CLI-owned subscription with `CNSRCLR`.

Condition search formulas are created and changed in Kiwoom Hero Moon HTS
(영웅문 HTS). This CLI command only selects and subscribes to a formula already
saved in HTS.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `(fixed)` | Yes | `trnm` | `market` |  | 서비스명 Fixed value: `CNSRREQ`. |
| `--seq` | No | `seq` | `market` |  | 조건검색식 일련번호; 생략 시 저장 조건검색식 목록의 첫 번째 조건식을 사용 |
| `(fixed)` | Yes | `search_type` | `market` |  | 조회타입 Fixed value: `1`. |
| `--exchange` | Yes | `stex_tp` | `market` | `KRX`, `NXT`, `ALL` | 거래소구분 |
| `--count` | No | CLI only | `positive_int` | | REAL 데이터 수신 후 종료할 건수. 기본값: `1`. |
| `--duration` | No | CLI only | `positive seconds` | | 조건검색 REAL 데이터를 기다릴 최대 시간(초). 기본값: `15`. |
| `--check` | No | CLI only | `flag` | | 등록 확인용으로 2초 동안 수집 후 REAL 수신 여부와 관계없이 종료한다. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams conditions-subscribe --exchange KRX --check --format json
```

### `kiwoomcli domestic streams conditions-unsubscribe`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `ka10174`

The one-shot CLI cannot clear a subscription created by a previous process.
This command performs a same-session register-and-clear proof:
`CNSRLST -> CNSRREQ(search_type=1) -> CNSRCLR`.

Condition search formulas are created and changed in Kiwoom Hero Moon HTS
(영웅문 HTS). This CLI command only selects and clears a same-session
subscription for a formula already saved in HTS.

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `(fixed)` | Yes | `trnm` | `market` |  | 서비스명 Fixed value: `CNSRCLR`. |
| `--seq` | No | `seq` | `market` |  | 조건검색식 일련번호; 생략 시 저장 조건검색식 목록의 첫 번째 조건식을 사용 |
| `--exchange` | No | CLI only | `market` | `KRX`, `NXT`, `ALL` | 같은 세션 해제 증적을 위한 선행 실시간 조건검색 거래소구분 |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams conditions-unsubscribe --exchange KRX --format json
```

### `kiwoomcli domestic streams order-fills`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `account_read`
Candidate API: `00`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | No | `item` | `market` |  | 주문체결 등록 요소; 보통 공백 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `00`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams order-fills --check --format json
```

Account identifiers must be redacted in formatted output; order numbers are shown.

### `kiwoomcli domestic streams balance`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `account_read`
Candidate API: `04`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | No | `item` | `market` |  | 잔고 등록 요소; 보통 공백 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `04`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams balance --check --format json
```

Account identifiers must be redacted in formatted output; order numbers are shown.

### `kiwoomcli domestic streams momentum`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0A`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `stock_code` |  | 6자리 국내 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0A`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams momentum --code 005930 --check --format json
```

### `kiwoomcli domestic streams trades`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0B`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `stock_code` |  | 6자리 국내 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0B`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams trades --code 005930 --check --format json
```

### `kiwoomcli domestic streams best-quotes`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0C`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `stock_code` |  | 6자리 국내 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0C`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams best-quotes --code 005930 --check --format json
```

### `kiwoomcli domestic streams orderbook`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0D`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `stock_code` |  | 6자리 국내 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0D`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams orderbook --code 005930 --check --format json
```

### `kiwoomcli domestic streams after-hours-orderbook`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0E`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `stock_code` |  | 6자리 국내 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0E`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams after-hours-orderbook --code 005930 --check --format json
```

### `kiwoomcli domestic streams brokers`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0F`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `stock_code` |  | 6자리 국내 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0F`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams brokers --code 005930 --check --format json
```

### `kiwoomcli domestic streams etf-nav`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0G`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `stock_code` |  | 6자리 국내 ETF 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0G`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams etf-nav --code 069500 --check --format json
```

### `kiwoomcli domestic streams expected-fills`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0H`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `stock_code` |  | 6자리 국내 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0H`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams expected-fills --code 005930 --check --format json
```

### `kiwoomcli domestic streams gold-conversion`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0I`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `market` | `MGD`, `MGU` | MGD 또는 MGU |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0I`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams gold-conversion --code MGD --check --format json
```

### `kiwoomcli domestic streams sector-index`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0J`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `sector_code` |  | 3자리 업종코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0J`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams sector-index --code 001 --check --format json
```

### `kiwoomcli domestic streams sector-change`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0U`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `sector_code` |  | 3자리 업종코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0U`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams sector-change --code 001 --check --format json
```

### `kiwoomcli domestic streams stock-info`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0g`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `stock_code` |  | 6자리 국내 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0g`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams stock-info --code 005930 --check --format json
```

### `kiwoomcli domestic streams elw-theory`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0m`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `instrument_code` |  | 6자리 ELW 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0m`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams elw-theory --code 57JBHH --check --format json
```

### `kiwoomcli domestic streams market-open`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0s`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | No | `item` | `market` |  | 장시작시간 등록 요소; 보통 공백 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0s`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams market-open --check --format json
```

### `kiwoomcli domestic streams elw-indicator`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0u`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `instrument_code` |  | 6자리 ELW 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0u`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams elw-indicator --code 57JBHH --check --format json
```

### `kiwoomcli domestic streams program-trades`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `0w`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | Yes | `item` | `stock_code` |  | 6자리 국내 종목코드 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `0w`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams program-trades --code 005930 --check --format json
```

### `kiwoomcli domestic streams vi`

Status: Implemented

Runtime: WebSocket through `get_ws_client`
Safety: `read`
Candidate API: `1h`

| Option | Required | Kiwoom field | Type | Choices | Description |
| --- | :---: | --- | --- | --- | --- |
| `--action` | No | `trnm` | `market` | `subscribe`, `unsubscribe` | 등록 또는 해지 |
| `--group` | No | `grp_no` | `quantity` |  | 그룹번호 |
| `--refresh` | No | `refresh` | `market` | `yes`, `no` | 기존등록 유지 여부 |
| `--code` | No | `item` | `market` |  | 종목코드; 전체 수신은 공백 |
| `(fixed)` | Yes | `type` | `market` |  | 실시간 항목 Fixed value: `1h`. |
| `--format` | No | output only | `output_format` | `pretty`, `json`, `jsonl`, `yaml` | Output format. |
| `--profile` | No | runtime | `account_alias` | | Profile alias. |
| `--mode` | No | runtime | `mode` | `demo`, `real` | Runtime mode. |

Example:

```sh
kiwoomcli domestic streams vi --check --format json
```

## Policy-Design APIs

### `해외주식 > 기타`

Status: Review

These APIs are included in `kiwoom_cli/maps/api_commands.csv` for full 352-API
coverage under the `overseas-review` group. 조회성 rows use `planned`
coverage status. 환전/설정/write-like rows start as `preview-only` and must stop
at request preview/validation until command semantics and safety policy are
approved.

Covered API themes:

- 미국주식 원화주문 가능금액
- 미국주식 원화주문설정금 환전
- 자동환전조회취소
- 목표환율 자동환전 신청
- 외화환전신청
- 해외주식 통합증거금 상세조회

## Blocked Transfers

### `kiwoom deposits list`

Status: Blocked

Only expose when local spec review confirms a clear supported deposit-history or
deposit-status command for the target market.

### `kiwoom withdraws create`

Status: Blocked

Do not expose. A withdrawal execution command requires explicit API support,
separate safety policy, real-call verification rules, and user approval.
