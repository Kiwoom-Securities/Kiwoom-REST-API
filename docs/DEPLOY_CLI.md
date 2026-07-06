# 배포 가이드 (Release Runbook)

`kiwoomcli`를 PyPI에 게시하는 운영 절차입니다. 모든 단계는 저장소 루트의
`./deploy.sh`로 실행합니다. 설계 배경은 [final-deploy-plan.md](final-deploy-plan.md) 참고.

배포 대상은 **단일 패키지** `kiwoomcli`(= `kiwoomcli` 코어 + `kiwoom_cli` + 번들 스펙),
콘솔 명령은 `kiwoomcli`입니다. `Examples/`(samplecode)는 휠에 포함되지 않으며 GitHub에만 둡니다.

## 사전 준비

- `uv` 설치 (macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- `rg`(ripgrep) — no-mock 게이트에 사용
- PyPI / TestPyPI 계정과 **API 토큰**

## 토큰 설정

토큰은 환경변수로만 전달합니다(스크립트에 하드코딩 금지).

- TestPyPI 토큰 발급: <https://test.pypi.org/manage/account/token/>
- PyPI 토큰 발급: <https://pypi.org/manage/account/token/>

```sh
export TESTPYPI_TOKEN='pypi-...'   # TestPyPI 업로드용
export PYPI_TOKEN='pypi-...'       # PyPI(운영) 업로드용
# 둘 중 하나만 쓸 때는 UV_PUBLISH_TOKEN 으로 대체 가능
```

## 표준 릴리스 절차

```sh
# 0) 필요 시 버전 올리기 (재업로드 불가 — 아래 '버전 관리' 참고)
#    pyproject.toml [project].version 수정

# 1) 안전 점검 (업로드 없음)
./deploy.sh dry-run

# 2) TestPyPI 리허설 (업로드 + 설치 검증)
./deploy.sh test

# 3) TestPyPI 페이지/설치 확인 후 실제 게시
./deploy.sh publish
```

각 복합 단계는 **항상 `dry-run`을 먼저 수행**한 뒤 업로드합니다.

## 명령 레퍼런스

복합 단계 (앞 단계 자동 포함):

| 명령 | 동작 |
| --- | --- |
| `./deploy.sh dry-run` | gates → clean → build → check → smoke (업로드 없음) |
| `./deploy.sh test` | dry-run → 버전 확인 → TestPyPI 업로드 → TestPyPI 설치 검증 |
| `./deploy.sh publish` | dry-run → 버전 확인 → 확인 프롬프트 → PyPI 업로드 → PyPI 설치 검증 |

개별 단계 (세밀 제어):

| 명령 | 동작 |
| --- | --- |
| `gates` | ruff + validate_maps + audit_implementation + no-mock 스캔 |
| `clean` | `dist/` 삭제 |
| `build` | `uv build` (wheel + sdist) |
| `check` | `twine check` + `audit_wheel` + 산출물 요약 |
| `smoke` | 빌드된 wheel을 격리 venv에 설치해 `--help`/`spec search`/입력오류(exit 2) 확인 |
| `upload-test` | TestPyPI 업로드만 |
| `upload-pypi` | PyPI 업로드만 (`--yes`로 확인 생략) |
| `verify-test` | TestPyPI에서 설치해 스모크 |
| `verify-pypi` | PyPI에서 설치해 스모크 |
| `version` | 현재 버전 출력 |

옵션: `--yes` — `publish`/`upload-pypi` 확인 프롬프트 생략(CI용).

## 단계 상세

- **gates** — 배포 전 저장소 정합성. 하나라도 실패하면 중단. `no-mock`은 배포 코드에 test-double이 없는지 확인.
- **build** — `dist/`에 `kiwoom_cli-<ver>-py3-none-any.whl` + `kiwoom_cli-<ver>.tar.gz` 생성.
- **check** — `twine check`로 메타데이터/README 렌더링 검증, `audit_wheel`로 휠 필수 멤버(스펙/맵/엔트리포인트) 확인.
- **smoke** — 저장소 밖(`/tmp`)에서 실행해 경로 의존성을 배제하고, 번들 스펙 로딩과 3계층 오류(입력=exit 2)를 검증.
- **verify-test/pypi** — 실제 인덱스에서 `kiwoomcli==<ver>`를 격리 설치해 스모크. TestPyPI는 의존성이 없어 PyPI를 `--extra-index-url`로 병용.

## 버전 관리

- **PyPI는 같은 버전 재업로드가 불가**합니다. 재배포 전 반드시 `pyproject.toml`의
  `[project].version`을 올리세요.
- `deploy.sh`는 업로드 전 해당 인덱스에 같은 버전이 있는지 확인하고, 있으면 중단합니다.

## 배포 후

사용자 설치(문서화된 경로):

```sh
uv tool install kiwoomcli
kiwoomcli setup
```

## 트러블슈팅

- **"이미 존재합니다"로 중단** — 이미 게시된 버전. `version`을 올린 뒤 다시.
- **"TOKEN 환경변수가 필요합니다"** — `TESTPYPI_TOKEN`/`PYPI_TOKEN`(또는 `UV_PUBLISH_TOKEN`) 설정.
- **`verify-test` 의존성 오류** — TestPyPI엔 런타임 의존성이 없음. 스크립트가 `--extra-index-url https://pypi.org/simple/`로 처리하므로, 수동 설치 시에도 동일 옵션 필요.
- **`twine check` 실패** — README(long description) 렌더링/메타데이터 문제. `pyproject`의 `readme`/`description` 확인.
- **smoke의 spec search 실패** — 번들 스펙(`kiwoom/_data/kiwoom_api_spec.json`) 누락. `pyproject`의 wheel `artifacts`에 `kiwoom/_data/*.json`이 있는지 확인.
- **keyring 관련** — 게시와 무관(설치 후 `kiwoomcli setup` 단계에서 필요). 헤드리스 환경은 `kiwoomcli setup`이 사전 점검으로 경고.
