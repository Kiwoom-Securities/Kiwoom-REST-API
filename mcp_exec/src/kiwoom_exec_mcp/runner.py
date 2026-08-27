"""kiwoomcli subprocess 실행기 — exit code 계약을 MCP 오류로 매핑한다.

자격증명은 두 소스 중 하나로 들어온다:

- **stdio / 단일 테넌트**: 프로세스 env(APP_KEY/APP_SECRET/KIWOOM_MODE 또는
  KIWOOM_PROFILE)를 subprocess가 상속한다. server가 credentials=None으로 호출.
  토큰은 사용자 자신의 홈 캐시(kwcli 기본 파일 저장소)에 남는다 — 사용자의 머신이다.
- **HTTP 멀티테넌트**: server가 요청 헤더에서 읽은 `TenantCredentials`를 넘긴다. 이때
  자격증명은 os.environ에 두지 않고 **요청별 env로만** subprocess에 주입되며,
  `KIWOOM_TOKEN_STORE=memory`로 토큰 저장소를 **subprocess 메모리**로 고정한다. 서버가
  키별로 짧게(TTL) 메모리에 들고 있는 접근 토큰(tokens.py)은 `KIWOOM_ACCESS_TOKEN`/
  `_EXPIRES_AT`로 함께 건네 subprocess가 `/oauth2/token`을 부르지 않게 한다.
  프로세스가 끝나면 서버 디스크에 자격증명·토큰·지문 어느 것도 남지 않는다.

키를 인자(argv)로 넘기지 않는다 — env로만. 키/토큰은 오류 메시지에서 스크럽한다
(print라도 유출 금지).

subprocess env 이름(kwcli 계약; 서버 설정 `KIWOOM_MCP_*`는 config.py):
  APP_KEY / APP_SECRET / APP_KEY_MOCK / APP_SECRET_MOCK — 자격증명 (demo는 _MOCK 이름)
  KIWOOM_MODE / KIWOOM_PROFILE                            — 대상 선택
  KIWOOM_TOKEN_STORE                                      — 토큰 저장소 (HTTP는 항상 memory)
  KIWOOM_ACCESS_TOKEN / KIWOOM_ACCESS_TOKEN_EXPIRES_AT    — 사전 발급 토큰
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path

from .tenant import TenantCredentials

# subprocess env 중 값이 비밀인 것 — 오류 출력 마스킹, 멀티테넌트 시 프로세스 env에서 제거.
_SECRET_ENV_NAMES = ("APP_KEY", "APP_SECRET", "APP_KEY_MOCK", "APP_SECRET_MOCK", "KIWOOM_ACCESS_TOKEN")
# 멀티테넌트 요청에서 프로세스 env로부터 걷어내는 선택 신호 — 요청 값만 유효해야 한다.
_TENANT_ENV_NAMES = (*_SECRET_ENV_NAMES, "KIWOOM_MODE", "KIWOOM_PROFILE", "KIWOOM_TOKEN_STORE", "KIWOOM_ACCESS_TOKEN_EXPIRES_AT")

# Windows에서 호출마다 콘솔 창이 뜨지 않게 하는 플래그.
#
# `kiwoomcli.exe`는 콘솔 서브시스템 앱이라(PE 헤더 subsystem=3, 플러그인 쪽에서 실측)
# 물려받을 콘솔이 없으면 OS가 호출마다 새 콘솔을 만든다. Claude Desktop 같은 GUI 호스트가
# 이 서버를 띄우면 콘솔이 없으므로 조회 한 번마다 검은 창이 뜨고 포커스를 뺏는다.
# 출력을 파이프로 받는 것과 콘솔 할당은 별개라 `stdout=PIPE`로는 막히지 않는다.
# 같은 문제를 `Plugins/kiwoom-plugin/kw_runtime/config.py`가 이 플래그로 해결했다.
_NO_WINDOW_KWARGS: dict = (
    {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if os.name == "nt" else {}
)


def require_token_contract() -> None:
    """설치된 kwcli가 요청별 메모리 토큰 계약(KIWOOM_TOKEN_STORE / KIWOOM_ACCESS_TOKEN)을 갖는지 확인한다.

    HTTP 멀티테넌트 경로에서만 필요하다 — 계약이 없는 kwcli는 이 env를 무시하고 컨테이너
    공용 캐시 파일에 토큰을 써서(테넌트 간 공유) 조용히 옛 동작으로 돌아가므로, 그 경로는
    시작하지 않는다. stdio(로컬 단일 사용자)는 사용자 자신의 홈 캐시를 쓰는 것이 정상이라
    검사하지 않는다. 버전 번호가 아니라 계약 자체(코어 settings의 env 상수)를 확인한다.
    """
    try:
        from kiwoom.core import secrets as core_secrets, settings as core_settings

        for name in ("TOKEN_STORE_ENV_VAR", "ACCESS_TOKEN_ENV_VAR", "get_preissued_token_from_env"):
            getattr(core_settings, name)
        getattr(core_secrets, "StaticSecretProvider")
    except (ImportError, AttributeError) as exc:
        try:
            installed = metadata.version("kwcli")
        except metadata.PackageNotFoundError:
            installed = "not installed"
        raise RuntimeError(
            "HTTP 멀티테넌트 경로에는 KIWOOM_TOKEN_STORE=memory 계약을 가진 kwcli(>=1.1.0)가 필요합니다 "
            f"(installed: {installed}). 계약이 없는 버전은 사용자 토큰을 서버 디스크에 남기므로 시작하지 않습니다. "
            "로컬 stdio는 이 검사 없이 동작합니다."
        ) from exc


class KiwoomCliError(RuntimeError):
    """kiwoomcli 실행 실패. exit code 2는 입력 오류, 그 외는 런타임 오류.

    output은 이미 시크릿이 마스킹된 상태로만 저장/노출한다.
    """

    def __init__(self, exit_code: int, output: str) -> None:
        kind = "input" if exit_code == 2 else "runtime"
        super().__init__(f"kiwoomcli {kind} error (exit {exit_code}): {output.strip()}")
        self.exit_code = exit_code
        self.output = output


def find_cli() -> str:
    """같은 환경에 설치된 kiwoomcli 실행 파일을 찾는다."""
    sibling = Path(sys.executable).parent / "kiwoomcli"
    if sibling.is_file():
        return str(sibling)
    found = shutil.which("kiwoomcli")
    if found:
        return found
    raise KiwoomCliError(
        1, "kiwoomcli not found — install the kwcli package in this environment."
    )


def mask_secrets(text: str, secrets: list[str]) -> str:
    """오류 출력에서 알려진 시크릿 값을 마스킹한다."""
    masked = text
    for secret in secrets:
        if secret:
            masked = masked.replace(secret, "***REDACTED***")
    return masked


def _subprocess_env(credentials: TenantCredentials | None) -> dict[str, str]:
    """subprocess에 넘길 env를 구성한다.

    credentials가 None이면 프로세스 env를 그대로 상속(stdio/단일 테넌트).
    credentials가 있으면(HTTP 멀티테넌트) 프로세스에 남아있을 수 있는 선택 신호를 전부 걷어내고
    요청 값만 넣는다: 자격증명·mode, 토큰 저장소=memory, (있으면) 사전 발급 토큰.
    demo 모드는 런타임이 읽는 _MOCK 이름으로 매핑한다.
    """
    env = os.environ.copy()

    if credentials is not None:
        require_token_contract()  # 멀티테넌트 요청은 계약 없는 kwcli로 실행하지 않는다
        for name in _TENANT_ENV_NAMES:
            env.pop(name, None)
        env["KIWOOM_MODE"] = credentials.mode
        env["APP_KEY"] = credentials.appkey
        env["APP_SECRET"] = credentials.secretkey
        # 멀티테넌트 하드룰: 다른 사용자의 토큰이 서버 디스크에 남지 않는다.
        env["KIWOOM_TOKEN_STORE"] = "memory"
        if credentials.access_token and credentials.access_token_expires_at:
            env["KIWOOM_ACCESS_TOKEN"] = credentials.access_token
            env["KIWOOM_ACCESS_TOKEN_EXPIRES_AT"] = credentials.access_token_expires_at.isoformat()

    # stdio(프로세스 env) 경로로 들어온 값도 대소문자 무관하게 인식한다.
    if env.get("KIWOOM_MODE", "").strip().lower() == "demo":
        if env.get("APP_KEY") and not env.get("APP_KEY_MOCK"):
            env["APP_KEY_MOCK"] = env["APP_KEY"]
        if env.get("APP_SECRET") and not env.get("APP_SECRET_MOCK"):
            env["APP_SECRET_MOCK"] = env["APP_SECRET"]

    return env


def run_cli(args: list[str], *, credentials: TenantCredentials | None = None, timeout: int = 60) -> str:
    """kiwoomcli를 실행하고 stdout을 돌려준다. 비정상 종료는 KiwoomCliError.

    credentials가 주어지면 그 자격증명으로만 실행(멀티테넌트), None이면 프로세스 env 상속.

    stdin은 DEVNULL로 끊는다 — stdio 전송에서 이 프로세스의 stdin은 MCP 클라이언트의
    JSON-RPC 입력 채널이라, 자식이 그 핸들을 물려받으면 클라이언트가 보낸 바이트를
    가로채거나 붙들 수 있다. kiwoomcli는 stdin을 읽지 않으므로 잃는 것이 없다.

    디코딩은 UTF-8로 고정한다. kiwoomcli가 자기 stdout을 UTF-8로 맞춰 내보내는데
    (`kiwoom_cli/main.py`), 여기서 플랫폼 기본값에 맡기면 한글 Windows에서 cp949로
    풀려 종목명 같은 한글이 깨진다. errors="replace"는 깨진 바이트가 서버를 죽이는
    대신 응답에 드러나게 한다.
    """
    env = _subprocess_env(credentials)
    result = subprocess.run(
        [find_cli(), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
        **_NO_WINDOW_KWARGS,
    )
    if result.returncode != 0:
        secrets = [env.get(name, "") for name in _SECRET_ENV_NAMES]
        raise KiwoomCliError(result.returncode, mask_secrets(result.stdout or "", secrets))
    return result.stdout


def run_json(args: list[str], *, credentials: TenantCredentials | None = None, timeout: int = 60) -> object:
    """--format json으로 실행하고 파싱된 객체를 돌려준다."""
    output = run_cli([*args, "--format", "json"], credentials=credentials, timeout=timeout)
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {"raw_output": output.strip()}


def options_to_args(options: dict | None) -> list[str]:
    """{"code": "005930", "adjusted": True} → ["--code", "005930", "--adjusted"]."""
    args: list[str] = []
    for key, value in (options or {}).items():
        flag = f"--{key.replace('_', '-').lstrip('-')}"
        if value is None:
            continue
        if isinstance(value, bool):
            if value:
                args.append(flag)
            continue
        args.extend([flag, str(value)])
    return args
