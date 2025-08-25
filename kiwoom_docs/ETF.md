# 키움증권 API 문서

## 국내주식 REST API

### ETF

#### TR 목록

| TR명 | 코드 | 설명 |
| ---- | ---- | ---- |
| ETF수익율요청 | ka40001 | ETF 수익률 정보 조회 |
| ETF종목정보요청 | ka40002 | ETF 종목 정보 조회 |
| ETF일별추이요청 | ka40003 | ETF 일별 추이 정보 조회 |
| ETF전체시세요청 | ka40004 | ETF 전체 시세 정보 조회 |
| ETF시간대별추이요청 | ka40006 | ETF 시간대별 추이 정보 조회 |
| ETF시간대별체결요청 | ka40007 | ETF 시간대별 체결 정보 조회 |
| ETF일자별체결요청 | ka40008 | ETF 일자별 체결 정보 조회 |
| ETF시간대별체결요청 | ka40009 | ETF 시간대별 체결 정보 조회 |
| ETF시간대별추이요청 | ka40010 | ETF 시간대별 추이 정보 조회 |

### ETF수익율요청 (ka40001)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/etf
- **Format**: JSON
- **Content-Type**: application/json;charset=UTF-8

#### 요청 Header

| Element       | 한글명       | Type   | Required | Length | Description                                                                             |
| ------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| authorization | 접근토큰     | String | Y        | 1000   | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출<br/>예) Bearer Egicyx...                     |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅  |
| next-key      | 연속조회키   | String | N        | 50     | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 |
| api-id        | TR명         | String | Y        | 10     |                                                                                         |

#### 요청 Body

| Element            | 한글명           | Type   | Required | Length | Description                   |
| ------------------ | ---------------- | ------ | -------- | ------ | ----------------------------- |
| stk_cd             | 종목코드         | String | Y        | 6      |                               |
| etfobjt_idex_cd    | ETF대상지수코드  | String | Y        | 3      |                               |
| dt                 | 기간             | String | Y        | 1      | 0:1주, 1:1달, 2:6개월, 3:1년  |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                        | 한글명                   | Type   | Required | Length | Description |
| ------------------------------ | ------------------------ | ------ | -------- | ------ | ----------- |
| etfprft_rt_lst                 | ETF수익율                | LIST   | N        |        |             |
| - etfprft_rt                   | ETF수익률                | String | N        | 20     |             |
| - cntr_prft_rt                 | 체결수익률               | String | N        | 20     |             |
| - for_netprps_qty              | 외인순매수수량           | String | N        | 20     |             |
| - orgn_netprps_qty             | 기관순매수수량           | String | N        | 20     |             |

#### 요청 예시

```json
{
	"stk_cd": "069500",
	"etfobjt_idex_cd": "207",
	"dt": "3"
}
```

#### 응답 예시

```json
{
	"etfprft_rt_lst":
		[
			{
				"etfprft_rt":"-1.33",
				"cntr_prft_rt":"-1.75",
				"for_netprps_qty":"0",
				"orgn_netprps_qty":""
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### ETF종목정보요청 (ka40002)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/etf
- **Format**: JSON
- **Content-Type**: application/json;charset=UTF-8

#### 요청 Header

| Element       | 한글명       | Type   | Required | Length | Description                                                                             |
| ------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| authorization | 접근토큰     | String | Y        | 1000   | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출<br/>예) Bearer Egicyx...                     |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅  |
| next-key      | 연속조회키   | String | N        | 50     | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 |
| api-id        | TR명         | String | Y        | 10     |                                                                                         |

#### 요청 Body

| Element | 한글명   | Type   | Required | Length | Description |
| ------- | -------- | ------ | -------- | ------ | ----------- |
| stk_cd  | 종목코드 | String | Y        | 6      |             |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element            | 한글명           | Type   | Required | Length | Description |
| ------------------ | ---------------- | ------ | -------- | ------ | ----------- |
| stk_nm             | 종목명           | String | N        | 20     |             |
| etfobjt_idex_nm    | ETF대상지수명    | String | N        | 20     |             |
| wonju_pric         | 원주가격         | String | N        | 20     |             |
| etftxon_type       | ETF과세유형      | String | N        | 20     |             |
| etntxon_type       | ETN과세유형      | String | N        | 20     |             |

#### 요청 예시

```json
{
	"stk_cd": "069500"
}
```

#### 응답 예시

```json
{
	"stk_nm":"KODEX 200",
	"etfobjt_idex_nm":"",
	"wonju_pric":"10",
	"etftxon_type":"보유기간과세",
	"etntxon_type":"보유기간과세",
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### ETF일별추이요청 (ka40003)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/etf
- **Format**: JSON
- **Content-Type**: application/json;charset=UTF-8

#### 요청 Header

| Element       | 한글명       | Type   | Required | Length | Description                                                                             |
| ------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| authorization | 접근토큰     | String | Y        | 1000   | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출<br/>예) Bearer Egicyx...                     |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅  |
| next-key      | 연속조회키   | String | N        | 50     | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 |
| api-id        | TR명         | String | Y        | 10     |                                                                                         |

#### 요청 Body

| Element | 한글명   | Type   | Required | Length | Description |
| ------- | -------- | ------ | -------- | ------ | ----------- |
| stk_cd  | 종목코드 | String | Y        | 6      |             |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                | 한글명           | Type   | Required | Length | Description |
| ---------------------- | ---------------- | ------ | -------- | ------ | ----------- |
| etfdaly_trnsn          | ETF일별추이      | LIST   | N        |        |             |
| - cntr_dt              | 체결일자         | String | N        | 20     |             |
| - cur_prc              | 현재가           | String | N        | 20     |             |
| - pre_sig              | 대비기호         | String | N        | 20     |             |
| - pred_pre             | 전일대비         | String | N        | 20     |             |
| - pre_rt               | 대비율           | String | N        | 20     |             |
| - trde_qty             | 거래량           | String | N        | 20     |             |
| - nav                  | NAV              | String | N        | 20     |             |
| - acc_trde_prica       | 누적거래대금     | String | N        | 20     |             |
| - navidex_dispty_rt    | NAV/지수괴리율   | String | N        | 20     |             |
| - navetfdispty_rt      | NAV/ETF괴리율    | String | N        | 20     |             |
| - trace_eor_rt         | 추적오차율       | String | N        | 20     |             |
| - trace_cur_prc        | 추적현재가       | String | N        | 20     |             |
| - trace_pred_pre       | 추적전일대비     | String | N        | 20     |             |
| - trace_pre_sig        | 추적대비기호     | String | N        | 20     |             |

#### 요청 예시

```json
{
	"stk_cd": "069500"
}
```

#### 응답 예시

```json
{
	"etfdaly_trnsn":
		[
			{
				"cntr_dt":"20241125",
				"cur_prc":"100535",
				"pre_sig":"0",
				"pred_pre":"0",
				"pre_rt":"0.00",
				"trde_qty":"0",
				"nav":"0.00",
				"acc_trde_prica":"0",
				"navidex_dispty_rt":"0.00",
				"navetfdispty_rt":"0.00",
				"trace_eor_rt":"0",
				"trace_cur_prc":"0",
				"trace_pred_pre":"0",
				"trace_pre_sig":"3"
			},
			{
				"cntr_dt":"20241122",
				"cur_prc":"100535",
				"pre_sig":"0",
				"pred_pre":"0",
				"pre_rt":"0.00",
				"trde_qty":"0",
				"nav":"+100584.57",
				"acc_trde_prica":"0",
				"navidex_dispty_rt":"0.00",
				"navetfdispty_rt":"-0.05",
				"trace_eor_rt":"0",
				"trace_cur_prc":"0",
				"trace_pred_pre":"0",
				"trace_pre_sig":"3"
			},
			{
				"cntr_dt":"20241121",
				"cur_prc":"100535",
				"pre_sig":"0",
				"pred_pre":"0",
				"pre_rt":"0.00",
				"trde_qty":"0",
				"nav":"+100563.36",
				"acc_trde_prica":"0",
				"navidex_dispty_rt":"0.00",
				"navetfdispty_rt":"-0.03",
				"trace_eor_rt":"0",
				"trace_cur_pric":"0",
				"trace_pred_pre":"0",
				"trace_pre_sig":"3"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### ETF전체시세요청 (ka40004)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/etf
- **Format**: JSON
- **Content-Type**: application/json;charset=UTF-8

#### 요청 Header

| Element       | 한글명       | Type   | Required | Length | Description                                                                             |
| ------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| authorization | 접근토큰     | String | Y        | 1000   | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출<br/>예) Bearer Egicyx...                     |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅  |
| next-key      | 연속조회키   | String | N        | 50     | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 |
| api-id        | TR명         | String | Y        | 10     |                                                                                         |

#### 요청 Body

| Element    | 한글명       | Type   | Required | Length | Description                                                                                                                                                      |
| ---------- | ------------ | ------ | -------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| txon_type  | 과세유형     | String | Y        | 1      | 0:전체, 1:비과세, 2:보유기간과세, 3:회사형, 4:외국, 5:비과세해외(보유기간관세)                                                                                   |
| navpre     | NAV대비      | String | Y        | 1      | 0:전체, 1:NAV > 전일종가, 2:NAV < 전일종가                                                                                                                       |
| mngmcomp   | 운용사       | String | Y        | 4      | 0000:전체, 3020:KODEX(삼성), 3027:KOSEF(키움), 3191:TIGER(미래에셋), 3228:KINDEX(한국투자), 3023:KStar(KB), 3022:아리랑(한화), 9999:기타운용사                 |
| txon_yn    | 과세여부     | String | Y        | 1      | 0:전체, 1:과세, 2:비과세                                                                                                                                         |
| trace_idex | 추적지수     | String | Y        | 1      | 0:전체                                                                                                                                                           |
| stex_tp    | 거래소구분   | String | Y        | 1      | 1:KRX, 2:NXT, 3:통합                                                                                                                                             |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element            | 한글명       | Type   | Required | Length | Description |
| ------------------ | ------------ | ------ | -------- | ------ | ----------- |
| etfall_mrpr        | ETF전체시세  | LIST   | N        |        |             |
| - stk_cd           | 종목코드     | String | N        | 20     |             |
| - stk_cls          | 종목분류     | String | N        | 20     |             |
| - stk_nm           | 종목명       | String | N        | 20     |             |
| - close_pric       | 종가         | String | N        | 20     |             |
| - pre_sig          | 대비기호     | String | N        | 20     |             |
| - pred_pre         | 전일대비     | String | N        | 20     |             |
| - pre_rt           | 대비율       | String | N        | 20     |             |
| - trde_qty         | 거래량       | String | N        | 20     |             |
| - nav              | NAV          | String | N        | 20     |             |
| - trace_eor_rt     | 추적오차율   | String | N        | 20     |             |
| - txbs             | 과표기준     | String | N        | 20     |             |
| - dvid_bf_base     | 배당전기준   | String | N        | 20     |             |
| - pred_dvida       | 전일배당금   | String | N        | 20     |             |
| - trace_idex_nm    | 추적지수명   | String | N        | 20     |             |
| - drng             | 배수         | String | N        | 20     |             |
| - trace_idex_cd    | 추적지수코드 | String | N        | 20     |             |
| - trace_idex       | 추적지수     | String | N        | 20     |             |
| - trace_flu_rt     | 추적등락율   | String | N        | 20     |             |

#### 요청 예시

```json
{
	"txon_type": "0",
	"navpre": "0",
	"mngmcomp": "0000",
	"txon_yn": "0",
	"trace_idex": "0",
	"stex_tp": "1"
}
```

#### 응답 예시

```json
{
	"etfall_mrpr":
		[
			{
				"stk_cd":"069500",
				"stk_cls":"19",
				"stk_nm":"KODEX 200",
				"close_pric":"24200",
				"pre_sig":"3",
				"pred_pre":"0",
				"pre_rt":"0.00",
				"trde_qty":"0",
				"nav":"25137.83",
				"trace_eor_rt":"0.00",
				"txbs":"",
				"dvid_bf_base":"",
				"pred_dvida":"",
				"trace_idex_nm":"KOSPI100",
				"drng":"",
				"trace_idex_cd":"",
				"trace_idex":"24200",
				"trace_flu_rt":"0.00"
			},
			{
				"stk_cd":"069500",
				"stk_cls":"19",
				"stk_nm":"KODEX 200",
				"close_pric":"33120",
				"pre_sig":"3",
				"pred_pre":"0",
				"pre_rt":"0.00",
				"trde_qty":"0",
				"nav":"33351.27",
				"trace_eor_rt":"0.00",
				"txbs":"",
				"dvid_bf_base":"",
				"pred_dvida":"",
				"trace_idex_nm":"KOSPI200",
				"drng":"",
				"trace_idex_cd":"",
				"trace_idex":"33120",
				"trace_flu_rt":"0.00"
			},
			{
				"stk_cd":"069660",
				"stk_cls":"19",
				"stk_nm":"KOSEF 200",
				"close_pric":"32090",
				"pre_sig":"3",
				"pred_pre":"0",
				"pre_rt":"0.00",
				"trde_qty":"0",
				"nav":"33316.97",
				"trace_eor_rt":"0.00",
				"txbs":"",
				"dvid_bf_base":"",
				"pred_dvida":"",
				"trace_idex_nm":"KOSPI200",
				"drng":"",
				"trace_idex_cd":"",
				"trace_idex":"32090",
				"trace_flu_rt":"0.00"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### ETF시간대별추이요청 (ka40006)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/etf
- **Format**: JSON
- **Content-Type**: application/json;charset=UTF-8

#### 요청 Header

| Element       | 한글명       | Type   | Required | Length | Description                                                                             |
| ------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| authorization | 접근토큰     | String | Y        | 1000   | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출<br/>예) Bearer Egicyx...                     |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅  |
| next-key      | 연속조회키   | String | N        | 50     | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 |
| api-id        | TR명         | String | Y        | 10     |                                                                                         |

#### 요청 Body

| Element | 한글명   | Type   | Required | Length | Description |
| ------- | -------- | ------ | -------- | ------ | ----------- |
| stk_cd  | 종목코드 | String | Y        | 6      |             |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                    | 한글명               | Type   | Required | Length | Description |
| -------------------------- | -------------------- | ------ | -------- | ------ | ----------- |
| stk_nm                     | 종목명               | String | N        | 20     |             |
| etfobjt_idex_nm            | ETF대상지수명        | String | N        | 20     |             |
| wonju_pric                 | 원주가격             | String | N        | 20     |             |
| etftxon_type               | ETF과세유형          | String | N        | 20     |             |
| etntxon_type               | ETN과세유형          | String | N        | 20     |             |
| etftisl_trnsn              | ETF시간대별추이      | LIST   | N        |        |             |
| - tm                       | 시간                 | String | N        | 20     |             |
| - close_pric               | 종가                 | String | N        | 20     |             |
| - pre_sig                  | 대비기호             | String | N        | 20     |             |
| - pred_pre                 | 전일대비             | String | N        | 20     |             |
| - flu_rt                   | 등락율               | String | N        | 20     |             |
| - trde_qty                 | 거래량               | String | N        | 20     |             |
| - nav                      | NAV                  | String | N        | 20     |             |
| - trde_prica               | 거래대금             | String | N        | 20     |             |
| - navidex                  | NAV지수              | String | N        | 20     |             |
| - navetf                   | NAVETF               | String | N        | 20     |             |
| - trace                    | 추적                 | String | N        | 20     |             |
| - trace_idex               | 추적지수             | String | N        | 20     |             |
| - trace_idex_pred_pre      | 추적지수전일대비     | String | N        | 20     |             |
| - trace_idex_pred_pre_sig  | 추적지수전일대비기호 | String | N        | 20     |             |

#### 요청 예시

```json
{
	"stk_cd": "069500"
}
```

#### 응답 예시

```json
{
	"stk_nm":"KODEX 200",
	"etfobjt_idex_nm":"KOSPI200",
	"wonju_pric":"-10",
	"etftxon_type":"보유기간과세",
	"etntxon_type":"보유기간과세",
	"etftisl_trnsn":
		[
			{
				"tm":"132211",
				"close_pric":"+4900",
				"pre_sig":"2",
				"pred_pre":"+450",
				"flu_rt":"+10.11",
				"trde_qty":"1",
				"nav":"-4548.33",
				"trde_prica":"0",
				"navidex":"-72.38",
				"navetf":"+7.18",
				"trace":"0.00",
				"trace_idex":"+164680",
				"trace_idex_pred_pre":"+123",
				"trace_idex_pred_pre_sig":"2"
			},
			{
				"tm":"132210",
				"close_pric":"+4900",
				"pre_sig":"2",
				"pred_pre":"+450",
				"flu_rt":"+10.11",
				"trde_qty":"1",
				"nav":"-4548.33",
				"trde_prica":"0",
				"navidex":"-72.38",
				"navetf":"+7.18",
				"trace":"0.00",
				"trace_idex":"+164680",
				"trace_idex_pred_pre":"+123",
				"trace_idex_pred_pre_sig":"2"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### ETF시간대별체결요청 (ka40007)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/etf
- **Format**: JSON
- **Content-Type**: application/json;charset=UTF-8

#### 요청 Header

| Element       | 한글명       | Type   | Required | Length | Description                                                                             |
| ------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| authorization | 접근토큰     | String | Y        | 1000   | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출<br/>예) Bearer Egicyx...                     |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅  |
| next-key      | 연속조회키   | String | N        | 50     | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 |
| api-id        | TR명         | String | Y        | 10     |                                                                                         |

#### 요청 Body

| Element | 한글명   | Type   | Required | Length | Description |
| ------- | -------- | ------ | -------- | ------ | ----------- |
| stk_cd  | 종목코드 | String | Y        | 6      |             |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                | 한글명               | Type   | Required | Length | Description         |
| ---------------------- | -------------------- | ------ | -------- | ------ | ------------------- |
| stk_cls                | 종목분류             | String | N        | 20     |                     |
| stk_nm                 | 종목명               | String | N        | 20     |                     |
| etfobjt_idex_nm        | ETF대상지수명        | String | N        | 20     |                     |
| etfobjt_idex_cd        | ETF대상지수코드      | String | N        | 20     |                     |
| objt_idex_pre_rt       | 대상지수대비율       | String | N        | 20     |                     |
| wonju_pric             | 원주가격             | String | N        | 20     |                     |
| etftisl_cntr_array     | ETF시간대별체결배열  | LIST   | N        |        |                     |
| - cntr_tm              | 체결시간             | String | N        | 20     |                     |
| - cur_prc              | 현재가               | String | N        | 20     |                     |
| - pre_sig              | 대비기호             | String | N        | 20     |                     |
| - pred_pre             | 전일대비             | String | N        | 20     |                     |
| - trde_qty             | 거래량               | String | N        | 20     |                     |
| - stex_tp              | 거래소구분           | String | N        | 20     | KRX, NXT, 통합      |

#### 요청 예시

```json
{
	"stk_cd": "069500"
}
```

#### 응답 예시

```json
{
	"stk_cls":"20",
	"stk_nm":"KODEX 200",
	"etfobjt_idex_nm":"KOSPI200",
	"etfobjt_idex_cd":"207",
	"objt_idex_pre_rt":"10.00",
	"wonju_pric":"-10",
	"etftisl_cntr_array":
		[
			{
				"cntr_tm":"130747",
				"cur_prc":"+4900",
				"pre_sig":"2",
				"pred_pre":"+450",
				"trde_qty":"1",
				"stex_tp":"KRX"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### ETF일자별체결요청 (ka40008)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/etf
- **Format**: JSON
- **Content-Type**: application/json;charset=UTF-8

#### 요청 Header

| Element       | 한글명       | Type   | Required | Length | Description                                                                             |
| ------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| authorization | 접근토큰     | String | Y        | 1000   | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출<br/>예) Bearer Egicyx...                     |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅  |
| next-key      | 연속조회키   | String | N        | 50     | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 |
| api-id        | TR명         | String | Y        | 10     |                                                                                         |

#### 요청 Body

| Element | 한글명   | Type   | Required | Length | Description |
| ------- | -------- | ------ | -------- | ------ | ----------- |
| stk_cd  | 종목코드 | String | Y        | 6      |             |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                | 한글명               | Type   | Required | Length | Description |
| ---------------------- | -------------------- | ------ | -------- | ------ | ----------- |
| cntr_tm                | 체결시간             | String | N        | 20     |             |
| cur_prc                | 현재가               | String | N        | 20     |             |
| pre_sig                | 대비기호             | String | N        | 20     |             |
| pred_pre               | 전일대비             | String | N        | 20     |             |
| trde_qty               | 거래량               | String | N        | 20     |             |
| etfnetprps_qty_array   | ETF순매수수량배열    | LIST   | N        |        |             |
| - dt                   | 일자                 | String | N        | 20     |             |
| - cur_prc_n            | 현재가n              | String | N        | 20     |             |
| - pre_sig_n            | 대비기호n            | String | N        | 20     |             |
| - pred_pre_n           | 전일대비n            | String | N        | 20     |             |
| - acc_trde_qty         | 누적거래량           | String | N        | 20     |             |
| - for_netprps_qty      | 외인순매수수량       | String | N        | 20     |             |
| - orgn_netprps_qty     | 기관순매수수량       | String | N        | 20     |             |

#### 요청 예시

```json
{
	"stk_cd": "069500"
}
```

#### 응답 예시

```json
{
	"cntr_tm":"130747",
	"cur_prc":"+4900",
	"pre_sig":"2",
	"pred_pre":"+450",
	"trde_qty":"1",
	"etfnetprps_qty_array":
		[
			{
				"dt":"20241125",
				"cur_prc_n":"+4900",
				"pre_sig_n":"2",
				"pred_pre_n":"+450",
				"acc_trde_qty":"1",
				"for_netprps_qty":"0",
				"orgn_netprps_qty":"0"
			},
			{
				"dt":"20241122",
				"cur_prc_n":"-4450",
				"pre_sig_n":"5",
				"pred_pre_n":"-60",
				"acc_trde_qty":"46",
				"for_netprps_qty":"--10558895",
				"orgn_netprps_qty":"0"
			},
			{
				"dt":"20241121",
				"cur_prc_n":"4510",
				"pre_sig_n":"3",
				"pred_pre_n":"0",
				"acc_trde_qty":"0",
				"for_netprps_qty":"--8894146",
				"orgn_netprps_qty":"0"
			},
			{
				"dt":"20241120",
				"cur_prc_n":"-4510",
				"pre_sig_n":"5",
				"pred_pre_n":"-160",
				"acc_trde_qty":"0",
				"for_netprps_qty":"--3073507",
				"orgn_netprps_qty":"0"
			},
			{
				"dt":"20241119",
				"cur_prc_n":"+4670",
				"pre_sig_n":"2",
				"pred_pre_n":"+160",
				"acc_trde_qty":"94",
				"for_netprps_qty":"--2902200",
				"orgn_netprps_qty":"0"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### ETF시간대별체결요청 (ka40009)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/etf
- **Format**: JSON
- **Content-Type**: application/json;charset=UTF-8

#### 요청 Header

| Element       | 한글명       | Type   | Required | Length | Description                                                                             |
| ------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| authorization | 접근토큰     | String | Y        | 1000   | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출<br/>예) Bearer Egicyx...                     |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅  |
| next-key      | 연속조회키   | String | N        | 50     | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 |
| api-id        | TR명         | String | Y        | 10     |                                                                                         |

#### 요청 Body

| Element | 한글명   | Type   | Required | Length | Description |
| ------- | -------- | ------ | -------- | ------ | ----------- |
| stk_cd  | 종목코드 | String | Y        | 6      |             |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                | 한글명               | Type   | Required | Length | Description |
| ---------------------- | -------------------- | ------ | -------- | ------ | ----------- |
| etfnavarray            | ETFNAV배열           | LIST   | N        |        |             |
| - nav                  | NAV                  | String | N        | 20     |             |
| - navpred_pre          | NAV전일대비          | String | N        | 20     |             |
| - navflu_rt            | NAV등락율            | String | N        | 20     |             |
| - trace_eor_rt         | 추적오차율           | String | N        | 20     |             |
| - dispty_rt            | 괴리율               | String | N        | 20     |             |
| - stkcnt               | 주식수               | String | N        | 20     |             |
| - base_pric            | 기준가               | String | N        | 20     |             |
| - for_rmnd_qty         | 외인보유수량         | String | N        | 20     |             |
| - repl_pric            | 대용가               | String | N        | 20     |             |
| - conv_pric            | 환산가격             | String | N        | 20     |             |
| - drstk                | DR/주                | String | N        | 20     |             |
| - wonju_pric           | 원주가격             | String | N        | 20     |             |

#### 요청 예시

```json
{
	"stk_cd": "069500"
}
```

#### 응답 예시

```json
{
	"etfnavarray":
		[
			{
				"nav":"",
				"navpred_pre":"",
				"navflu_rt":"",
				"trace_eor_rt":"",
				"dispty_rt":"",
				"stkcnt":"133100",
				"base_pric":"4450",
				"for_rmnd_qty":"",
				"repl_pric":"",
				"conv_pric":"",
				"drstk":"",
				"wonju_pric":""
			},
			{
				"nav":"",
				"navpred_pre":"",
				"navflu_rt":"",
				"trace_eor_rt":"",
				"dispty_rt":"",
				"stkcnt":"133100",
				"base_pric":"4510",
				"for_rmnd_qty":"",
				"repl_pric":"",
				"conv_pric":"",
				"drstk":"",
				"wonju_pric":""
			},
			{
				"nav":"",
				"navpred_pre":"",
				"navflu_rt":"",
				"trace_eor_rt":"",
				"dispty_rt":"",
				"stkcnt":"133100",
				"base_pric":"4510",
				"for_rmnd_qty":"",
				"repl_pric":"",
				"conv_pric":"",
				"drstk":"",
				"wonju_pric":""
			},
			{
				"nav":"",
				"navpred_pre":"",
				"navflu_rt":"",
				"trace_eor_rt":"",
				"dispty_rt":"",
				"stkcnt":"133100",
				"base_pric":"4670",
				"for_rmnd_qty":"",
				"repl_pric":"",
				"conv_pric":"",
				"drstk":"",
				"wonju_pric":""
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

### ETF시간대별추이요청 (ka40010)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/etf
- **Format**: JSON
- **Content-Type**: application/json;charset=UTF-8

#### 요청 Header

| Element       | 한글명       | Type   | Required | Length | Description                                                                             |
| ------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| authorization | 접근토큰     | String | Y        | 1000   | 토큰 지정시 토큰타입("Bearer") 붙혀서 호출<br/>예) Bearer Egicyx...                     |
| cont-yn       | 연속조회여부 | String | N        | 1      | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 cont-yn값 세팅  |
| next-key      | 연속조회키   | String | N        | 50     | 응답 Header의 연속조회여부값이 Y일 경우 다음데이터 요청시 응답 Header의 next-key값 세팅 |
| api-id        | TR명         | String | Y        | 10     |                                                                                         |

#### 요청 Body

| Element | 한글명   | Type   | Required | Length | Description |
| ------- | -------- | ------ | -------- | ------ | ----------- |
| stk_cd  | 종목코드 | String | Y        | 6      |             |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                | 한글명               | Type   | Required | Length | Description |
| ---------------------- | -------------------- | ------ | -------- | ------ | ----------- |
| etftisl_trnsn          | ETF시간대별추이      | LIST   | N        |        |             |
| - cur_prc              | 현재가               | String | N        | 20     |             |
| - pre_sig              | 대비기호             | String | N        | 20     |             |
| - pred_pre             | 전일대비             | String | N        | 20     |             |
| - trde_qty             | 거래량               | String | N        | 20     |             |
| - for_netprps          | 외인순매수           | String | N        | 20     |             |

#### 요청 예시

```json
{
	"stk_cd": "069500"
}
```

#### 응답 예시

```json
{
	"etftisl_trnsn":
		[
			{
				"cur_prc":"4450",
				"pre_sig":"3",
				"pred_pre":"0",
				"trde_qty":"0",
				"for_netprps":"0"
			},
			{
				"cur_prc":"-4450",
				"pre_sig":"5",
				"pred_pre":"-60",
				"trde_qty":"46",
				"for_netprps":"--10558895"
			},
			{
				"cur_prc":"4510",
				"pre_sig":"3",
				"pred_pre":"0",
				"trde_qty":"0",
				"for_netprps":"--8894146"
			},
			{
				"cur_prc":"-4510",
				"pre_sig":"5",
				"pred_pre":"-160",
				"trde_qty":"0",
				"for_netprps":"--3073507"
			},
			{
				"cur_prc":"+4670",
				"pre_sig":"2",
				"pred_pre":"+160",
				"trde_qty":"94",
				"for_netprps":"--2902200"
			},
			{
				"cur_prc":"-4510",
				"pre_sig":"5",
				"pred_pre":"-275",
				"trde_qty":"0",
				"for_netprps":"--1249609"
			},
			{
				"cur_prc":"-4510",
				"pre_sig":"5",
				"pred_pre":"-315",
				"trde_qty":"0",
				"for_netprps":"--2634816"
			},
			{
				"cur_prc":"-4510",
				"pre_sig":"5",
				"pred_pre":"-285",
				"trde_qty":"0",
				"for_netprps":"--2365477"
			},
			{
				"cur_prc":"-4450",
				"pre_sig":"5",
				"pred_pre":"-225",
				"trde_qty":"6",
				"for_netprps":"--571909"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---
