# Examples 코드 컨벤션

이 문서는 납품되는 `examples/` 샘플코드의 폴더 구조, 파일명, 주석, 함수, 실행 블록 규칙을 정리한다.
샘플코드는 사용자가 그대로 실행해 API 동작을 확인하고, LLM이 읽고 상황에 맞게 변형할 수 있는 기준 코드이다.

생성기 내부 구현 방식은 이 문서의 범위가 아니다. 이 문서는 최종 산출물인 예제 파일이 어떤 형태를 가져야 하는지만 정의한다.

---

## 1. 기본 원칙

- 예제 파일은 하나의 API 또는 하나의 사용 패턴을 독립적으로 보여주는 실행 단위이다.
- 파일을 읽는 사람이 별도 문서 없이도 API ID, API명, 요청 파라미터, 반환 형태, 실행 예시를 파악할 수 있어야 한다.
- 주석과 docstring은 샘플코드의 핵심 설명이다. 임의로 축약하거나 제거하지 않는다.
- REST, OAuth, WebSocket 템플릿은 같은 문서 구조를 따르되, 실행 방식이 다른 부분은 템플릿별 규칙으로 구분한다.

---

## 2. 폴더 구조

`examples/` 아래는 API 대분류와 소분류를 기준으로 정리한다.

```text
examples/
├── {category}/
│   ├── {sub_category}/
│   │   ├── {function_name}.py
│   │   ├── ...
```

- 1단계 폴더는 API 대분류이다. 예: `국내주식`, `OAuth 인증`
- 2단계 폴더는 API 소분류이다. 예: `종목정보`, `계좌`, `접근토큰발급`, `실시간시세`
- 파일명은 대표 public 함수명과 동일한 snake_case 이름을 사용한다.
- 폴더명은 API 문서의 한글 분류를 보존하되, 파일시스템에서 사용할 수 없는 문자는 안전한 문자로 치환한다.

---

## 3. 파일명과 함수명

파일명은 `{function_name}.py` 형식이다. 파일 안에는 파일명과 같은 대표 public 함수를 둔다.

함수명은 API의 목적이 드러나야 하며, 다음 접두어를 우선 사용한다.

- `get_`: 단건 조회, 상세 조회, 일반 조회
- `list_`: 목록 조회
- `check_`: 확인, 검증
- `create_`: 생성, 발급
- `delete_`: 삭제, 폐기
- `buy_`, `sell_`, `modify_`, `cancel_`: 주문 계열 동작
- `request_`: 조건검색 등 요청 성격이 강한 WebSocket 호출
- `subscribe_`: 실시간 WebSocket 구독

WebSocket 실시간 예제는 사용 패턴에 따라 suffix를 붙일 수 있다.

- `_async`: 실시간 메시지를 직접 수신해 DataFrame 또는 JSON 형태로 반환하는 예제
- `_pubsub`: 수신 메시지를 in-process Pub/Sub 구조로 분배하는 예제

suffix는 `template` 값과 무관하다. `_async`와 `_pubsub`는 모두 `template: websocket_realtime`을 사용하며, suffix는 같은 실시간 템플릿의 사용 패턴 차이만 나타낸다.

조건검색 실시간(CNSRREQ 실시간)은 도메인 용어 보존을 위해 `request_` 접두어를 유지하되, 실제로는 `websocket_realtime` 템플릿과 `_async`/`_pubsub` 변형을 가진다. 즉 `request_` 접두어가 항상 단건 요청을 의미하지는 않는다.

---

## 4. 파일 내부 순서

예제 파일은 위에서 아래로 다음 순서를 따른다.

1. 프론트매터
2. import
3. 템플릿 설명 주석
4. 모듈 수준 상수
5. 표시용 helper 또는 WebSocket helper
6. 대표 public 함수
7. `main()` 또는 `if __name__ == "__main__"` 실행 블록

템플릿에 따라 일부 섹션은 생략될 수 있다. 예를 들어 OAuth는 페이지네이션 상수를 사용하지 않고, WebSocket Pub/Sub 예제는 여러 helper 함수와 class를 포함할 수 있다.

---

## 5. 프론트매터

모든 예제 파일은 파일 상단에 YAML 스타일 주석 블록을 둔다.
단, 수동 생성 마커가 있는 경우 마커 주석이 프론트매터 위에 올 수 있다. (이 절 하단 "수동 생성 마커" 참고)

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

프론트매터 필드는 다음 의미를 가진다.

- `api_id`: API 고유 식별자
- `api_name`: API 한글명
- `category`: 1단계 폴더와 대응되는 대분류
- `sub_category`: 2단계 폴더와 대응되는 소분류
- `template`: 예제 템플릿 유형
- `api_url`: API endpoint path
- `menu_path`: 사용자가 API 문서에서 확인할 수 있는 메뉴 경로

`template` 값은 다음 중 하나를 사용한다.

- `rest`
- `oauth`
- `websocket_request_once`
- `websocket_realtime`

`_async`/`_pubsub` suffix는 별도 template 값을 두지 않으며, 자세한 내용은 3절을 참고한다.

### 수동 생성 마커

자동 생성으로 다루기 어려워 수동 검수가 필요한 API는 프론트매터 바로 위에 마커 주석을 둔다.
예를 들어 조건검색 요청(CNSRREQ)은 같은 WebSocket 연결에서 CNSRLST를 선행 호출해야 안정적으로 응답하므로 수동 생성 대상이다.

```python
# 수동 생성 필요: CNSRREQ는 같은 WebSocket 연결에서 CNSRLST 선행 호출 후 요청해야 안정적으로 응답합니다.
# generator marker: MANUAL_REQUIRED_API_IDS
# ---
# api_id: ka10172
# ...
# ---
```

- 첫 줄은 수동 생성이 필요한 이유를 사람이 읽을 수 있게 적는다.
- 둘째 줄 `# generator marker: MANUAL_REQUIRED_API_IDS`는 생성기가 인식하는 고정 마커이다.
- 마커 주석은 항상 프론트매터 위에 두며, 임의로 제거하지 않는다.

---

## 6. Import 규칙

import는 표준 라이브러리, 서드파티, 프로젝트 패키지 순서로 배치한다.

REST 예제는 다음 구조를 따른다.

```python
import logging
import time

import pandas as pd

from kiwoom import get_client
```

OAuth 예제는 다음 구조를 따른다.

```python
import logging
from typing import Any, Literal

import pandas as pd

from kiwoom import get_auth
```

WebSocket 단건 요청 또는 실시간 수신 예제는 다음 구조를 따른다.

```python
import asyncio
import logging
from typing import Any, Literal

import pandas as pd

from kiwoom import get_ws_client
```

실시간 FID 값을 decode하는 예제는 다음 import를 추가할 수 있다.

```python
from kiwoom.realtime.decoders import decode_values
```

Pub/Sub 예제는 `pandas` 없이 메시지 분배 구조만 보여줄 수 있으며, 이 경우 `collections.defaultdict`와 `asyncio.Queue` 기반 helper를 포함할 수 있다.

---

## 7. 모듈 수준 상수

상수는 API 식별 정보, 요청 제어 값, 응답 매핑 값 순서로 둔다.

REST 예제의 기본 상수 구조는 다음과 같다.

```python
API_ID = "ka10001"
API_URL = "/api/dostk/stkinfo"
MAX_PAGES = 10 # 최대 조회 페이지 수
REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {
    "return_code": "응답코드",
    "return_msg": "응답메시지"
}
TABLE_KEYS = {}
COLUMNS = {
    "stk_cd": "종목코드",
    "stk_nm": "종목명"
}
```

OAuth 예제는 `API_URL` 대신 `API_PATH`를 사용한다.

```python
API_ID = "au10001"
API_PATH = "/oauth2/token"
COLUMNS = {
    "expires_dt": "만료일",
    "token_type": "토큰타입",
    "token": "접근토큰"
}
```

WebSocket 예제는 `API_URL`을 사용한다.

```python
API_ID = "0B"
API_URL = "/api/dostk/websocket"
```

응답에 테이블 데이터가 있으면 `TABLE_KEYS`를 둔다.

```python
TABLE_KEYS = {
    "data": "검색결과데이터"
}
```

응답에 요약 데이터가 있으면 `SUMMARY_KEY`, `SUMMARY_COLUMNS`를 둔다.

```python
SUMMARY_KEY = "요약"
SUMMARY_COLUMNS = {
    "flu_rt": "등락률"
}
```

숫자 표시 포맷 대상 컬럼은 `NUMERIC_COLUMNS`에 한글 컬럼명 기준으로 둔다.

```python
NUMERIC_COLUMNS = (
    '누적거래량',
    '현재가',
)
```

---

## 8. 표시용 Helper

REST, OAuth, WebSocket 단건 요청 예제처럼 DataFrame을 사람이 읽기 좋게 출력하는 예제는 `_format_display()`와 `_format_display_value()`를 함께 둔다.

```python
def _format_display(df: pd.DataFrame) -> pd.DataFrame:
    ...


def _format_display_value(value: object) -> object:
    ...
```

- `_format_display()`는 원본 DataFrame을 직접 바꾸지 않고 복사본을 만든다.
- `NUMERIC_COLUMNS`에 포함된 컬럼만 표시용 천 단위 콤마 포맷을 적용한다.
- 코드 실행 결과를 사람이 읽기 쉽게 보여주기 위한 helper이며, API 응답 의미를 바꾸지 않는다.

WebSocket 실시간 수신 예제는 표시 포맷보다 수신 구조가 중요하므로 `_format_display()`만 두거나(단순 복사) 생략할 수 있으며, 이 경우 `_format_display_value()`는 두지 않는다. Pub/Sub 예제처럼 DataFrame을 만들지 않는 파일은 표시용 helper를 모두 생략할 수 있다.

---

## 9. Public 함수와 Docstring

예제 파일에는 파일명을 대표하는 public 함수를 둔다.
대표 함수는 API 사용자가 import해서 직접 호출할 수 있는 함수여야 한다.

REST 예제의 대표 함수 형태는 다음과 같다.

```python
def get_domestic_stock_info(
    stk_cd: str,
) -> pd.DataFrame:
    """
    주식기본정보요청[ka10001] API를 호출합니다.

    공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.

    Args:
        stk_cd: 종목코드

    Returns:
        API 응답 데이터입니다.

    Example:
        >>> df = get_domestic_stock_info(
        ...     stk_cd='005930',
        ... )
        >>> print(df)
    """
```

Docstring은 다음 구성을 유지한다.

- 첫 문장: `{api_name}[{api_id}] API를 호출합니다.`
- 인증 설명: 공통 클라이언트 또는 공통 인증 객체가 토큰을 처리한다는 설명
- `Args`: 파라미터별 의미
- `Returns`: 반환 데이터 설명
- `Example`: doctest 스타일 호출 예시

WebSocket 실시간 예제는 첫 문장을 다음처럼 쓸 수 있다.

```python
"""
주식체결[0B] 실시간 데이터를 수신합니다.
...
"""
```

Pub/Sub 예제는 분배 구조를 보여주는 목적을 docstring에 명시한다.

```python
"""
주식체결[0B] 실시간 데이터를 Pub/Sub로 분배합니다.
...
"""
```

---

## 10. REST 템플릿

REST 예제는 `get_client()`를 통해 공통 REST client를 가져오고, `client.fetch_page()`로 API를 호출한다.

함수 내부 흐름은 번호 주석으로 구분한다.

```python
# 1. 필수 파라미터 검증
# 2. 요청 파라미터 바디
# 3. 인증 클라이언트
# 4. 응답 데이터 저장소
# 5. API 호출 및 연속조회
# 6. DataFrame 변환
```

REST 예제는 연속조회가 가능한 API를 고려해 `MAX_PAGES`, `REQUEST_DELAY_SECONDS`, `next_cont_yn`, `next_key`를 사용한다.

응답 구조에 따라 반환 형태가 달라진다.

- 플랫 응답: `pd.DataFrame`
- 테이블 응답: `dict[str, pd.DataFrame]`
- 테이블 + 요약 응답: `dict[str, pd.DataFrame]`

응답 메시지가 포함되면 `MESSAGE_KEY`를 key로 하는 메시지 DataFrame을 결과 dict 앞쪽에 포함할 수 있다.

---

## 11. OAuth 템플릿

OAuth 예제는 `get_auth()`를 통해 토큰 발급 또는 폐기 흐름을 보여준다.

OAuth 예제의 특징은 다음과 같다.

- `template`은 `oauth`이다.
- `API_URL` 대신 `API_PATH`를 사용한다.
- `MAX_PAGES`, `REQUEST_DELAY_SECONDS`, `MESSAGE_KEY`, `TABLE_KEYS`는 사용하지 않는다.
- 대표 함수는 `output`, `mode` 파라미터를 가진다.
- `output == "json"`이면 원본 응답 dict를 반환할 수 있다.
- 기본 출력은 DataFrame 형태이다.

대표 함수 형태는 다음과 같다.

```python
def create_access_token(
    output: Literal["dataframe", "json"] = "dataframe",
    mode: Literal["real", "demo"] | None = None,
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    ...
```

`mode`를 생략하면 현재 설정된 auth profile을 사용한다.

---

## 12. WebSocket 단건 요청 템플릿

WebSocket 단건 요청 예제는 `template: websocket_request_once`를 사용한다.
조건검색 요청처럼 WebSocket endpoint를 사용하지만 요청-응답 형태로 한 번 호출하는 예제에 적용한다.

기본 규칙은 다음과 같다.

- `async def` 대표 함수를 사용한다.
- 단순 단건 요청은 `get_ws_client().request_once(api_url=API_URL, body=body)`로 요청한다. (예: `list_domestic_condition_searches`)
- `output: Literal["dataframe", "json"] = "dataframe"` 파라미터를 둔다.
- `output == "json"`이면 원본 응답 dict를 반환한다.
- DataFrame 출력이 필요한 경우 REST 예제와 동일하게 `TABLE_KEYS`, `COLUMNS`, `SUMMARY_COLUMNS`, `_format_display()`를 사용할 수 있다.

선행 호출이 필요한 API는 `request_once()` 대신 같은 연결을 유지하는 패턴을 사용한다.

- 예: 조건검색 요청(CNSRREQ)은 같은 연결에서 CNSRLST를 먼저 호출해야 한다.
- `await client.connect(api_url=API_URL)`로 연결을 연 뒤, 송수신을 묶은 `_send_and_receive()` helper로 CNSRLST → CNSRREQ를 순차 호출한다.
- 이 경우 `request_once()`를 사용하지 않으며, 이런 파일은 수동 생성 마커를 둔다. (5절 참고)

실행 블록은 `asyncio.run(main())`을 사용한다.

```python
async def main() -> None:
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    result = await request_domestic_condition_search(
        ...
    )
    # 결과 출력
    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):
        print(k, _format_display(v).head() if isinstance(v, pd.DataFrame) else v)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 13. WebSocket 실시간 수신 템플릿

WebSocket 실시간 수신 예제는 `template: websocket_realtime`을 사용한다.
실시간 등록 패킷을 만들고, WebSocket 메시지를 반복 수신하는 예제에 적용한다.

기본 규칙은 다음과 같다.

- `async def` 대표 함수를 사용한다.
- `get_ws_client()`로 WebSocket client를 가져온다.
- `client.subscribe(api_url=API_URL, body=body)`로 구독한다.
- `async for message in client.iter_messages()`로 메시지를 수신한다.
- `max_messages`로 수집할 실시간 데이터 개수를 제한한다.
- `output`은 `"dataframe"` 또는 `"json"`을 지원한다.
- `finally`에서 `await client.close()`로 연결을 닫는다.

실시간 등록 패킷이 필요한 예제는 `build_realtime_reg_packet()` helper를 둘 수 있다.

```python
def build_realtime_reg_packet(
    *,
    items: list[str],
    types: list[str],
    group_no: str = "1",
    refresh: str = "1",
) -> dict[str, Any]:
    """키움 실시간 항목 등록(REG) 패킷을 생성합니다."""
    ...
```

실시간 수신 결과는 일반 데이터와 시스템 메시지를 구분한다.

- 실시간 데이터: `data`
- 등록/시스템/오류 메시지: `system`

FID 기반 실시간 데이터는 `decode_values()`를 사용해 사람이 읽을 수 있는 key로 변환할 수 있다.

조건검색 실시간(CNSRREQ 실시간)처럼 초기 조회 데이터와 실시간 데이터가 분리되어 도착하는 예제는 결과 key를 더 세분화한다.

- 조건검색식 목록, 조회데이터, 실시간데이터, 시스템메시지, 요약처럼 단계별로 key를 나눈다.
- 같은 연결에서 CNSRLST를 먼저 호출한 뒤 CNSRREQ로 실시간 등록을 한다.
- 종료 시 CNSRCLR로 실시간 등록을 해제하고 연결을 닫는다.
- 이런 파일도 수동 생성 마커를 둔다. (5절 참고)

---

## 14. WebSocket Pub/Sub 변형

Pub/Sub 예제는 WebSocket 수신 메시지를 여러 소비자에게 분배하는 구조를 보여준다.
실전 인프라가 아니라 샘플코드 안에서 이해 가능한 in-process 구조를 사용한다.

Pub/Sub는 별도 frontmatter `template` 값이 아니라 `websocket_realtime`의 한 변형이며, 대표 함수명에 `_pubsub` suffix를 붙여 구분한다.

기본 규칙은 다음과 같다.

- `AsyncPubSub` class를 둘 수 있다.
- `asyncio.Queue`로 subscriber queue를 만든다.
- `resolve_topic()`으로 메시지 topic을 결정한다.
- publisher는 WebSocket 메시지를 topic별 queue로 publish한다.
- 예시 subscriber는 전략 로직과 로그/저장 로직처럼 역할을 나눠 보여준다.
- 대표 함수명은 `_pubsub` suffix를 사용한다.

topic은 `kiwoom.` 네임스페이스로 구분한다.

| topic | 용도 |
| --- | --- |
| `kiwoom.realtime.{type}` | 실시간(REAL) 데이터, 실시간 타입별 분기 |
| `kiwoom.realtime` | 타입을 판별할 수 없는 실시간 데이터 |
| `kiwoom.system.reg` | 등록(REG) 응답 |
| `kiwoom.system` | 시스템(SYSTEM) 메시지 |
| `kiwoom.system.{trnm}` | 기타 trnm 시스템 메시지 (trnm은 소문자로 정규화) |
| `kiwoom.raw` | dict가 아닌 원본 메시지 등 분류 불가 메시지 |
| `kiwoom.all` | 모든 메시지를 받는 통합 topic |

Pub/Sub 예제의 대표 함수는 반환값보다 실행 구조 설명이 중요하므로 `-> None`을 사용할 수 있다.

```python
async def subscribe_domestic_stock_trade_pubsub(
    items: list[str],
    types: list[str] | None = None,
    group_no: str = "1",
    refresh: str = "1",
    max_messages: int | None = None,
) -> None:
    ...
```

Pub/Sub 예제의 `main()`은 메시지 분배 실행에 집중하므로 DataFrame 출력 옵션을 생략할 수 있다.

---

## 15. `__main__` 실행 블록

모든 예제는 파일을 직접 실행할 수 있어야 한다.

동기 REST/OAuth 예제는 다음 순서를 따른다.

```python
if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    # 출력 옵션 설정
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)

    # API 호출
    result = get_domestic_stock_info(
        ...
    )
    # 결과 출력
    print(_format_display(result))
```

결과가 dict이면 key별로 출력한다.

```python
for key, df in result.items():
    print(f"\n[{key}]")
    print(_format_display(df))
```

비동기 WebSocket 예제는 `main()`을 정의하고 `asyncio.run(main())`으로 실행한다.

```python
async def main() -> None:
    ...


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 16. 응답 구조별 반환 규칙

상수 정의는 7절을 따르고, 이 절은 응답 구조에 따른 반환 형태만 정리한다.

- 플랫 응답(`TABLE_KEYS = {}`): 하나의 `pd.DataFrame`으로 반환한다.
- 테이블 응답: table key별 `pd.DataFrame` dict로 반환한다.
- 테이블 + 요약 응답: `SUMMARY_KEY`를 가장 앞에 두고, 그 뒤에 테이블 DataFrame을 둔다.
- REST 응답 메시지가 존재하면 `MESSAGE_KEY`가 결과 dict의 가장 앞에 올 수 있다.

WebSocket 실시간 수신 예제는 시스템 메시지와 실시간 데이터를 구분해 반환할 수 있다.

```python
{
    "system": pd.DataFrame(system_rows),
    "data": pd.DataFrame(rows),
}
```

`output == "json"`인 템플릿은 DataFrame 변환 전 원본 dict 또는 list를 반환할 수 있다.

---

## 17. 주석 유지 규칙

샘플코드의 주석은 사용자가 코드를 변형할 때 기준이 되는 설명이다.

- 프론트매터는 제거하지 않는다.
- 수동 생성 마커(`# generator marker: MANUAL_REQUIRED_API_IDS`)는 제거하지 않는다.
- 인증, 출력, API 호출, 결과 출력 주석은 유지한다.
- REST 함수 내부의 번호 주석은 유지한다.
- WebSocket 자동 처리 설명 주석은 유지한다.
- Pub/Sub 예제의 구조 설명 docstring은 유지한다.

주석을 줄이는 방식으로 코드를 간결화하지 않는다. 코드가 길어지더라도 사용자가 읽고 수정할 수 있는 설명을 우선한다.
