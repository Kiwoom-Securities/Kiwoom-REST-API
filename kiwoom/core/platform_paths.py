import os
import shutil
import subprocess
from pathlib import Path

from platformdirs import user_cache_dir, user_config_dir


APP_NAME = "kiwoom"


def config_dir() -> Path:
    return Path(user_config_dir(APP_NAME))


def cache_dir() -> Path:
    return Path(user_cache_dir(APP_NAME))


def ensure_private_directory(path: Path, *, strict: bool = False) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    _protect_path(path, strict=strict, is_dir=True)
    return path


def protect_file(path: Path, *, strict: bool = False) -> Path:
    _protect_path(path, strict=strict, is_dir=False)
    return path


def _protect_path(path: Path, *, strict: bool, is_dir: bool) -> None:
    if os.name == "nt":
        success = _protect_windows_path(path, is_dir=is_dir)
        if strict and not success:
            raise PermissionError(f"Could not restrict access to {path}")
        return

    mode = 0o700 if is_dir else 0o600
    path.chmod(mode)


def _protect_windows_path(path: Path, *, is_dir: bool) -> bool:
    # Prefer OS-specific user directories and then try to remove inherited ACLs.
    icacls = shutil.which("icacls")
    if not icacls:
        return False

    target = str(path)
    commands = [
        [icacls, target, "/inheritance:r"],
        [icacls, target, "/grant:r", f"{os.environ.get('USERNAME', '%USERNAME%')}:F"],
    ]

    if is_dir:
        commands[1].append("/t")
        commands[1].append("/c")

    for command in commands:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False

    return True
