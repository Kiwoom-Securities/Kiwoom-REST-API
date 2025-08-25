# 키움증권 API 문서

## 국내주식 REST API

### ELW

#### TR 목록

| TR명 | 코드 | 설명 |
| ---- | ---- | ---- |

### ELW일별민감도지표요청 (ka10048)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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
| elwdaly_snst_ix        | ELW일별민감도지표    | LIST   | N        |        |             |
| - dt                   | 일자                 | String | N        | 20     |             |
| - iv                   | IV                   | String | N        | 20     |             |
| - delta                | 델타                 | String | N        | 20     |             |
| - gam                  | 감마                 | String | N        | 20     |             |
| - theta                | 쎄타                 | String | N        | 20     |             |
| - vega                 | 베가                 | String | N        | 20     |             |
| - law                  | 로                   | String | N        | 20     |             |
| - lp                   | LP                   | String | N        | 20     |             |

#### 요청 예시

```json
{
	"stk_cd": "57JBHH"
}
```

#### 응답 예시

```json
{
	"elwdaly_snst_ix":
		[
			{
				"dt":"000000",
				"iv":"1901",
				"delta":"126664",
				"gam":"5436",
				"theta":"-5271886",
				"vega":"41752995",
				"law":"13982453",
				"lp":"0"
			},
			{
				"dt":"000000",
				"iv":"1901",
				"delta":"126664",
				"gam":"5436",
				"theta":"-5271886",
				"vega":"41752995",
				"law":"13982453",
				"lp":"0"
			},
			{
				"dt":"000000",
				"iv":"1901",
				"delta":"126664",
				"gam":"5436",
				"theta":"-5271886",
				"vega":"41752995",
				"law":"13982453",
				"lp":"0"
			},
			{
				"dt":"000000",
				"iv":"1901",
				"delta":"126664",
				"gam":"5436",
				"theta":"-5271886",
				"vega":"41752995",
				"law":"13982453",
				"lp":"0"
			},
			{
				"dt":"000000",
				"iv":"1901",
				"delta":"126664",
				"gam":"5436",
				"theta":"-5271886",
				"vega":"41752995",
				"law":"13982453",
				"lp":"0"
			},
			{
				"dt":"000000",
				"iv":"1901",
				"delta":"126664",
				"gam":"5436",
				"theta":"-5271886",
				"vega":"41752995",
				"law":"13982453",
				"lp":"0"
			},
			{
				"dt":"000000",
				"iv":"1901",
				"delta":"126664",
				"gam":"5436",
				"theta":"-5271886",
				"vega":"41752995",
				"law":"13982453",
				"lp":"0"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---

### ELW민감도지표요청 (ka10050)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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
| elwsnst_ix_array       | ELW민감도지표배열    | LIST   | N        |        |             |
| - cntr_tm              | 체결시간             | String | N        | 20     |             |
| - cur_prc              | 현재가               | String | N        | 20     |             |
| - elwtheory_pric       | ELW이론가            | String | N        | 20     |             |
| - iv                   | IV                   | String | N        | 20     |             |
| - delta                | 델타                 | String | N        | 20     |             |
| - gam                  | 감마                 | String | N        | 20     |             |
| - theta                | 쎄타                 | String | N        | 20     |             |
| - vega                 | 베가                 | String | N        | 20     |             |
| - law                  | 로                   | String | N        | 20     |             |
| - lp                   | LP                   | String | N        | 20     |             |

#### 요청 예시

```json
{
	"stk_cd": "57JBHH"
}
```

#### 응답 예시

```json
{
	"elwsnst_ix_array":
		[
			{
				"cntr_tm":"095820",
				"cur_prc":"5",
				"elwtheory_pric":"4",
				"iv":"3336",
				"delta":"7128",
				"gam":"904",
				"theta":"-2026231",
				"vega":"1299294",
				"law":"95218",
				"lp":"0"
			},
			{
				"cntr_tm":"095730",
				"cur_prc":"5",
				"elwtheory_pric":"4",
				"iv":"3342",
				"delta":"7119",
				"gam":"902",
				"theta":"-2026391",
				"vega":"1297498",
				"law":"95078",
				"lp":"0"
			},
			{
				"cntr_tm":"095640",
				"cur_prc":"5",
				"elwtheory_pric":"4",
				"iv":"3345",
				"delta":"7114",
				"gam":"900",
				"theta":"-2026285",
				"vega":"1296585",
				"law":"95012",
				"lp":"0"
			},
			{
				"cntr_tm":"095550",
				"cur_prc":"5",
				"elwtheory_pric":"4",
				"iv":"3346",
				"delta":"7111",
				"gam":"900",
				"theta":"-2026075",
				"vega":"1296025",
				"law":"94974",
				"lp":"0"
			},
			{
				"cntr_tm":"095500",
				"cur_prc":"5",
				"elwtheory_pric":"4",
				"iv":"3339",
				"delta":"7121",
				"gam":"902",
				"theta":"-2025002",
				"vega":"1298269",
				"law":"95168",
				"lp":"0"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---

### ELW가격급등락요청 (ka30001)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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

| Element              | 한글명             | Type   | Required | Length | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| -------------------- | ------------------ | ------ | -------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| flu_tp               | 등락구분           | String | Y        | 1      | 1:급등, 2:급락                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| tm_tp                | 시간구분           | String | Y        | 1      | 1:분전, 2:일전                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| tm                   | 시간               | String | Y        | 2      | 분 혹은 일입력 (예 1, 3, 5)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| trde_qty_tp          | 거래량구분         | String | Y        | 4      | 0:전체, 10:만주이상, 50:5만주이상, 100:10만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| isscomp_cd           | 발행사코드         | String | Y        | 12     | 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| bsis_aset_cd         | 기초자산코드       | String | Y        | 12     | 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200..                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| rght_tp              | 권리구분           | String | Y        | 3      | 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 005:EX, 006:조기종료콜, 007:조기종료풋                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| lpcd                 | LP코드             | String | Y        | 12     | 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| trde_end_elwskip     | 거래종료ELW제외    | String | Y        | 1      | 0:포함, 1:제외                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                        | 한글명                   | Type   | Required | Length | Description |
| ------------------------------ | ------------------------ | ------ | -------- | ------ | ----------- |
| base_pric_tm                   | 기준가시간               | String | N        | 20     |             |
| elwpric_jmpflu                 | ELW가격급등락            | LIST   | N        |        |             |
| - stk_cd                       | 종목코드                 | String | N        | 20     |             |
| - rank                         | 순위                     | String | N        | 20     |             |
| - stk_nm                       | 종목명                   | String | N        | 20     |             |
| - pre_sig                      | 대비기호                 | String | N        | 20     |             |
| - pred_pre                     | 전일대비                 | String | N        | 20     |             |
| - trde_end_elwbase_pric        | 거래종료ELW기준가        | String | N        | 20     |             |
| - cur_prc                      | 현재가                   | String | N        | 20     |             |
| - base_pre                     | 기준대비                 | String | N        | 20     |             |
| - trde_qty                     | 거래량                   | String | N        | 20     |             |
| - jmp_rt                       | 급등율                   | String | N        | 20     |             |

#### 요청 예시

```json
{
	"flu_tp": "1",
	"tm_tp": "2",
	"tm": "1",
	"trde_qty_tp": "0",
	"isscomp_cd": "000000000000",
	"bsis_aset_cd": "000000000000",
	"rght_tp": "000",
	"lpcd": "000000000000",
	"trde_end_elwskip": "0"
}
```

#### 응답 예시

```json
{
	"base_pric_tm":"기준가(11/21)",
	"elwpric_jmpflu":
		[
			{
			"stk_cd":"57JBHH",
			"rank":"1",
			"stk_nm":"한국JBHHKOSPI200풋",
			"pre_sig":"2",
			"pred_pre":"+10",
			"trde_end_elwbase_pric":"20",
			"cur_prc":"+30",
			"base_pre":"10",
			"trde_qty":"30",
			"jmp_rt":"+50.00"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---

### 거래원별ELW순매매상위요청 (ka30002)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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

| Element              | 한글명             | Type   | Required | Length | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| -------------------- | ------------------ | ------ | -------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| isscomp_cd           | 발행사코드         | String | Y        | 3      | 3자리, 영웅문4 0273화면참조 (교보:001, 신한금융투자:002, 한국투자증권:003, 대신:004, 미래대우:005, ,,,)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| trde_qty_tp          | 거래량구분         | String | Y        | 4      | 0:전체, 5:5천주, 10:만주, 50:5만주, 100:10만주, 500:50만주, 1000:백만주                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| trde_tp              | 매매구분           | String | Y        | 1      | 1:순매수, 2:순매도                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| dt                   | 기간               | String | Y        | 2      | 1:전일, 5:5일, 10:10일, 40:40일, 60:60일                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| trde_end_elwskip     | 거래종료ELW제외    | String | Y        | 1      | 0:포함, 1:제외                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                        | 한글명                   | Type   | Required | Length | Description |
| ------------------------------ | ------------------------ | ------ | -------- | ------ | ----------- |
| trde_ori_elwnettrde_upper      | 거래원별ELW순매매상위    | LIST   | N        |        |             |
| - stk_cd                       | 종목코드                 | String | N        | 20     |             |
| - stk_nm                       | 종목명                   | String | N        | 20     |             |
| - stkpc_flu                    | 주가등락                 | String | N        | 20     |             |
| - flu_rt                       | 등락율                   | String | N        | 20     |             |
| - trde_qty                     | 거래량                   | String | N        | 20     |             |
| - netprps                      | 순매수                   | String | N        | 20     |             |
| - buy_trde_qty                 | 매수거래량               | String | N        | 20     |             |
| - sel_trde_qty                 | 매도거래량               | String | N        | 20     |             |

#### 요청 예시

```json
{
	"isscomp_cd": "003",
	"trde_qty_tp": "0",
	"trde_tp": "2",
	"dt": "60",
	"trde_end_elwskip": "0"
}
```

#### 응답 예시

```json
{
	"trde_ori_elwnettrde_upper":
		[
			{
				"stk_cd":"57JBHH",
				"stk_nm":"한국JBHHKOSPI200풋",
				"stkpc_flu":"--3140",
				"flu_rt":"-88.95",
				"trde_qty":"500290",
				"netprps":"--846970",
				"buy_trde_qty":"+719140",
				"sel_trde_qty":"-1566110"
			},
			{
				"stk_cd":"57JBHH",
				"stk_nm":"한국JBHHKOSPI200풋",
				"stkpc_flu":"+205",
				"flu_rt":"+73.21",
				"trde_qty":"4950000",
				"netprps":"--108850",
				"buy_trde_qty":"+52450",
				"sel_trde_qty":"-161300"
			},
			{
				"stk_cd":"57JBHH",
				"stk_nm":"한국JBHHKOSPI200풋",
				"stkpc_flu":"+340",
				"flu_rt":"+115.25",
				"trde_qty":"60",
				"netprps":"--73960",
				"buy_trde_qty":"+29560",
				"sel_trde_qty":"-103520"
			},
			{
				"stk_cd":"57JBHH",
				"stk_nm":"한국JBHHKOSPI200풋",
				"stkpc_flu":"--65",
				"flu_rt":"-86.67",
				"trde_qty":"20",
				"netprps":"--23550",
				"buy_trde_qty":"+422800",
				"sel_trde_qty":"-446350"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---

### ELWLP보유일별추이요청 (ka30003)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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

| Element        | 한글명       | Type   | Required | Length | Description                                                                             |
| -------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| bsis_aset_cd   | 기초자산코드 | String | Y        | 12     |                                                                                         |
| base_dt        | 기준일자     | String | Y        | 8      | YYYYMMDD                                                                                |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                    | 한글명               | Type   | Required | Length | Description |
| ---------------------------- | -------------------- | ------ | -------- | ------ | ----------- |
| elwlpposs_daly_trnsn       | ELWLP보유일별추이    | LIST   | N        |        |             |
| - dt                       | 일자                 | String | N        | 20     |             |
| - cur_prc                  | 현재가               | String | N        | 20     |             |
| - pre_tp                   | 대비구분             | String | N        | 20     |             |
| - pred_pre                 | 전일대비             | String | N        | 20     |             |
| - flu_rt                   | 등락율               | String | N        | 20     |             |
| - trde_qty                 | 거래량               | String | N        | 20     |             |
| - trde_prica               | 거래대금             | String | N        | 20     |             |
| - chg_qty                  | 변동수량             | String | N        | 20     |             |
| - lprmnd_qty               | LP보유수량           | String | N        | 20     |             |
| - wght                     | 비중                 | String | N        | 20     |             |

#### 요청 예시

```json
{
	"bsis_aset_cd": "57KJ99",
	"base_dt": "20241122"
}
```

#### 응답 예시

```json
{
	"elwlpposs_daly_trnsn":
		[
			{
				"dt":"20241122",
				"cur_prc":"-125700",
				"pre_tp":"5",
				"pred_pre":"-900",
				"flu_rt":"-0.71",
				"trde_qty":"54",
				"trde_prica":"7",
				"chg_qty":"0",
				"lprmnd_qty":"0",
				"wght":"0.00"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---

### ELW괴리율요청 (ka30004)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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

| Element              | 한글명             | Type   | Required | Length | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| -------------------- | ------------------ | ------ | -------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| isscomp_cd           | 발행사코드         | String | Y        | 12     | 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| bsis_aset_cd         | 기초자산코드       | String | Y        | 12     | 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200..                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| rght_tp              | 권리구분           | String | Y        | 3      | 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 005:EX, 006:조기종료콜, 007:조기종료풋                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| lpcd                 | LP코드             | String | Y        | 12     | 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| trde_end_elwskip     | 거래종료ELW제외    | String | Y        | 1      | 1:거래종료ELW제외, 0:거래종료ELW포함                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                        | 한글명                   | Type   | Required | Length | Description |
| ------------------------------ | ------------------------ | ------ | -------- | ------ | ----------- |
| elwdispty_rt                   | ELW괴리율                | LIST   | N        |        |             |
| - stk_cd                       | 종목코드                 | String | N        | 20     |             |
| - isscomp_nm                   | 발행사명                 | String | N        | 20     |             |
| - sqnc                         | 회차                     | String | N        | 20     |             |
| - base_aset_nm                 | 기초자산명               | String | N        | 20     |             |
| - rght_tp                      | 권리구분                 | String | N        | 20     |             |
| - dispty_rt                    | 괴리율                   | String | N        | 20     |             |
| - basis                        | 베이시스                 | String | N        | 20     |             |
| - srvive_dys                   | 잔존일수                 | String | N        | 20     |             |
| - theory_pric                  | 이론가                   | String | N        | 20     |             |
| - cur_prc                      | 현재가                   | String | N        | 20     |             |
| - pre_tp                       | 대비구분                 | String | N        | 20     |             |
| - pred_pre                     | 전일대비                 | String | N        | 20     |             |
| - flu_rt                       | 등락율                   | String | N        | 20     |             |
| - trde_qty                     | 거래량                   | String | N        | 20     |             |
| - stk_nm                       | 종목명                   | String | N        | 20     |             |

#### 요청 예시

```json
{
	"isscomp_cd": "000000000000",
	"bsis_aset_cd": "000000000000",
	"rght_tp": "000",
	"lpcd": "000000000000",
	"trde_end_elwskip": "0"
}
```

#### 응답 예시

```json
{
	"elwdispty_rt":
		[
			{
				"stk_cd":"57JBHH",
				"isscomp_nm":"키움증권",
				"sqnc":"KK27",
				"base_aset_nm":"삼성전자",
				"rght_tp":"콜",
				"dispty_rt":"0",
				"basis":"+5.00",
				"srvive_dys":"21",
				"theory_pric":"0",
				"cur_prc":"5",
				"pre_tp":"3",
				"pred_pre":"0",
				"flu_rt":"0.00",
				"trde_qty":"0",
				"stk_nm":"한국JBHHKOSPI200풋"
			},
			{
				"stk_cd":"57JBHH",
				"isscomp_nm":"키움증권",
				"sqnc":"KL57",
				"base_aset_nm":"삼성전자",
				"rght_tp":"콜",
				"dispty_rt":"0",
				"basis":"+10.00",
				"srvive_dys":"49",
				"theory_pric":"0",
				"cur_prc":"10",
				"pre_tp":"3",
				"pred_pre":"0",
				"flu_rt":"0.00",
				"trde_qty":"0",
				"stk_nm":"한국JBHHKOSPI200풋"
			},
			{
				"stk_cd":"57JBHH",
				"isscomp_nm":"키움증권",
				"sqnc":"KK28",
				"base_aset_nm":"삼성전자",
				"rght_tp":"콜",
				"dispty_rt":"0",
				"basis":"+5.00",
				"srvive_dys":"49",
				"theory_pric":"0",
				"cur_prc":"5",
				"pre_tp":"3",
				"pred_pre":"0",
				"flu_rt":"0.00",
				"trde_qty":"0",
				"stk_nm":"한국JBHHKOSPI200풋"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---

### ELW조건검색요청 (ka30005)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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

| Element        | 한글명       | Type   | Required | Length | Description                                                                             |
| -------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| isscomp_cd     | 발행사코드   | String | Y        | 12     | 12자리입력(전체:000000000000, 한국투자증권:000,,,3, 미래대우:000,,,5, 신영:000,,,6, NK투자증권:000,,,12, KB증권:000,,,17)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| bsis_aset_cd   | 기초자산코드 | String | Y        | 12     | 전체일때만 12자리입력(전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼정전자:005930, KT:030200,,)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| rght_tp        | 권리구분     | String | Y        | 1      | 0:전체, 1:콜, 2:풋, 3:DC, 4:DP, 5:EX, 6:조기종료콜, 7:조기종료풋                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| lpcd           | LP코드       | String | Y        | 12     | 전체일때만 12자리입력(전체:000000000000, 한국투자증권:003, 미래대우:005, 신영:006, NK투자증권:012, KB증권:017)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| sort_tp        | 정렬구분     | String | Y        | 1      | 0:정렬없음, 1:상승율순, 2:상승폭순, 3:하락율순, 4:하락폭순, 5:거래량순, 6:거래대금순, 7:잔존일순                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                        | 한글명                   | Type   | Required | Length | Description |
| ------------------------------ | ------------------------ | ------ | -------- | ------ | ----------- |
| elwcnd_qry                     | ELW조건검색              | LIST   | N        |        |             |
| - stk_cd                       | 종목코드                 | String | N        | 20     |             |
| - isscomp_nm                   | 발행사명                 | String | N        | 20     |             |
| - sqnc                         | 회차                     | String | N        | 20     |             |
| - base_aset_nm                 | 기초자산명               | String | N        | 20     |             |
| - rght_tp                      | 권리구분                 | String | N        | 20     |             |
| - expr_dt                      | 만기일                   | String | N        | 20     |             |
| - cur_prc                      | 현재가                   | String | N        | 20     |             |
| - pre_tp                       | 대비구분                 | String | N        | 20     |             |
| - pred_pre                     | 전일대비                 | String | N        | 20     |             |
| - flu_rt                       | 등락율                   | String | N        | 20     |             |
| - trde_qty                     | 거래량                   | String | N        | 20     |             |
| - trde_qty_pre                 | 거래량대비               | String | N        | 20     |             |
| - trde_prica                   | 거래대금                 | String | N        | 20     |             |
| - pred_trde_qty                | 전일거래량               | String | N        | 20     |             |
| - sel_bid                      | 매도호가                 | String | N        | 20     |             |
| - buy_bid                      | 매수호가                 | String | N        | 20     |             |
| - prty                         | 패리티                   | String | N        | 20     |             |
| - gear_rt                      | 기어링비율               | String | N        | 20     |             |
| - pl_qutr_rt                   | 손익분기율               | String | N        | 20     |             |
| - cfp                          | 자본지지점               | String | N        | 20     |             |
| - theory_pric                  | 이론가                   | String | N        | 20     |             |
| - innr_vltl                    | 내재변동성               | String | N        | 20     |             |
| - delta                        | 델타                     | String | N        | 20     |             |
| - lvrg                         | 레버리지                 | String | N        | 20     |             |
| - exec_pric                    | 행사가격                 | String | N        | 20     |             |
| - cnvt_rt                      | 전환비율                 | String | N        | 20     |             |
| - lpposs_rt                    | LP보유비율               | String | N        | 20     |             |
| - pl_qutr_pt                   | 손익분기점               | String | N        | 20     |             |
| - fin_trde_dt                  | 최종거래일               | String | N        | 20     |             |
| - flo_dt                       | 상장일                   | String | N        | 20     |             |
| - lpinitlast_suply_dt          | LP초종공급일             | String | N        | 20     |             |
| - stk_nm                       | 종목명                   | String | N        | 20     |             |
| - srvive_dys                   | 잔존일수                 | String | N        | 20     |             |
| - dispty_rt                    | 괴리율                   | String | N        | 20     |             |
| - lpmmcm_nm                    | LP회원사명               | String | N        | 20     |             |
| - lpmmcm_nm_1                  | LP회원사명1              | String | N        | 20     |             |
| - lpmmcm_nm_2                  | LP회원사명2              | String | N        | 20     |             |
| - xraymont_cntr_qty_arng_trde_tp | Xray순간체결량정리매매구분 | String | N        | 20     |             |
| - xraymont_cntr_qty_profa_100tp | Xray순간체결량증거금100구분 | String | N        | 20     |             |

#### 요청 예시

```json
{
	"isscomp_cd": "000000000017",
	"bsis_aset_cd": "201",
	"rght_tp": "1",
	"lpcd": "000000000000",
	"sort_tp": "0"
}
```

#### 응답 예시

```json
{
	"elwcnd_qry":
		[
			{
				"stk_cd":"57JBHH",
				"isscomp_nm":"키움증권",
				"sqnc":"K411",
				"base_aset_nm":"KOSPI200",
				"rght_tp":"콜",
				"expr_dt":"20241216",
				"cur_prc":"15",
				"pre_tp":"3",
				"pred_pre":"0",
				"flu_rt":"0.00",
				"trde_qty":"0",
				"trde_qty_pre":"0.00",
				"trde_prica":"0",
				"pred_trde_qty":"0",
				"sel_bid":"0",
				"buy_bid":"0",
				"prty":"90.10",
				"gear_rt":"2267.53",
				"pl_qutr_rt":"+11.03",
				"cfp":"",
				"theory_pric":"65637",
				"innr_vltl":"2015",
				"delta":"282426",
				"lvrg":"640.409428",
				"exec_pric":"377.50",
				"cnvt_rt":"100.0000",
				"lpposs_rt":"+99.90",
				"pl_qutr_pt":"+377.65",
				"fin_trde_dt":"20241212",
				"flo_dt":"20240320",
				"lpinitlast_suply_dt":"20241212",
				"stk_nm":"한국JBHHKOSPI200풋",
				"srvive_dys":"21",
				"dispty_rt":"--97.71",
				"lpmmcm_nm":"키움증권",
				"lpmmcm_nm_1":"0.00",
				"lpmmcm_nm_2":"",
				"xraymont_cntr_qty_arng_trde_tp":"",
				"xraymont_cntr_qty_profa_100tp":""
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---

### ELW등락율순위요청 (ka30009)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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

| Element        | 한글명       | Type   | Required | Length | Description                                                                             |
| -------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| sort_tp        | 정렬구분     | String | Y        | 1      | 1:상승률, 2:상승폭, 3:하락률, 4:하락폭                                                |
| rght_tp        | 권리구분     | String | Y        | 3      | 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 006:조기종료콜, 007:조기종료풋                |
| trde_end_skip  | 거래종료제외 | String | Y        | 1      | 0:거래종료포함, 1:거래종료제외                                                          |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                        | 한글명                   | Type   | Required | Length | Description |
| ------------------------------ | ------------------------ | ------ | -------- | ------ | ----------- |
| elwflu_rt_rank                 | ELW등락율순위            | LIST   | N        |        |             |
| - rank                         | 순위                     | String | N        | 20     |             |
| - stk_cd                       | 종목코드                 | String | N        | 20     |             |
| - stk_nm                       | 종목명                   | String | N        | 20     |             |
| - cur_prc                      | 현재가                   | String | N        | 20     |             |
| - pre_sig                      | 대비기호                 | String | N        | 20     |             |
| - pred_pre                     | 전일대비                 | String | N        | 20     |             |
| - flu_rt                       | 등락률                   | String | N        | 20     |             |
| - sel_req                      | 매도잔량                 | String | N        | 20     |             |
| - buy_req                      | 매수잔량                 | String | N        | 20     |             |
| - trde_qty                     | 거래량                   | String | N        | 20     |             |
| - trde_prica                   | 거래대금                 | String | N        | 20     |             |

#### 요청 예시

```json
{
	"sort_tp": "1",
	"rght_tp": "000",
	"trde_end_skip": "0"
}
```

#### 응답 예시

```json
{
	"elwflu_rt_rank":
		[
			{
				"rank":"1",
				"stk_cd":"57JBHH",
				"stk_nm":"한국JBHHKOSPI200풋",
				"cur_prc":"+30",
				"pre_sig":"2",
				"pred_pre":"+10",
				"flu_rt":"+50.00",
				"sel_req":"0",
				"buy_req":"0",
				"trde_qty":"30",
				"trde_prica":"0"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---

### ELW잔량순위요청 (ka30010)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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

| Element        | 한글명       | Type   | Required | Length | Description                                                                             |
| -------------- | ------------ | ------ | -------- | ------ | --------------------------------------------------------------------------------------- |
| sort_tp        | 정렬구분     | String | Y        | 1      | 1:순매수잔량상위, 2: 순매도 잔량상위                                                |
| rght_tp        | 권리구분     | String | Y        | 3      | 000: 전체, 001: 콜, 002: 풋, 003: DC, 004: DP, 006:조기종료콜, 007:조기종료풋                |
| trde_end_skip  | 거래종료제외 | String | Y        | 1      | 1:거래종료제외, 0:거래종료포함                                                          |

#### 응답 Header

| Element  | 한글명       | Type   | Required | Length | Description                         |
| -------- | ------------ | ------ | -------- | ------ | ----------------------------------- |
| cont-yn  | 연속조회여부 | String | N        | 1      | 다음 데이터가 있을시 Y값 전달       |
| next-key | 연속조회키   | String | N        | 50     | 다음 데이터가 있을시 다음 키값 전달 |
| api-id   | TR명         | String | Y        | 10     |                                     |

#### 응답 Body

| Element                        | 한글명                   | Type   | Required | Length | Description |
| ------------------------------ | ------------------------ | ------ | -------- | ------ | ----------- |
| elwreq_rank                    | ELW잔량순위              | LIST   | N        |        |             |
| - stk_cd                       | 종목코드                 | String | N        | 20     |             |
| - rank                         | 순위                     | String | N        | 20     |             |
| - stk_nm                       | 종목명                   | String | N        | 20     |             |
| - cur_prc                      | 현재가                   | String | N        | 20     |             |
| - pre_sig                      | 대비기호                 | String | N        | 20     |             |
| - pred_pre                     | 전일대비                 | String | N        | 20     |             |
| - flu_rt                       | 등락률                   | String | N        | 20     |             |
| - trde_qty                     | 거래량                   | String | N        | 20     |             |
| - sel_req                      | 매도잔량                 | String | N        | 20     |             |
| - buy_req                      | 매수잔량                 | String | N        | 20     |             |
| - netprps_req                  | 순매수잔량               | String | N        | 20     |             |
| - trde_prica                   | 거래대금                 | String | N        | 20     |             |

#### 요청 예시

```json
{
	"sort_tp": "1",
	"rght_tp": "000",
	"trde_end_skip": "0"
}
```

#### 응답 예시

```json
{
	"elwreq_rank":
		[
			{
				"stk_cd":"57JBHH",
				"rank":"1",
				"stk_nm":"한국JBHHKOSPI200풋",
				"cur_prc":"170",
				"pre_sig":"3",
				"pred_pre":"0",
				"flu_rt":"0.00",
				"trde_qty":"0",
				"sel_req":"0",
				"buy_req":"20",
				"netprps_req":"20",
				"trde_prica":"0"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---

### ELW근접율요청 (ka30011)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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

| Element                        | 한글명                   | Type   | Required | Length | Description |
| ------------------------------ | ------------------------ | ------ | -------- | ------ | ----------- |
| elwalacc_rt                    | ELW근접율                | LIST   | N        |        |             |
| - stk_cd                       | 종목코드                 | String | N        | 20     |             |
| - stk_nm                       | 종목명                   | String | N        | 20     |             |
| - cur_prc                      | 현재가                   | String | N        | 20     |             |
| - pre_sig                      | 대비기호                 | String | N        | 20     |             |
| - pred_pre                     | 전일대비                 | String | N        | 20     |             |
| - flu_rt                       | 등락율                   | String | N        | 20     |             |
| - acc_trde_qty                 | 누적거래량               | String | N        | 20     |             |
| - alacc_rt                     | 근접율                   | String | N        | 20     |             |

#### 요청 예시

```json
{
	"stk_cd": "57JBHH"
}
```

#### 응답 예시

```json
{
	"elwalacc_rt":
		[
			{
				"stk_cd":"201",
				"stk_nm":"KOSPI200",
				"cur_prc":"+431.78",
				"pre_sig":"2",
				"pred_pre":"+0.03",
				"flu_rt":"+0.01",
				"acc_trde_qty":"31",
				"alacc_rt":"0.00"
			}
		],
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---

### ELW종목상세정보요청 (ka30012)

#### 기본 정보

- **Method**: POST
- **운영 도메인**: https://api.kiwoom.com
- **모의투자 도메인**: https://mockapi.kiwoom.com(KRX만 지원가능)
- **URL**: /api/dostk/elw
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

| Element                      | 한글명                 | Type   | Required | Length | Description |
| ---------------------------- | ---------------------- | ------ | -------- | ------ | ----------- |
| aset_cd                      | 자산코드               | String | N        | 20     |             |
| cur_prc                      | 현재가                 | String | N        | 20     |             |
| pred_pre_sig                 | 전일대비기호           | String | N        | 20     |             |
| pred_pre                     | 전일대비               | String | N        | 20     |             |
| flu_rt                       | 등락율                 | String | N        | 20     |             |
| lpmmcm_nm                    | LP회원사명             | String | N        | 20     |             |
| lpmmcm_nm_1                  | LP회원사명1            | String | N        | 20     |             |
| lpmmcm_nm_2                  | LP회원사명2            | String | N        | 20     |             |
| elwrght_cntn                 | ELW권리내용            | String | N        | 20     |             |
| elwexpr_evlt_pric            | ELW만기평가가격        | String | N        | 20     |             |
| elwtheory_pric               | ELW이론가              | String | N        | 20     |             |
| dispty_rt                    | 괴리율                 | String | N        | 20     |             |
| elwinnr_vltl                 | ELW내재변동성          | String | N        | 20     |             |
| exp_rght_pric                | 예상권리가             | String | N        | 20     |             |
| elwpl_qutr_rt                | ELW손익분기율          | String | N        | 20     |             |
| elwexec_pric                 | ELW행사가              | String | N        | 20     |             |
| elwcnvt_rt                   | ELW전환비율            | String | N        | 20     |             |
| elwcmpn_rt                   | ELW보상율              | String | N        | 20     |             |
| elwpric_rising_part_rt       | ELW가격상승참여율      | String | N        | 20     |             |
| elwrght_type                 | ELW권리유형            | String | N        | 20     |             |
| elwsrvive_dys                | ELW잔존일수            | String | N        | 20     |             |
| stkcnt                       | 주식수                 | String | N        | 20     |             |
| elwlpord_pos                 | ELWLP주문가능          | String | N        | 20     |             |
| lpposs_rt                    | LP보유비율             | String | N        | 20     |             |
| lprmnd_qty                   | LP보유수량             | String | N        | 20     |             |
| elwspread                    | ELW스프레드            | String | N        | 20     |             |
| elwprty                      | ELW패리티              | String | N        | 20     |             |
| elwgear                      | ELW기어링              | String | N        | 20     |             |
| elwflo_dt                    | ELW상장일              | String | N        | 20     |             |
| elwfin_trde_dt               | ELW최종거래일          | String | N        | 20     |             |
| expr_dt                      | 만기일                 | String | N        | 20     |             |
| exec_dt                      | 행사일                 | String | N        | 20     |             |
| lpsuply_end_dt               | LP공급종료일           | String | N        | 20     |             |
| elwpay_dt                    | ELW지급일              | String | N        | 20     |             |
| elwinvt_ix_comput            | ELW투자지표산출        | String | N        |        |             |
| elwpay_agnt                  | ELW지급대리인          | String | N        |        |             |
| elwappr_way                  | ELW결재방법            | String | N        |        |             |
| elwrght_exec_way             | ELW권리행사방식        | String | N        |        |             |
| elwpblicte_orgn              | ELW발행기관            | String | N        |        |             |
| dcsn_pay_amt                 | 확정지급액             | String | N        |        |             |
| kobarr                       | KO베리어               | String | N        |        |             |
| iv                           | IV                     | String | N        |        |             |
| clsprd_end_elwocr            | 종기종료ELW발생        | String | N        |        |             |
| bsis_aset_1                  | 기초자산1              | String | N        |        |             |
| bsis_aset_comp_rt_1          | 기초자산구성비율1      | String | N        |        |             |
| bsis_aset_2                  | 기초자산2              | String | N        |        |             |
| bsis_aset_comp_rt_2          | 기초자산구성비율2      | String | N        |        |             |
| bsis_aset_3                  | 기초자산3              | String | N        |        |             |
| bsis_aset_comp_rt_3          | 기초자산구성비율3      | String | N        |        |             |
| bsis_aset_4                  | 기초자산4              | String | N        |        |             |
| bsis_aset_comp_rt_4          | 기초자산구성비율4      | String | N        |        |             |
| bsis_aset_5                  | 기초자산5              | String | N        |        |             |
| bsis_aset_comp_rt_5          | 기초자산구성비율5      | String | N        |        |             |
| fr_dt                        | 평가시작일자           | String | N        |        |             |
| to_dt                        | 평가종료일자           | String | N        |        |             |
| fr_tm                        | 평가시작시간           | String | N        |        |             |
| evlt_end_tm                  | 평가종료시간           | String | N        |        |             |
| evlt_pric                    | 평가가격               | String | N        |        |             |
| evlt_fnsh_yn                 | 평가완료여부           | String | N        |        |             |
| all_hgst_pric                | 전체최고가             | String | N        |        |             |
| all_lwst_pric                | 전체최저가             | String | N        |        |             |
| imaf_hgst_pric               | 직후최고가             | String | N        |        |             |
| imaf_lwst_pric               | 직후최저가             | String | N        |        |             |
| sndhalf_mrkt_hgst_pric       | 후반장최고가           | String | N        |        |             |
| sndhalf_mrkt_lwst_pric       | 후반장최저가           | String | N        |        |             |

#### 요청 예시

```json
{
	"stk_cd": "57JBHH"
}
```

#### 응답 예시

```json
{
	"aset_cd":"201",
	"cur_prc":"10",
	"pred_pre_sig":"3",
	"pred_pre":"0",
	"flu_rt":"0.00",
	"lpmmcm_nm":"",
	"lpmmcm_nm_1":"키움증권",
	"lpmmcm_nm_2":"",
	"elwrght_cntn":"만기평가가격이 행사가격 초과인 경우,\n\t 1워런트당 (만기평가가격-행사가격)*전환비율",
	"elwexpr_evlt_pric":"최종거래일 종가",
	"elwtheory_pric":"27412",
	"dispty_rt":"--96.35",
	"elwinnr_vltl":"1901",
	"exp_rght_pric":"3179.00",
	"elwpl_qutr_rt":"--7.33",
	"elwexec_pric":"400.00",
	"elwcnvt_rt":"100.0000",
	"elwcmpn_rt":"0.00",
	"elwpric_rising_part_rt":"0.00",
	"elwrght_type":"CALL",
	"elwsrvive_dys":"15",
	"stkcnt":"8000",
	"elwlpord_pos":"가능",
	"lpposs_rt":"+95.20",
	"lprmnd_qty":"7615830",
	"elwspread":"15.00",
	"elwprty":"107.94",
	"elwgear":"4317.90",
	"elwflo_dt":"20240124",
	"elwfin_trde_dt":"20241212",
	"expr_dt":"20241216",
	"exec_dt":"20241216",
	"lpsuply_end_dt":"20241212",
	"elwpay_dt":"20241218",
	"elwinvt_ix_comput":"산출종목",
	"elwpay_agnt":"국민은행증권타운지점",
	"elwappr_way":"현금 결제",
	"elwrght_exec_way":"유럽형",
	"elwpblicte_orgn":"키움증권(주)",
	"dcsn_pay_amt":"0.000",
	"kobarr":"0",
	"iv":"0.00",
	"clsprd_end_elwocr":"",
	"bsis_aset_1":"KOSPI200",
	"bsis_aset_comp_rt_1":"0.00",
	"bsis_aset_2":"",
	"bsis_aset_comp_rt_2":"0.00",
	"bsis_aset_3":"",
	"bsis_aset_comp_rt_3":"0.00",
	"bsis_aset_4":"",
	"bsis_aset_comp_rt_4":"0.00",
	"bsis_aset_5":"",
	"bsis_aset_comp_rt_5":"0.00",
	"fr_dt":"",
	"to_dt":"",
	"fr_tm":"",
	"evlt_end_tm":"",
	"evlt_pric":"",
	"evlt_fnsh_yn":"",
	"all_hgst_pric":"0.00",
	"all_lwst_pric":"0.00",
	"imaf_hgst_pric":"0.00",
	"imaf_lwst_pric":"0.00",
	"sndhalf_mrkt_hgst_pric":"0.00",
	"sndhalf_mrkt_lwst_pric":"0.00",
	"return_code":0,
	"return_msg":"정상적으로 처리되었습니다"
}
```

---
