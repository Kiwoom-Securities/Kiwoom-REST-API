# generate_postman.py 구조 설명

`generate_postman.py`는 키움 REST API 원천 `xlsx` 파일을 입력받아 Postman Collection v2.1 JSON을 직접 생성하는 단일 실행파일입니다. 레거시 생성기 패키지를 import하지 않으며, `api_list.csv`나 `kiwoom_api_spec.json` 같은 중간 산출물을 필수 입력으로 사용하지 않습니다.

## 실행 흐름

```text
xlsx
  -> parse_workbook()
  -> load_postman_config()
  -> build_postman_collection()
  -> _build_request_item()
  -> write_postman_collection()
  -> postman/*.postman_collection.json
```

CLI 진입점은 파일 하단의 `_parse_args()`와 `main()`입니다.

## 큰 섹션

### 1. 상수와 데이터 모델

파일 상단에는 기본 출력 경로, Postman schema URL, workbook section 이름, 지원 옵션이 있습니다.

주요 dataclass는 다음 책임을 갖습니다.

- `ApiListRow`: xlsx의 `API 리스트` 시트 한 행
- `ApiSpec`: Postman 생성에 필요한 정규화된 API 스펙
- `PostmanEnvironmentConfig`: 운영/모의투자 등 Postman 폴더와 변수 매핑
- `PostmanConfig`: collection 생성 정책 전체
- `BodyVariable`: request body 값을 Postman 변수로 치환할 때 쓰는 변수 정보
- `SkippedApi`: 생성에서 제외한 API 정보
- `PostmanGenerationReport`: 생성 결과 리포트

수정 포인트:

- Postman 변수 기본값은 `default_postman_config()`를 봅니다.
- 지원 body parameter mode를 추가하려면 `SUPPORTED_BODY_PARAMETER_MODES`와 `_build_request_item()`을 함께 봅니다.
- WebSocket 처리 전략을 추가하려면 `SUPPORTED_WEBSOCKET_STRATEGIES`, `build_postman_collection()`, `_api_kind()`를 함께 봅니다.

### 2. 기본 Postman 설정

`generator/postman_collection_config.json`이 기본 config 파일입니다.
`default_postman_config()`는 해당 파일이 없거나 config 항목이 비어 있을 때 적용되는 기본 정책입니다.

기본 설정:

- collection name: `Kiwoom OpenAPI`
- schema: Postman Collection v2.1
- static variables: `PRD`, `MOCK`, `APP_KEY`, `APP_SECRET`, `APP_KEY_MOCK`, `APP_SECRET_MOCK`
- environments: 운영, 모의투자
- WebSocket: skip
- REST body mode: `query_params_and_body`
- 날짜 계열 request field 기본값 override

수정 포인트:

- 기본 base URL은 `static_variables`에서 바꿉니다.
- 운영/모의투자 폴더명은 `PostmanEnvironmentConfig.folder_name` 기본값을 바꿉니다.
- 기본 request field 값은 `request_value_overrides_by_field`를 바꿉니다.

주의:

- `--config`를 생략하면 `generator/postman_collection_config.json`을 사용합니다.
- config 파일이 없어도 동작해야 하므로 fallback 기본 정책은 이 함수 안에 완결되어 있어야 합니다.

### 3. xlsx 파싱

이 섹션은 원천 workbook을 직접 읽어서 `ApiSpec` 목록을 만듭니다.

주요 함수:

- `parse_workbook()`
- `_parse_api_list()`
- `_parse_api_sheet()`
- `_find_sections()`
- `_section_range()`
- `_parse_request_response_block()`
- `_parse_api_meta()`
- `_parse_example_block()`
- `_parse_element_depth()`
- `_cell_text()`

수정 포인트:

- xlsx 시트 구조가 바뀌면 이 섹션만 먼저 봅니다.
- `API 리스트` 컬럼명이 바뀌면 `_parse_api_list()`를 수정합니다.
- 상세 API 시트의 section 탐색 규칙은 `_find_sections()`와 `_section_range()`를 수정합니다.
- Request/Response 표의 컬럼 해석은 `_parse_request_response_block()`을 수정합니다.

주의:

- 이 섹션은 Postman JSON 구조를 몰라야 합니다.
- xlsx 원천 해석과 Postman 생성 정책을 섞지 않는 것이 유지보수에 유리합니다.

### 4. Postman config 로딩과 검증

`load_postman_config()`는 optional config JSON을 읽고 기본 config 위에 명시 설정을 적용합니다.

주요 함수:

- `load_postman_config()`
- `_load_static_variables()`
- `_load_environment_configs()`
- `_load_request_value_overrides()`
- `_required_string()`
- `_optional_string()`

수정 포인트:

- config JSON의 schema를 바꾸려면 이 섹션을 봅니다.
- static variable을 추가/삭제하려면 `REQUIRED_STATIC_VARIABLES`와 `_load_static_variables()`를 같이 봅니다.
- 환경별 access token 변수 정책은 `_load_environment_configs()`를 봅니다.
- request value override 규칙은 `_load_request_value_overrides()`를 봅니다.

주의:

- `--config`를 생략하면 `generator/postman_collection_config.json`을 사용하고, 다른 파일을 넘기면 해당 파일이 기본 config를 대체/보강합니다.
- 기본값을 완전히 대체하는 항목과 기본값에 merge되는 항목을 구분해야 합니다.
- 현재 `request_value_overrides.by_field`는 기본값 위에 override를 덮어씁니다.

### 5. Collection 생성 오케스트레이션

`build_postman_collection()`은 `ApiSpec` 목록과 `PostmanConfig`를 받아 최종 collection dict와 report를 만듭니다.

주요 책임:

- environment별 최상위 폴더 생성
- category/sub_category별 폴더 구성
- API kind 분류
- WebSocket skip 처리
- request path 중복 검증
- report count 계산

수정 포인트:

- Postman 폴더 구조를 바꾸려면 `build_postman_collection()`과 `_environment_folder()`를 봅니다.
- WebSocket을 skip이 아닌 다른 방식으로 생성하려면 `build_postman_collection()`의 skip 분기를 바꿉니다.
- 중복 request name 검증 정책은 `request_paths` 처리 부분을 봅니다.

### 6. 파일 쓰기

`write_postman_collection()`은 CLI와 생성 로직 사이의 실행 단위입니다.

주요 책임:

- workbook 파싱
- config 로딩
- collection/report 생성
- output JSON 쓰기
- optional report 쓰기

수정 포인트:

- 산출물 포맷을 바꾸려면 여기보다 `build_postman_collection()`을 먼저 봅니다.
- 파일 저장 위치 기본값은 상단의 `DEFAULT_OUTPUT_PATH`, `DEFAULT_REPORT_PATH`를 봅니다.
- 저장 여부 옵션은 CLI와 이 함수의 `report_path` 흐름을 같이 봅니다.

### 7. Request item 생성

`_build_request_item()`은 API 하나를 Postman request item 하나로 바꿉니다.

주요 처리:

- body parameter mode에 따라 body/query 생성
- header 생성
- raw URL과 Postman URL object 생성
- description 생성
- pre-request/test event 생성

수정 포인트:

- Postman request의 전체 shape을 바꾸려면 `_build_request_item()`을 봅니다.
- request body와 query parameter 관계를 바꾸려면 `_build_request_item()`, `_request_body()`, `_request_query_parameters()`, `_query_parameters()`를 같이 봅니다.
- request 이름 규칙은 `_build_request_item()`의 `name` 값을 바꿉니다.

### 8. Header 생성

`_request_headers()`는 API kind와 request header spec을 바탕으로 Postman header 목록을 만듭니다.

현재 규칙:

- 모든 request에 `Content-Type` 추가
- OAuth가 아니면 `api-id`, `authorization` 추가
- 원천 spec에 `cont-yn`, `next-key`가 있으면 disabled header로 추가

수정 포인트:

- 인증 header 형식을 바꾸려면 `_request_headers()`를 봅니다.
- 연속조회 header 설명을 바꾸려면 `cont-yn`, `next-key` append 블록을 봅니다.

### 9. Body와 Query 생성

Postman request 입력값 생성의 핵심 섹션입니다.

주요 함수:

- `_request_body()`
- `_request_query_parameters()`
- `_replace_body_values_with_postman_variables()`
- `_query_parameters()`
- `_request_body_example()`
- `_request_body_descriptions()`

body mode별 대략적 의미:

```text
inline_examples       -> request example 값을 body에 직접 넣음
postman_variables    -> body 값을 collection variable 참조로 치환
query_params_to_body  -> query param 변수를 만들고 pre-request에서 body에 반영
query_params          -> top-level body field를 Params 탭에 노출
query_params_and_body -> Params 탭과 raw JSON body를 함께 생성
```

수정 포인트:

- Postman Params 탭 노출 방식을 바꾸려면 `_request_query_parameters()`를 봅니다.
- raw JSON body 생성 방식을 바꾸려면 `_request_body()`와 `_build_request_item()`을 봅니다.
- Postman variable 이름 규칙은 `_body_variable_name()`을 봅니다.
- request example fallback은 `_request_body_example()`을 봅니다.

### 10. 민감값 치환

`_replace_sensitive_values()`는 request body 안의 민감 필드를 Postman 변수 참조로 바꿉니다.

관련 함수:

- `_replace_sensitive_values()`
- `_sensitive_field_role()`

현재 인식하는 role:

- `appkey` -> app key variable
- `secretkey`, `appsecret` -> app secret variable
- `token` -> access token variable
- `authorization` -> `Bearer {{ACCESS_TOKEN}}`

수정 포인트:

- 민감 필드명을 추가하려면 `_sensitive_field_role()`을 봅니다.
- 값 치환 형식을 바꾸려면 `_replace_sensitive_values()`를 봅니다.

### 11. Event script 생성

Postman pre-request/test script를 만드는 섹션입니다.

주요 함수:

- `_request_events()`
- `_token_save_event()`
- `_revoke_token_cleanup_event()`
- `_body_variable_defaults_event()`
- `_query_params_to_body_event()`
- `_query_params_to_body_script()`
- `_script_event()`

수정 포인트:

- OAuth token 저장 스크립트는 `_token_save_event()`를 봅니다.
- revoke 후 token cleanup은 `_revoke_token_cleanup_event()`를 봅니다.
- Params 탭 값을 JSON body에 반영하는 스크립트는 `_query_params_to_body_script()`를 봅니다.
- 새 Postman event를 추가하려면 `_request_events()`에 분기를 추가합니다.

### 12. Description 생성

`_request_description()`은 Postman request description markdown을 만듭니다.

관련 함수:

- `_request_description()`
- `_field_table()`
- `_markdown_cell()`

수정 포인트:

- description 전체 구성을 바꾸려면 `_request_description()`을 봅니다.
- 요청/응답 field table 컬럼을 바꾸려면 `_field_table()`을 봅니다.
- markdown escaping 규칙은 `_markdown_cell()`을 봅니다.

### 13. URL과 Collection folder helper

이 섹션은 Postman URL object와 folder object를 만듭니다.

주요 함수:

- `_environment_folder()`
- `_raw_url()`
- `_postman_url()`
- `_raw_query_component()`
- `_query_value()`

수정 포인트:

- Postman folder depth를 바꾸려면 `_environment_folder()`를 봅니다.
- raw URL query string 생성 방식을 바꾸려면 `_raw_url()`을 봅니다.
- Postman URL object shape을 바꾸려면 `_postman_url()`을 봅니다.

### 14. API kind와 공통 helper

주요 함수:

- `_api_kind()`
- `_jsonish()`
- `_is_required_field()`
- `_requires_raw_json_body()`
- `_is_list_container()`
- `_is_existing_postman_variable()`
- `_json_dump()`

수정 포인트:

- OAuth/REST/WebSocket 분류 기준은 `_api_kind()`를 봅니다.
- GET/HEAD body 생성 여부는 `_requires_raw_json_body()`를 봅니다.
- JSON pretty format은 `_json_dump()`를 봅니다.

### 15. CLI

파일 하단의 `_parse_args()`와 `main()`이 CLI 진입점입니다.

현재 주요 옵션:

```bash
uv run python generator/generate_postman.py workbook.xlsx
uv run python generator/generate_postman.py workbook.xlsx --out postman/kiwoom-openapi.postman_collection.json
uv run python generator/generate_postman.py workbook.xlsx --config custom_postman_config.json
uv run python generator/generate_postman.py workbook.xlsx --no-report
```

수정 포인트:

- 새 CLI 옵션은 `_parse_args()`에 추가하고, `main()`에서 `write_postman_collection()`로 넘깁니다.
- 새 옵션이 collection 구조에 영향을 주면 `PostmanConfig` 또는 `build_postman_collection()`까지 같이 변경합니다.

## LLM에게 수정 요청할 때 권장 범위

파일 전체를 한 번에 수정 요청하지 말고 아래처럼 범위를 좁히는 것이 좋습니다.

- "Postman config 로딩 부분만 수정해줘"
- "Params 탭 생성 규칙만 수정해줘"
- "OAuth token 저장 test script만 수정해줘"
- "request description markdown만 수정해줘"
- "WebSocket skip 정책만 수정해줘"
- "folder 구조를 environment/category/sub_category에서 category/environment/sub_category로 바꿔줘"

## 금지된 방향

`generator`는 다음 방향을 피해야 합니다.

- 레거시 생성기 모듈 import
- 레거시 Postman generator wrapper 호출
- 중간 `api_list.csv`, `kiwoom_api_spec.json`을 필수 입력으로 되돌리기
- 파일 끝에 임시 patch/appending 코드 추가
- request builder를 작은 adapter 함수들로 불필요하게 감싸기
