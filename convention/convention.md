# Examples 코드 컨벤션

REST API 예제 파일의 폴더 구조, 파일명, 파이썬 내부 구조에 대한 규칙을 정리한다.

---

## 1. 폴더 구조

```
examples/
├── {category}/
│   ├── {sub_category}/
│   │   ├── {function_name}.py
│   │   ├── ...
```

- 1단계: **category** — API 대분류 (예: `국내주식`, `OAuth 인증`)
- 2단계: **sub_category** — API 소분류 (예: `종목정보`, `계좌`, `접근토큰발급`, `접근토큰폐기`)
- 3단계: 파이썬 파일

카테고리 및 서브카테고리는 한글 폴더명을 사용한다.

---

## 2. 파일명

- **`{function_name}.py`** — 파일 내부의 public 함수명과 동일한 snake_case 이름을 사용한다.
- 함수명 접두어 규칙:
  | 접두어 | 의미 | 예시 |
  |--------|------|------|
  | `get_` | 단건/목록 조회 | `get_domestic_stock_info.py` |
  | `list_` | 리스트 조회 | `list_domestic_stocks.py` |
  | `check_` | 확인/검증 | `check_domestic_credit_loanable.py` |
  | `create_` | 생성/발급 | `create_access_token.py` |
  | `delete_` | 삭제/폐기 | `delete_access_token.py` |

---

## 3. 파이썬 파일 내부 구조

파일은 위에서 아래로 다음 순서를 따른다.

### 3.1 프론트매터 (메타데이터 주석)

파일 최상단에 YAML 스타일 주석 블록을 배치한다.

```python
# ---
# api_id: ka10001
# api_name: 주식기본정보요청
# category: 국내주식
# sub_category: 종목정보
# template: rest
# api_url: /api/dostk/stkinfo
# menu_path: 국내주식 > 종목정보 > 주식기본정보요청(ka10001)
# ---
```

| 필드 | 설명 |
|------|------|
| `api_id` | API 고유 식별자 (소문자 2자리 + 숫자) |
| `api_name` | API 한글명 |
| `category` | 대분류 (폴더 1단계와 일치) |
| `sub_category` | 소분류 (폴더 2단계와 일치) |
| `template` | 템플릿 유형 (`rest` 또는 `oauth`) |
| `api_url` | API 엔드포인트 경로 |
| `menu_path` | 메뉴 경로 (카테고리 > 서브카테고리 > API명(api_id)) |

### 3.2 임포트

```python
import logging
import time

import pandas as pd

from kiwoom import get_client    # rest 템플릿
from kiwoom import get_auth      # oauth 템플릿
```

- 표준 라이브러리 → 서드파티 → 프로젝트 순서 (isort 기본 규칙)
- `rest` 템플릿은 `get_client`, `oauth` 템플릿은 `get_auth`를 사용한다.

### 3.3 모듈 수준 상수

선언 순서를 아래와 같이 유지한다.

```python
API_ID = "ka10001"
API_URL = "/api/dostk/stkinfo"          # rest 템플릿
# API_PATH = "/oauth2/token"            # oauth 템플릿
MAX_PAGES = 10
REQUEST_DELAY_SECONDS = 0.2
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = { ... }               # API 필드 → 한글명 매핑
TABLE_KEYS = { ... }                    # 테이블 키 → 한글명 매핑 (없으면 빈 dict)
COLUMNS = { ... }                       # 응답 필드 → 한글명 매핑
# SUMMARY_KEY = "요약"                  # 요약 데이터가 있는 경우
# SUMMARY_COLUMNS = { ... }            # 요약 필드 → 한글명 매핑
NUMERIC_COLUMNS = ( ... )               # 숫자 포맷팅 대상 한글 컬럼명 (tuple, 정렬)
```

- `COLUMNS`, `MESSAGE_COLUMNS` 등의 dict는 `{"api_field": "한글명"}` 형태이다.
- `NUMERIC_COLUMNS`는 한글 컬럼명 기준, 알파벳/가나다 오름차순 정렬된 tuple이다.

### 3.4 Private 헬퍼 함수

```python
def _format_display(df: pd.DataFrame) -> pd.DataFrame: ...
def _format_display_value(value: object) -> object: ...
```

- `_format_display` — DataFrame의 `NUMERIC_COLUMNS` 대상 컬럼에 천 단위 쉼표 포맷을 적용한다.
- `_format_display_value` — 개별 값에 대한 포맷팅 로직이다.
- 두 함수는 모든 예제에 동일한 구현으로 포함된다.

### 3.5 Public API 함수

파일명과 동일한 이름의 함수를 정의한다. 파일 내 유일한 public 함수이다.

#### 시그니처

```python
def get_domestic_stock_info(
    stk_cd: str,
) -> pd.DataFrame:
```

- 파라미터는 각각 별도 줄에 작성하고, 닫는 괄호도 별도 줄에 둔다.
- 타입 힌트를 반드시 명시한다.

#### 반환 타입

응답 구조에 따라 두 가지로 나뉜다.

| 응답 구조 | 반환 타입 | 조건 |
|-----------|----------|------|
| 플랫 응답 (테이블 없음) | `pd.DataFrame` | `TABLE_KEYS = {}` |
| 테이블/요약 응답 | `dict[str, pd.DataFrame]` | `TABLE_KEYS`에 키가 있거나 `SUMMARY_KEY` 존재 |

#### Docstring

```python
"""
{api_name}[{api_id}] API를 호출합니다.

공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

Args:
    {param}: {설명}

Returns:
    API 응답 데이터입니다.

Example:
    >>> df = get_domestic_stock_info(
    ...     stk_cd='005930',
    ... )
    >>> print(df)
"""
```

- 첫 줄: `{api_name}[{api_id}] API를 호출합니다.`
- Args: 파라미터별 설명
- Example: 실제 호출 예시 (doctest 형식)

#### 함수 내부 흐름 (rest 템플릿)

번호 주석으로 단계를 구분한다.

```python
# 1. 필수 파라미터 검증
# 2. 요청 파라미터 바디
# 3. 인증 클라이언트
# 4. 응답 데이터 저장소
# 5. API 호출 및 연속조회
# 6. DataFrame 변환
```

### 3.6 `__main__` 블록

```python
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    df = get_domestic_stock_info(
        stk_cd='005930',
    )
    # 결과 출력
    print(_format_display(df))
```

- 로깅, pandas 출력 옵션 설정 → API 호출 → 결과 출력 순서이다.
- 반환 타입이 `dict[str, pd.DataFrame]`인 경우 `for key, df in result.items()` 로 순회하며 출력한다.

---

## 4. 응답 구조별 변형

### Type A — 플랫 응답 (테이블/요약 없음)

```python
TABLE_KEYS = {}
# SUMMARY_KEY, SUMMARY_COLUMNS 없음
```
- 응답 body의 최상위 필드를 직접 단일 row로 수집한다.
- 반환: `pd.DataFrame`

### Type B — 테이블 응답 (요약 없음)

```python
TABLE_KEYS = {
    "daly_trde_dtl": "일별거래상세"
}
# SUMMARY_KEY, SUMMARY_COLUMNS 없음
```
- 응답 body의 list 필드를 테이블로 수집한다.
- 반환: `dict[str, pd.DataFrame]`

### Type C — 테이블 + 요약 응답

```python
TABLE_KEYS = {
    "acnt_evlt_remn_indv_tot": "계좌평가잔고개별합산"
}
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = { ... }
```
- 요약 데이터(body 최상위 필드) + 테이블 데이터(body 내 list 필드)를 함께 수집한다.
- 반환: `dict[str, pd.DataFrame]` (요약이 첫 번째 키)

### Type D — OAuth 템플릿

```python
# template: oauth
from kiwoom import get_auth
API_PATH = "/oauth2/token"    # API_URL 대신 API_PATH 사용
```
- 페이지네이션 루프가 없다.
- `get_auth()`를 통해 인증 처리한다.
- 내부 로직이 REST 템플릿과 다르다.
