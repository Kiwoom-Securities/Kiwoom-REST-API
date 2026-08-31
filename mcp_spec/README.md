# 키움증권 Spec MCP (Kiwoom Spec MCP)

`kiwoom-spec-mcp`는 키움증권 OpenAPI 스펙을 검색하고, 해당 API의 실행 가능한
예제 코드를 GitHub 공개 저장소에서 가져와 돌려주는 **자격증명이 필요 없는**
MCP(Model Context Protocol) 서버입니다. 사용자가 "무슨 기능을 만들고 싶다"고
말하면, AI 에이전트가 이 서버로 API를 찾고 예제를 확보한 뒤 답하도록 설계됐습니다.

키움 API를 직접 호출하지 않으며, 네트워크 요청은 예제 코드를 가져오는
`raw.githubusercontent.com` 요청뿐입니다. 인증·주문 실행은 `kiwoom-exec-mcp`가
담당합니다.

배포 패키지 이름은 `kiwoom-spec-mcp`이며, 콘솔 명령도 동일합니다.

## 설치 · 로컬 실행

```sh
cd mcp_spec
uv sync --frozen
uv run kiwoom-spec-mcp   # 기본 전송: stdio
```

MCP 클라이언트(Claude Desktop 등) 설정에 등록할 때는 자격증명이 필요 없으므로
`env` 없이 등록합니다.

```json
{
  "mcpServers": {
    "kiwoom-spec": {
      "command": "uv",
      "args": ["run", "--frozen", "--directory", "/path/to/mcp_spec", "kiwoom-spec-mcp"]
    }
  }
}
```

- `--frozen`은 `uv.lock`에 고정된 버전만 쓰게 해 기동을 빠르고 재현 가능하게 합니다.
- 원격(streamable HTTP)으로 띄우려면 `KIWOOM_MCP_TRANSPORT=http`를 설정합니다(포트는
  `KIWOOM_MCP_PORT` > `PORT` > 기본 8000). 이 문서는 로컬 사용을 기준으로 합니다.

## 제공 도구

| 도구 | 역할 |
| --- | --- |
| `spec_search(query, market, group, limit)` | 키워드로 API 검색. `market`(domestic\|overseas\|auth)·`group`(그룹명)으로 선필터 가능. 스펙 인덱스(API명·필드 한글명)가 한글이라 한글 검색이 기본이고, API ID(`ka10081`)나 필드 코드(`stk_cd`)도 찾을 수 있습니다. |
| `spec_show(api_id)` | 특정 API의 요청/응답 필드 계약 상세 조회 |
| `spec_groups()` | market×group별 API 수 목록 — 검색 필터에 쓸 수 있는 값 확인용 |
| `get_example(api_id)` | 실행 가능한 예제 코드 반환(GitHub raw). 주문/환전/토큰 등 쓰기성 API 19개는 응답에 `safety` 경고 필드가 붙습니다 |

`spec_search`가 돌려주는 `command_path`는 `kiwoom-exec-mcp`의 `kiwoom_query`
인자로 그대로 사용할 수 있습니다 — 두 서버는 같은 명령 어휘를 씁니다.

## 예제 코드 출처

`get_example`은 키움증권 공식 공개 저장소(`Kiwoom-Securities/Kiwoom-REST-API`,
`main` 브랜치)에서 예제를 가져옵니다. 이 출처는 서버 코드에 고정돼 있으며 환경변수
등으로 바꿀 수 없습니다 — 다른 저장소의 코드가 공식 예제로 서빙되는 경로를
원천 차단하기 위한 설계입니다.

아직 해당 저장소에 게시되지 않은 API의 예제를 요청하면 404 안내를 반환합니다.

예제 코드를 그대로 실행하려면 별도의 설치와 인증 절차가 필요합니다. 자세한
절차는 예제 코드 상단의 안내를 참고하세요.

## 안전 유의사항

- 이 서버는 키움 자격증명을 받지 않고, 요구하지도 않습니다.
- 반환된 예제 코드에 `safety` 필드가 있으면(주문/환전/토큰 발급류 API) 반드시
  demo(모의투자) 모드로 먼저 실행해 보세요.
