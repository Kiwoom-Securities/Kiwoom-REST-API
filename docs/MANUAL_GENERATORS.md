# Generator 실행 가이드

이 문서는 `generator/` 폴더의 생성기를 실행하는 방법을 설명합니다.
생성기는 키움 REST API 원천 workbook을 입력받아 `examples/` 샘플코드와 `postman/` Collection 파일을 생성합니다.

운영체제별 shell 명령이 다르므로 각 섹션은 `macOS/Linux`와 `Windows PowerShell`을 구분해 작성합니다.

---

## 1. Python 설치 확인

이 프로젝트는 Python 3.13 이상을 기준으로 실행합니다.
먼저 로컬 환경에 Python이 설치되어 있는지 확인합니다.

### macOS/Linux

```bash
python3 --version
```

버전이 출력되면 설치되어 있는 상태입니다.

```text
Python x.x.x
```

Python이 없거나 버전이 낮다면 Python 3.13 이상을 설치합니다.

macOS에서 Homebrew를 사용하는 경우:

```bash
brew install python@3.13
```

Linux에서는 사용 중인 배포판의 패키지 관리자 또는 Python 공식 배포판을 사용해 Python 3.13 이상을 설치합니다.

- [https://www.python.org/downloads/](https://www.python.org/downloads/)

### Windows PowerShell

```powershell
py --version
```

버전이 출력되면 설치되어 있는 상태입니다.

```text
Python x.x.x
```

Python이 없거나 버전이 낮다면 Python 3.13 이상을 설치합니다.

winget을 사용할 수 있는 경우:

```powershell
winget install Python.Python.3.13
```

또는 Python 공식 다운로드 페이지에서 Windows installer를 설치합니다.

- [https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)

---

## 2. uv 설치 확인

이 프로젝트의 표준 실행 방식은 `uv run`입니다.
로컬 환경에 `uv`가 설치되어 있는지 확인합니다.

```bash
uv --version
```

버전이 출력되면 설치되어 있는 상태입니다.

```text
uv x.x.x
```

명령을 찾을 수 없다면 OS에 맞게 설치합니다.

### macOS

Homebrew를 사용하는 경우:

```bash
brew install uv
```

Homebrew를 사용하지 않는 경우 공식 설치 스크립트를 사용할 수 있습니다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Linux

공식 설치 스크립트를 사용합니다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

설치 후 새 shell을 열거나 shell 설정을 다시 로드합니다.

### Windows PowerShell

PowerShell에서 공식 설치 스크립트를 실행합니다.

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 후 새 PowerShell 창을 엽니다.

### 설치 후 재확인

설치가 끝나면 다시 버전을 확인합니다.

```bash
uv --version
```

Windows PowerShell에서도 같은 명령을 사용합니다.

```powershell
uv --version
```

최신 설치 방법은 공식 문서를 기준으로 확인합니다.

- [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)

---

## 3. 프로젝트 위치로 이동 및 의존성 동기화

생성기는 프로젝트 루트에서 실행합니다.
처음 실행하거나 의존성이 바뀐 경우 `uv sync`로 의존성을 동기화합니다.

### macOS/Linux

```bash
cd Kiwoom-Github-Active-Project
uv sync
uv run python --version
```

### Windows PowerShell

```powershell
cd Kiwoom-Github-Active-Project
uv sync
uv run python --version
```

`uv run python --version`이 정상 출력되면 생성기를 실행할 준비가 된 상태입니다.

---

## 4. 원천 workbook 준비

생성기는 키움 REST API 원천 workbook(`.xlsx`)을 입력으로 사용합니다.
이 프로젝트에는 workbook이 포함되어 있지 않을 수 있으므로, 사용자가 보유한 원천 workbook의 실제 경로를 실행 시 지정합니다.
파일명은 정해져 있지 않습니다. 아래의 `<workbook.xlsx>`는 실제 파일 경로로 바꿔 입력합니다.
경로에 공백이나 괄호가 있으면 반드시 따옴표로 감쌉니다.

### macOS/Linux

```bash
WORKBOOK="<workbook.xlsx>"
```

### Windows PowerShell

```powershell
$WORKBOOK = "<workbook.xlsx>"
```

---

## 5. Examples 생성

`generator/generate_examples.py`는 원천 workbook을 읽어 `examples/` 샘플코드를 생성합니다.

기본 생성 대상은 `examples/`입니다.
기존 `examples/` 폴더를 덮어쓸 수 있으므로, 먼저 별도 폴더에 생성해 확인하는 것을 권장합니다.

### macOS/Linux

검사용 별도 폴더에 생성:

```bash
uv run python generator/generate_examples.py "$WORKBOOK" \
  --out generated_examples \
  --mapping generator/function_name_map.csv \
  --report generated_examples_report.json
```

기존 `examples/` 폴더에 반영:

```bash
uv run python generator/generate_examples.py "$WORKBOOK" \
  --out examples \
  --mapping generator/function_name_map.csv \
  --report generator/examples_generation_report.json
```

### Windows PowerShell

검사용 별도 폴더에 생성:

```powershell
uv run python generator/generate_examples.py $WORKBOOK `
  --out generated_examples `
  --mapping generator/function_name_map.csv `
  --report generated_examples_report.json
```

기존 `examples/` 폴더에 반영:

```powershell
uv run python generator/generate_examples.py $WORKBOOK `
  --out examples `
  --mapping generator/function_name_map.csv `
  --report generator/examples_generation_report.json
```

특정 템플릿만 생성하려면 `--kind`를 사용합니다.

```bash
uv run python generator/generate_examples.py "$WORKBOOK" --kind rest --out generated_examples
```

Windows PowerShell에서는 다음처럼 실행합니다.

```powershell
uv run python generator/generate_examples.py $WORKBOOK --kind rest --out generated_examples
```

---

## 6. Postman Collection 생성

`generator/generate_postman.py`는 원천 workbook을 읽어 Postman Collection JSON을 생성합니다.

기본 산출물은 다음 위치에 둡니다.

```text
postman/kiwoom-openapi.postman_collection.json
```

기존 Postman Collection을 덮어쓸 수 있으므로, 먼저 별도 파일에 생성해 확인하는 것을 권장합니다.

### macOS/Linux

검사용 별도 파일에 생성:

```bash
uv run python generator/generate_postman.py "$WORKBOOK" \
  --config generator/postman_collection_config.json \
  --out generated_postman_collection.json \
  --report generated_postman_report.json
```

기존 `postman/` 산출물에 반영:

```bash
uv run python generator/generate_postman.py "$WORKBOOK" \
  --config generator/postman_collection_config.json \
  --out postman/kiwoom-openapi.postman_collection.json \
  --report generator/generate_postman_report.json
```

### Windows PowerShell

검사용 별도 파일에 생성:

```powershell
uv run python generator/generate_postman.py $WORKBOOK `
  --config generator/postman_collection_config.json `
  --out generated_postman_collection.json `
  --report generated_postman_report.json
```

기존 `postman/` 산출물에 반영:

```powershell
uv run python generator/generate_postman.py $WORKBOOK `
  --config generator/postman_collection_config.json `
  --out postman/kiwoom-openapi.postman_collection.json `
  --report generator/generate_postman_report.json
```

---

## 7. 생성 결과 확인

생성 후에는 파일이 원하는 위치에 만들어졌는지 확인합니다.

### macOS/Linux

Examples 생성 결과:

```bash
find generated_examples -type f | head
```

Postman 생성 결과:

```bash
ls -lh generated_postman_collection.json
```

### Windows PowerShell

Examples 생성 결과:

```powershell
Get-ChildItem generated_examples -Recurse -File | Select-Object -First 10
```

Postman 생성 결과:

```powershell
Get-Item generated_postman_collection.json
```

---

## 8. 기존 산출물 덮어쓰기 주의

다음 경로는 납품 산출물에 직접 반영되는 위치입니다.

```text
examples/
postman/kiwoom-openapi.postman_collection.json
```

덮어쓰기 전에 검사용 경로에 먼저 생성한 뒤 내용을 확인하는 것을 권장합니다.

### macOS/Linux

검사용 examples를 기존 examples와 비교할 때:

```bash
diff -rq examples generated_examples
```

### Windows PowerShell

검사용 examples 목록을 확인할 때:

```powershell
Compare-Object `
  (Get-ChildItem examples -Recurse -File | ForEach-Object FullName) `
  (Get-ChildItem generated_examples -Recurse -File | ForEach-Object FullName)
```

---

## 9. 자주 발생하는 오류

생성기 실행 중 자주 발생하는 오류와 확인 방법입니다.

### workbook 파일을 찾을 수 없는 경우

```text
FileNotFoundError
```

원인:

- workbook 경로가 틀렸습니다.
- 파일명에 공백이나 괄호가 있는데 따옴표로 감싸지 않았습니다.
- 프로젝트 루트가 아닌 다른 위치에서 실행했습니다.

macOS/Linux 확인:

```bash
pwd
ls -lh "$WORKBOOK"
```

Windows PowerShell 확인:

```powershell
Get-Location
Get-Item $WORKBOOK
```

### xlsx 읽기 오류가 발생하는 경우

원인:

- `uv sync`가 실행되지 않아 `pandas`, `openpyxl` 의존성이 준비되지 않았습니다.
- workbook 파일이 손상되었거나 xlsx 형식이 아닙니다.

확인:

```bash
uv sync
```

Windows PowerShell에서도 같은 명령을 사용합니다.

```powershell
uv sync
```

### 출력 경로가 예상과 다른 경우

원인:

- `--out` 값을 생략했습니다.
- 상대 경로 기준이 프로젝트 루트가 아닙니다.

확인:

```bash
pwd
```

Windows PowerShell:

```powershell
Get-Location
```

---

## 10. 실행 순서 추천

처음 실행할 때는 다음 순서로 확인합니다.

1. Python 설치 확인
2. `uv` 설치 확인
3. 프로젝트 루트로 이동
4. `uv sync` 실행
5. 원천 workbook 경로 지정
6. 검사용 폴더/파일에 생성
7. 생성 결과 확인
8. 필요 시 기존 `examples/`, `postman/` 산출물에 반영

### macOS/Linux

```bash
python3 --version
uv --version
cd Kiwoom-Github-Active-Project
uv sync

WORKBOOK="<workbook.xlsx>"

uv run python generator/generate_examples.py "$WORKBOOK" \
  --out generated_examples \
  --mapping generator/function_name_map.csv \
  --report generated_examples_report.json

uv run python generator/generate_postman.py "$WORKBOOK" \
  --config generator/postman_collection_config.json \
  --out generated_postman_collection.json \
  --report generated_postman_report.json
```

### Windows PowerShell

```powershell
py --version
uv --version
cd Kiwoom-Github-Active-Project
uv sync

$WORKBOOK = "<workbook.xlsx>"

uv run python generator/generate_examples.py $WORKBOOK `
  --out generated_examples `
  --mapping generator/function_name_map.csv `
  --report generated_examples_report.json

uv run python generator/generate_postman.py $WORKBOOK `
  --config generator/postman_collection_config.json `
  --out generated_postman_collection.json `
  --report generated_postman_report.json
```

