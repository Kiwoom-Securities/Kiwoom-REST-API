# 키움증권 CLI(kwcli) 설치 가이드

> **에이전트용 실행 문서입니다.**
>
> 이 문서를 읽는 주체는 Cursor, Codex, Claude Code, Claude Desktop, Antigravity 등 터미널(Bash/PowerShell)을 실행할 수 있는 AI Agent입니다.
>
> 목적은 설치 방법을 설명하는 것이 아니라, **Agent가 사용자의 로컬 환경에 `kwcli`를 직접 설치하고 `kiwoomcli doctor` 검증까지 마치는 것**입니다. 단 하나의 예외가 있습니다 — App Key/Secret 입력(Step 3)은 구조적으로 Agent가 대신할 수 없습니다. 이유는 Step 3에 명시합니다.

---

## 설치 메타데이터

```text
PACKAGE  = kwcli          (PyPI)
COMMAND  = kiwoomcli       (설치 후 사용하는 콘솔 명령)
INSTALL  = uv tool install kwcli   (대안: pipx install kwcli / pip install kwcli)
```

`kiwoomcli`는 키움증권 OpenAPI용 커맨드라인 클라이언트입니다. 조회는 즉시 가능하고, 주문은 `--confirm` 없이는 절대 전송되지 않는 안전장치가 내장돼 있습니다. 이 문서는 설치와 계좌 등록, 그리고 그 등록이 실제로 작동하는지 검증하는 것까지만 다룹니다.

---

# Agent Rules

아래 규칙은 전체 설치 과정에서 반드시 지킵니다.

1. **설치 방법만 설명하지 말고 Step 1·2·4를 실제로 실행합니다.**
2. **Step 3(`kiwoomcli setup`)은 Agent가 절대 대신 실행하지 않습니다.** 명령만 제시하고, 사용자가 자신의 실제 터미널에서 직접 실행하도록 안내한 뒤 완료 여부를 확인받습니다. 이유는 Step 3에서 설명합니다 — 우회하려 시도하지 않습니다.
3. **App Key / Secret의 실제 값을 묻지도, 읽지도, 기록하지도, 대신 입력하지도 않습니다.** `.env` 파일이나 OS 자격 증명 저장소(keyring)를 뒤져 값을 확인하지도 않습니다.
4. macOS와 Windows를 모두 지원합니다. Windows는 PowerShell을 우선 사용합니다.
5. 이미 설치된 `kwcli`, 기존 계좌 별칭·토큰 캐시를 삭제하거나 덮어쓰지 않습니다.
6. **설치 명령이 성공했다는 이유만으로 완료라고 보고하지 않습니다.** Step 4의 검증을 통과해야 완료입니다.
7. 검증 목적으로 주문 명령이나 그 밖의 쓰기 작업을 실행하지 않습니다. 계좌 조회 스모크는 `kiwoomcli setup` 내부에서 이미 수행되므로 Agent가 별도로 반복하지 않습니다.
8. 기존에 저장된 계좌 별칭이 있다면 함부로 재설정하거나 삭제하지 않고, 먼저 사용자에게 확인합니다.
9. **사용자는 개발 경험이 없을 수 있습니다.** `PATH`, TTY, `getpass`, `keyring`, `SetupError` 같은 용어나 원본 에러 메시지를 그대로 던지지 않습니다. 터미널이 무엇인지부터 필요하면 설명하고, "이 창을 열고 이 줄을 그대로 붙여넣은 뒤 Enter를 누르세요"처럼 구체적인 행동으로 안내합니다. 진단 결과는 원문이 아니라 "성공/실패 + 다음에 할 일"로 요약해 전달합니다.

---

# Step 0. 운영체제 확인

지원 대상은 macOS와 Windows입니다. Windows에서는 PowerShell 환경을 우선 사용합니다. 이후 단계의 명령과 경로 표기를 확인된 OS에 맞게 선택합니다.

---

# Step 1. uv 확인·설치 (Agent 실행)

`kwcli`는 `uv tool install`로 설치하는 것이 기본입니다. 먼저 uv가 있는지 확인합니다.

### macOS

```bash
command -v uv
```

### Windows PowerShell

```powershell
(Get-Command uv -ErrorAction SilentlyContinue).Source
```

경로가 출력되면 Step 2로 진행합니다. 없으면 설치합니다.

### macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows PowerShell

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **설치 직후에는 현재 shell의 PATH에 uv가 아직 없을 수 있습니다.** 새 터미널을 요구하지 말고, installer의 기본 설치 위치(`~/.local/bin/uv`, `%USERPROFILE%\.local\bin\uv.exe`)를 직접 확인해 그 절대 경로로 이후 명령을 실행합니다.

uv 없이 진행하고 싶다면 `pipx install kwcli` 또는 `pip install kwcli`도 동일한 결과를 냅니다 — 이 문서의 이후 단계는 콘솔 명령 `kiwoomcli`가 PATH에서 실행되는지만 확인하므로 어떤 방법으로 설치했든 동일하게 적용됩니다.

---

# Step 2. kwcli 설치 (Agent 실행)

```bash
uv tool install kwcli
```

설치 후 확인합니다.

```bash
kiwoomcli --help
```

### PATH에 `kiwoomcli`가 안 잡히는 경우

`uv tool install`은 실행 파일을 uv 전용 bin 디렉터리에 넣습니다. 위치를 직접 확인합니다.

```bash
uv tool dir --bin
```

이 디렉터리가 PATH에 없다면:

```bash
uv tool update-shell
```

실행 후 **새 터미널 세션**에서 `kiwoomcli --help`가 동작하는지 확인합니다. 그래도 현재 세션에서 바로 확인해야 한다면, `uv tool dir --bin`이 알려준 절대 경로로 직접 실행합니다 (예: `<BIN_DIR>/kiwoomcli --help`).

이 단계까지는 비밀 정보가 전혀 관여하지 않으므로 Agent가 전부 대신 실행합니다.

---

# Step 3. 계좌 인증 — **사용자가 직접 실행** (우회 불가)

> **이 단계는 Agent가 대신 실행하면 반드시 실패합니다.** 아래 이유를 이해하고 넘어갑니다.

`kiwoomcli setup`은 App Key/Secret을 **화면에 표시되지 않는 입력**(`getpass`)으로 받습니다. 이 입력 방식은 실제 대화형 터미널(TTY)이 연결돼 있어야만 동작합니다. Agent가 Bash/PowerShell 도구로 실행하는 프로세스는 TTY가 아니므로, `setup`이 자격 증명을 요구하는 순간 다음과 같이 즉시 실패합니다.

```text
SetupError: setup에서 자격 증명 입력은 대화형 터미널에서만 지원합니다.
```

이것은 버그가 아니라 **App Key/Secret이 Agent를 거치지 않고 곧장 사용자 입력 → OS 자격 증명 저장소로만 흐르게 하는 설계**입니다. 따라서 Agent는 이 단계를 다음과 같이 처리합니다.

1. 아래 명령을 사용자에게 **제시만** 합니다.

   ```bash kiwoomcli setup ```

   실행하면 계좌 별칭 → demo/real 선택 → App Key/Secret 입력(화면에 표시되지 않음) → 실제 조회 1건으로 자동 검증까지 5단계가 진행됩니다.

2. 사용자에게 다음을 안내합니다.
   - 자신의 터미널을 열어 직접 실행할 것. 터미널을 처음 열어보는 사용자에게는 구체적으로 안내합니다.
     - macOS: `⌘ + Space`를 누르고 "터미널"을 입력한 뒤 Enter.
     - Windows: 시작 메뉴에서 "PowerShell"을 입력한 뒤 Enter (관리자 권한 불필요).
     - 이미 이 대화 자체가 터미널 세션이라면(예: Claude Code의 `!kiwoomcli setup` 처럼 `!` 접두사로 명령을 직접 실행할 수 있는 환경) 새로 열 필요 없이 그 방식을 안내합니다.
   - App Key는 [키움증권 개발자센터](https://openapi.kiwoom.com)에서 발급받으며, **모의투자(demo)로 먼저 시작**하기를 권장할 것 — demo/real은 서로 다른 키를 쓴다는 점.
   - 실제 키 값은 **채팅에 입력하지 말 것**.
3. 사용자가 "완료했다"고 확인하기 전까지 Step 4로 넘어가지 않습니다.
4. 사용자가 setup 도중 오류를 만나면, 에러 메시지를 그대로 보여달라고 요청하고 Troubleshooting 항목에서 원인을 찾습니다 — 이 과정에서도 키 값 자체는 절대 요청하지 않습니다.

이미 계좌 별칭이 있는 사용자라면 `setup`이 자동으로 감지해 전환/토큰 재발급/재입력/ 삭제 후 재설정 중 하나를 대화형으로 물어봅니다. 이 선택도 사용자가 직접 합니다.

---

# Step 4. 설치 검증 (Agent 실행 — 비밀값 노출 없음)

Step 3가 끝났다는 사용자의 확인을 받은 뒤, 아래 두 명령으로 검증합니다. 둘 다 저장된 키 값을 출력하지 않으므로 Agent가 안전하게 실행할 수 있습니다.

```bash
kiwoomcli auth list
kiwoomcli doctor
```

## 성공 조건

```text
auth list  : 계좌 별칭이 1개 이상 나타난다.
doctor     : "판정 → 지금 호출 가능: 예" 로 표시된다.
```

`doctor`가 "지금 호출 가능: 아니오"를 보고하면 함께 출력되는 "발견된 문제"와 "고치려면" 항목을 그대로 사용자에게 전달합니다 — 대부분 Step 3을 다시 실행하거나 `kiwoomcli auth login --alias <별칭> --mode <demo|real>`로 이어집니다(이 명령도 동일하게 자격 증명 입력 시 TTY가 필요하므로 사용자가 직접 실행합니다).

Step 3의 `setup` 마법사는 내부적으로 실제 API 호출 1건(삼성전자 조회)로 이미 연결을 검증했습니다. 따라서 Agent가 별도로 조회 명령을 실행해 재검증할 필요는 없습니다 — `doctor`의 판정만으로 충분합니다.

---

# Step 5. 최종 결과 보고

```text
키움 CLI(kwcli) 설치 완료

OS: <OS>
kwcli 버전 경로: <kiwoomcli 실행 파일 경로>
계좌 별칭: <auth list 결과>

Verification:
- kiwoomcli --help: OK
- auth list: 별칭 <N>개 확인
- doctor 판정: 지금 호출 가능 = 예

다음 명령 예시:
  kiwoomcli spec search "체결"
  kiwoomcli domestic stocks info --code 005930 --format json
```

`doctor` 판정이 "예"가 아니라면 **설치 완료라고 보고하지 않습니다.**

---

# Troubleshooting

## `command not found: uv`

macOS `command -v uv` / Windows `(Get-Command uv).Source`로 경로를 확인하고, 없으면 기본 설치 위치(`~/.local/bin/uv`, `%USERPROFILE%\.local\bin\uv.exe`)를 직접 확인해 절대 경로로 실행합니다.

## `command not found: kiwoomcli`

`uv tool dir --bin`이 가리키는 디렉터리가 PATH에 없는 상태입니다. `uv tool update-shell` 실행 후 새 터미널에서 재확인합니다.

## 비대화형 환경에서 `kiwoomcli setup`을 실행하면 `SetupError`가 난다

의도된 동작입니다(Step 3 참고). Agent가 대신 실행하려던 것이 원인입니다 — 사용자 본인의 대화형 터미널에서 실행하도록 안내합니다.

## 사전 점검에서 "자격 증명 저장소 사용 불가" 경고

OS에 사용 가능한 keyring 백엔드가 없는 환경입니다. App Key/Secret 저장이 실패할 수 있습니다. 두 가지 대안을 사용자에게 안내합니다.

```text
1) 지원되는 keyring 백엔드를 설치한다 (OS별로 다름).
2) 환경변수로 대체한다 — 이 값 역시 사용자가 직접 자신의 셸 프로파일에 설정한다:
     real 모드 : APP_KEY / APP_SECRET
     demo 모드 : APP_KEY_MOCK / APP_SECRET_MOCK
```

이 값도 App Key/Secret과 동일하게 다루는 비밀 정보입니다 — Agent는 설정할 명령의 형태만 제시하고, 실제 값을 채우거나 대신 실행하지 않습니다. 사용자가 자신의 셸 설정 파일(`~/.zshrc`, `~/.bashrc`, PowerShell 프로필 등)에 직접 추가하도록 안내합니다.

## PATH에 `kiwoomcli` 실행 파일이 여러 개 있다는 경고 (`doctor`)

`which -a kiwoomcli` (Windows: `where.exe kiwoomcli`)로 우선순위를 확인하도록 안내합니다. 삭제나 정리는 사용자가 직접 판단해 수행합니다.

## `kiwoomcli setup`은 됐는데 실제 조회에서 인증 오류

App Key/Secret이 틀렸거나, demo 키를 real로(또는 그 반대로) 등록한 경우입니다. `kiwoomcli doctor` 또는 `kiwoomcli auth status --profile <별칭>`으로 원인을 확인하도록 안내합니다. 설치 문제가 아닙니다.

---

# Definition of Done

아래 조건을 **모두 만족해야 설치 완료**입니다.

* [ ] 운영체제를 확인했다.
* [ ] uv의 존재를 확인했거나 설치했다.
* [ ] `uv tool install kwcli`가 성공했고 `kiwoomcli --help`가 동작한다.
* [ ] App Key/Secret 입력은 Agent가 대신 실행하지 않고, 사용자가 자신의 터미널에서 직접 `kiwoomcli setup`을 실행했다.
* [ ] `kiwoomcli auth list`에 계좌 별칭이 1개 이상 나타난다.
* [ ] `kiwoomcli doctor` 판정이 "지금 호출 가능: 예"다.
* [ ] App Key/Secret 값을 묻지도, 읽지도, 기록하지도 않았다.
* [ ] 검증 목적으로 주문이나 그 밖의 쓰기 작업을 실행하지 않았다.

`doctor` 판정이 "예"가 되기 전에는 설치 완료라고 보고하지 않습니다.
