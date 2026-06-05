# Kiwoom OpenAPI 프로젝트

키움증권 OpenAPI 연동 샘플코드, 런타임 패키지, Postman Collection, 생성기를 포함한 납품용 프로젝트입니다.

---

## 1-depth 구성

아래 목록은 프로젝트 루트의 1-depth 폴더와 파일을 트리 표시 순서대로 정리한 것입니다.
폴더를 먼저 표시하고, 파일은 그 아래에 표시합니다.
`.git/`처럼 Git 내부 메타데이터에 해당하는 항목은 제외했습니다.

```text
Kiwoom-Github-Active-Project/
├── .venv/
├── convention/
├── examples/
├── examples_prove/
├── kiwoom/
├── postman/
├── generator/
├── .env.example
├── .gitignore
├── EXAMPLES_GUIDE.md
├── GENERATOR_GUIDE.md
├── pyproject.toml
├── README.md
├── smoke_check.py
└── uv.lock
```

### `.venv/`

`uv sync` 또는 `uv run` 실행 과정에서 생성되는 Python 가상환경 폴더입니다.
원본 납품 파일로 직접 관리하는 대상은 아니며, 실행 환경에서 필요 시 생성됩니다.

### `convention/`

`examples/` 샘플코드의 폴더 구조, 파일명, 함수 구조, 주석 규칙을 설명하는 컨벤션 문서를 둡니다.

### `examples/`

키움 OpenAPI를 바로 실행해볼 수 있는 Python 샘플코드 폴더입니다.
각 파일은 하나의 API 또는 사용 패턴을 독립적으로 실행하는 단위입니다.

### `examples_prove/`

주요 샘플코드 실행 결과를 증적으로 보관하는 폴더입니다.
콘솔 출력이나 실행 화면 캡처 등 검증용 자료를 둡니다.

### `kiwoom/`

샘플코드가 공통으로 사용하는 런타임 패키지입니다.
인증, 토큰 관리, REST client, WebSocket client, 응답 타입, 실시간 decoder 등을 포함합니다.

### `postman/`

Postman에서 import해 사용할 수 있는 Kiwoom OpenAPI Collection을 둡니다.

### `generator/`

원천 API workbook으로부터 `examples/`와 `postman/` 산출물을 만드는 생성기와 설정 파일을 둡니다.

### `.env.example`

샘플코드 실행에 필요한 환경변수 예시 파일입니다.
실행 시에는 이 파일을 복사해 `.env`를 만들고 실제 API 키와 실행 모드를 입력합니다.

### `.gitignore`

Git에 포함하지 않을 파일과 폴더를 정의합니다.
가상환경, 캐시, `.env`, 생성 중간 산출물 등을 제외합니다.

### `EXAMPLES_GUIDE.md`

`examples/` 샘플코드를 실행하는 방법을 설명하는 문서입니다.
Python, uv, 환경변수, OAuth 예제, 조회 예제, 주문 예제 주의사항을 포함합니다.

### `GENERATOR_GUIDE.md`

`generator/` 생성기를 실행하는 방법을 설명하는 문서입니다.
원천 workbook을 입력으로 examples와 Postman Collection을 생성하는 절차를 다룹니다.

### `pyproject.toml`

프로젝트 메타데이터와 Python 의존성을 정의합니다.
`uv sync`, `uv run`은 이 파일을 기준으로 실행 환경을 구성합니다.

### `README.md`

프로젝트 최상위 안내 문서입니다.
루트 구성과 각 파일/폴더의 목적을 설명합니다.

### `smoke_check.py`

납품 전 기본 상태를 확인하는 smoke check 스크립트입니다.
실제 API 호출 없이 컴파일, 주요 import, 생성기 CLI, `.env.example` 키를 확인합니다.

### `uv.lock`

`uv sync`가 사용하는 의존성 잠금 파일입니다.
동일한 의존성 조합으로 실행 환경을 재현하기 위해 사용하며, 일반 사용자가 직접 수정할 필요는 없습니다.
