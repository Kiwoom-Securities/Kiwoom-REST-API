# Kiwoom MCP 설치 안내 (Claude Desktop, `.mcpb`)

이 폴더에는 키움 MCP 서버(`mcp_exec/`, `mcp_spec/`)를 **Claude Desktop**에
설치하는 사전 빌드 `.mcpb` 번들이 들어 있습니다. Claude Code, Codex 등
CLI로 동작하는 MCP 클라이언트를 쓴다면 이 문서 대신
[NOTICE_MCP_CLI_INSTALLER.md](./NOTICE_MCP_CLI_INSTALLER.md)를 참고하세요.

## 포함된 서버 (공통)

두 설치 방법 모두 같은 서버 두 개를 대상으로 합니다.

| 서버 | 역할 | 자격증명 |
| --- | --- | --- |
| `kiwoom-spec-mcp` | API 검색·명세·예제 코드 조회 | 불필요 |
| `kiwoom-exec-mcp` | 시세·계좌 조회, 주문 | 필요 |

두 서버를 모두 설치해도 되고, 필요한 것만 골라 설치해도 됩니다. `spec`
서버로 API를 찾고 예제를 확인한 뒤, 실제 조회·주문은 `exec` 서버로 실행하는
구성을 권장합니다.

---

## Claude Desktop 설치 (`.mcpb`)

`mcp_exec/`, `mcp_spec/`의 소스코드를 미리 packing해 둔 사전 빌드 번들입니다.
클라이언트 설정 JSON을 손으로 작성하지 않아도 Claude Desktop에서 바로 사용할
수 있습니다.

### 요구 사항

- **Claude Desktop** (최신 버전, macOS 또는 Windows). Linux는 지원하지
  않습니다.
- **Python 3.13 이상**과 **uv**가 시스템에 미리 설치되어 있어야 합니다.
  Claude Desktop은 Node.js 런타임은 내장하고 있지만 Python/uv는 내장하지
  않습니다 — 시스템에 Python이 없으면 설치 자체가 막히거나, 설치는 되어도
  도구 목록이 비어 보이는 등 조용히 실패할 수 있습니다.
  - Python 확인: `python3 --version`(Windows는 `py --version`). 없으면
    [python.org](https://www.python.org/downloads/) 또는 `brew install
    python@3.13`으로 설치하세요.
  - uv 확인: `uv --version`. 없으면 `curl -LsSf
    https://astral.sh/uv/install.sh | sh`(macOS/Linux) 또는
    `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`(Windows)로
    설치하세요. 설치 후 새 터미널(또는 재부팅)이 필요할 수 있습니다.
- 최초 실행 시 uv가 나머지 의존성을 내려받습니다 — 인터넷 연결이 필요하고,
  kwcli가 pandas·numpy를 물고 있어 약 140MB, 수십 초가 걸릴 수 있습니다.
  이후 실행부터는 빠릅니다.

### 설치 방법

1. 이 폴더에서 설치할 `.mcpb` 파일을 로컬에 내려받습니다.
2. 아래 세 가지 방법 중 하나로 설치합니다.
   - **더블클릭**: 내려받은 `.mcpb` 파일을 더블클릭하면 Claude Desktop이
     실행되며 설치 화면이 뜹니다(가장 간단한 방법).
   - **드래그 앤 드롭**: 파일 탐색기에서 `.mcpb` 파일을 실행 중인 Claude
     Desktop 창으로 끌어다 놓습니다.
   - **설정 메뉴**: Claude Desktop을 열고 **설정** → **확장 프로그램**
     탭으로 이동한 뒤, **고급 설정**을 클릭하고 **확장 프로그램 개발자**
     섹션에서 **확장 프로그램 설치...**를 눌러 `.mcpb` 파일을 선택합니다.
3. 설치 화면에 표시되는 입력 필드를 채웁니다.
   - **`kiwoom-spec-mcp`**: 입력할 필드가 없습니다. 설치만 하면 바로
     사용할 수 있습니다.
   - **`kiwoom-exec-mcp`**: 아래 필드를 채웁니다.
     - **App Key** / **App Secret**: 키움증권 개발자센터에서 발급한 값.
       화면에 그대로 표시되지 않는 보안 입력란입니다.
     - **계좌 종류 - demo/real**: 기본값은 `demo`(모의투자)입니다. 운영
       계좌를 쓰려면 `real`로 바꾸고, 그에 맞는 App Key/Secret을
       입력하세요. 모의투자와 실전 앱키는 **따로 발급**됩니다.
     - **주문 도구 활성화 여부 (1 = 켬)**: 기본값은 `0`(꺼짐, 조회만
       가능)입니다. 주문 도구가 필요할 때만 `1`로 바꾸세요.
4. 설치를 마치면 대화창에서 바로 도구를 쓸 수 있습니다. 도구가 보이지
   않으면 Claude Desktop을 재시작하세요. 재시작 후에도 도구가 하나도
   안 보이거나 호출할 때 오류가 나면, 시스템에 Python 3.13+/uv가 제대로
   설치되어 있는지("요구 사항" 참고) 다시 확인하세요 — 설치는 되어도
   런타임을 못 찾으면 조용히 실패할 수 있습니다.

### 안전 유의사항

- App Key/Secret은 **설치 화면의 입력란에만** 입력하세요. 대화창에 텍스트로
  붙여넣지 마세요 — 대화 기록에 평문으로 남습니다.
- 실제 자금이 오가기 전에는 항상 `demo`(모의투자)로 먼저 확인하세요.
- 주문 도구를 켜더라도 `kiwoom_order_submit`은 `confirm=true`를 명시적으로
  받아야 실제 전송됩니다. 사람의 승인은 Claude Desktop의 도구 실행 승인
  대화상자에 의존하므로, 도구 실행을 자동 승인하도록 설정하지 마세요.
- 계좌 종류(`demo`/`real`)와 주문 활성화 여부는 설치 후에도 확장 설정
  화면에서 다시 바꿀 수 있습니다.

### 버전과 업데이트

`.mcpb`에는 자동 업데이트 기능이 없습니다. 새 버전이 나오면 이 폴더의 새
`.mcpb` 파일을 다시 받아 같은 방식으로 설치하세요(기존 확장을 지우지 않아도
같은 이름의 확장은 덮어 설치됩니다).
