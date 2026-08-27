FROM python:3.13-slim

# 버퍼링 없는 로그(운영 관찰성) + .pyc 미생성(레이어 슬림).
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 의존성은 uv.lock으로 고정한다(uv sync --frozen) — 빌드마다 버전이 흔들리지 않게.
COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /usr/local/bin/uv

WORKDIR /app

# 의존성 레이어와 소스 레이어를 분리해 캐시를 살린다(소스만 바뀌면 재설치 없음).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev
COPY src ./src
RUN uv sync --frozen --no-dev

# 콘솔 스크립트(kiwoom-exec-mcp)를 PATH에 올린다.
ENV PATH="/app/.venv/bin:$PATH"

# HTTP 멀티테넌트로 기동. 자격증명은 요청 헤더로만 받으므로 이미지에 키를 넣지 않는다.
# 포트는 런타임에 $PORT(Railway 등)를 서버가 읽는다.
# 토큰은 요청별 subprocess 메모리에만 존재한다(KIWOOM_TOKEN_STORE=memory를 runner가 주입).
# 컨테이너 디스크에 자격증명·토큰·지문 디렉터리를 두지 않으므로 캐시 경로 설정이 없다.
ENV KIWOOM_MCP_TRANSPORT=http \
    KIWOOM_MCP_HOST=0.0.0.0

# 비루트 사용자로 실행(컨테이너 권한 최소화).
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

CMD ["kiwoom-exec-mcp"]
