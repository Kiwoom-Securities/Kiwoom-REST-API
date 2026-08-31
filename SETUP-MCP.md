# 키움증권 MCP Local 설치 가이드

> **에이전트용 실행 문서입니다.**
>
> 이 문서를 읽는 주체는 Cursor, Codex, Claude Code, Claude Desktop, Antigravity 등의 AI Agent입니다.
>
> 이 문서의 목적은 설치 방법을 설명하는 것이 아니라, **Agent가 사용자의 로컬 환경에 MCP 서버를 직접 설치하고 `tools/list` 호출까지 검증하는 것**입니다.

---

## 설치 메타데이터

```text
REPOSITORY_URL=https://github.com/Kiwoom-Securities/Kiwoom-REST-API
REPO_DIR=Kiwoom-REST-API
```

이 저장소는 MCP 서버 **두 개**를 담고 있습니다. 성격이 다르므로 둘 다 설치하는 것이 기본입니다.

| server | 무엇을 하나 | 앱 키 필요? | EXPECTED_TOOL |
| --- | --- | --- | --- |
| `kiwoom-spec` | API 명세 검색, 예제 코드 조회 | 불필요 | `spec_search` |
| `kiwoom-exec` | 시세·계좌 조회, (게이트 뒤) 주문 | 조회 실행 시 필요 · **설치 검증에는 불필요** | `kiwoom_query` |

MCP 서버 실행 정의:

```text
# kiwoom-spec
COMMAND=uv
ARGS=[
  "run", "--frozen",
  "--directory", "{{REPO_PATH}}/mcp_spec",
  "kiwoom-spec-mcp"
]

# kiwoom-exec
COMMAND=uv
ARGS=[
  "run", "--frozen",
  "--directory", "{{REPO_PATH}}/mcp_exec",
  "kiwoom-exec-mcp"
]
ENV={
  "APP_KEY":     "your_app_key",     # placeholder — 실제 값은 사용자가 직접 교체 (Step 9)
  "APP_SECRET":  "your_app_secret",  # placeholder — Agent는 절대 채우지 않는다
  "KIWOOM_MODE": "demo"
}
```

`ARGS` 안의 `{{REPO_PATH}}`는 설치 과정에서 실제 clone된 repository의 **절대 경로**로 치환합니다. 이것이 이 문서에 남아 있는 유일한 placeholder이며, Step 4에서 Agent가 치환합니다.

- `KIWOOM_MODE`는 `demo`(모의투자) 또는 `real`(실전투자). 두 모드는 **서로 다른 앱 키**를 씁니다. 기본값은 `demo`로 설치합니다.
- 주문 도구는 기본 **꺼짐**입니다. Step 1.2에서 사용자에게 묻고, 사용자가 켜기를 선택한 경우에만 exec의 ENV에 `"KIWOOM_MCP_ALLOW_ORDERS": "1"`을 추가합니다. 값이 **정확히 `1`** 일 때만 켜집니다(`true`/`yes` 무효 — 오타로 주문이 열리지 않게 설계됨). Agent가 임의로 켜지 않습니다.

---

# Agent Rules

아래 규칙은 전체 설치 과정에서 반드시 지킵니다.

1. **설치 방법만 설명하지 말고 실제 설치 작업을 수행합니다.**
2. 설치 전에 반드시 사용자에게 사용할 MCP 클라이언트를 묻습니다.
3. 사용자가 클라이언트를 선택하면 한 번 명확히 확인하고 이후 설치 절차를 계속 진행합니다.
4. 이미 선택한 클라이언트를 다시 묻지 않습니다.
5. macOS와 Windows를 모두 지원합니다.
6. MCP 서버는 원격 서버가 아니라 **사용자의 컴퓨터에서 실행되는 local stdio MCP**로 설치합니다.
7. GitHub repository를 로컬에 clone하고 그 source code를 직접 실행합니다.
8. 기존 MCP 설정을 삭제하거나 덮어쓰지 않습니다.
9. 기존 설정에 `kiwoom-spec` / `kiwoom-exec` 항목만 추가하거나 갱신합니다.
10. 다른 MCP server 설정 및 client 설정은 그대로 보존합니다.
11. repository 경로는 MCP config에 기록하기 전에 실제 **absolute path**로 확정합니다.
12. 예제 경로나 예제 사용자 이름을 실제 config에 쓰지 않습니다.
13. Windows 경로는 JSON/TOML에서 안전하게 표현하고, 가능하면 `C:/Users/...` 형태의 forward slash 경로를 사용합니다.
14. **`APP_KEY`, `APP_SECRET`의 실제 값을 사용자에게 묻거나 읽거나 출력하지 않습니다.** `.env`나 keychain을 뒤져 값을 확인하지도 않습니다.
15. 앱 키는 config에 placeholder(`your_app_key`)로만 쓰고, 실제 값 교체는 사용자에게 안내합니다 (Step 9).
16. 설정 파일을 저장한 뒤 JSON/TOML syntax를 검증합니다.
17. **설정 파일이 생성됐다는 이유만으로 설치 성공이라고 판단하지 않습니다.**
18. **MCP `tools/list` 요청이 실제로 성공해야 설치 완료입니다.**
19. 설치 검증 목적으로 `tools/call`을 호출하지 않습니다 — 조회도, 주문은 더더욱 호출하지 않습니다. **`tools/list`까지만 수행하고 종료합니다.**
20. `KIWOOM_MCP_ALLOW_ORDERS`는 Step 1.2에서 사용자에게 물은 결과로만 결정합니다. 사용자가 켜기를 선택하지 않았다면 켜지 않고, 답이 모호하면 끄기로 둡니다.

---

# Step 0. uv / git 확인

이 프로젝트의 runtime 구성은 고정되어 있습니다 — 추측할 필요가 없습니다.

```text
runtime            : Python >= 3.13 (uv가 자동으로 설치·관리)
dependency manager : uv (mcp_spec/uv.lock, mcp_exec/uv.lock으로 버전 고정)
사용자가 준비할 것  : uv, git 뿐
```

## 0.1 uv 확인·설치

먼저 uv가 이미 있는지 확인합니다.

### macOS

```bash
command -v uv
```

### Windows PowerShell

```powershell
(Get-Command uv -ErrorAction SilentlyContinue).Source
```

경로가 출력되면 0.2로 진행합니다. 없으면 설치합니다.

### macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows PowerShell

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **설치 직후에는 현재 shell의 PATH에 uv가 아직 없을 수 있습니다.** 새 터미널을 요구하지
> 말고, installer의 기본 설치 위치를 직접 확인해 그 절대 경로를 사용합니다.
>
> ```text
> macOS   : ~/.local/bin/uv
> Windows : %USERPROFILE%\.local\bin\uv.exe
> ```
>
> 해당 파일이 존재하면 이후 모든 단계에서 `uv` 대신 이 절대 경로로 실행합니다.

## 0.2 UV_PATH 확정

uv executable의 **absolute path**를 확정합니다.

### macOS

```bash
command -v uv || ls ~/.local/bin/uv
```

### Windows PowerShell

```powershell
if ($p = (Get-Command uv -ErrorAction SilentlyContinue).Source) { $p }
elseif (Test-Path "$env:USERPROFILE/.local/bin/uv.exe") { "$env:USERPROFILE/.local/bin/uv.exe" }
```

이 값을 이후부터 `<UV_PATH>`로 사용하며, 실행 가능 여부를 검증합니다.

```bash
<UV_PATH> --version
```

MCP config의 `command`에는 `uv`가 아니라 **`<UV_PATH>`를 넣습니다.** GUI 기반 MCP
client(특히 Claude Desktop)는 shell의 PATH를 상속하지 않아서, `"command": "uv"`로 적으면
터미널에서는 되는데 client에서만 `command not found`로 죽는 사례가 전형적입니다.
Windows 경로는 `C:/Users/<user>/.local/bin/uv.exe` forward slash 표기로 기록합니다.

## 0.3 git 확인

```bash
git --version
```

없으면 설치를 안내합니다.

```text
macOS   : xcode-select --install  (또는 brew install git)
Windows : winget install Git.Git  (또는 git-scm.com/download/win)
Linux   : 배포판 패키지 매니저 (예: sudo apt install git)
```

git은 Step 3의 repository clone에만 필요합니다. 이미 clone된 repository를 쓰는 경우
(3.1) git이 없어도 진행할 수 있습니다.

---

# Step 1. 설치 대상 MCP Client · 주문 도구 확인

설정을 변경하기 전에 반드시 사용자에게 다음 두 가지를 묻습니다.

## 1.1 MCP Client

> 어느 MCP 클라이언트에 설치할까요?
>
> * Cursor
> * Codex
> * Claude Code
> * Claude Desktop
> * Antigravity

`Claude`라고만 답해 Claude Desktop인지 Claude Code인지 구분할 수 없는 경우에만 한 번 구분을 요청합니다.

## 1.2 주문 도구 활성화 여부

> 주문 도구(`kiwoom_order_preview` / `kiwoom_order_submit`)를 켤까요?
>
> * **끄기 (기본, 권장)** — 시세·계좌 조회만 가능합니다. 나중에 설정에 한 줄 추가로 켤 수 있습니다.
> * **켜기** — AI 대화로 **실제 주문이 전송될 수 있습니다.** 켜는 경우 클라이언트의 도구 실행
>   자동 승인을 사용하지 않는 것이 전제입니다 — 최종 안전장치는 도구 실행 승인 화면입니다.

사용자가 답하지 않거나 모호하면 **끄기**로 진행합니다. Agent가 먼저 켜기를 권하지 않습니다.

## 1.3 확정

두 답을 받으면 다음과 같이 한 번 확인합니다.

> `<SELECTED_CLIENT>`용 Local MCP 설정으로 진행하겠습니다. spec(명세 검색)과 exec(시세·계좌 조회)
> 서버 두 개를 설치하고, 주문 도구는 <켜기|끄기(기본)>로 둡니다.

그 이후에는 동일한 선택을 다시 묻지 않고 설치를 진행합니다.

---

# Step 2. 운영체제 확인

현재 운영체제를 확인합니다.

지원 대상:

```text
macOS
Windows
```

Windows에서는 PowerShell 환경을 우선 사용합니다.

설치 경로, executable 경로 및 MCP config 경로를 이후 단계에서 OS에 맞게 결정합니다.

---

# Step 3. Repository 준비

## 3.1 이미 clone된 repository 확인

현재 workspace 또는 로컬 filesystem에 `REPOSITORY_URL`과 동일한 Git repository가 이미 존재하는지 확인합니다.

동일 repository가 있고 정상적으로 사용할 수 있으면 다시 clone하지 않고 해당 repository를 사용합니다.

기존 repository의 변경사항을 삭제하거나 다음과 같은 destructive operation을 실행하면 안 됩니다.

```text
git reset --hard
git clean -fd
git checkout -- .
```

## 3.2 기본 clone 위치

repository가 없는 경우 아래 위치를 기본값으로 사용합니다.

### macOS

```text
~/.local/share/mcp/Kiwoom-REST-API
```

### Windows

```text
%LOCALAPPDATA%\mcp\Kiwoom-REST-API
```

필요한 상위 directory를 생성한 후:

```bash
git clone https://github.com/Kiwoom-Securities/Kiwoom-REST-API <TARGET_PATH>
```

를 실행합니다.

clone 후 다음을 확인합니다.

```text
- directory가 존재한다.
- .git directory가 존재한다.
- git remote origin이 REPOSITORY_URL과 일치한다.
- mcp_spec/ 과 mcp_exec/ directory가 존재한다.
```

이미 기본 설치 directory가 존재하지만 다른 repository인 경우 그 directory를 삭제하거나 덮어쓰지 않습니다.

---

# Step 4. Repository 절대 경로 확정

clone된 repository의 실제 absolute path를 구합니다.

### macOS

```bash
cd <TARGET_PATH> && pwd
```

### Windows PowerShell

```powershell
(Get-Item <TARGET_PATH>).FullName
```

이 값을 이후부터 `<REPO_PATH>`로 사용하며, 설치 메타데이터 `ARGS`의 `{{REPO_PATH}}`를 이 값으로 치환합니다.

MCP config에는 `~`, `%USERPROFILE%`, `%LOCALAPPDATA%` 같은 상대적 표현보다 실제 absolute path를 우선 사용합니다. Windows는 `C:/Users/...` forward slash 표기를 사용합니다.

---

# Step 5. Dependency 설치

Step 0의 `<UV_PATH>`로 두 서버 directory에 대해 각각 실행합니다. `uv.lock`에 고정된
버전만 설치됩니다.

```bash
<UV_PATH> sync --frozen --directory <REPO_PATH>/mcp_spec
<UV_PATH> sync --frozen --directory <REPO_PATH>/mcp_exec
```

> **첫 sync는 시간이 걸립니다.** Python 3.13과 의존성(pandas 포함, 약 140MB)을 받아옵니다.
> 지금 미리 받아두기 때문에 클라이언트의 첫 기동이 timeout으로 죽지 않습니다.

---

# Step 6. MCP 실행 정의 생성

설치 메타데이터에 Step 4의 `<REPO_PATH>`와 Step 0의 `<UV_PATH>`를 적용한 최종 정의:

```text
server: kiwoom-spec
  transport: stdio
  command: <UV_PATH>
  args: ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_spec", "kiwoom-spec-mcp"]

server: kiwoom-exec
  transport: stdio
  command: <UV_PATH>
  args: ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_exec", "kiwoom-exec-mcp"]
  env:
    APP_KEY / APP_SECRET  ← placeholder로 두고 사용자가 직접 교체 (Step 9)
    KIWOOM_MODE = "demo"
```

이 정의를 이후 client별 config 형식으로 변환합니다.

---

# Step 7. Client별 MCP 설정

기본 설치 범위는 **현재 사용자의 모든 프로젝트에서 사용할 수 있는 user/global scope**입니다.

## 설정 위치

| Client | macOS | Windows | Format |
| --- | --- | --- | --- |
| Cursor | `~/.cursor/mcp.json` | `%USERPROFILE%\.cursor\mcp.json` | JSON |
| Claude Code | `~/.claude.json` | `%USERPROFILE%\.claude.json` | JSON |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` | `%APPDATA%\Claude\claude_desktop_config.json` | JSON |
| Antigravity | `~/.gemini/config/mcp_config.json` | `%USERPROFILE%\.gemini\config\mcp_config.json` | JSON |
| Codex | `~/.codex/config.toml` | `%USERPROFILE%\.codex\config.toml` | TOML |

설정 directory 또는 file이 없다면 생성합니다. 이미 파일이 있다면 **반드시 먼저 읽고** 기존 설정을 보존합니다.

**Step 1.2에서 주문 도구 켜기를 선택한 경우**, 아래 각 예시의 `kiwoom-exec` `env`에
`"KIWOOM_MCP_ALLOW_ORDERS": "1"`을 한 줄 추가합니다 (Codex는 `[mcp_servers.kiwoom_exec.env]`
table에 `KIWOOM_MCP_ALLOW_ORDERS = "1"`). 끄기를 선택했으면 이 항목을 **아예 넣지 않습니다.**

## 앱 키 전달 방식

`kiwoom-exec`의 `APP_KEY`/`APP_SECRET`은 **설정 파일에 사용자가 직접 입력**하는 것이
기본입니다. 다섯 client 모두 동일하게 동작하는 유일한 방법이고, 값은 MCP 서버
프로세스에만 전달됩니다.

- Agent는 아래 예시처럼 `your_app_key` / `your_app_secret` **placeholder 상태로 파일을
  만들어 두고**, 사용자에게 "파일을 열어 직접 값을 넣으라"고 안내합니다 (Step 9).
  Agent가 실제 값을 채우지 않습니다.
- 이 설정 파일들은 홈 디렉터리의 user-scope 파일입니다. **저장소 커밋·dotfiles 동기화·
  공유 금지**를 사용자에게 안내합니다.
- 값을 파일에 두고 싶지 않은 사용자를 위한 환경변수 참조 방식은 Step 9의 **대안** 항목에
  있습니다 (일부 client만 지원).

## 7.1 Cursor

`~/.cursor/mcp.json`의 `mcpServers`에 다음 두 server를 추가 또는 갱신합니다.

```json
{
  "mcpServers": {
    "kiwoom-spec": {
      "type": "stdio",
      "command": "<UV_PATH>",
      "args": ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_spec", "kiwoom-spec-mcp"]
    },
    "kiwoom-exec": {
      "type": "stdio",
      "command": "<UV_PATH>",
      "args": ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_exec", "kiwoom-exec-mcp"],
      "env": {
        "APP_KEY": "your_app_key",
        "APP_SECRET": "your_app_secret",
        "KIWOOM_MODE": "demo"
      }
    }
  }
}
```

기존 `mcpServers` 항목은 모두 유지합니다.

## 7.2 Claude Code

user scope 설정 파일 `~/.claude.json`의 top-level `mcpServers`에 다음 항목만 추가 또는 갱신합니다. **기존 파일 전체를 교체하지 않습니다** — 이 파일에는 MCP 외의 Claude 설정과 project 정보가 함께 들어 있습니다.

```json
{
  "mcpServers": {
    "kiwoom-spec": {
      "type": "stdio",
      "command": "<UV_PATH>",
      "args": ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_spec", "kiwoom-spec-mcp"]
    },
    "kiwoom-exec": {
      "type": "stdio",
      "command": "<UV_PATH>",
      "args": ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_exec", "kiwoom-exec-mcp"],
      "env": {
        "APP_KEY": "your_app_key",
        "APP_SECRET": "your_app_secret",
        "KIWOOM_MODE": "demo"
      }
    }
  }
}
```

`claude` 명령이 사용 가능하면 직접 편집 대신 아래가 더 안전합니다 (merge를 CLI가 처리).
앱 키를 명령 인자로 넣지 않도록 `-e`에는 placeholder를 그대로 둡니다 — 실제 값은
등록 후 사용자가 `~/.claude.json`에서 교체합니다.

```bash
claude mcp add kiwoom-spec -s user -- <UV_PATH> run --frozen --directory <REPO_PATH>/mcp_spec kiwoom-spec-mcp
claude mcp add kiwoom-exec -s user -e KIWOOM_MODE=demo -e APP_KEY=your_app_key -e APP_SECRET=your_app_secret -- <UV_PATH> run --frozen --directory <REPO_PATH>/mcp_exec kiwoom-exec-mcp
```

설정 후 등록 상태를 확인합니다.

```bash
claude mcp list
```

이 명령의 성공은 **등록 확인일 뿐 최종 설치 검증이 아닙니다.** 최종 검증은 Step 10의 `tools/list`입니다.

## 7.3 Claude Desktop

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

`mcpServers`에 다음 항목만 추가 또는 갱신합니다.

```json
{
  "mcpServers": {
    "kiwoom-spec": {
      "command": "<UV_PATH>",
      "args": ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_spec", "kiwoom-spec-mcp"]
    },
    "kiwoom-exec": {
      "command": "<UV_PATH>",
      "args": ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_exec", "kiwoom-exec-mcp"],
      "env": {
        "APP_KEY": "your_app_key",
        "APP_SECRET": "your_app_secret",
        "KIWOOM_MODE": "demo"
      }
    }
  }
}
```

`your_app_key` / `your_app_secret`은 **사용자가 직접** 실제 값으로 바꿉니다 (Step 9). 이 파일은 저장소에 커밋하지 않도록 안내합니다.

기존 MCP server는 모두 유지합니다. 설정 변경 후 Claude Desktop을 **완전히 종료했다 다시 실행**해야 반영됩니다.

## 7.4 Antigravity

- macOS: `~/.gemini/config/mcp_config.json`
- Windows: `%USERPROFILE%\.gemini\config\mcp_config.json`

(IDE에서는 Settings → Customizations → **Open MCP Config**로 열 수 있습니다.)

7.3 Claude Desktop과 동일한 JSON을 `mcpServers`에 추가 또는 갱신합니다 — `your_app_key` placeholder 방식도 동일합니다. 기존 server는 모두 유지합니다.

## 7.5 Codex

Codex는 JSON이 아니라 TOML을 사용합니다. server 이름은 TOML 키 경로 파싱 때문에 하이픈 대신 **밑줄**을 씁니다.

`~/.codex/config.toml`에 다음 MCP table을 추가 또는 갱신합니다.

```toml
[mcp_servers.kiwoom_spec]
command = "<UV_PATH>"
args = ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_spec", "kiwoom-spec-mcp"]

[mcp_servers.kiwoom_exec]
command = "<UV_PATH>"
args = ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_exec", "kiwoom-exec-mcp"]

[mcp_servers.kiwoom_exec.env]
APP_KEY = "your_app_key"
APP_SECRET = "your_app_secret"
KIWOOM_MODE = "demo"
```

`your_app_key` / `your_app_secret`은 **사용자가 직접** 실제 값으로 바꿉니다 (Step 9).

기존 `config.toml`의 model, sandbox, approval, profile 및 다른 MCP 설정은 모두 보존합니다.

설정 후 `codex mcp list`로 등록 여부를 확인할 수 있습니다. 이 역시 최종 설치 검증은 아닙니다.

---

# Step 8. Config merge 규칙

JSON 설정 파일을 수정할 때 반드시 다음 방식으로 처리합니다.

```text
1. 기존 파일 읽기
2. JSON parse
3. mcpServers가 없으면 생성
4. mcpServers["kiwoom-spec"], mcpServers["kiwoom-exec"]만 upsert
5. 나머지 key 그대로 유지
6. JSON serialize
7. 다시 parse하여 syntax 검증
8. 저장
```

절대로 전체 config를 예제 JSON으로 덮어쓰지 않습니다.

TOML도 동일한 원칙을 적용합니다.

```text
1. 기존 config.toml 읽기
2. 기존 설정 보존
3. [mcp_servers.kiwoom_spec] / [mcp_servers.kiwoom_exec]만 추가 또는 갱신
4. TOML syntax 확인
5. 저장
```

---

# Step 9. 인증정보 처리

`kiwoom-exec`는 조회 실행에 키움 앱 키가 필요합니다. **단, Step 10의 `tools/list` 검증에는 앱 키가 필요 없습니다** — 서버는 키 없이 기동하고, 자격증명은 실제 조회 시점에만 씁니다. 따라서 앱 키가 아직 없어도 설치 검증은 그대로 진행합니다.

Agent는 다음을 해서는 안 됩니다.

```text
- 앱 키 값을 사용자에게 요청
- secret 값을 채팅에 입력하도록 요청
- credential을 대신 config에 기록
- credential을 로그에 출력
- .env 파일이나 keychain을 읽어 credential 값을 확인
```

앱 키는 [키움증권 개발자센터](https://openapi.kiwoom.com)에서 발급받습니다. **모의투자(demo)와 실전투자(real)는 서로 다른 키**이며, `KIWOOM_MODE`와 짝이 맞아야 합니다. 먼저 demo 키로 시작하기를 권합니다.

## 9.1 기본 — 설정 파일에 직접 입력

사용자에게 다음을 안내합니다.

> Step 7에서 만든 설정 파일(`<CONFIG_PATH>`)을 열어 `your_app_key` / `your_app_secret`을
> 발급받은 실제 값으로 바꾼 뒤 저장하세요. 실제 키 값은 채팅에 입력하지 마세요.

함께 안내할 주의사항:

```text
- 이 파일을 저장소에 커밋하거나 dotfiles로 동기화하거나 남에게 공유하지 않는다.
- 값 교체 후 client를 재시작해야 반영된다 (Step 11).
```

사용자가 교체 완료했다고 확인하면 계속 진행합니다.

## 9.2 대안 — 환경변수 참조 (일부 client만)

설정 파일에 값을 두고 싶지 않은 사용자에게만 안내합니다. **지원 client가 제한적입니다** —
Claude Desktop과 Antigravity는 `${...}` 확장을 지원하지 않아 이 방식을 쓸 수 없습니다
(Claude Desktop은 GUI 앱이라 shell 환경변수도 상속하지 않습니다).

| Client | Step 7 예시의 `your_app_key` 자리를 이렇게 교체 |
| --- | --- |
| Claude Code | `"${APP_KEY}"` |
| Cursor | `"${env:APP_KEY}"` |
| Codex | `env` table에서 두 키를 지우고 `env_vars = ["APP_KEY", "APP_SECRET"]` 추가 |

환경변수 설정은 사용자가 직접 합니다. 아래 명령을 **제시만** 합니다 (Agent가 실행하지
않고, `your_app_key`도 채우지 않습니다).

### macOS / Linux

```bash
echo 'export APP_KEY="your_app_key"' >> ~/.zshrc
echo 'export APP_SECRET="your_app_secret"' >> ~/.zshrc
source ~/.zshrc
```

### Windows PowerShell

```powershell
[System.Environment]::SetEnvironmentVariable("APP_KEY", "your_app_key", "User")
[System.Environment]::SetEnvironmentVariable("APP_SECRET", "your_app_secret", "User")
```

> 설정 후 터미널과 client를 재시작해야 반영됩니다. GUI에서 실행한 client는 shell
> 환경변수를 못 볼 수 있습니다 — 안 되면 9.1로 돌아갑니다.

---

# Step 10. MCP Protocol 설치 검증

> **이 단계까지 성공해야 설치 완료입니다.**

다음은 설치 성공으로 간주하지 않습니다.

```text
repository clone 성공
dependency 설치 성공
config 파일 생성 성공
client에 server 이름 표시
MCP process 실행 성공
```

최소 설치 완료 조건은 **두 서버 각각**에 대해:

```text
MCP initialize
→ tools/list
→ tools 배열 반환
```

입니다.

## 10.1 실제 설정과 동일한 server definition 사용

검증할 때 별도의 임의 command를 만들지 않습니다. MCP config에 기록한 것과 동일한 `command` / `args`를 사용합니다. `kiwoom-exec`의 검증에는 `env`가 필요 없습니다 (앱 키 없이 tools/list가 동작).

## 10.2 방법 A — uv 내장 검증 (기본, 추가 설치 불필요)

Node.js 등 어떤 추가 runtime도 요구하지 않습니다 — Step 0에서 준비한 uv만 씁니다.
아래 스크립트를 **임시 파일**(예: `verify_tools_list.py`)로 저장합니다. 표준 라이브러리만
사용하며, initialize → tools/list를 수행하고 10.3의 성공 조건까지 스스로 판정합니다
(성공 시 exit 0, 실패 시 비0).

```python
"""MCP stdio tools/list verifier — stdlib only (Node/npx 불필요).

Usage: python verify_tools_list.py <EXPECTED_TOOL> -- <server command> [args...]
Exit 0 = tools/list 성공 AND tools.length > 0 AND EXPECTED_TOOL 존재.
"""
import json
import subprocess
import sys
import threading


def main() -> int:
    sep = sys.argv.index("--")
    expected, cmd = sys.argv[1], sys.argv[sep + 1 :]
    proc = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
    )
    timer = threading.Timer(120, proc.kill)
    timer.daemon = True  # FAIL 경로에서도 즉시 종료되게 (non-daemon이면 120s를 기다린다)
    timer.start()

    def send(msg: dict) -> None:
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()

    def recv(want_id: int) -> dict:
        while True:
            line = proc.stdout.readline()
            if not line:
                raise SystemExit("FAIL: server closed stdout before responding")
            try:
                msg = json.loads(line)
            except ValueError:
                continue  # 프로토콜 외 출력은 무시
            if msg.get("id") == want_id:
                if "error" in msg:
                    raise SystemExit(f"FAIL: MCP error: {msg['error']}")
                return msg["result"]

    send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "setup-verify", "version": "0"}}})
    recv(1)
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools = [t["name"] for t in recv(2)["tools"]]
    timer.cancel()
    proc.terminate()

    found = expected in tools
    print(json.dumps({"tools": tools, "count": len(tools),
                      "expected_tool": expected, "found": found}, ensure_ascii=False))
    return 0 if tools and found else 1


if __name__ == "__main__":
    sys.exit(main())
```

두 서버를 각각 검증합니다. Step 5에서 만든 venv의 python을 uv가 그대로 재사용하므로
추가 다운로드가 없습니다.

```bash
<UV_PATH> run --frozen --directory <REPO_PATH>/mcp_spec python verify_tools_list.py spec_search -- \
  <UV_PATH> run --frozen --directory <REPO_PATH>/mcp_spec kiwoom-spec-mcp

<UV_PATH> run --frozen --directory <REPO_PATH>/mcp_exec python verify_tools_list.py kiwoom_query -- \
  <UV_PATH> run --frozen --directory <REPO_PATH>/mcp_exec kiwoom-exec-mcp
```

각 명령의 exit code가 0이고 출력의 `"found": true`이면 그 서버는 검증 성공입니다.
임시 스크립트는 완료 후 삭제합니다.

## 10.2-B 방법 B — MCP Inspector (Node.js가 이미 있는 환경)

`node`/`npx`가 이미 설치된 환경에서는 공식 MCP Inspector CLI를 써도 됩니다.
검증용 임시 JSON config를 생성합니다. **이 파일에 secret 값을 기록하지 않습니다.**

```json
{
  "mcpServers": {
    "kiwoom-spec": {
      "command": "<UV_PATH>",
      "args": ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_spec", "kiwoom-spec-mcp"]
    },
    "kiwoom-exec": {
      "command": "<UV_PATH>",
      "args": ["run", "--frozen", "--directory", "<REPO_PATH>/mcp_exec", "kiwoom-exec-mcp"]
    }
  }
}
```

```bash
npx -y @modelcontextprotocol/inspector --cli \
  --config <TEMP_MCP_CONFIG_PATH> --server kiwoom-spec --method tools/list

npx -y @modelcontextprotocol/inspector --cli \
  --config <TEMP_MCP_CONFIG_PATH> --server kiwoom-exec --method tools/list
```

Inspector는 tools 배열만 돌려주므로 10.3의 성공 조건은 Agent가 직접 판정합니다.
검증용 임시 config는 완료 후 삭제합니다.

> **Node.js가 없다고 설치하지 마세요.** 방법 A가 같은 protocol-level 검증을 추가 설치
> 없이 수행합니다. 어떤 방법을 쓰든 **실제 MCP `tools/list`가 실행되어야 합니다.**

## 10.3 성공 조건

`tools/list` 결과가 MCP error 없이 반환되고 `tools.length > 0`이어야 하며, EXPECTED_TOOL이 존재해야 합니다.

```text
kiwoom-spec : "spec_search" 존재   (전체 4개: spec_search, spec_show, spec_groups, get_example)
kiwoom-exec : "kiwoom_query" 존재
  주문 도구 끄기(기본) : 정확히 3개 — kiwoom_commands, kiwoom_help, kiwoom_query
  주문 도구 켜기       : 정확히 5개 — 위 3개 + kiwoom_order_preview, kiwoom_order_submit
```

논리적 검증 조건 (두 서버 모두):

```text
tools/list succeeded
AND tools.length > 0
AND EXPECTED_TOOL exists
```

> exec의 도구 수가 Step 1.2의 선택과 다르면(끄기인데 5개, 켜기인데 3개) `KIWOOM_MCP_ALLOW_ORDERS` 설정을 확인하고 사용자에게 알립니다. 그 외의 도구가 보이면 `KIWOOM_MCP_DEBUG_HEADERS` 등 다른 게이트 env가 켜져 있는 것입니다.

## 10.4 검증 범위

설치 검증은 `tools/list`에서 종료합니다. 다음은 실행하지 않습니다.

```text
tools/call
실제 시세·계좌 조회
실제 주문·거래
파일 변경
기타 destructive operation
```

Tool 목록을 조회하는 것만으로 설치를 검증합니다.

---

# Step 11. Client reload

protocol-level `tools/list` 검증이 성공한 뒤 해당 client가 새로운 MCP config를 읽도록 합니다.

필요한 경우 사용자에게 다음을 안내합니다.

### Cursor

새 agent session을 시작하거나 MCP 설정을 reload합니다.
Settings → MCP에서 `kiwoom-spec` / `kiwoom-exec`가 초록 상태인지 확인할 수 있습니다.

### Claude Code

새 Claude Code session을 시작합니다.

```bash
claude mcp list
```

로 `✔ Connected` 2건(kiwoom-spec, kiwoom-exec)을 확인할 수 있습니다.

### Claude Desktop

Claude Desktop을 **완전히 종료한 뒤** 다시 실행합니다. 창을 닫는 것만으로는 종료되지
않습니다 — macOS는 메뉴바에서 Quit(Cmd+Q), Windows는 시스템 트레이 아이콘에서 종료합니다.

placeholder(`your_app_key`)를 아직 실제 값으로 바꾸지 않았다면, 재시작 후 도구 목록은
뜨지만 실제 조회만 인증 오류가 납니다 — 정상이며, 값을 채운 뒤 한 번 더 재시작합니다.

### Antigravity

MCP configuration을 reload하거나 새 agent session을 시작합니다.
Settings → Customizations의 MCP 패널에서 서버 상태를 확인할 수 있습니다.

### Codex

Codex CLI는 새 session을 시작합니다. IDE extension을 사용하는 경우 extension을
restart합니다. `codex mcp list`로 등록 상태를 확인할 수 있습니다.

> 어느 client든 첫 기동은 Step 5에서 dependency를 미리 받아뒀으므로 빠르게 끝납니다.

reload 후 사용자가 바로 써볼 수 있는 예시를 안내합니다.

```text
앱 키 없이  : "일봉 차트 조회하는 키움 API 찾아줘"        (spec)
             "키움에서 조회할 수 있는 명령 목록 보여줘"     (exec, 키움 미호출)
앱 키 필요  : "삼성전자 현재가 알려줘"                     (exec, 실제 조회)
```

---

# Step 12. 최종 결과 보고

모든 과정이 끝나면 사용자에게 다음 형식으로 간단히 보고합니다.

```text
키움 MCP 로컬 설치 완료

Client: <SELECTED_CLIENT>
OS: <OS>
Repository: <REPO_PATH>
Config: <CONFIG_PATH>
Servers: kiwoom-spec, kiwoom-exec
주문 도구: <켜짐|꺼짐(기본)> (Step 1.2 선택)

Verification:
- config parse: OK
- MCP initialize: OK (spec, exec)
- tools/list: OK (spec, exec)
- tools discovered: spec <COUNT> / exec <COUNT>
- expected tool "spec_search": FOUND
- expected tool "kiwoom_query": FOUND

남은 일 (사용자):
- 설정 파일의 your_app_key / your_app_secret을 실제 값으로 교체 (Step 9.1, 미완료 시)
- client 재시작
```

`tools/list`가 실패했다면 **설치 완료라고 보고하면 안 됩니다.**

---

# Troubleshooting

## Repository clone 실패

확인: git 설치 여부, GitHub 접근 가능 여부, repository URL. 기존 사용자 repository나 파일을 삭제해 문제를 해결하지 않습니다.

## command not found: uv

macOS `command -v uv` / Windows `(Get-Command uv).Source`로 경로를 확인하고, 없으면 기본 설치 위치(`~/.local/bin/uv`, `%USERPROFILE%\.local\bin\uv.exe`)를 봅니다. GUI client는 shell의 PATH를 상속하지 않으므로 config의 `command`에는 반드시 uv의 **absolute path**를 사용합니다 (Step 0.2).

## MCP process immediately exits

동일한 command를 직접 실행해 stderr를 확인합니다.

```bash
<UV_PATH> run --frozen --directory <REPO_PATH>/mcp_exec kiwoom-exec-mcp
```

확인 대상:

```text
- repository absolute path가 정확한가 (--directory 값)
- uv sync --frozen이 성공했는가
- Python 3.13을 uv가 받을 수 있는 네트워크 환경인가
```

주의: `mcp_exec/src/.../server.py`를 python으로 직접 실행하지 않습니다 — `src/` 패키지 구조라 상대 import가 깨집니다. 반드시 콘솔 스크립트(`kiwoom-exec-mcp`) 형태로 실행합니다.

## tools/list는 되는데 실제 조회에서 `인증에 실패했습니다[8001...]`

앱 키/시크릿이 틀렸거나, 모의투자 키를 `real`로(또는 그 반대로) 쓰고 있습니다. `KIWOOM_MODE`와 키의 짝을 확인하도록 안내합니다. 설치 문제가 아닙니다.

## 앱 키가 `${APP_KEY}` 문자열 그대로 서버에 전달됨

9.2 대안(환경변수 참조)을 쓰는 중인데 그 client가 `${...}` 확장을 지원하지 않는
경우입니다 (Claude Desktop, Antigravity). 9.1 기본 방식(직접 입력)으로 전환합니다.

## 주문 도구만 안 보인다

Step 1.2에서 끄기를 선택했다면 이것은 오류가 아니라 의도된 상태입니다. 켜기를 선택했는데
안 보인다면 `KIWOOM_MCP_ALLOW_ORDERS`가 **정확히 `1`** 인지 확인합니다.

## JSON / TOML parse 실패

기존 config를 복구한 뒤 kiwoom server entry만 다시 merge합니다. 기존 파일 전체를 예제 config로 교체하지 않습니다.

## `tools/list` 연결 실패

다음 순서로 확인합니다.

```text
1. configured command (uv absolute path)
2. repository absolute path
3. arguments (mcp_spec / mcp_exec directory)
4. uv sync --frozen 성공 여부
5. server stderr
```

수정 후 다시 `initialize → tools/list`를 수행합니다.

---

# Definition of Done

아래 조건을 **모두 만족해야 설치 완료**입니다.

* [ ] 사용자가 설치 대상 MCP client를 선택했다.
* [ ] Agent가 선택된 client를 명확히 확정했다.
* [ ] 주문 도구 활성화 여부를 사용자에게 물었고, 선택(기본: 끄기)이 config와 tools/list 결과에 그대로 반영됐다.
* [ ] 운영체제를 확인했다.
* [ ] GitHub repository가 로컬에 준비됐다 (`mcp_spec/`·`mcp_exec/` 존재 확인 포함).
* [ ] repository absolute path를 확인했다.
* [ ] uv의 absolute path(`<UV_PATH>`)를 확정했고 두 서버의 `sync --frozen`이 성공했다.
* [ ] 실제 MCP command와 args를 확정했다.
* [ ] 기존 client config를 보존했다.
* [ ] `kiwoom-spec` / `kiwoom-exec` 설정만 추가 또는 갱신했다.
* [ ] JSON 또는 TOML syntax가 정상이다.
* [ ] 두 서버 모두 MCP initialize handshake가 성공했다.
* [ ] 두 서버 모두 실제 MCP `tools/list` 요청이 성공했다.
* [ ] `spec_search`와 `kiwoom_query`가 각 tool 목록에서 확인됐다.
* [ ] 앱 키 값을 묻지도, 읽지도, 기록하지도 않았다.
* [ ] 설치 검증을 위해 `tools/call` 또는 destructive operation을 실행하지 않았다.

**`tools/list` 성공 전에는 설치 완료라고 보고하지 않습니다.**
