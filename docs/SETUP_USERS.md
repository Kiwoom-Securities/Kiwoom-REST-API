# Kiwoom OpenAPI 사용자 가이드

이 문서 하나만 따라 하면 **키 발급 → 설치 → 인증 → CLI/샘플코드 실행**까지 끝낼 수 있습니다.
처음 사용하는 분을 기준으로, 위에서 아래로 순서대로 진행하면 됩니다.
운영체제별로 명령이 다른 곳은 `macOS/Linux`와 `Windows PowerShell`을 나누어 표기했습니다.

---

## 시작하기 전에

- **인증은 CLI(`kiwoom setup`)로 하는 것을 권장합니다.** App Key/Secret이 운영체제 자격 증명 저장소(macOS Keychain, Windows 자격 증명 관리자, Linux Secret Service)에 저장되며, 프로젝트 폴더나 Git에는 저장되지 않습니다.
- CLI로 인증하면 같은 자격 증명을 샘플코드(`examples/`)도 그대로 사용합니다. 즉 **CLI 인증만 마치면 `.env`를 따로 만들지 않아도 예제가 실행됩니다.**
- 반대로 `.env`를 만들어 두면 예제가 그쪽을 먼저 사용하므로, CLI로 인증하는 경우에는 `.env`를 만들지 마세요. `.env` 방식은 자격 증명 저장소를 쓸 수 없는 환경을 위한 대체 경로이며 [부록 A](#부록-a-env-대체-경로)에서 다룹니다.

---

## 빠른 시작 (Quickstart)

App Key/Secret을 이미 발급받았다면, 아래 순서대로 진행하면 됩니다. 각 단계의 자세한 설명은 이어지는 절에 있습니다.

### macOS/Linux

```bash
# 1) Python 3.13+ 확인
python3 --version

# 2) uv 설치 (없을 때)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3) CLI 설치
uv tool install kiwoom-cli

# 4) 인증 설정 (대화형: 별칭/서버/키 입력)
kiwoom setup

# 5) 동작 확인
kiwoom auth status
kiwoom stocks info --code 005930

# 6) (선택) 샘플코드 실행 - 이 프로젝트 폴더에서
uv sync
uv run python "examples/국내주식/종목정보/list_domestic_stocks.py"
```

### Windows PowerShell

```powershell
# 1) Python 3.13+ 확인
py --version

# 2) uv 설치 (없을 때)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# 3) CLI 설치
uv tool install kiwoom-cli

# 4) 인증 설정 (대화형: 별칭/서버/키 입력)
kiwoom setup

# 5) 동작 확인
kiwoom auth status
kiwoom stocks info --code 005930

# 6) (선택) 샘플코드 실행 - 이 프로젝트 폴더에서
uv sync
uv run python "examples/국내주식/종목정보/list_domestic_stocks.py"
```

---

## 1단계: 키움 App Key / Secret 발급

키움증권 OpenAPI를 호출하려면 **App Key**와 **App Secret**이 필요합니다.

- **운영(real)** 과 **모의투자(demo)** 는 키가 **서로 다릅니다.** 사용할 환경의 키를 발급받으세요.
- 발급받은 키는 외부에 노출되지 않도록 보관합니다. 문자 메시지/메일/공유 문서에 그대로 두지 마세요.

발급 절차(요약):

1. 키움증권 OpenAPI 포털에 로그인합니다.
2. OpenAPI 사용 신청 후 앱(App)을 등록합니다.
3. 등록한 앱에서 **App Key**와 **App Secret**을 확인/발급합니다.
4. 운영과 모의투자를 모두 사용할 경우, 각 환경의 키를 따로 발급받습니다.

> 발급 화면의 메뉴 이름과 위치는 키움 포털 정책에 따라 달라질 수 있습니다. 포털 안내를 기준으로 진행하세요.

이 단계에서 준비물:

- 운영용 App Key / App Secret (운영을 쓸 경우)
- 모의투자용 App Key / App Secret (모의투자를 쓸 경우)

---

## 2단계: Python 설치

이 프로젝트는 **Python 3.13 이상**을 기준으로 합니다.

### macOS/Linux

설치 여부 확인:

```bash
python3 --version
```

`Python 3.13.x` 이상이 출력되면 설치된 상태입니다. 없거나 버전이 낮으면 설치합니다.

macOS(Homebrew):

```bash
brew install python@3.13
```

Linux는 배포판 패키지 관리자 또는 공식 배포판을 사용합니다.

- https://www.python.org/downloads/

### Windows PowerShell

설치 여부 확인:

```powershell
py --version
```

`Python 3.13.x` 이상이 출력되면 설치된 상태입니다. 없거나 버전이 낮으면 설치합니다.

winget 사용 시:

```powershell
winget install Python.Python.3.13
```

또는 공식 Windows installer를 사용합니다.

- https://www.python.org/downloads/windows/

---

## 3단계: uv 설치

이 프로젝트의 표준 실행 도구는 [`uv`](https://docs.astral.sh/uv/)입니다. CLI 설치와 샘플코드 실행 모두 `uv`를 사용합니다.

설치 여부 확인:

```bash
uv --version
```

버전이 출력되면 설치된 상태입니다. 없으면 아래로 설치합니다.

### macOS

Homebrew 사용 시:

```bash
brew install uv
```

Homebrew를 쓰지 않으면 공식 스크립트:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Linux

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 후 새 터미널을 열거나 shell 설정을 다시 로드합니다.

### Windows PowerShell

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 후 새 PowerShell 창을 엽니다.

설치가 끝나면 다시 확인합니다.

```bash
uv --version
```

---

## 4단계: CLI 설치

`kiwoom` 명령(CLI)을 설치합니다. `uv tool install`로 설치하면 어느 폴더에서나 `kiwoom` 명령을 쓸 수 있습니다.

### macOS/Linux

```bash
uv tool install kiwoom-cli
```

### Windows PowerShell

```powershell
uv tool install kiwoom-cli
```

설치 확인(공통):

```bash
kiwoom --help
```

명령 목록이 출력되면 설치된 상태입니다.

> `kiwoom` 명령을 찾을 수 없다는 메시지가 나오면, `uv tool` 실행 경로가 PATH에 등록되도록 새 터미널을 열거나 `uv tool update-shell`(안내가 나올 경우)을 실행한 뒤 다시 시도하세요.

---

## 5단계: 인증 설정 (`kiwoom setup`)

CLI로 인증을 설정합니다. 이 한 번으로 키가 자격 증명 저장소에 저장되고, 이후 CLI와 샘플코드가 모두 이 자격 증명을 사용합니다.

```bash
kiwoom setup
```

대화형으로 다음을 진행합니다.

1. **계좌 별칭** 입력 (예: `모의계좌`, `실전계좌`). 그냥 Enter를 누르면 기본 별칭으로 저장됩니다.
2. **서버 선택**: `[1] demo(모의투자)` 또는 `[2] real(실전투자)`. Enter는 안전을 위해 demo가 기본입니다.
3. **App Key / Secret 입력**: 1단계에서 발급받은 값을 붙여넣습니다. 입력값은 화면에 표시되지 않습니다.
4. CLI가 안전한 조회 API로 연결을 검증하고, 성공하면 키를 자격 증명 저장소에 저장합니다.

성공하면 다음과 같은 다음 단계 안내가 출력됩니다.

```text
kiwoom auth status --profile <별칭>
kiwoom stocks info --code 005930 --profile <별칭>
```

상태 확인:

```bash
kiwoom auth status
```

자격 증명 존재 여부, 토큰 유효/만료 시각 등이 출력됩니다.

> 같은 별칭을 다시 `kiwoom setup`하면 "전환 / 토큰만 재발급 / 키 다시 입력 / 삭제 후 재설정" 중에서 선택할 수 있습니다.

---

## 6단계: CLI 사용법

인증이 끝나면 CLI로 바로 조회할 수 있습니다. 전체 명령은 `--help`로 확인합니다.

```bash
kiwoom --help
```

예시 — 종목 정보 조회(삼성전자 `005930`):

```bash
kiwoom stocks info --code 005930
```

여러 계좌(별칭)를 쓰는 경우 `--profile`로 대상을 지정할 수 있습니다.

```bash
kiwoom stocks info --code 005930 --profile 모의계좌
kiwoom auth status --profile 실전계좌
```

각 하위 명령의 옵션은 해당 명령에 `--help`를 붙여 확인합니다.

```bash
kiwoom stocks --help
kiwoom auth --help
```

> 주문 등 실제 계좌에 영향을 줄 수 있는 명령은 별도의 확인 절차(`--confirm` 등)를 요구합니다. 실행 전 대상 계좌(`real`/`demo`)와 입력값을 반드시 확인하세요.

---

## 7단계: 샘플코드(examples) 실행

`examples/` 폴더에는 키움 OpenAPI를 호출하는 Python 샘플코드가 들어 있습니다. **5단계에서 CLI로 인증을 마쳤다면 `.env` 없이 그대로 실행됩니다.**

먼저 이 프로젝트 폴더로 이동해 의존성을 설치합니다.

### macOS/Linux

```bash
cd Kiwoom-Github-Active-Project
uv sync
uv run python "examples/국내주식/종목정보/list_domestic_stocks.py"
```

### Windows PowerShell

```powershell
cd Kiwoom-Github-Active-Project
uv sync
uv run python "examples/국내주식/종목정보/list_domestic_stocks.py"
```

다른 조회 예제도 같은 방식으로 실행합니다(경로에 공백이 있으므로 따옴표로 감쌉니다).

```bash
uv run python "examples/국내주식/시세/get_domestic_stock_quote.py"
uv run python "examples/국내주식/차트/get_domestic_stock_daily_chart.py"
uv run python "examples/국내주식/계좌/list_domestic_accounts.py"
```

실행 결과는 `pandas.DataFrame` 형태로 출력되며, 표 응답은 `[테이블명]` 단위로 나뉘어 표시됩니다.

> `examples/국내주식/주문/` 아래 예제는 실제 주문/정정/취소를 수행할 수 있습니다. 운영 환경에서는 반드시 파일 내용과 대상 계좌를 확인한 뒤 실행하세요.

---

## 부록 A: `.env` 대체 경로

운영체제 자격 증명 저장소를 쓸 수 없는 환경(예: 일부 헤드리스 서버)에서는 `.env` 파일로 자격 증명을 제공할 수 있습니다. **CLI로 인증한 경우에는 이 절을 사용하지 마세요**(중복되면 충돌합니다).

이 프로젝트 폴더에서 `.env.example`을 복사해 `.env`를 만듭니다.

### macOS/Linux

```bash
cp .env.example .env
```

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

`.env`에서 사용할 환경의 값을 채웁니다.

- 운영(real): `KIWOOM_MODE=real`, `APP_KEY=<운영 App Key>`, `APP_SECRET=<운영 App Secret>`
- 모의투자(demo): `KIWOOM_MODE=demo`, `APP_KEY_MOCK=<모의 App Key>`, `APP_SECRET_MOCK=<모의 App Secret>`

환경에 로드합니다.

### macOS/Linux

```bash
set -a
source .env
set +a
echo "$KIWOOM_MODE"
```

### Windows PowerShell

```powershell
Get-Content .env | ForEach-Object {
    if ($_ -and -not $_.StartsWith("#")) {
        $name, $value = $_ -split "=", 2
        Set-Item -Path "Env:$name" -Value $value
    }
}
$env:KIWOOM_MODE
```

이후 샘플코드를 실행하면 환경변수의 자격 증명을 사용합니다.

> `.env`는 비밀 정보를 담으므로 절대 Git에 커밋하지 마세요. 이 프로젝트의 `.gitignore`는 `.env`를 제외하도록 설정되어 있습니다.

---

## 부록 B: 자주 발생하는 오류

### `kiwoom` 명령을 찾을 수 없음

- CLI 설치 후 PATH가 반영되도록 **새 터미널**을 엽니다.
- `uv tool install kiwoom-cli`가 정상 완료되었는지 확인합니다.

### 자격 증명을 찾을 수 없음 (`CredentialsNotFoundError`)

- `kiwoom setup`을 완료했는지 확인합니다: `kiwoom auth status`
- `.env`를 로드한 상태라면, `KIWOOM_MODE`만 있고 키가 비어 있을 수 있습니다. CLI 인증을 쓰는 경우 **로드된 `.env` 환경변수를 해제**하거나 새 터미널을 사용하세요.

### 자격 증명 저장소를 쓸 수 없음 (`KeyringUnavailableError`)

- 자격 증명 저장소가 없는 환경입니다. [부록 A](#부록-a-env-대체-경로)의 `.env` 방식을 사용하세요.

### 모듈을 찾을 수 없음 (`ModuleNotFoundError`) — 샘플코드 실행 시

- 프로젝트 폴더에서 `uv sync`를 먼저 실행했는지, 그리고 `uv run python ...`으로 실행했는지 확인합니다.

### API 응답 코드/메시지가 보임

- 응답에 키움 서버의 `return_code` / `return_msg`가 포함될 수 있습니다. 요청 파라미터, 계좌 권한, 운영/모의 환경, 장 운영 시간을 확인하세요.

---

## 부록 C: 보안 주의

- App Key/Secret은 **운영 자금에 직접 영향**을 줄 수 있는 민감 정보입니다.
- 가능하면 자격 증명 저장소를 쓰는 CLI 인증(`kiwoom setup`)을 사용하고, `.env`는 꼭 필요한 환경에서만 쓰세요.
- 키를 화면 공유, 캡처, 공용 저장소에 노출하지 마세요.
- 운영(real)과 모의투자(demo)를 구분해 사용하고, 주문 계열 명령/예제는 대상 환경을 반드시 확인한 뒤 실행하세요.

---

## 부록 D: AI 에이전트에게 "CLI 설치까지" 맡길 때

> 이 절은 사용자가 AI 코딩 에이전트에게 "이 문서대로 CLI를 설정해줘"라고 요청할 때를 위한 **실행 규칙**입니다.
> 명령 자체는 위 본문(2~4단계)을 그대로 사용하고, 이 절은 **에이전트가 지켜야 할 범위와 경계**만 정의합니다.

**수행 범위**: 본문 **2단계(Python) → 3단계(uv) → 4단계(CLI 설치)** 까지. 각 단계는 "버전 확인 후 없을 때만 설치"(멱등) 원칙을 따르고, OS는 자동 판별해 해당 명령만 실행한다.

**멈추는 지점**: 4단계의 `kiwoom --help` 검증이 성공하면 **종료**한다. 그 다음(5단계 `kiwoom setup` 이후)은 진행하지 않는다.

**세션 내 PATH 처리**: 설치 직후 `kiwoom`이 안 잡히면, 새 터미널 대신 `uv tool update-shell`(필요 시 `uv tool dir`/`uv tool list`로 경로 확인)로 **현재 세션에 PATH를 반영**한다. (자세한 안내는 4단계 끝의 주석 참고)

**절대 하지 않을 것**:

- `kiwoom setup` / `kiwoom auth` / `kiwoom stocks` 등 **자격 증명이 필요한 명령 실행** — App Key/Secret은 사용자만 입력한다.
- `examples/` 실행 등 **실제 API 호출**, 특히 주문 계열.
- `.env` 등 자격 증명 관련 파일 임의 생성.

**완료 후**: CLI 설치 완료를 알리고, 남은 **1단계(키 발급)**와 **5단계(`kiwoom setup` 인증)**는 사용자가 직접 진행하도록 안내한다.

---

## 실행 순서 요약

1. 키움에서 App Key/Secret 발급 (운영/모의 각각)
2. Python 3.13+ 설치
3. `uv` 설치
4. `uv tool install kiwoom-cli`로 CLI 설치
5. `kiwoom setup`으로 인증 설정
6. `kiwoom auth status` / `kiwoom stocks info --code 005930`로 확인
7. (선택) 프로젝트 폴더에서 `uv sync` 후 `uv run python "examples/..."`로 샘플코드 실행
