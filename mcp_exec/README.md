# 키움증권 Exec MCP (Kiwoom Exec MCP)

`kiwoom-exec-mcp`는 실제 키움증권 OpenAPI 조회·주문을 실행하는 MCP(Model Context Protocol) 서버입니다. AI 에이전트가 계좌를 조회하거나(읽기), 운영자가 명시적으로 허용한 경우에만 주문을 전송하도록(쓰기, 사람 승인 전제) 설계됐습니다.

API를 찾고 예제 코드를 확인하는 건 `kiwoom-spec-mcp`가 담당합니다. 이 서버의 `command_path` 인자는 `spec_search` 결과나 `kiwoom_commands` 목록에서 그대로 가져다 쓸 수 있습니다.

배포 패키지 이름은 `kiwoom-exec-mcp`이며, 콘솔 명령도 동일합니다. 지원하는 명령 범위는 서버 업데이트에 따라 늘어날 수 있습니다.

## 설치 · 로컬 실행

```sh
cd mcp_exec
uv sync --frozen
uv run kiwoom-exec-mcp   # 기본 전송: stdio
```

- `--frozen`은 `uv.lock`에 고정된 버전만 쓰게 해 기동을 빠르고 재현 가능하게 합니다.
- 원격(streamable HTTP)은 `KIWOOM_MCP_TRANSPORT=http`로 켭니다(포트는 `KIWOOM_MCP_PORT` > `PORT` > 기본 8000). 자격증명은 요청 헤더 `x-kiwoom-app-key` / `x-kiwoom-app-secret` / `x-kiwoom-mode`로 받습니다. 로컬 stdio 사용에는 도커가 필요 없습니다.

## 인증 설정

로컬 stdio에서는 자격증명을 **MCP 클라이언트 설정의 `env`로만** 주입합니다. 도구 인자로 키를 받는 방식은 쓰지 않습니다 — 도구 인자는 대화 트랜스크립트에 평문으로 남기 때문입니다.

키 이름은 mode와 무관하게 항상 `APP_KEY`/`APP_SECRET`이고, demo(모의투자)/real(실전)은 `KIWOOM_MODE` 한 줄로 구분합니다. 모의투자와 실전 앱키는 키움증권 개발자센터에서 **따로 발급**되므로, mode에 맞는 키를 넣어야 합니다. `kiwoomcli setup`을 마친 머신에서는 키 대신 `KIWOOM_PROFILE=<별칭>`으로 대체할 수 있습니다.

**demo (모의투자)**:

```json
{
  "mcpServers": {
    "kiwoom-exec": {
      "command": "uv",
      "args": ["run", "--frozen", "--directory", "/path/to/mcp_exec", "kiwoom-exec-mcp"],
      "env": {
        "KIWOOM_MODE": "demo",
        "APP_KEY": "<모의투자 앱키>",
        "APP_SECRET": "<모의투자 시크릿>",
        "KIWOOM_MCP_ALLOW_ORDERS": "0"
      }
    }
  }
}
```

**real (실전)** — `KIWOOM_MODE` 값과 키만 실전용으로 바꿉니다:

```json
      "env": {
        "KIWOOM_MODE": "real",
        "APP_KEY": "<실전 앱키>",
        "APP_SECRET": "<실전 시크릿>"
      }
```

`env`를 비워두면 로컬 환경에 이미 설정된 자격증명으로 폴백할 수 있는데, 그게 실전 계좌일 수 있으니 항상 위처럼 명시적으로 지정하는 걸 권장합니다.

`KIWOOM_MCP_ALLOW_ORDERS`는 **정확히 `"1"`일 때만** 주문 도구 2개가 등록됩니다. `"true"`/`"TRUE"`/`"yes"`는 참으로 해석되지 않고 **전부 off**입니다(값을 지운 `""`나 키 자체를 뺀 것과 동일). 위 config처럼 `"0"`으로 미리 넣어두면 안전하게 off인 상태로 토글이 보이고, 실제로 쓸 때만 `"1"`로 바꾸면 됩니다.

## 제공 도구

| 도구 | 정책 | 역할 |
| --- | --- | --- |
| `kiwoom_commands(market, group)` | — | 실행 가능한 command_path 목록(market/group 필터) |
| `kiwoom_help(command_path)` | — | 명령 옵션 계약 확인 |
| `kiwoom_query(command_path, options)` | 조회만 | 조회 실행, JSON 형식 고정. 계좌번호는 정책에 따라 자동 마스킹됩니다 |
| `kiwoom_order_preview(...)` | 주문(env 게이트) | 미전송 주문 확인. `options`에는 주문 인자만 넣고 `confirm`/`profile`/`mode`는 넣지 마세요 |
| `kiwoom_order_submit(..., confirm)` | 주문(env 게이트) | 최상위 `confirm=true`일 때만 실제로 전송 |
| `kiwoom_debug_headers()` | 진단(env 게이트) | 도착 헤더의 이름·길이만 반환(값은 반환하지 않음). `KIWOOM_MCP_DEBUG_HEADERS=1`일 때만 등록 |

주문 도구 2개는 `KIWOOM_MCP_ALLOW_ORDERS=1`일 때만 존재합니다. 이 값을 주지 않은 설정에는 주문 표면 자체가 없습니다.

## 주문 안전장치

- `kiwoom_order_submit`은 최상위 `confirm=true`를 명시적으로 넘겨야 실제 전송하며, 넘기지 않으면 미전송 안내만 돌아옵니다.
- 국내·해외 주문 쓰기는 모두 `confirm=true`로 실전송됩니다.
- `confirm`은 **호출자(AI 포함)가 설정할 수 있는 값입니다.** 사람의 실제 승인은 MCP 클라이언트의 도구 실행 승인 UI에 의존합니다 — 주문을 자동 승인하도록 클라이언트를 설정하지 마세요.
- `options` dict는 CLI 플래그로 그대로 변환됩니다. `confirm`/`profile`/`mode`를 `options`에 넣지 마세요.
- 실제 자금이 오가기 전에는 항상 demo(모의투자) 모드에서 먼저 확인하세요.

## 환경 변수

정수 항목에 숫자가 아닌 값을 넣으면 기동 시 실패합니다. 게이트(`ALLOW_ORDERS`, `DEBUG_HEADERS`)는 값이 **정확히 `1`일 때만** 켜집니다.

| 변수 | 기본 | 역할 |
| --- | --- | --- |
| `KIWOOM_MODE` | (stdio) | `demo` 또는 `real`. HTTP 헤더 `x-kiwoom-mode`가 있으면 요청값이 이김 |
| `APP_KEY` / `APP_SECRET` | (stdio) | 키움 앱키·시크릿. demo여도 이 이름을 쓰고, 서버가 `_MOCK` 이름으로 매핑 |
| `KIWOOM_PROFILE` | (stdio) | `kiwoomcli setup` 별칭. 키 대신 쓸 수 있음 |
| `KIWOOM_MCP_TRANSPORT` | `stdio` | `stdio` 또는 `http`(streamable HTTP) |
| `KIWOOM_MCP_HOST` | `127.0.0.1` | HTTP 바인드 주소 |
| `KIWOOM_MCP_PORT` | `8000` | HTTP 포트. `KIWOOM_MCP_PORT` > `PORT` > 기본값 |
| `KIWOOM_MCP_ALLOW_ORDERS` | off | `1`이면 주문 도구 2개 등록 |
| `KIWOOM_MCP_DEBUG_HEADERS` | off | `1`이면 `kiwoom_debug_headers` 등록 |
| `KIWOOM_MCP_MAX_CONCURRENCY` | `8` | 동시 `kiwoomcli` subprocess 상한 |
| `KIWOOM_MCP_TOKEN_TTL` | `900` | HTTP 경로에서 서버 RAM에 두는 접근 토큰 상한(초). `0`=요청마다 발급. 디스크에 쓰지 않음 |
| `KIWOOM_MCP_RATELIMIT` | `0`(off) | HTTP, 윈도우당 최대 요청 / IP |
| `KIWOOM_MCP_RATELIMIT_APPKEY` | `0`(off) | HTTP, 윈도우당 최대 요청 / AppKey 지문 |
| `KIWOOM_MCP_RATELIMIT_WINDOW` | `60` | rate limit 윈도우(초). 두 축이 공유 |

HTTP rate limit 두 축은 함께 켜야 의미가 있습니다. 한쪽만 켜면 우회됩니다.

## 안전 유의사항

- 키/시크릿을 도구 인자로 넘기는 방식은 지원하지 않으며, 앞으로도 추가되지 않습니다. 인증은 항상 `env`(또는 원격 배포의 요청 헤더)로만 이뤄집니다.
- 자격 증명, 토큰, 계좌번호가 포함된 원본 응답을 로그로 남기거나 커밋하지 마세요.
- 자격 증명·네트워크·계좌 안전 제약으로 호출이 막히면, 서버는 결과를 지어내지 않고 오류(`error` 필드)로 보고합니다.

## 알려진 제약

이 서버는 `kiwoomcli`를 그대로 호출하므로, 아래 제약은 키움 API 자체의 제약이며 `command_path`를 바꿔도 피할 수 없습니다.

- `command_path`가 `overseas orders cancel`이면 전량만 취소되고, `overseas orders modify`는 수량은 바꿀 수 없고 가격만 바꿀 수 있습니다(원주문이 STOP이면 `stop_price` 필수). 국내 취소(`domestic orders cancel`)는 `qty` 옵션으로 부분 취소가 가능합니다.
- `overseas accounts open-orders`는 `code` 없이 `exchange`만 넘기는 조회를 지원하지 않습니다(서버 제약) — 종목을 특정하지 않을 때는 `exchange`를 빼고 전체로 조회하세요.
- 너무 짧은 간격으로 `kiwoom_query`를 반복 호출하면 유량 제한(429) 오류가 날 수 있습니다.
- 모의투자(demo) 모드에서는 환율 조회, 주문가능금액 조회가 거절됩니다.
- 프로필/계좌마다 거래 가능한 시장이 다를 수 있습니다. 해당 계좌가 다루지 않는 시장은 주문이 거절되거나 조회 결과가 빈 목록으로 돌아올 수 있습니다 — 결과가 비어 있다면 먼저 `KIWOOM_PROFILE`/`KIWOOM_MODE`로 선택한 계좌를 확인하세요.
- 현재가 조회(`domestic quotes price`) 응답에는 전일대비 값이 직접 포함되어 있지 않습니다 — 현재가와 전일 종가의 차이로 직접 계산해야 합니다.
