# generate_examples.py 구조 설명

`generate_examples.py`는 키움 REST API 원천 `xlsx` 파일을 입력받아 실행 가능한 Python 예제 파일을 직접 생성하는 단일 실행파일입니다. 기존 `utils` 패키지를 import하지 않으며, `api_list.csv`나 `kiwoom_api_spec.json` 같은 중간 산출물을 필수 입력으로 사용하지 않습니다.

## 실행 흐름

```text
xlsx
  -> parse_workbook()
  -> build_api_specs()
  -> load_mapping() / apply_function_name_overrides()
  -> validate_mapping()
  -> generate_examples()
  -> render_*_example()
  -> Examples/**/*.py
```

CLI 진입점은 파일 하단의 `_parse_args()`와 `main()`입니다.

## 큰 섹션

### 1. 상수와 데이터 모델

파일 상단에는 경로, 템플릿 종류, CSV 컬럼명, 응답 공통 필드 같은 상수가 있습니다.

주요 dataclass는 다음 책임을 갖습니다.

- `ApiListRow`: xlsx의 `API 리스트` 시트 한 행
- `ApiSpec`: 예제 생성에 필요한 정규화된 API 스펙
- `FunctionNameMapEntry`: API ID와 생성 함수명, 템플릿 종류 매핑
- `RequestParameter`: 생성 함수의 파라미터 표현
- `ResponseTableSpec`: 응답을 DataFrame으로 바꿀 때 필요한 컬럼 정보
- `GenerationReport`: 생성 결과 리포트

수정 포인트:

- 새 템플릿 종류를 추가하려면 `TEMPLATE_KINDS`, `FunctionNameMapEntry.template_kind`, `_default_template_kind()`, `render_example()`을 함께 봅니다.
- 생성 리포트 필드를 바꾸려면 `GenerationReport`와 `generate_examples()`의 report 작성 부분을 봅니다.

### 2. xlsx 파싱

이 섹션은 원천 workbook을 읽어서 `ApiListRow` 목록과 API 상세 payload dict를 만듭니다.

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
- 상세 API 시트의 `Request`, `Response`, `Request Example`, `Response Example` 위치 규칙이 바뀌면 `_find_sections()`와 `_section_range()`를 수정합니다.
- Request/Response 표 컬럼 규칙이 바뀌면 `_parse_request_response_block()`을 수정합니다.

주의:

- 이 섹션은 파일 출력 정책을 몰라야 합니다.
- 여기서는 `ApiSpec`이 아니라 원천 payload를 만듭니다.

### 3. ApiSpec 정규화

`build_api_specs()`는 xlsx 파싱 결과를 예제 생성용 `ApiSpec` 목록으로 변환합니다.

수정 포인트:

- xlsx meta의 필드명을 `ApiSpec.method`, `ApiSpec.content_type`, `ApiSpec.menu_path` 등에 매핑하는 방식은 여기서 바꿉니다.
- 생성기 전체에서 사용하는 표준 API 스펙 형태를 바꾸려면 `ApiSpec` dataclass와 이 함수를 같이 봅니다.

### 4. 함수명 매핑과 검증

이 섹션은 API ID별 생성 함수명과 템플릿 종류를 결정합니다.

주요 함수:

- `load_mapping()`
- `apply_function_name_overrides()`
- `validate_mapping()`
- `default_mapping_entry()`
- `_default_template_kind()`
- `_default_function_name()`
- `_identifier()`
- `_is_valid_function_name()`

수정 포인트:

- 기본 mapping 파일은 `utils_v2/function_name_map.csv`입니다.
- 최신 함수명은 이 mapping 파일의 `function_name` 컬럼에 반영되어 있습니다.
- `function_name_map.csv` 포맷을 바꾸려면 `MAPPING_COLUMNS`와 `load_mapping()`을 봅니다.
- 임시 함수명 override 옵션을 바꾸려면 `FUNCTION_NAME_OVERRIDE_COLUMNS`와 `apply_function_name_overrides()`를 봅니다.
- REST/OAuth/WebSocket 템플릿 자동 분류 기준은 `_default_template_kind()`에서 바꿉니다.
- Python 함수명 sanitizing 규칙은 `_default_function_name()`과 `_identifier()`에서 바꿉니다.

주의:

- `--mapping`을 생략하면 `utils_v2/function_name_map.csv`를 사용합니다.
- `--function-name-overrides`는 별도 임시 override가 필요할 때만 명시합니다.
- 기본 mapping 파일을 제거하거나 다른 경로를 넘기면 `default_mapping_entry()` 기준 자동 생성/커스텀 mapping으로 동작할 수 있습니다.
- examples 생성 정책만 다루며 Postman 생성기와 공유하지 않습니다.

### 5. 생성 오케스트레이션

`generate_examples()`가 전체 생성 흐름을 조율합니다.

주요 책임:

- workbook 파싱
- `ApiSpec` 변환
- mapping/override 적용
- template kind 필터링
- 출력 디렉터리 생성
- renderer 호출
- report 작성

수정 포인트:

- 생성 파일 경로 규칙은 `generate_examples()`와 `_build_filename_map()`, `_safe_path()`를 봅니다.
- 특정 template kind만 다른 파일명 정책을 쓰려면 `generate_examples()`의 per-spec loop를 봅니다.
- report 내용을 바꾸려면 `GenerationReport`와 `generate_examples()` 하단을 봅니다.

### 6. 템플릿 라우팅

`render_example()`은 `FunctionNameMapEntry.template_kind`에 따라 실제 renderer를 선택합니다.

현재 라우팅:

```text
oauth                  -> render_oauth_example()
websocket_request_once -> render_websocket_request_once()
websocket_realtime     -> render_websocket_realtime_async()
rest                   -> render_rest_example()
```

주의:

- 실시간 WebSocket은 `generate_examples()`에서 `_async`, `_pubsub` 두 파일을 직접 생성합니다.
- `render_example()`은 단일 파일 렌더링 라우터입니다.

### 7. REST 예제 렌더러

`render_rest_example()`는 REST API 예제 파일 전체 문자열을 생성합니다.

주요 생성 내용:

- imports
- API 상수
- DataFrame 표시 helper
- 함수 signature/docstring
- 필수 파라미터 검증
- 요청 body 구성
- `get_client().fetch_page()` 호출
- 연속조회 처리
- 응답 DataFrame 변환
- `if __name__ == "__main__"` 실행 블록

수정 포인트:

- REST 호출 방식은 `render_rest_example()` 내부의 `client.fetch_page()` 블록을 봅니다.
- 연속조회 정책은 `next_cont_yn`, `next_key`, `MAX_PAGES`, `REQUEST_DELAY_SECONDS` 주변을 봅니다.
- REST 응답 DataFrame 형태는 `_response_table_spec()`, `_dataframe_rows_extend()`, `_summary_rows_append()`를 같이 봅니다.

### 8. OAuth 예제 렌더러

`render_oauth_example()`는 OAuth token/revoke 예제를 생성합니다.

수정 포인트:

- `/oauth2/token` 처리 방식은 `auth.refresh_access_token()` 블록을 봅니다.
- `/oauth2/revoke` 처리 방식은 `auth.revoke_access_token()` 블록을 봅니다.
- OAuth 경로가 추가되면 `render_oauth_example()`에 분기를 추가합니다.

### 9. WebSocket 예제 렌더러

WebSocket 관련 renderer는 세 종류입니다.

- `render_websocket_request_once()`
- `render_websocket_realtime_async()`
- `render_websocket_realtime_pubsub()`

관련 helper:

- `_realtime_reg_packet_builder()`
- `_fid_realtime_function()`
- `_realtime_receive_loop()`
- `_realtime_main()`
- `_pubsub_helpers()`
- `_fid_pubsub_function()`
- `_parameter_pubsub_function()`
- `_fid_pubsub_main()`
- `_parameter_pubsub_main()`
- `_example_realtime_items()`
- `_example_realtime_types()`

수정 포인트:

- 단건 WebSocket 요청은 `render_websocket_request_once()`를 봅니다.
- 실시간 수신 루프는 `_realtime_receive_loop()`를 봅니다.
- REG 패킷 생성 규칙은 `_realtime_reg_packet_builder()`를 봅니다.
- Pub/Sub 예제 구조는 `_pubsub_helpers()`를 봅니다.

### 10. 요청/응답 분석 helper

이 섹션은 xlsx 스펙을 Python 함수 파라미터와 DataFrame 변환 정보로 해석합니다.

주요 함수:

- `_request_parameters()`
- `_request_body_example()`
- `_response_table_spec()`
- `_top_level_list_keys()`
- `_scalar_columns()`
- `_table_labels()`
- `_list_child_columns()`
- `_find_example_value()`

수정 포인트:

- 생성 함수의 파라미터 목록이 이상하면 `_request_parameters()`를 봅니다.
- request example JSON이 원하는 기본값으로 반영되지 않으면 `_request_body_example()`와 `_find_example_value()`를 봅니다.
- 응답 DataFrame 컬럼명이 이상하면 `_response_table_spec()` 계열 함수를 봅니다.

### 11. 코드 조각 렌더링 helper

이 섹션은 생성될 `.py` 파일의 반복 코드 조각을 만듭니다.

주요 함수:

- `_module_header()`
- `_signature()`
- `_docstring()`
- `_required_checks()`
- `_body_builder()`
- `_dataframe_conversion()`
- `_table_rows_initializer()`
- `_dataframe_rows_extend()`
- `_main_block()`
- `_display_helpers()`

수정 포인트:

- 생성 파일 상단 front matter는 `_module_header()`를 봅니다.
- 생성 함수 signature는 `_signature()`를 봅니다.
- 생성 docstring은 `_docstring()`을 봅니다.
- `__main__` 실행 예시는 `_main_block()`을 봅니다.
- 숫자 표시 포맷은 `_display_helpers()`와 `_is_numeric_label()`을 봅니다.

### 12. CLI

파일 하단의 `_parse_args()`와 `main()`이 CLI 진입점입니다.

현재 주요 옵션:

```bash
uv run utils_v2/generate_examples.py workbook.xlsx --out Examples
uv run utils_v2/generate_examples.py workbook.xlsx --kind rest --kind oauth
uv run utils_v2/generate_examples.py workbook.xlsx --mapping custom_function_name_map.csv
uv run utils_v2/generate_examples.py workbook.xlsx --function-name-overrides custom_function_name_overrides.csv
```

수정 포인트:

- 새 CLI 옵션은 `_parse_args()`에 추가하고, `main()`에서 `generate_examples()`로 넘깁니다.
- 옵션이 생성 정책에 영향을 주면 `generate_examples()`의 인자도 함께 변경합니다.

## LLM에게 수정 요청할 때 권장 범위

파일 전체를 한 번에 수정 요청하지 말고 아래처럼 범위를 좁히는 것이 좋습니다.

- "xlsx 파싱 중 Request/Response 표 해석만 수정해줘"
- "REST 예제의 연속조회 처리만 수정해줘"
- "WebSocket realtime receive loop만 수정해줘"
- "생성 함수명 sanitizing 규칙만 수정해줘"
- "DataFrame 컬럼 생성 규칙만 수정해줘"
- "CLI 옵션 하나 추가하고 generate_examples()에 연결해줘"

## 금지된 방향

`utils_v2`는 다음 방향을 피해야 합니다.

- 기존 `utils` 모듈 import
- 기존 generator wrapper 호출
- 중간 `api_list.csv`, `kiwoom_api_spec.json`을 필수 입력으로 되돌리기
- 파일 끝에 임시 patch/appending 코드 추가
- 사용처가 하나뿐인 adapter layer 추가
