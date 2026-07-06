# CLI Parameter Naming Audit Evidence

This is non-authoritative audit evidence for CLI parameter naming.

The command-system SSOT is `kiwoom_cli/docs/command-system.md`. If this audit
and `command-system.md` differ, `command-system.md` wins. Do not implement a
rename solely from this file unless the target change is approved in
`command-system.md`.

목적: `kiwoom_api_spec.json`의 원 API 파라미터와 현재 CLI 매핑을 대조해,
사용자에게 보이는 파라미터 이름의 문제 후보와 근거를 기록한다.

관찰 요약: 키움 원 파라미터의 `*_tp`는 대체로 “구분”이지만, CLI에서 전부
`--type`으로 통일하면 더 헷갈리는 경우가 많다. 승인된 명명 규칙은
`command-system.md`를 따른다.

## 1. 조사 범위
| 항목 | 수량 | 출처 |
| --- | --- | --- |
| 전체 spec API | 207 | kiwoom_api_spec.json (국내주식 205 + OAuth 인증 2; 해외주식 제외) |
| spec request body 필드 발생 수 | 766 | apis.*.request.body |
| spec request body 고유 필드 수 | 143 | element 기준 |
| CLI command 매핑 수 | 207 | kiwoom_cli/maps/api_commands.csv |
| CLI argument 매핑 수 | 731 | kiwoom_cli/maps/arguments.csv |
| 1차 rename 근거 | 적용 완료 | Section 3의 과거 옵션 근거 표 |
| 2차 rename/condition 보강 후보 | 적용 완료 | `command-system.md` Applied Argument Reform Scope |

## 2. 원 파라미터군별 관찰 요약
| 원 파라미터군 | 고유 필드 수 | 관찰 |
| --- | --- | --- |
| *_cd/code 코드 | 21 | 일반 대상 코드와 특수 역할 코드가 섞여 있다. |
| *_cnd 조건 | 7 | 조건 코드가 많고 choices/value_map 보강이 필요한 항목이 있다. |
| *_dt/date 일자 | 24 | 단일 일자와 기간 일자가 섞여 있다. |
| *_tp 구분/유형 | 86 | 기계적 `--type` 변환으로는 사용자 의미를 보존하기 어렵다. |
| incls/skip/yn 포함여부 | 10 | 원 필드는 skip/exclude 관점인 경우가 있어 사용자 관점 변환이 필요할 수 있다. |
| pric/amt/uv 가격/금액 | 19 | 주문 단가와 조회 조건 필터가 섞여 있다. |
| qty/cnt 수량/건수 | 15 | 주문 수량, 조회 수량, 기간/건수 의미가 섞여 있다. |
| 기타 | 70 | 명령별 도메인 의미 확인이 필요하다. |

## 3. SSOT 승인 1차 변경(구현 완료) 과거 옵션 근거
아래 표는 `command-system.md`의 First Argument Reform Scope에 승인된
1차 변경의 상세 근거다. 적용 정책과 현재 옵션명은 `command-system.md` 및
`kiwoom_cli/maps/arguments.csv`를 따른다. 표의 `이전 옵션`은 현재 CLI
표면이 아니며, legacy alias로 유지하지 않는다.
| API ID | API명 | 명령어 | 이전 옵션 | 키움 원 파라미터 | 원래 이름 | 원 설명 | 이전 값 | 적용 옵션 | 이유 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ka30005 | ELW조건검색요청 | kiwoomcli domestic elws conditions | --asset | bsis_aset_cd | 기초자산코드 | 전체일때만 12자리입력(전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼정전자:005930, KT:030200,,) |  | --underlying-code | `bsis_aset_cd`는 자산종류가 아니라 기초자산코드다. |
| ka30005 | ELW조건검색요청 | kiwoomcli domestic elws conditions | --right | rght_tp | 권리구분 | 0:전체, 1:콜, 2:풋, 3:DC, 4:DP, 5:EX, 6:조기종료콜, 7:조기종료풋 | all\|call\|put\|dc\|dp\|ex\|early-call\|early-put / all=0;call=1;put=2;dc=3;dp=4;ex=5;early-call=6;early-put=7 | --right-type | `rght_tp`는 권리구분이며 `right` 단독은 모호하다. |
| ka30001 | ELW가격급등락요청 | kiwoomcli domestic elws price-move | --asset | bsis_aset_cd | 기초자산코드 | 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200.. |  | --underlying-code | `bsis_aset_cd`는 자산종류가 아니라 기초자산코드다. |
| ka30001 | ELW가격급등락요청 | kiwoomcli domestic elws price-move | --right | rght_tp | 권리구분 | 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 005:EX, 006:조기종료콜, 007:조기종료풋 | all\|call\|put\|dc\|dp\|ex\|early-call\|early-put / all=000;call=001;put=002;dc=003;dp=004;ex=005;early-call=006;early-put=007 | --right-type | `rght_tp`는 권리구분이며 `right` 단독은 모호하다. |
| ka30001 | ELW가격급등락요청 | kiwoomcli domestic elws price-move | --ended | trde_end_elwskip | 거래종료ELW제외 | 0:포함, 1:제외 | include\|exclude / include=0;exclude=1 | --include-ended | 거래종료/만기 ELW 포함 여부로 표현하는 편이 명확하다. 값 매핑은 `yes=0`, `no=1`. |
| ka30002 | 거래원별ELW순매매상위요청 | kiwoomcli domestic elws broker-net | --ended | trde_end_elwskip | 거래종료ELW제외 | 0:포함, 1:제외 | include\|exclude / include=0;exclude=1 | --include-ended | 거래종료/만기 ELW 포함 여부로 표현하는 편이 명확하다. 값 매핑은 `yes=0`, `no=1`. |
| ka30004 | ELW괴리율요청 | kiwoomcli domestic elws divergence | --asset | bsis_aset_cd | 기초자산코드 | 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200.. |  | --underlying-code | `bsis_aset_cd`는 자산종류가 아니라 기초자산코드다. |
| ka30004 | ELW괴리율요청 | kiwoomcli domestic elws divergence | --right | rght_tp | 권리구분 | 000: 전체, 001: 콜, 002: 풋, 003: DC, 004: DP, 005: EX, 006: 조기종료콜, 007: 조기종료풋 | all\|call\|put\|dc\|dp\|ex\|early-call\|early-put / all=000;call=001;put=002;dc=003;dp=004;ex=005;early-call=006;early-put=007 | --right-type | `rght_tp`는 권리구분이며 `right` 단독은 모호하다. |
| ka30004 | ELW괴리율요청 | kiwoomcli domestic elws divergence | --ended | trde_end_elwskip | 거래종료ELW제외 | 1:거래종료ELW제외, 0:거래종료ELW포함 | include\|exclude / include=0;exclude=1 | --include-ended | 거래종료/만기 ELW 포함 여부로 표현하는 편이 명확하다. 값 매핑은 `yes=0`, `no=1`. |
| ka30009 | ELW등락율순위요청 | kiwoomcli domestic elws change-rank | --right | rght_tp | 권리구분 | 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 006:조기종료콜, 007:조기종료풋 | all\|call\|put\|dc\|dp\|early-call\|early-put / all=000;call=001;put=002;dc=003;dp=004;early-call=006;early-put=007 | --right-type | `rght_tp`는 권리구분이며 `right` 단독은 모호하다. |
| ka30009 | ELW등락율순위요청 | kiwoomcli domestic elws change-rank | --ended | trde_end_skip | 거래종료제외 | 1:거래종료제외, 0:거래종료포함 | include\|exclude / include=0;exclude=1 | --include-ended | 거래종료/만기 ELW 포함 여부로 표현하는 편이 명확하다. 값 매핑은 `yes=0`, `no=1`. |
| ka30010 | ELW잔량순위요청 | kiwoomcli domestic elws balance-rank | --right | rght_tp | 권리구분 | 000: 전체, 001: 콜, 002: 풋, 003: DC, 004: DP, 006: 조기종료콜, 007: 조기종료풋 | all\|call\|put\|dc\|dp\|early-call\|early-put / all=000;call=001;put=002;dc=003;dp=004;early-call=006;early-put=007 | --right-type | `rght_tp`는 권리구분이며 `right` 단독은 모호하다. |
| ka30010 | ELW잔량순위요청 | kiwoomcli domestic elws balance-rank | --ended | trde_end_skip | 거래종료제외 | 1:거래종료제외, 0:거래종료포함 | include\|exclude / include=0;exclude=1 | --include-ended | 거래종료/만기 ELW 포함 여부로 표현하는 편이 명확하다. 값 매핑은 `yes=0`, `no=1`. |
| kt00001 | 예수금상세현황요청 | kiwoomcli domestic accounts cash | --query | qry_tp | 조회구분 | 3:추정조회, 2:일반조회 | estimated\|normal / estimated=3;normal=2 | --cash-basis | `query`는 검색어처럼 보이나 원 파라미터 `qry_tp`는 예수금 조회구분이다. |
| kt00003 | 추정자산조회요청 | kiwoomcli domestic accounts assets | --delisted | qry_tp | 상장폐지조회구분 | 0:전체, 1:상장폐지종목제외 | all\|exclude / all=0;exclude=1 | --include-delisted | 상장폐지조회구분은 포함 여부로 표현하는 편이 명확하다. 값 매핑은 `yes=0`, `no=1`. |
| kt00004 | 계좌평가현황요청 | kiwoomcli domestic accounts valuation | --delisted | qry_tp | 상장폐지조회구분 | 0:전체, 1:상장폐지종목제외 | all\|exclude / all=0;exclude=1 | --include-delisted | 상장폐지조회구분은 포함 여부로 표현하는 편이 명확하다. 값 매핑은 `yes=0`, `no=1`. |
| kt00007 | 계좌별주문체결내역상세요청 | kiwoomcli domestic accounts order-fill-detail | --asset | stk_bond_tp | 주식채권구분 | 0:전체, 1:주식, 2:채권 | all\|stock\|bond / all=0;stock=1;bond=2 | --asset-kind | `stk_bond_tp`는 주식/채권 자산 종류다. ELW `--asset`과 의미 충돌을 줄인다. |
| kt00009 | 계좌별주문체결현황요청 | kiwoomcli domestic accounts order-fill-status | --asset | stk_bond_tp | 주식채권구분 | 0:전체, 1:주식, 2:채권 | all\|stock\|bond / all=0;stock=1;bond=2 | --asset-kind | `stk_bond_tp`는 주식/채권 자산 종류다. ELW `--asset`과 의미 충돌을 줄인다. |
| kt50030 | 금현물 주문체결전체조회 | kiwoomcli domestic accounts gold-all-order-fills | --asset | stk_bond_tp | 주식채권구분 | 0:전체, 1:주식, 2:채권 | all\|stock\|bond / all=0;stock=1;bond=2 | --asset-kind | `stk_bond_tp`는 주식/채권 자산 종류다. ELW `--asset`과 의미 충돌을 줄인다. |
| kt50031 | 금현물 주문체결조회 | kiwoomcli domestic accounts gold-order-fills | --asset | stk_bond_tp | 주식채권구분 | 0:전체, 1:주식, 2:채권 | all\|stock\|bond / all=0;stock=1;bond=2 | --asset-kind | `stk_bond_tp`는 주식/채권 자산 종류다. ELW `--asset`과 의미 충돌을 줄인다. |
| kt50075 | 금현물 미체결조회 | kiwoomcli domestic accounts gold-open-orders | --asset | stk_bond_tp | 주식채권구분 | 0:전체, 1:주식, 2:채권 | all\|stock\|bond / all=0;stock=1;bond=2 | --asset-kind | `stk_bond_tp`는 주식/채권 자산 종류다. ELW `--asset`과 의미 충돌을 줄인다. |

## 4. 2차/condition 검토 결과

이 절의 상세 후보 표는 `command-system.md`의 Applied Argument Reform Scope와
`kiwoom_cli/maps/arguments.csv`에 편입되었으므로 여기서 중복 유지하지 않는다.
현재 구현 계약은 아래 파일을 우선한다.

| 항목 | 현재 상태 | 권위 소스 |
| --- | --- | --- |
| `--sort` 중 순수 정렬 기준 | 유지 | `arguments.csv` |
| `qry_tp`의 주문순/역순 의미 | `--order`로 분리 | `arguments.csv`, `command-system.md` |
| 미체결/체결 상태 필터 | `--fill-status`로 분리 | `arguments.csv`, `command-system.md` |
| 전체/종목 범위 | `--stock-scope` 또는 내부 기본값으로 분리 | `arguments.csv`, `command-system.md` |
| `crd_tp` | `--credit-type` | `arguments.csv`, `command-system.md` |
| `crd_cnd` | `--credit-condition` | `arguments.csv`, `command-system.md` |
| 조건형 가격/수량/대금/종목 필터 | `--price-condition`, `--volume-condition`, `--amount-condition`, `--stock-condition` with choices/value_map | `arguments.csv` |

남은 작업은 이름 변경이 아니라 value map 정확도를 upstream spec과 대조하는
검증 작업이다.

## 5. `*_tp`를 전부 type으로 통일하지 않는 예
| API ID | API명 | 명령어 | 현재 옵션 | 키움 원 파라미터 | 원래 이름 | 원 설명 | 판단 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ka10081 | 주식일봉차트조회요청 | kiwoomcli domestic candles daily | --adjusted | upd_stkpc_tp | 수정주가구분 | 0 or 1 | 현재 이름 유지 가능 |
| ka10060 | 종목별투자자기관별차트요청 | kiwoomcli domestic candles by-stock | --basis | amt_qty_tp | 금액수량구분 | 1:금액, 2:수량 | 현재 이름 유지 가능 |
| ka10060 | 종목별투자자기관별차트요청 | kiwoomcli domestic candles by-stock | --side | trde_tp | 매매구분 | 0:순매수, 1:매수, 2:매도 | 현재 이름 유지 가능 |
| ka10060 | 종목별투자자기관별차트요청 | kiwoomcli domestic candles by-stock | --unit | unit_tp | 단위구분 | 1000:천주, 1:단주 | 현재 이름 유지 가능 |
| ka10064 | 장중투자자별매매차트요청 | kiwoomcli domestic candles lookup | --market | mrkt_tp | 시장구분 | 000:전체, 001:코스피, 101:코스닥 | 현재 이름 유지 가능 |
| ka10064 | 장중투자자별매매차트요청 | kiwoomcli domestic candles lookup | --basis | amt_qty_tp | 금액수량구분 | 1:금액, 2:수량 | 현재 이름 유지 가능 |
| ka10064 | 장중투자자별매매차트요청 | kiwoomcli domestic candles lookup | --side | trde_tp | 매매구분 | 0:순매수, 1:매수, 2:매도 | 현재 이름 유지 가능 |
| ka40004 | ETF전체시세요청 | kiwoomcli domestic etfs list | --exchange | stex_tp | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 현재 이름 유지 가능 |
| ka30001 | ELW가격급등락요청 | kiwoomcli domestic elws price-move | --direction | flu_tp | 등락구분 | 1:급등, 2:급락 | 현재 이름 유지 가능 |
| ka30001 | ELW가격급등락요청 | kiwoomcli domestic elws price-move | --time-unit | tm_tp | 시간구분 | 1:분전, 2:일전 | 현재 이름 유지 가능 |
| ka30001 | ELW가격급등락요청 | kiwoomcli domestic elws price-move | --volume | trde_qty_tp | 거래량구분 | 0:전체, 10:만주이상, 50:5만주이상, 100:10만주이상, 300:30만주이상, 500:50만주이상, 1000:백만주이상 | 현재 이름 유지 가능 |
| ka30002 | 거래원별ELW순매매상위요청 | kiwoomcli domestic elws broker-net | --volume | trde_qty_tp | 거래량구분 | 0:전체, 5:5천주, 10:만주, 50:5만주, 100:10만주, 500:50만주, 1000:백만주 | 현재 이름 유지 가능 |
| ka30002 | 거래원별ELW순매매상위요청 | kiwoomcli domestic elws broker-net | --side | trde_tp | 매매구분 | 1:순매수, 2:순매도 | 현재 이름 유지 가능 |
| ka10131 | 기관외국인연속매매현황요청 | kiwoomcli domestic investors trend | --market | mrkt_tp | 장구분 | 001:코스피, 101:코스닥 | 현재 이름 유지 가능 |
| ka10131 | 기관외국인연속매매현황요청 | kiwoomcli domestic investors trend | --side | netslmt_tp | 순매도수구분 | 2:순매수(고정값) | 현재 이름 유지 가능 |
| ka10131 | 기관외국인연속매매현황요청 | kiwoomcli domestic investors trend | --target | stk_inds_tp | 종목업종구분 | 0:종목(주식),1:업종 | 현재 이름 유지 가능 |
| ka10131 | 기관외국인연속매매현황요청 | kiwoomcli domestic investors trend | --basis | amt_qty_tp | 금액수량구분 | 0:금액, 1:수량 | 현재 이름 유지 가능 |
| ka10131 | 기관외국인연속매매현황요청 | kiwoomcli domestic investors trend | --exchange | stex_tp | 거래소구분 | 1:KRX, 2:NXT, 3:통합 | 현재 이름 유지 가능 |
| ka10069 | 대차거래상위10종목요청 | kiwoomcli domestic securities-lending list | --market | mrkt_tp | 시장구분 | 001:코스피, 101:코스닥 | 현재 이름 유지 가능 |
| ka90012 | 대차거래내역요청 | kiwoomcli domestic securities-lending lookup | --market | mrkt_tp | 시장구분 | 001:코스피, 101:코스닥 | 현재 이름 유지 가능 |

## 6. 중복 옵션 관찰 결과

이전 감사에서는 `--sort`, `--scope`, `--asset`, `--credit`, `--query`,
`--price` 등이 여러 원 파라미터를 가리키는 후보로 잡혔다. 그중 실제
사용자 의미가 충돌한 항목은 현재 `arguments.csv`에 반영되어 다음처럼 정리되었다.

| 과거 충돌 후보 | 현재 처리 |
| --- | --- |
| ELW `--asset` | `--underlying-code` |
| 계좌/금현물 `--asset` | `--asset-kind` |
| 예수금 `--query` | `--cash-basis` |
| 계좌/금현물 `--sort` 중 순서/상태 의미 | `--order` / `--fill-status` |
| `--scope` | `--stock-scope`, `--fill-status`, 또는 내부 기본값 |
| `--credit` | `--credit-type` / `--credit-condition` |
| 조회 조건 `--price` | `--price-condition` |

`--code`, `--date`, 주문 `--price`처럼 사용자가 같은 개념으로 이해할 수
있는 중복은 유지한다. 전체 현재 인벤토리는 이 문서에 복제하지 않고
`kiwoom_cli/maps/arguments.csv`와 생성된 agent reference를 기준으로 확인한다.

## 7. 전체 CLI argument 인벤토리

전체 인벤토리는 중복 문서화를 피하기 위해 이 문서에서 제거했다. 현재 상태는
다음 파일들이 권위 소스다.

| 목적 | 권위 소스 |
| --- | --- |
| 현재 CLI 옵션/필드/value_map | `kiwoom_cli/maps/arguments.csv` |
| 현재 command/API/safety 매핑 | `kiwoom_cli/maps/api_commands.csv` |
| 적용된 명명 원칙 | `kiwoom_cli/docs/command-system.md` |
| agent용 생성 reference | `.agents/skills/kiwoom/kiwoom/references/` |

## 8. spec request 고유 필드 인벤토리
<details>
<summary>고유 원 파라미터 펼치기</summary>

| 원 파라미터 | 발생 API 수 | 원래 이름 예시 | 설명 예시 | API 예시 |
| --- | --- | --- | --- | --- |
| abnd_dt | 1 | 해지일자 |  | ust31281 자동환전조회취소 |
| acnt_no | 2 | 계좌번호 | 필수 | usa21500 미국주식 실시간 잔고<br>ust21121 미국주식 원장 잔고현황 |
| acnt_rqst_seq | 1 | 계좌신청일련번호 |  | ust31281 자동환전조회취소 |
| acnt_seq | 1 | 계좌상품 |  | ust21121 미국주식 원장 잔고현황 |
| alacc_rt | 4 | 근접율 | 05:0.5 10:1.0, 15:1.5, 20:2.0. 25:2.5, 30:3.0 | ka10018 고저가근접요청<br>usa20970 미국주식 고가/저가 접근<br>usa20971 미국주식 고가/저가 접근<br>usa24140 미국주식 갭상승/갭하락 |
| all_stk_tp | 1 | 전체종목구분 | 0:전체, 1:종목 | ka10075 미체결요청 |
| all_tp | 2 | 전체구분 | 1: 전체표시 | ka10068 대차거래추이요청<br>ka20068 대차거래추이요청(종목별) |
| am_pm_tp | 2 | 오전오후구분 | A오전 P오후 | ust21200 미국주식 기간별 예약주문<br>ust21201 미국주식 예약주문 내역조회 |
| amt_qty_tp | 16 | 금액수량구분 | 금액:0, 수량:1 | ka10051 업종별투자자순매수요청<br>ka10059 종목별투자자기관별요청<br>ka10060 종목별투자자기관별차트요청<br>ka10061 종목별투자자기관별합계요청<br>ka10063 장중투자자별매매요청 |
| amt_tp | 1 | 금액구분 | 1:출금가능금액전체,2:출금가능금액중일부 | ust30132 미국주식 원화주문 가능금액 |
| aplc_exrt | 1 | 적용환율 |  | ust30141 미국주식 원화주문설정금 환전 |
| appkey | 2 | 앱키 |  | au10001 접근토큰 발급<br>au10002 접근토큰폐기 |
| appr_seq | 1 | 승인일련번호 |  | ust31302 외화환전신청 |
| arn_grp_id | 1 | 그룹SEQ |  | usa20201 관심종목 그룹 상세 조회 |
| auto_asgn_abnd_tp | 1 | 자동지정해지구분 | 0:한국 1:미국 | ust30133 미국주식 원화주문 가능금액 |
| base_dt | 28 | 기준일자 | YYYYMMDD | ka10051 업종별투자자순매수요청<br>ka10080 주식분봉차트조회요청<br>ka10081 주식일봉차트조회요청<br>ka10082 주식주봉차트조회요청<br>ka10083 주식월봉차트조회요청 |
| base_dt_tp | 2 | 기준일구분 | 0:당일기준, 1:전일기준 | ka10035 외인연속순매매상위요청<br>ust21201 미국주식 예약주문 내역조회 |
| bf_mkrt_tp | 1 | 장전구분 | 0:전체, 1:정규시장,2:시간외단일가 | ka10054 변동성완화장치발동종목요청 |
| boan_check | 1 | 고객정보제한여부 | Y:제한, N:비제한 | ust21100 미국주식 거래내역 |
| bsis_aset_cd | 4 | 기초자산코드 | 전체:000000000000, KOSPI200:201, KOSDAQ150:150, 삼성전자:005930, KT:030200.. | ka30001 ELW가격급등락요청<br>ka30003 ELWLP보유일별추이요청<br>ka30004 ELW괴리율요청<br>ka30005 ELW조건검색요청 |
| buy_aplc_exrt | 1 | 매수적용환율 |  | ust31302 외화환전신청 |
| buy_crnc_code | 3 | 매수통화코드 |  | ust31300 외화환전신청<br>ust31301 외화환전신청<br>ust31302 외화환전신청 |
| cate1_cd | 2 | 카테고리1 코드 |  | usa26501 미국주식 배당주 검색<br>usa26511 미국주식 배당주 순위 |
| cate2_cd | 2 | 카테고리2 코드 |  | usa26501 미국주식 배당주 검색<br>usa26511 미국주식 배당주 순위 |
| ch_crd_tp | 1 | 현금신용구분 | 0:전체, 1:현금매매만, 2:신용매매만 | ka10170 당일매매일지요청 |
| cmsn_incl_tp | 3 | 수수료포함구분 | 0:미포함 1:포함 20180702추가 | ust21120 미국주식 원장 잔고현황<br>ust21121 미국주식 원장 잔고현황<br>ust21122 해외증권 계좌 잔고평가현황 |
| cncl_qty | 4 | 취소수량 | '0' 입력시 잔량 전부 취소 | kt10003 주식 취소주문<br>kt10009 신용 취소주문<br>kt50003 금현물 취소주문<br>ust20003 미국주식 취소 주문 |
| cntr_dt | 1 | 체결일자 |  | ust21640 미국주식 일별 종목별 실현손익 |
| cntr_tp | 1 | 체결,미체결구분 | 1:체결 포함 | usa21520 미국주식 실시간 미체결 |
| cond | 1 | 조건 |  | usa24220 미국주식 매물대집중 |
| cond_uv | 4 | 조건단가 |  | kt10000 주식 매수주문<br>kt10001 주식 매도주문<br>kt10006 신용 매수주문<br>kt10007 신용 매도주문 |
| cons_cnt | 2 | 컨센서스 개수 |  | usa06060 미국주식 재무차트-연간<br>usa06061 미국주식 재무차트-분기 |
| cont_yn | 1 | 연속조회여부 | Y:연속조회요청,N:연속조회미요청 | ka10172 조건검색 요청 일반 |
| crd_cnd | 10 | 신용조건 | 0:전체조회, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 7:신용융자E군, 9:신용융자전체 | ka10016 신고저가요청<br>ka10017 상하한가요청<br>ka10018 고저가근접요청<br>ka10019 가격급등락요청<br>ka10020 호가잔량상위요청 |
| crd_deal_tp | 1 | 신용거래구분 | 33:융자 , 99:융자합 | kt10007 신용 매도주문 |
| crd_loan_dt | 1 | 대출일 | YYYYMMDD(융자일경우필수) | kt10007 신용 매도주문 |
| crd_stk_grde_tp | 1 | 신용종목등급구분 | %:전체, A:A군, B:B군, C:C군, D:D군, E:E군 | kt20016 신용융자 가능종목요청 |
| crd_tp | 1 | 신용구분 | 0:전체조회, 9:신용융자전체, 1:신용융자A군, 2:신용융자B군, 3:신용융자C군, 4:신용융자D군, 8:신용대주 | ka10030 당일거래량상위요청 |
| crnc_cd | 1 | 통화코드 |  | kt00015 위탁종합거래내역요청 |
| crnc_code | 10 | 통화코드 |  | ust21100 미국주식 거래내역<br>ust21530 미국주식 실현손익<br>ust30140 미국주식 원화주문설정금 환전<br>ust30142 미국주식 원화주문설정금 환전<br>ust31280 자동환전조회취소 |
| cur_prc_entry | 1 | 현재가진입 | 0:현재가 매물대 진입 포함안함, 1:현재가 매물대 진입포함 | ka10025 매물대집중요청 |
| cust_no | 2 | 고객번호 |  | usa20200 관심종목 그룹 리스트 조회<br>usa20201 관심종목 그룹 상세 조회 |
| cycle_tp | 2 | 주기구분 | 5:5일, 10:10일, 20:20일, 60:60일, 250:250일 | ka10024 거래량갱신요청<br>ka10025 매물대집중요청 |
| data | 19 | 실시간 등록 리스트 |  | 00 주문체결<br>04 잔고<br>0A 주식기세<br>0B 주식체결<br>0C 주식우선호가 |
| date | 7 | 날짜 | YYYYMMDD | ka90005 프로그램매매추이요청 시간대별<br>ka90006 프로그램매매차익잔고추이요청<br>ka90007 프로그램매매누적추이요청<br>ka90008 종목시간별프로그램매매추이요청<br>ka90009 외국인기관매매상위요청 |
| date_tp | 2 | 날짜구분 | n일전 (1일 ~ 99일 날짜입력) | ka90001 테마그룹별요청<br>ka90002 테마구성종목요청 |
| dcpn_tp | 3 | 소수점구분 | 0:전체 1:온주 2:소수점 | usa21500 미국주식 실시간 잔고<br>usa21520 미국주식 실시간 미체결<br>ust21380 미국주식 권리내역 |
| deal_dt | 1 | 거래일자 | 업무용비밀번호 사용 승인 | ust31302 외화환전신청 |
| dfr_tp | 1 | 미수구분 | "1:현금미수 3:기타대여금 4:미수유가증권 9:전체 | ust31510 미국주식 미수금 내역조회 |
| dly_rpy_tp | 1 | 변제구분 | "1:일부 | ust31510 미국주식 미수금 내역조회 |
| dmst_stex_tp | 17 | 국내거래소구분 | KRX:한국거래소,NXT:넥스트트레이드 | kt00004 계좌평가현황요청<br>kt00005 체결잔고요청<br>kt00007 계좌별주문체결내역상세요청<br>kt00009 계좌별주문체결현황요청<br>kt00015 위탁종합거래내역요청 |
| dt | 18 | 일자 | YYYYMMDD | ka10013 신용매매동향요청<br>ka10016 신고저가요청<br>ka10034 외인기간별매매상위요청<br>ka10036 외인한도소진율증가상위<br>ka10037 외국계창구매매상위요청 |
| dt_tp | 1 | 기간구분 | 0:연중 1:52주 | usa24110 미국주식 최고최저가대비 상승하 |
| dt_unit_tp | 2 | 일,주,월단위구분 | D:일,W:주,M:월 | usa01990 관심종목 등록 상위<br>usa20880 키움 거래 상위 종목(주식/ETF) |
| dvid_cycl | 4 | 배당주기 | 0:전체 1:년 2:반기 3:분기 4:월 | usa26500 미국주식 배당주 검색<br>usa26501 미국주식 배당주 검색<br>usa26510 미국주식 배당주 순위<br>usa26511 미국주식 배당주 순위 |
| dvid_dt_tp | 1 | 배당기간구분(M, Q, Y) |  | usa26533 미국주식 종목별 배당 |
| dvid_erat_max | 3 | 배당수익률(최대) | 단위(%) | usa26500 미국주식 배당주 검색<br>usa26501 미국주식 배당주 검색<br>usa26511 미국주식 배당주 순위 |
| dvid_erat_min | 3 | 배당수익률(최소) | 단위(%) | usa26500 미국주식 배당주 검색<br>usa26501 미국주식 배당주 검색<br>usa26511 미국주식 배당주 순위 |
| dvid_payout_max | 1 | 배당성향(최대) | 단위(%) | usa26500 미국주식 배당주 검색 |
| dvid_payout_min | 1 | 배당성향(최소) | 단위(%) | usa26500 미국주식 배당주 검색 |
| end_dt | 34 | 종료일자 | YYYYMMDD | ka10014 공매도추이요청<br>ka10038 종목별증권사순위요청<br>ka10042 순매수거래원순위요청<br>ka10043 거래원매물대분석요청<br>ka10044 일별기관매매종목요청 |
| engg_yn | 2 | 약정여부 |  | ust30141 미국주식 원화주문설정금 환전<br>ust31302 외화환전신청 |
| etf_cat1 | 31 | ETF코드1 | ETF 대카테고리코드 | usa20510 미국주식 기간별 등락률상위<br>usa20511 미국주식 기간별 등락률상위<br>usa20520 미국주식 거래량급등락<br>usa20530 미국주식 당일 거래량 상위<br>usa20540 미국주식 당일 거래대금 상위 |
| etf_cat2 | 31 | ETF코드2 | ETF 중카테고리코드 | usa20510 미국주식 기간별 등락률상위<br>usa20511 미국주식 기간별 등락률상위<br>usa20520 미국주식 거래량급등락<br>usa20530 미국주식 당일 거래량 상위<br>usa20540 미국주식 당일 거래대금 상위 |
| etfobjt_idex_cd | 1 | ETF대상지수코드 |  | ka40001 ETF수익율요청 |
| exmn_crnc | 1 | 환전통화 |  | ust30141 미국주식 원화주문설정금 환전 |
| exmn_end_dt | 1 | 환전종료기간 |  | ust31290 목표환율 자동환전 신청 |
| exmn_strt_dt | 1 | 환전시작기간 |  | ust31290 목표환율 자동환전 신청 |
| exmn_tp | 8 | 환전구분 | 1:외화매도 2:외화매수 3:매매기준환율 | ust30142 미국주식 원화주문설정금 환전<br>ust31280 자동환전조회취소<br>ust31290 목표환율 자동환전 신청<br>ust31291 목표환율 자동환전 신청<br>ust31292 목표환율 자동환전 신청 |
| exmn_tp_nm | 1 | 환전구분명 |  | ust31281 자동환전조회취소 |
| exp_buy_unp | 1 | 예상매수단가 |  | kt00010 주문인출가능금액요청 |
| exrt | 1 | 환율 |  | ust31281 자동환전조회취소 |
| exrt_appl_tp | 4 | 환율적용구분(0:미적용, 1:적용) |  | usa06012 미국주식 일 차트<br>usa06013 미국주식 주 차트<br>usa06014 미국주식 월 차트<br>usa06015 미국주식 년 차트 |
| exrt_tp | 3 | 환율구분 | 0:기준환율, 1:계좌적용환율, 2:전일최종환율 | ust21120 미국주식 원장 잔고현황<br>ust21121 미국주식 원장 잔고현황<br>ust21122 해외증권 계좌 잔고평가현황 |
| fc_amt | 1 | 외화금액 |  | ust31281 자동환전조회취소 |
| fc_exmn_amt | 4 | 외화환전금액 |  | ust30141 미국주식 원화주문설정금 환전<br>ust31290 목표환율 자동환전 신청<br>ust31300 외화환전신청<br>ust31302 외화환전신청 |
| fc_krw_tp | 6 | 외화원화구분 | 0:외화 1:원화 | ust21170 미국주식 당일 종목별 실현손익<br>ust21530 미국주식 실현손익<br>ust21610 미국주식 당일매매<br>ust21620 미국주식 당일매매정리<br>ust21630 미국주식 당일 실현손익 |
| flu_cnd | 1 | 등락조건 | 1:상위, 2:하위 | ka10028 시가대비등락률요청 |
| flu_pl_amt_tp | 1 | 등락수익구분 | 1:상위기간수익률, 2:하위기간수익률, 3:상위등락률, 4:하위등락률 | ka90001 테마그룹별요청 |
| flu_tp | 6 | 등락구분 | 1:급등, 2:급락 | ka10019 가격급등락요청<br>ka30001 ELW가격급등락요청<br>usa20510 미국주식 기간별 등락률상위<br>usa20511 미국주식 기간별 등락률상위<br>usa20930 미국주식 가격급등락 |
| for_prsm_unp_tp | 1 | 외인추정단가구분 | 1:매수단가, 2:매도단가 | ka10045 종목별기관매매추이요청 |
| fr_dt | 2 | 평가시작일 |  | kt00016 일별계좌수익률상세현황요청<br>ust21650 미국주식 기간별 수익률 현황 |
| fr_ord_no | 6 | 시작주문번호 | 공백허용 (공백일때 전체주문) | kt00007 계좌별주문체결내역상세요청<br>kt00009 계좌별주문체결현황요청<br>kt50030 금현물 주문체결전체조회<br>kt50031 금현물 주문체결조회<br>kt50075 금현물 미체결조회 |
| fr_rsrv_dt | 1 | 시작예약일자 | 미입력시 당일 | ust21201 미국주식 예약주문 내역조회 |
| fr_rsrv_ord_no | 1 | 시작예약번호 |  | ust21201 미국주식 예약주문 내역조회 |
| frcs_dt | 1 | 예정일자 |  | ust31500 미국주식 반대매매 예정내역 |
| frgn_all | 1 | 외국계전체 | 1:체크, 0:미체크 | ka10063 장중투자자별매매요청 |
| frgn_stex_code | 1 | 해외거래소코드 |  | kt00015 위탁종합거래내역요청 |
| frgn_trde_tp | 1 | 매매구분 | 00지정가 03시장가 34:Stop Limit 35:Stop Market | ust21200 미국주식 기간별 예약주문 |
| gds_tp | 2 | 상품구분 | 0:전체, 1:국내주식, 2:수익증권, 3:해외주식, 4:금융상품 | kt00015 위탁종합거래내역요청<br>usa20201 관심종목 그룹 상세 조회 |
| goal_exrt | 1 | 목표환율 |  | ust31290 목표환율 자동환전 신청 |
| grant_type | 1 | grant_type | client_credentials 입력 | au10001 접근토큰 발급 |
| grp_no | 19 | 그룹번호 |  | 00 주문체결<br>04 잔고<br>0A 주식기세<br>0B 주식체결<br>0C 주식우선호가 |
| high_low_close_tp | 1 | 고저종구분 | 1:고저기준, 2:종가기준 | ka10016 신고저가요청 |
| high_low_tp | 4 | 고저구분 | 1:고가, 2:저가 | ka10018 고저가근접요청<br>usa20970 미국주식 고가/저가 접근<br>usa20971 미국주식 고가/저가 접근<br>usa24100 미국주식 신고가/신저가 |
| indc_tp | 1 | 표시구분 | 0:수량, 1:금액(백만원) | ka10086 일별주가요청 |
| inds_cd | 47 | 업종코드 | 001:종합(KOSPI), 002:대형주, 003:중형주, 004:소형주 101:종합(KOSDAQ), 201:KOSPI200, 302:KOSTAR, 701: KRX100 나머지 ※ 업종코드 참고 | ka20001 업종현재가요청<br>ka20002 업종별주가요청<br>ka20003 전업종지수요청<br>ka20004 업종틱차트조회요청<br>ka20005 업종분봉조회요청 |
| inds_cls_tp | 3 | 해외주식업종분류구분 | 해외주식업종분류구분(조회KEY)<br>미국 (1:다우30,2:나스닥100,3:S&P500)<br>홍콩(4:H주20 2:H주  3:레드침20 5:ETF 1:레드칩)<br>상해A( 2:SSE380  1:SSE180)<br>심천A( 5:SSE380  6:SSE180) | usa24120 미국주식 특정일자 상승/하락<br>usa24260 미국주식 주요종목<br>usa24290 미국주식 주간거래 괴리율 상위 |
| inds_tp | 1 | 업종 구분 | 0:전체 (fid:9008이 일반주식일 경우 사용) | usa20930 미국주식 가격급등락 |
| inpt_cnt | 1 | 입력건수 | 20 | ust31281 자동환전조회취소 |
| input_tp | 3 | 입력구분 | 1:기준일 2:배당락일 | usa26500 미국주식 배당주 검색<br>usa26501 미국주식 배당주 검색<br>usa26511 미국주식 배당주 순위 |
| invsr | 1 | 투자자별 | 6:외국인, 7:기관계, 1:투신, 0:보험, 2:은행, 3:연기금, 4:국가, 5:기타법인 | ka10063 장중투자자별매매요청 |
| invsr_tp | 1 | 투자자구분 | 8000:개인, 9000:외국인, 1000:금융투자, 3000:투신, 3100:사모펀드, 5000:기타금융, 4000:은행, 2000:보험, 6000:연기금, 7000:국가, 7100:기타법인, 9999:기관계 | ka10058 투자자별일별매매종목요청 |
| io_amt | 1 | 입출금액 |  | kt00010 주문인출가능금액요청 |
| isin_code | 1 | 표준종목코드 |  | ust21380 미국주식 권리내역 |
| isscomp_cd | 4 | 발행사코드 | 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17 | ka30001 ELW가격급등락요청<br>ka30002 거래원별ELW순매매상위요청<br>ka30004 ELW괴리율요청<br>ka30005 ELW조건검색요청 |
| item | 19 | 실시간 등록 요소 | 종목코드,업종코드 등 | 00 주문체결<br>04 잔고<br>0A 주식기세<br>0B 주식체결<br>0C 주식우선호가 |
| item_cd | 2 | 아이템코드(재무계정코드) |  | usa06060 미국주식 재무차트-연간<br>usa06061 미국주식 재무차트-분기 |
| krw_exmn_amt | 1 | 원화환전금액 |  | ust30141 미국주식 원화주문설정금 환전 |
| krw_repl_asgna | 1 | 원화대용지정금액 | 해외원화주문설정금 | ust30132 미국주식 원화주문 가능금액 |
| krw_repl_skip_yn | 1 | 원화대용입출금제외여부 | Y:제외, N:비제외 | ust21100 미국주식 거래내역 |
| lpcd | 3 | LP코드 | 전체:000000000000, 한국투자증권:3, 미래대우:5, 신영:6, NK투자증권:12, KB증권:17 | ka30001 ELW가격급등락요청<br>ka30004 ELW괴리율요청<br>ka30005 ELW조건검색요청 |
| mang_stk_incls | 2 | 관리종목포함 | 0:관리종목 포함, 1:관리종목 미포함, 3:우선주제외, 11:정리매매종목제외, 4:관리종목, 우선주제외, 5:증100제외, 6:증100마나보기, 13:증60만보기, 12:증50만보기, 7:증40만보기, 8:증30만보기, 9:증20만보기, 14:ETF제외, 15:스팩제외, 16:ETF+ETN제외 | ka10030 당일거래량상위요청<br>ka10032 거래대금상위요청 |
| max_trde_prica | 1 | 최대거래대금 | 100000000 백만원 이하, 거래대금구분 1일때만 입력(공백허용) | ka10054 변동성완화장치발동종목요청 |
| max_trde_qty | 1 | 최대거래량 | 100000000 주 이하, 거래량구분이 1일때만 입력(공백허용) | ka10054 변동성완화장치발동종목요청 |
| mdfy_cond_uv | 2 | 정정조건단가 |  | kt10002 주식 정정주문<br>kt10008 신용 정정주문 |
| mdfy_qty | 4 | 정정수량 |  | kt10002 주식 정정주문<br>kt10008 신용 정정주문<br>kt50002 금현물 정정주문<br>ust20002 미국주식 정정 주문 |
| mdfy_uv | 5 | 정정단가 |  | kt10002 주식 정정주문<br>kt10008 신용 정정주문<br>kt50002 금현물 정정주문<br>ust20002 미국주식 정정 주문<br>ust21203 미국주식 예약주문 정정 |
| min_avg_tp | 1 | n분전/분평균 구분 | 0:n분전 1:분평균 | usa24210 미국주식 잔량률급증 |
| min_tic_tp | 2 | 분틱구분 | 0:틱, 1:분 | ka90005 프로그램매매추이요청 시간대별<br>ka90010 프로그램매매추이요청 일자별 |
| min_trde_prica | 1 | 최소거래대금 | 0 백만원 이상, 거래대금구분 1일때만 입력(공백허용) | ka10054 변동성완화장치발동종목요청 |
| min_trde_qty | 1 | 최소거래량 | 0 주 이상, 거래량구분이 1일때만 입력(공백허용) | ka10054 변동성완화장치발동종목요청 |
| mmcm_cd | 4 | 회원사코드 | 회원사 코드는 ka10102 조회 | ka10039 증권사별매매상위요청<br>ka10043 거래원매물대분석요청<br>ka10052 거래원순간거래량요청<br>ka10078 증권사별종목매매동향요청 |
| mngmcomp | 1 | 운용사 | 0000:전체, 3020:KODEX(삼성), 3027:KOSEF(키움), 3191:TIGER(미래에셋), 3228:KINDEX(한국투자), 3023:KStar(KB), 3022:아리랑(한화), 9999:기타운용사 | ka40004 ETF전체시세요청 |
| mnstar_eval_tp | 1 | 모닝스타 평가 | 0(전체), 1,2,3,4,5 | usa26500 미국주식 배당주 검색 |
| motn_drc | 1 | 발동방향 | 0:전체, 1:상승, 2:하락 | ka10054 변동성완화장치발동종목요청 |
| motn_tp | 1 | 발동구분 | 0:전체, 1:정적VI, 2:동적VI, 3:동적VI + 정적VI | ka10054 변동성완화장치발동종목요청 |
| mrkt_deal_tp | 3 | 시장거래구분 | %:전체, 1:코스피, 0:코스닥 | kt20016 신용융자 가능종목요청<br>kt50030 금현물 주문체결전체조회<br>kt50075 금현물 미체결조회 |
| mrkt_open_tp | 1 | 장운영구분 | 0:전체조회, 1:장중, 2:장전시간외, 3:장후시간외 | ka10030 당일거래량상위요청 |
| mrkt_tp | 50 | 시장구분 | 000:전체, 001:코스피, 101:코스닥 | ka10016 신고저가요청<br>ka10017 상하한가요청<br>ka10018 고저가근접요청<br>ka10019 가격급등락요청<br>ka10020 호가잔량상위요청 |
| natn_cd | 2 | 국가코드 | 미국 :1 | usa01990 관심종목 등록 상위<br>usa20880 키움 거래 상위 종목(주식/ETF) |
| navpre | 1 | NAV대비 | 0:전체, 1:NAV > 전일종가, 2:NAV < 전일종가 | ka40004 ETF전체시세요청 |
| netslmt_tp | 1 | 순매도수구분 | 2:순매수(고정값) | ka10131 기관외국인연속매매현황요청 |
| newstk_recvrht_tp | 1 | 신주인수권구분 | 00:전체, 05:신주인수권증권, 07:신주인수권증서 | ka10011 신주인수권전체시세요청 |
| next_key | 1 | 연속조회키 |  | ka10172 조건검색 요청 일반 |
| ntl_tp | 2 | 신고저구분 | 1:신고가,2:신저가 | ka10016 신고저가요청<br>usa24100 미국주식 신고가/신저가 |
| oppo_trde_tp | 2 | 반대매매구분 |  | ust21150 미국주식 일별 주문체결내역<br>ust21180 미국주식 기간별 주문체결내역 |
| ord_dt | 8 | 주문일자 | YYYYMMDD | kt00007 계좌별주문체결내역상세요청<br>kt00009 계좌별주문체결현황요청<br>kt50030 금현물 주문체결전체조회<br>kt50031 금현물 주문체결조회<br>kt50075 금현물 미체결조회 |
| ord_no | 2 | 주문번호 | 검색 기준 값으로 입력한 주문번호 보다 과거에 체결된 내역이 조회됩니다. | ka10076 체결요청<br>ka10088 미체결 분할주문 상세 |
| ord_qty | 9 | 주문수량 |  | kt10000 주식 매수주문<br>kt10001 주식 매도주문<br>kt10006 신용 매수주문<br>kt10007 신용 매도주문<br>kt50000 금현물 매수주문 |
| ord_send_dt | 1 | 주문전송일 |  | ust21204 미국주식 계좌별 일자별 예약내역 조회 |
| ord_uv | 9 | 주문단가 |  | kt10000 주식 매수주문<br>kt10001 주식 매도주문<br>kt10006 신용 매수주문<br>kt10007 신용 매도주문<br>kt50000 금현물 매수주문 |
| orgn_prsm_unp_tp | 1 | 기관추정단가구분 | 1:매수단가, 2:매도단가 | ka10045 종목별기관매매추이요청 |
| orgn_tp | 1 | 기관구분 | 9000:외국인, 9100:외국계, 1000:금융투자, 3000:투신, 5000:기타금융, 4000:은행, 2000:보험, 6000:연기금, 7000:국가, 7100:기타법인, 9999:기관계 | ka10065 장중투자자별매매상위요청 |
| orig_ord_no | 8 | 원주문번호 |  | kt10002 주식 정정주문<br>kt10003 주식 취소주문<br>kt10008 신용 정정주문<br>kt10009 신용 취소주문<br>kt50002 금현물 정정주문 |
| ottks_tp | 1 | 단주구분 | 1:당일매수에 대한 당일매도,2:당일매도 전체 | ka10170 당일매매일지요청 |
| pertp | 1 | PER구분 | 1:저PBR, 2:고PBR, 3:저PER, 4:고PER, 5:저ROE, 6:고ROE | ka10026 고저PER요청 |
| pot_tp | 2 | 시점구분 | 0:당일, 1:전일 | ka10042 순매수거래원순위요청<br>ka10043 거래원매물대분석요청 |
| prev_trde_qty | 2 | 이전거래량 | 5:5일, 10:10일, 20:20일, 60:60일, 250:250일 | usa23400 미국주식 거래량갱신<br>usa23401 미국주식 거래량갱신 |
| pric_cnd | 27 | 가격조건 | 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~3천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상 | ka10019 가격급등락요청<br>ka10027 전일대비등락률상위요청<br>ka10029 예상체결등락률상위요청<br>usa20510 미국주식 기간별 등락률상위<br>usa20511 미국주식 기간별 등락률상위 |
| pric_cnd1 | 5 | 가격조건1 |  | usa20570 미국주식 가격대별주가<br>usa20940 미국주식 누적 등락률 상위<br>usa26500 미국주식 배당주 검색<br>usa26501 미국주식 배당주 검색<br>usa26511 미국주식 배당주 순위 |
| pric_cnd2 | 5 | 가격조건2 |  | usa20570 미국주식 가격대별주가<br>usa20940 미국주식 누적 등락률 상위<br>usa26500 미국주식 배당주 검색<br>usa26501 미국주식 배당주 검색<br>usa26511 미국주식 배당주 순위 |
| pric_cnd_ed | 2 | 가격조건 끝 | *이상인 경우  0으로 | usa20970 미국주식 고가/저가 접근<br>usa20971 미국주식 고가/저가 접근 |
| pric_cnd_st | 2 | 가격조건 시작 | 미만 인 경우 :0으로 | usa20970 미국주식 고가/저가 접근<br>usa20971 미국주식 고가/저가 접근 |
| pric_tp | 3 | 가격구분 | 0:전체조회, 2:5만원이상, 5:1만원이상, 6:5천원이상, 8:1천원이상, 9:10만원이상 | ka10023 거래량급증요청<br>ka10030 당일거래량상위요청<br>ka10052 거래원순간거래량요청 |
| proc_tp | 1 | 처리구분 | %:전체, 0:미처리, 1:처리, 3:만료, 5:취소, 9:오류 | ust31280 자동환전조회취소 |
| proc_tp_nm | 1 | 처리구분명 |  | ust31281 자동환전조회취소 |
| prps_cnctr_rt | 2 | 매물집중비율 | 0~100 입력 | ka10025 매물대집중요청<br>usa24220 미국주식 매물대집중 |
| prpscnt | 2 | 매물대수 | 숫자입력 | ka10025 매물대집중요청<br>usa24220 미국주식 매물대집중 |
| pswd | 1 | 비밀번호 |  | ust21121 미국주식 원장 잔고현황 |
| pswd_inpt_mdia_tp | 3 | 비밀번호입력매체구분 | 00일반(기본값) | ust21111 해외주식 인출가능금액<br>ust21121 미국주식 원장 잔고현황<br>ust21150 미국주식 일별 주문체결내역 |
| qry_dt | 3 | 조회일자 |  | ka01690 일별잔고수익률<br>ka10086 일별주가요청<br>ust21531 미국주식 실현손익 |
| qry_dt_tp | 3 | 조회기간구분 | 0:기간으로 조회, 1:시작일자, 종료일자로 조회 | ka10042 순매수거래원순위요청<br>ka10043 거래원매물대분석요청<br>ka90009 외국인기관매매상위요청 |
| qry_tp | 25 | 구분 | 1:1분, 2:10분, 3:1시간, 4:당일 누적, 5:30초 | ka00198 실시간종목조회순위<br>ka10013 신용매매동향요청<br>ka10031 전일거래량상위요청<br>ka10038 종목별증권사순위요청<br>ka10076 체결요청 |
| qty_tp | 1 | 수량구분 | 0:전체, 1:1000주, 2:2000주, 3:, 5:, 10:10000주, 30: 30000주, 50: 50000주, 100: 100000주 | ka10052 거래원순간거래량요청 |
| query_tp | 1 | 조회구분 |  | ust21150 미국주식 일별 주문체결내역 |
| rank_end | 1 | 순위끝 | 0 ~ 100 값 중에  조회를 원하는 순위 끝값 | ka10031 전일거래량상위요청 |
| rank_strt | 1 | 순위시작 | 0 ~ 100 값 중에  조회를 원하는 순위 시작값 | ka10031 전일거래량상위요청 |
| refresh | 19 | 기존등록유지여부 | 등록(REG)시<br><br>기존유지안함 1:기존유지(Default)<br><br> 0일경우 기존등록한 item/type은 해지, 1일경우 기존등록한 item/type 유지<br><br>해지(REMOVE)시 값 불필요 | 00 주문체결<br>04 잔고<br>0A 주식기세<br>0B 주식체결<br>0C 주식우선호가 |
| rght_tp | 6 | 권리구분 | 000:전체, 001:콜, 002:풋, 003:DC, 004:DP, 005:EX, 006:조기종료콜, 007:조기종료풋 | ka30001 ELW가격급등락요청<br>ka30004 ELW괴리율요청<br>ka30005 ELW조건검색요청<br>ka30009 ELW등락율순위요청<br>ka30010 ELW잔량순위요청 |
| rgst_abnd_tp_nm | 1 | 등록해지구분명 |  | ust31281 자동환전조회취소 |
| rprt_exrt_tp | 2 | 예약환율구분 | %:전체, 1:직접입력, 2:최근1주일최저, 3:최근1개월최저 | ust31280 자동환전조회취소<br>ust31290 목표환율 자동환전 신청 |
| rqst_dt | 1 | 신청일자 |  | ust31281 자동환전조회취소 |
| rqst_tp | 1 | 등록구분 | %:전체, 1:등록, 2:해지 | ust31280 자동환전조회취소 |
| rsrv_cncl_yn | 1 | 예약취소구분 | 0:전체, Y:취소, N:미취소 | ust21201 미국주식 예약주문 내역조회 |
| rsrv_dt | 2 | 예약일 |  | ust21202 미국주식 예약주문 취소<br>ust21203 미국주식 예약주문 정정 |
| rsrv_end_dt | 2 | 기간예약종료일자 |  | ust21200 미국주식 기간별 예약주문<br>ust21203 미국주식 예약주문 정정 |
| rsrv_exrt_tp | 1 | 예약환율구분 | 2:최근1주일최저 3:최근1개월최저 4:최근1주일최고 5:최근1개월최고 | ust31292 목표환율 자동환전 신청 |
| rsrv_exrt_tp_nm | 1 | 예약환율구분명 |  | ust31281 자동환전조회취소 |
| rsrv_ord_no | 2 | 예약주문번호 |  | ust21202 미국주식 예약주문 취소<br>ust21203 미국주식 예약주문 정정 |
| rsrv_ord_tp | 3 | 예약주문구분 | 1일반예약 2기간예약(잔량주문) 3기간예약(지정수량주문) | ust21200 미국주식 기간별 예약주문<br>ust21201 미국주식 예약주문 내역조회<br>ust21204 미국주식 계좌별 일자별 예약내역 조회 |
| rsrv_proc_tp | 1 | 예약처리구분 | %:전체 0:미처리 1:처리및오류 | ust21201 미국주식 예약주문 내역조회 |
| rsrv_strt_dt | 1 | 기간예약시작일자 |  | ust21200 미국주식 기간별 예약주문 |
| rt_tp | 2 | 비율구분 | 1:매수/매도비율, 2:매도/매수비율 | ka10022 잔량율급증요청<br>usa24210 미국주식 잔량률급증 |
| search_type | 2 | 조회타입 | 0:조건검색 | ka10172 조건검색 요청 일반<br>ka10173 조건검색 요청 실시간 |
| secretkey | 2 | 시크릿키 |  | au10001 접근토큰 발급<br>au10002 접근토큰폐기 |
| sell_aplc_exrt | 1 | 매도적용환율 |  | ust31302 외화환전신청 |
| sell_crnc_code | 3 | 매도통화코드 |  | ust31300 외화환전신청<br>ust31301 외화환전신청<br>ust31302 외화환전신청 |
| sell_tp | 6 | 매도수구분 | 0:전체, 1:매도, 2:매수 | ka10076 체결요청<br>kt00007 계좌별주문체결내역상세요청<br>kt00009 계좌별주문체결현황요청<br>kt50031 금현물 주문체결조회<br>kt50075 금현물 미체결조회 |
| seq | 3 | 조건검색식 일련번호 |  | ka10172 조건검색 요청 일반<br>ka10173 조건검색 요청 실시간<br>ka10174 조건검색 실시간 해제 |
| skip_stk | 1 | 제외종목 | 전종목포함 조회시 9개 0으로 설정(000000000),전종목제외 조회시 9개 1으로 설정(111111111),9개 종목조회여부를 조회포함(0), 조회제외(1)로 설정하며 종목순서는 우선주,관리종목,투자경고/위험,투자주의,환기종목,단기과열종목,증거금100%,ETF,ETN가 됨.우선주만 조회시"011111111"", 관리종목만 조회시 ""101111111"" 설정" | ka10054 변동성완화장치발동종목요청 |
| slby_tp | 7 | 매도수구분 | 0:전체, 1:매도, 2:매수 | kt50030 금현물 주문체결전체조회<br>ust21050 미국주식 원장 미체결<br>ust21150 미국주식 일별 주문체결내역<br>ust21180 미국주식 기간별 주문체결내역<br>ust21200 미국주식 기간별 예약주문 |
| smtm_netprps_tp | 1 | 동시순매수구분 | 1:체크, 0:미체크 | ka10063 장중투자자별매매요청 |
| sort_base | 3 | 정렬기준 | 1:종가순, 2:날짜순 | ka10042 순매수거래원순위요청<br>ka10043 거래원매물대분석요청<br>ka10098 시간외단일가등락율순위요청 |
| sort_cnd | 1 | 정렬조건 | 1:수량, 2:금액 | ka10062 동일순매매순위요청 |
| sort_tp | 29 | 정렬구분 | 1:종목코드순, 2:연속횟수순(상위100개), 3:등락률순 | ka10017 상하한가요청<br>ka10020 호가잔량상위요청<br>ka10021 호가잔량급증요청<br>ka10023 거래량급증요청<br>ka10027 전일대비등락률상위요청 |
| srch_yr | 1 | 조회연도 |  | usa26411 미국주식 연도별 등락률 |
| start_dt | 1 | 시작조회기간 | YYYYMMDD | kt00002 일별추정예탁자산현황요청 |
| stex_code | 3 | 거래소코드 |  | ust21100 미국주식 거래내역<br>ust31520 미국주식 배당금 입금 내역<br>ust31521 미국주식 배당금 입금 내역 |
| stex_tp | 104 | 거래소구분 | 1:KRX, 2:NXT 3.통합 | ka10016 신고저가요청<br>ka10017 상하한가요청<br>ka10018 고저가근접요청<br>ka10019 가격급등락요청<br>ka10020 호가잔량상위요청 |
| stk_bond_tp | 5 | 주식채권구분 | 0:전체, 1:주식, 2:채권 | kt00007 계좌별주문체결내역상세요청<br>kt00009 계좌별주문체결현황요청<br>kt50030 금현물 주문체결전체조회<br>kt50031 금현물 주문체결조회<br>kt50075 금현물 미체결조회 |
| stk_cd | 128 | 종목코드 | 거래소별 종목코드<br>(KRX:039490,NXT:039490_NX,SOR:039490_AL) | ka10001 주식기본정보요청<br>ka10002 주식거래원요청<br>ka10003 체결정보요청<br>ka10004 주식호가요청<br>ka10005 주식일주월시분요청 |
| stk_cnd | 41 | 종목조건 | 0:전체조회,1:관리종목제외, 3:우선주제외, 5:증100제외, 6:증100만보기, 7:증40만보기, 8:증30만보기 | ka10016 신고저가요청<br>ka10017 상하한가요청<br>ka10018 고저가근접요청<br>ka10019 가격급등락요청<br>ka10020 호가잔량상위요청 |
| stk_code | 22 | 종목코드 |  | ust20000 미국주식 매수 주문<br>ust20001 미국주식 매도 주문<br>ust20002 미국주식 정정 주문<br>ust20003 미국주식 취소 주문<br>ust21050 미국주식 원장 미체결 |
| stk_inds_tp | 1 | 종목업종구분 | 0:종목(주식),1:업종 | ka10131 기관외국인연속매매현황요청 |
| stk_tp | 36 | 시장구분 | (A:전체,S:주식,E:ETF) | usa01990 관심종목 등록 상위<br>usa20510 미국주식 기간별 등락률상위<br>usa20511 미국주식 기간별 등락률상위<br>usa20520 미국주식 거래량급등락<br>usa20530 미국주식 당일 거래량 상위 |
| stop_pric | 4 | STOP가격 |  | ust20001 미국주식 매도 주문<br>ust20002 미국주식 정정 주문<br>ust21200 미국주식 기간별 예약주문<br>ust21203 미국주식 예약주문 정정 |
| strt_dcd_seq | 1 | 시작결제번호 |  | kt00008 계좌별익일결제예정내역요청 |
| strt_dt | 52 | 시작일자 | YYYYMMDD | ka10014 공매도추이요청<br>ka10015 일별거래상세요청<br>ka10038 종목별증권사순위요청<br>ka10042 순매수거래원순위요청<br>ka10043 거래원매물대분석요청 |
| svc_type | 1 | 서비스 유형 |  | usa01980 실시간 종목 조회 순위 |
| tdy_pred | 2 | 당일전일 | 1:당일, 2:전일 | ka10055 당일전일체결량요청<br>ka10084 당일전일체결요청 |
| thema_grp_cd | 1 | 테마그룹코드 | 테마그룹코드 번호 | ka90002 테마구성종목요청 |
| thema_nm | 1 | 테마명 | 검색하려는 테마명 | ka90001 테마그룹별요청 |
| tic_min | 1 | 틱분 | 0:틱, 1:분 | ka10084 당일전일체결요청 |
| tic_scope | 13 | 틱범위 | 1:1틱, 3:3틱, 5:5틱, 10:10틱, 30:30틱 | ka10079 주식틱차트조회요청<br>ka10080 주식분봉차트조회요청<br>ka20004 업종틱차트조회요청<br>ka20005 업종분봉조회요청<br>ka50079 금현물틱차트조회요청 |
| tm | 11 | 시간 | 분 혹은 일입력 | ka10019 가격급등락요청<br>ka10023 거래량급증요청<br>ka10084 당일전일체결요청<br>ka30001 ELW가격급등락요청<br>usa20510 미국주식 기간별 등락률상위 |
| tm_tp | 8 | 시간구분 | 0:시작일, 1:기간 | ka10014 공매도추이요청<br>ka10019 가격급등락요청<br>ka10021 호가잔량급증요청<br>ka10022 잔량율급증요청<br>ka10023 거래량급증요청 |
| to_dt | 2 | 평가종료일 |  | kt00016 일별계좌수익률상세현황요청<br>ust21650 미국주식 기간별 수익률 현황 |
| to_rsrv_dt | 1 | 종료예약일자 | 미입력시 당일 | ust21201 미국주식 예약주문 내역조회 |
| token | 1 | 접근토큰 |  | au10002 접근토큰폐기 |
| tp | 5 | 구분 | 0:전체,1:입출금,2:입출고,3:매매,4:매수,5:매도,6:입금,7:출금,A:예탁담보대출입금,B:매도담보대출입금,C:현금상환(융자,담보상환),F:환전,M:입출금+환전,G:외화매수,H:외화매도,I:환전정산입금,J:환전정산출금 | kt00015 위탁종합거래내역요청<br>kt50032 금현물 거래내역조회<br>ust21100 미국주식 거래내역<br>ust30132 미국주식 원화주문 가능금액<br>ust31290 목표환율 자동환전 신청 |
| trace_idex | 1 | 추적지수 | 0:전체 | ka40004 ETF전체시세요청 |
| trde_end_elwskip | 3 | 거래종료ELW제외 | 0:포함, 1:제외 | ka30001 ELW가격급등락요청<br>ka30002 거래원별ELW순매매상위요청<br>ka30004 ELW괴리율요청 |
| trde_end_skip | 2 | 거래종료제외 | 1:거래종료제외, 0:거래종료포함 | ka30009 ELW등락율순위요청<br>ka30010 ELW잔량순위요청 |
| trde_gold_tp | 1 | 매매금구분 | 0:전체조회, 1:1천원미만, 2:1천원~2천원, 3:2천원~3천원, 4:5천원~1만원, 5:1만원이상, 8:1천원이상 | ka10017 상하한가요청 |
| trde_pric_cnd_ed | 2 | 거래대금조건끝 |  | usa20970 미국주식 고가/저가 접근<br>usa20971 미국주식 고가/저가 접근 |
| trde_pric_cnd_st | 2 | 거래대금조건시작 |  | usa20970 미국주식 고가/저가 접근<br>usa20971 미국주식 고가/저가 접근 |
| trde_prica | 1 | 거래대금 | 0:전체조회, 5:5백만원이상,10:1천만원이상, 30:3천만원이상, 50:5천만원이상, 100:1억원이상, 300:3억원이상, 500:5억원이상, 1000:10억원이상, 3000:30억원이상, 5000:50억원이상, 10000:100억원이상 | ka10098 시간외단일가등락율순위요청 |
| trde_prica_cnd | 26 | 거래대금조건 | 0:전체조회, 3:3천만원이상, 5:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상 | ka10027 전일대비등락률상위요청<br>ka10028 시가대비등락률요청<br>usa20510 미국주식 기간별 등락률상위<br>usa20511 미국주식 기간별 등락률상위<br>usa20520 미국주식 거래량급등락 |
| trde_prica_tp | 2 | 거래대금구분 | 0:전체조회, 1:1천만원이상, 3:3천만원이상, 4:5천만원이상, 10:1억원이상, 30:3억원이상, 50:5억원이상, 100:10억원이상, 300:30억원이상, 500:50억원이상, 1000:100억원이상, 3000:300억원이상, 5000:500억원이상 | ka10030 당일거래량상위요청<br>ka10054 변동성완화장치발동종목요청 |
| trde_qty | 1 | 매매수량 |  | kt00010 주문인출가능금액요청 |
| trde_qty_cnd | 4 | 거래량조건 | 0000:전체조회, 0010:만주이상, 0050:5만주이상, 0100:10만주이상, 0150:15만주이상, 0200:20만주이상, 0300:30만주이상, 0500:50만주이상, 1000:백만주이상 | ka10027 전일대비등락률상위요청<br>ka10028 시가대비등락률요청<br>ka10029 예상체결등락률상위요청<br>ka10098 시간외단일가등락율순위요청 |
| trde_qty_cnd_fr | 2 | 거래량조건시작(from) | 전체 :  9515=9616=0<br>미만 : 9515=0 9516 = 10(10만 미만)<br>이상 : 9510 :10 (10만주이상) 9516=0 | usa20970 미국주식 고가/저가 접근<br>usa20971 미국주식 고가/저가 접근 |
| trde_qty_cnd_to | 2 | 거래량조건끝(to) |  | usa20970 미국주식 고가/저가 접근<br>usa20971 미국주식 고가/저가 접근 |
| trde_qty_tp | 42 | 거래량구분 | 00000:전체조회, 00010:만주이상, 00050:5만주이상, 00100:10만주이상, 00150:15만주이상, 00200:20만주이상, 00300:30만주이상, 00500:50만주이상, 01000:백만주이상 | ka10016 신고저가요청<br>ka10017 상하한가요청<br>ka10018 고저가근접요청<br>ka10019 가격급등락요청<br>ka10020 호가잔량상위요청 |
| trde_tp | 25 | 매매구분 | 1:매수잔량, 2:매도잔량 | ka10021 호가잔량급증요청<br>ka10034 외인기간별매매상위요청<br>ka10035 외인연속순매매상위요청<br>ka10037 외국계창구매매상위요청<br>ka10039 증권사별매매상위요청 |
| trde_upper_tp | 1 | 매매상위구분 | 1:순매도상위, 2:순매수상위 | ka90003 프로그램순매수상위50요청 |
| trnm | 23 | TR명 | CNSRLST고정값 | ka10171 조건검색 목록조회<br>ka10172 조건검색 요청 일반<br>ka10173 조건검색 요청 실시간<br>ka10174 조건검색 실시간 해제<br>00 주문체결 |
| txon_type | 1 | 과세유형 | 0:전체, 1:비과세, 2:보유기간과세, 3:회사형, 4:외국, 5:비과세해외(보유기간관세) | ka40004 ETF전체시세요청 |
| txon_yn | 1 | 과세여부 | 0:전체, 1:과세, 2:비과세 | ka40004 ETF전체시세요청 |
| type | 19 | 실시간 항목 | TR 명(0A,0B....) | 00 주문체결<br>04 잔고<br>0A 주식기세<br>0B 주식체결<br>0C 주식우선호가 |
| unit_tp | 4 | 단위구분 | 1000:천주, 1:단주 | ka10059 종목별투자자기관별요청<br>ka10060 종목별투자자기관별차트요청<br>ka10061 종목별투자자기관별합계요청<br>ka10062 동일순매매순위요청 |
| upd_stkpc_tp | 13 | 수정주가구분 | 0 or 1 | ka10079 주식틱차트조회요청<br>ka10080 주식분봉차트조회요청<br>ka10081 주식일봉차트조회요청<br>ka10082 주식주봉차트조회요청<br>ka10083 주식월봉차트조회요청 |
| updown_incls | 5 | 상하한포함 | 0:미포함, 1:포함 | ka10016 신고저가요청<br>ka10019 가격급등락요청<br>ka10027 전일대비등락률상위요청<br>ka10028 시가대비등락률요청<br>ka10033 신용비율상위요청 |
| updown_tp | 2 | 상하한구분 | 1:상한, 2:상승, 3:보합, 4: 하한, 5:하락, 6:전일상한, 7:전일하한 | ka10017 상하한가요청<br>usa24140 미국주식 갭상승/갭하락 |
| usid | 2 | 사용자ID |  | usa20200 관심종목 그룹 리스트 조회<br>usa20201 관심종목 그룹 상세 조회 |
| uv | 4 | 매수가격 |  | kt00010 주문인출가능금액요청<br>kt00011 증거금율별주문가능수량조회요청<br>kt00012 신용보증금율별주문가능수량조회요청<br>ust31490 미국주식 주문가능수량(종목/증거금률별) |
| wi_crnc_code | 6 | 통화코드 |  | usa21670 일별계좌수익률현황<br>usa21680 월별계좌수익률현황<br>usa21690 연도별계좌수수익률현황<br>usa21730 일별종목수익률현황<br>usa21731 월별종목수익률현황 |
| wi_from | 6 | from 일자 | YYYYMMDD | usa21670 일별계좌수익률현황<br>usa21680 월별계좌수익률현황<br>usa21690 연도별계좌수수익률현황<br>usa21730 일별종목수익률현황<br>usa21731 월별종목수익률현황 |
| wi_isin_code | 3 | ISIN 코드 |  | usa21730 일별종목수익률현황<br>usa21731 월별종목수익률현황<br>usa21732 연도별종목수익률현황 |
| wi_stex_tp | 6 | 거래소구분 |  | usa21670 일별계좌수익률현황<br>usa21680 월별계좌수익률현황<br>usa21690 연도별계좌수수익률현황<br>usa21730 일별종목수익률현황<br>usa21731 월별종목수익률현황 |
| wi_to | 6 | to 일자 | YYYYMMDD | usa21670 일별계좌수익률현황<br>usa21680 월별계좌수익률현황<br>usa21690 연도별계좌수수익률현황<br>usa21730 일별종목수익률현황<br>usa21731 월별종목수익률현황 |

</details>
