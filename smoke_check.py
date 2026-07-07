from __future__ import annotations

import compileall
import importlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REQUIRED_ENV_KEYS = {
    "PRD",
    "MOCK",
    "W_PRD",
    "W_MOCK",
    "KIWOOM_MODE",
    "APP_KEY",
    "APP_SECRET",
}
REQUIRED_IMPORTS = (
    "kiwoom",
    "pandas",
    "requests",
    "websockets",
)


def main() -> int:
    checks = [
        ("compile python files", check_compile),
        ("import runtime dependencies", check_imports),
        ("generator CLI help", check_generator_help),
        (".env.example keys", check_env_example),
    ]

    for label, check in checks:
        print(f"[check] {label}")
        check()

    print("[ok] smoke check passed")
    return 0


def check_compile() -> None:
    targets = [
        ROOT / "kiwoom",
        ROOT / "examples",
        ROOT / "generator",
    ]
    for target in targets:
        if not target.exists():
            raise RuntimeError(f"missing path: {target.relative_to(ROOT)}")
        ok = compileall.compile_dir(
            str(target),
            quiet=1,
            force=False,
        )
        if not ok:
            raise RuntimeError(f"compile failed: {target.relative_to(ROOT)}")


def check_imports() -> None:
    for module_name in REQUIRED_IMPORTS:
        importlib.import_module(module_name)


def check_generator_help() -> None:
    commands = [
        [sys.executable, "generator/generate_examples.py", "--help"],
        [sys.executable, "generator/generate_postman.py", "--help"],
    ]
    for command in commands:
        subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )


def check_env_example() -> None:
    path = ROOT / ".env.example"
    if not path.exists():
        raise RuntimeError("missing .env.example")

    keys = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _value = stripped.split("=", 1)
        keys.add(key.strip())

    missing = sorted(REQUIRED_ENV_KEYS - keys)
    if missing:
        raise RuntimeError(f".env.example missing keys: {', '.join(missing)}")


if __name__ == "__main__":
    raise SystemExit(main())
