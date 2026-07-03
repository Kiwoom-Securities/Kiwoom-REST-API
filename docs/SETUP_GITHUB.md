# 키움증권 OpenAPI GitHub 공개 저장소 구성 안내

본 문서는 GitHub 공개 저장소 운영자를 위한 안내입니다.
납품받은 프로젝트에서 아래 구성만 공개 저장소에 포함하고, 명시된 작업을 수행해 주세요.

---

## 1. 공개 저장소에 포함할 구성

[폴더]
- kiwoom/        런타임 패키지 (필수)
- examples/      키움 OpenAPI 샘플코드 (필수)
- postman/       Postman Collection (검토) — 키움 측 확인 후 포함 여부 결정

[파일]
- .env.example   환경변수 예시
- .gitignore     Git 제외 규칙
- LICENSE.md     키움증권 라이선스
- README.md      사용자 가이드 (아래 2번 작업으로 생성)
- pyproject.toml 프로젝트 메타데이터 / 의존성
- uv.lock        의존성 잠금 파일 (재현성 위해 포함)

---

## 2. 운영자 작업 사항

1) README 교체
   - docs/SETUP_USERS.md 의 내용을 README.md 로 변경(rename)하여 공개합니다.
   - 납품본에 포함된 기존 README.md 는 "키움증권 납품용 설명서"이므로
     공개 저장소에는 포함하지 않습니다. (docs/SETUP_USERS.md → README.md 로 대체)

2) .DS_Store 제거
   - 저장소 내 .DS_Store 파일은 모두 삭제합니다. (.gitignore에 이미 등록되어 있음)

3) 내부용 자료 제외
   - 아래 항목은 내부 제작/검증용이므로 공개 저장소에서 제외합니다.
     - generator/          (예제/Postman 생성 도구)
     - examples_prove/     (실행 증적 자료)
     - convention/         (샘플코드 작성 컨벤션)
     - smoke_check.py      (납품 전 점검 스크립트)
     - docs/               (내부 문서 폴더. 단, docs/SETUP_USERS.md 는 위 1번대로
                            README.md 로 추출 후 제외)

4) Postman 포함 여부
   - postman/ 은 키움 측 확인 후 공개 여부를 결정합니다. (현재 "검토" 상태)

---

## 3. 최종 공개 트리(예시)

Kiwoom-OpenAPI/
├── kiwoom/
├── examples/
├── postman/         (검토)
├── .env.example
├── .gitignore
├── LICENSE.md
├── README.md        (← docs/SETUP_USERS.md)
├── pyproject.toml
└── uv.lock

---

## 4. AI 에이전트에게 "공개 저장소 구성" 맡길 때

> 이 절은 운영자가 AI 코딩 에이전트에게 "이 문서대로 공개 저장소 폴더를 만들어줘"라고
> 요청할 때를 위한 실행 규칙입니다. 위 1~3번의 구성/매핑을 그대로 사용하며,
> 이 절은 **에이전트가 지켜야 할 방식과 경계**만 정의합니다.

### 기본 방식: 비파괴적 "허용 목록 복사(export)"

- **납품 원본은 절대 수정/삭제하지 않는다.** 원본에서 파일을 지우는 대신,
  **새 폴더(예: `Kiwoom-OpenAPI/`)를 만들고 공개 대상만 복사**한다.
- 즉 "제외"는 삭제가 아니라 **"복사하지 않음"**으로 처리한다. (제외 목록을 빠뜨려도 유출되지 않도록)

### 복사할 것 (허용 목록)

- 폴더: `kiwoom/`, `examples/`
- 파일: `.env.example`, `.gitignore`, `LICENSE.md`, `pyproject.toml`, `uv.lock`
- 매핑: `docs/SETUP_USERS.md` → 새 폴더의 **`README.md`** (복사 후 이름 변경)

### 복사하지 말 것 (제외)

- 내부용: `generator/`, `examples_prove/`, `convention/`, `smoke_check.py`, `docs/`(위 매핑 제외)
- 납품용 `README.md` (공개 README는 `SETUP_USERS.md`에서 생성)
- 작업 부산물: `.git/`, `.venv/`, `__pycache__/`, `.DS_Store`
- **실제 자격 증명 파일: `.env` 등은 절대 복사 금지** (`.env.example`만 복사)

### 운영자에게 반드시 확인할 것

- **`postman/` 포함 여부**: 현재 "검토" 상태이므로 에이전트가 단독으로 결정하지 않는다.
  복사 전 **운영자에게 포함 여부를 물어보고**, 답변에 따라 포함/제외한다.
  (확답이 없으면 기본값은 **제외**.)

### 완료 후 검증

- 생성된 폴더의 트리를 위 **3번 "최종 공개 트리"**와 대조해 일치하는지 확인하고,
  제외 대상(특히 내부 자료·실제 `.env`)이 섞이지 않았는지 점검해 운영자에게 보고한다.
- 공개 저장소 push(원격 연결, 커밋, 푸시)는 운영자가 직접 수행하도록 안내한다.
