# Examples 실행 가이드

이 문서는 `examples/` 폴더의 샘플코드를 실행하는 방법을 설명합니다.
샘플코드는 `kiwoom/` 런타임 패키지를 사용해 실제 키움 OpenAPI를 호출합니다.

운영체제별 shell 명령이 다르므로 각 섹션은 `macOS/Linux`와 `Windows PowerShell`을 구분해 작성합니다.

---

## 1. Python 설치 확인

이 프로젝트는 Python 3.13 이상을 기준으로 실행합니다.
먼저 로컬 환경에 Python이 설치되어 있는지 확인합니다.

### macOS/Linux

```bash
python3 --version
```

버전이 출력되면 설치되어 있는 상태입니다.

```text
Python x.x.x
```

Python이 없거나 버전이 낮다면 Python 3.13 이상을 설치합니다.

macOS에서 Homebrew를 사용하는 경우:

```bash
brew install python@3.13
```

Linux에서는 사용 중인 배포판의 패키지 관리자 또는 Python 공식 배포판을 사용해 Python 3.13 이상을 설치합니다.

- https://www.python.org/downloads/

### Windows PowerShell

```powershell
py --version
```

버전이 출력되면 설치되어 있는 상태입니다.

```text
Python x.x.x
```

Python이 없거나 버전이 낮다면 Python 3.13 이상을 설치합니다.

winget을 사용할 수 있는 경우:

```powershell
winget install Python.Python.3.13
```

또는 Python 공식 다운로드 페이지에서 Windows installer를 설치합니다.

- https://www.python.org/downloads/windows/

---

## 2. uv 설치 확인

이 프로젝트의 표준 실행 방식은 `uv run`입니다.
로컬 환경에 `uv`가 설치되어 있는지 확인합니다.

```bash
uv --version
```

버전이 출력되면 설치되어 있는 상태입니다.

```text
uv x.x.x
```

명령을 찾을 수 없다면 OS에 맞게 설치합니다.

### macOS

Homebrew를 사용하는 경우:

```bash
brew install uv
```

Homebrew를 사용하지 않는 경우 공식 설치 스크립트를 사용할 수 있습니다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Linux

공식 설치 스크립트를 사용합니다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 후 새 shell을 열거나 shell 설정을 다시 로드합니다.

### Windows PowerShell

PowerShell에서 공식 설치 스크립트를 실행합니다.

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 후 새 PowerShell 창을 엽니다.

### 설치 후 재확인

설치가 끝나면 다시 버전을 확인합니다.

```bash
uv --version
```

Windows PowerShell에서도 같은 명령을 사용합니다.

```powershell
uv --version
```

최신 설치 방법은 공식 문서를 기준으로 확인합니다.

- https://docs.astral.sh/uv/getting-started/installation/

---

## 3. 프로젝트 위치로 이동 및 의존성 동기화

예제는 프로젝트 루트에서 실행합니다.
처음 실행하거나 의존성이 바뀐 경우 `uv sync`로 의존성을 동기화합니다.

### macOS/Linux

```bash
cd Kiwoom-Github-Active-Project
uv sync
uv run python --version
```

### Windows PowerShell

```powershell
cd Kiwoom-Github-Active-Project
uv sync
uv run python --version
```

`uv run python --version`이 정상 출력되면 예제를 실행할 준비가 된 상태입니다.

---

## 4. 환경변수 설정

`.env.example`을 참고해 `.env` 파일을 만들고, 실행 환경과 앱 인증 정보를 입력합니다.

`.env` 주요 항목은 다음과 같습니다.

```text
KIWOOM_MODE=real
APP_KEY=...
APP_SECRET=...
```

`KIWOOM_MODE`는 다음 값을 사용합니다.

- `real`: 운영 환경
- `demo`: 모의투자 환경

### macOS/Linux

`.env.example`을 복사합니다.

```bash
cp .env.example .env
```

`.env` 파일을 수정한 뒤 shell 환경에 로드합니다.

```bash
set -a
source .env
set +a
```

로드 여부는 다음처럼 확인할 수 있습니다.

```bash
echo "$KIWOOM_MODE"
```

### Windows PowerShell

`.env.example`을 복사합니다.

```powershell
Copy-Item .env.example .env
```

`.env` 파일을 수정한 뒤 PowerShell 환경에 로드합니다.

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -and -not $_.StartsWith("#")) {
        $name, $value = $_ -split "=", 2
        Set-Item -Path "Env:$name" -Value $value
    }
}
```

로드 여부는 다음처럼 확인할 수 있습니다.

```powershell
$env:KIWOOM_MODE
```

---

## 5. OAuth 예제 실행

먼저 접근토큰 발급 예제를 실행해 인증 설정이 정상인지 확인합니다.
정상 실행되면 토큰 발급 여부, 저장 시각, 만료 시각, 토큰 유효 여부가 출력됩니다.
샘플코드는 접근토큰 값을 직접 출력하지 않습니다.

### macOS/Linux

```bash
uv run python "examples/OAuth 인증/접근토큰발급/create_access_token.py"
```

토큰을 폐기해야 할 때는 다음 예제를 실행합니다.

```bash
uv run python "examples/OAuth 인증/접근토큰폐기/delete_access_token.py"
```

### Windows PowerShell

```powershell
uv run python "examples/OAuth 인증/접근토큰발급/create_access_token.py"
```

토큰을 폐기해야 할 때는 다음 예제를 실행합니다.

```powershell
uv run python "examples/OAuth 인증/접근토큰폐기/delete_access_token.py"
```

---

## 6. 조회 예제 실행

조회성 예제는 상대적으로 안전하게 실행할 수 있습니다.
실행 결과는 `pandas.DataFrame` 또는 `dict[str, pandas.DataFrame]` 형태로 출력됩니다.
테이블 응답은 `[테이블명]` 단위로 나누어 표시됩니다.

### macOS/Linux

국내주식 종목리스트 예제:

```bash
uv run python "examples/국내주식/종목정보/list_domestic_stocks.py"
```

다른 조회 예제도 같은 방식으로 실행합니다.

```bash
uv run python "examples/국내주식/시세/get_domestic_stock_quote.py"
uv run python "examples/국내주식/차트/get_domestic_stock_daily_chart.py"
uv run python "examples/국내주식/계좌/list_domestic_accounts.py"
```

### Windows PowerShell

국내주식 종목리스트 예제:

```powershell
uv run python "examples/국내주식/종목정보/list_domestic_stocks.py"
```

다른 조회 예제도 같은 방식으로 실행합니다.

```powershell
uv run python "examples/국내주식/시세/get_domestic_stock_quote.py"
uv run python "examples/국내주식/차트/get_domestic_stock_daily_chart.py"
uv run python "examples/국내주식/계좌/list_domestic_accounts.py"
```

---

## 7. 주문 예제 실행 주의

`examples/국내주식/주문/` 아래 예제는 실제 주문 또는 주문 정정/취소 요청을 수행할 수 있습니다.
운영 환경에서 실행하면 실제 계좌에 영향을 줄 수 있으므로 반드시 내용을 확인한 뒤 실행합니다.

주문 예제에는 다음 파일들이 포함됩니다.

```text
examples/국내주식/주문/
├── buy_domestic_stock.py
├── sell_domestic_stock.py
├── modify_domestic_stock_order.py
├── cancel_domestic_stock_order.py
├── buy_domestic_gold_spot.py
├── sell_domestic_gold_spot.py
├── modify_domestic_gold_spot_order.py
└── cancel_domestic_gold_spot_order.py
```

주문 예제를 실행하기 전에는 다음을 확인합니다.

- `KIWOOM_MODE`가 의도한 환경인지 확인합니다.
- 종목코드, 주문수량, 주문가격, 거래소 구분 값을 확인합니다.
- 정정/취소 예제는 원주문번호가 실제 주문과 맞는지 확인합니다.
- 운영 환경에서는 소액 또는 테스트 가능한 조건에서만 실행합니다.

### macOS/Linux

현재 실행 모드를 확인합니다.

```bash
echo "$KIWOOM_MODE"
```

주문 예제는 파일 내용을 직접 확인한 뒤 실행합니다.

```bash
uv run python "examples/국내주식/주문/buy_domestic_stock.py"
```

### Windows PowerShell

현재 실행 모드를 확인합니다.

```powershell
$env:KIWOOM_MODE
```

주문 예제는 파일 내용을 직접 확인한 뒤 실행합니다.

```powershell
uv run python "examples/국내주식/주문/buy_domestic_stock.py"
```

---

## 8. 자주 발생하는 오류

예제 실행 중 자주 발생하는 오류와 확인 방법입니다.

### 자격 증명을 찾을 수 없는 경우

```text
CredentialsNotFoundError
```

원인:

- `.env`가 로드되지 않았습니다.
- `APP_KEY`, `APP_SECRET`이 비어 있습니다.
- `KIWOOM_MODE`가 의도한 환경과 다릅니다.

macOS/Linux 확인:

```bash
echo "$KIWOOM_MODE"
```

macOS/Linux에서 `.env`를 다시 로드:

```bash
set -a
source .env
set +a
```

Windows PowerShell 확인:

```powershell
$env:KIWOOM_MODE
```

Windows PowerShell에서 `.env`를 다시 로드:

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -and -not $_.StartsWith("#")) {
        $name, $value = $_ -split "=", 2
        Set-Item -Path "Env:$name" -Value $value
    }
}
```

### 모듈을 찾을 수 없는 경우

```text
ModuleNotFoundError
```

프로젝트 루트에서 `uv run`으로 실행했는지 확인합니다.

macOS/Linux:

```bash
pwd
uv run python "examples/OAuth 인증/접근토큰발급/create_access_token.py"
```

Windows PowerShell:

```powershell
Get-Location
uv run python "examples/OAuth 인증/접근토큰발급/create_access_token.py"
```

### 공통 확인 사항

API 서버에서 반환한 `return_code`, `return_msg`가 결과에 포함될 수 있습니다.
요청 파라미터, 계좌 권한, 운영/모의 환경, 장 운영 시간을 확인합니다.

---

## 9. 실행 순서 추천

처음 실행할 때는 다음 순서로 확인합니다.

1. Python 설치 확인
2. `uv` 설치 확인
3. 프로젝트 루트로 이동
4. `uv sync` 실행
5. `.env` 작성
6. `.env` 로드
7. OAuth 접근토큰 발급 예제 실행
8. 조회성 예제 실행
9. 계좌 조회 예제 실행
10. 주문 예제는 별도 확인 후 실행

### macOS/Linux

```bash
python3 --version
uv --version
cd Kiwoom-Github-Active-Project
uv sync

cp .env.example .env
# .env 파일에 KIWOOM_MODE, APP_KEY, APP_SECRET 값을 입력합니다.

set -a
source .env
set +a

uv run python "examples/OAuth 인증/접근토큰발급/create_access_token.py"
uv run python "examples/국내주식/종목정보/list_domestic_stocks.py"
```

### Windows PowerShell

```powershell
py --version
uv --version
cd Kiwoom-Github-Active-Project
uv sync

Copy-Item .env.example .env
# .env 파일에 KIWOOM_MODE, APP_KEY, APP_SECRET 값을 입력합니다.

Get-Content .env | ForEach-Object {
    if ($_ -and -not $_.StartsWith("#")) {
        $name, $value = $_ -split "=", 2
        Set-Item -Path "Env:$name" -Value $value
    }
}

uv run python "examples/OAuth 인증/접근토큰발급/create_access_token.py"
uv run python "examples/국내주식/종목정보/list_domestic_stocks.py"
```
