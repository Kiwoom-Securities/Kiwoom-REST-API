"""`kiwoomcli setup` 시작 시 표시하는 ASCII 배너.

컬러: KIWOOM 워드마크는 네이비, 오른쪽 'K' 로고는 기본 회색(#BEBEBE)에
상단 화살표만 마젠타 핑크로 포인트. 자막/버전은 회색. 색은 대화형 터미널에서만
적용하고, 파이프/리다이렉트(비-TTY)나 NO_COLOR 환경에서는 무채색으로 출력한다.
"""

from __future__ import annotations

import ctypes
import os
import sys
from importlib.metadata import PackageNotFoundError, version

# 키움 브랜드 컬러 (truecolor).
_NAVY = "\033[1;38;2;26;31;113m"      # KIWOOM 워드마크
_GRAY = "\033[1;38;2;190;190;190m"    # 오른쪽 K 기본색 #BEBEBE
_MAGENTA = "\033[1;38;2;230;0;122m"   # K 상단 화살표 포인트
_WHITE = "\033[1;38;2;255;255;255m"   # 자막 / 버전
_RESET = "\033[0m"

# 워드마크(좌) / 오른쪽 K(우) 경계 컬럼.
_SPLIT = 51
# 오른쪽 K에서 상단 화살표(마젠타) 행. 하단(4~6행)은 회색.
_ARROW_ROWS = {0, 1, 2, 3}

_ART = """\
██╗  ██╗██╗██╗    ██╗ ██████╗  ██████╗ ███╗   ███╗  ██   ▜██
██║ ██╔╝██║██║    ██║██╔═══██╗██╔═══██╗████╗ ████║  ██  ╱█▛▜
█████╔╝ ██║██║ █╗ ██║██║   ██║██║   ██║██╔████╔██║  ██ ███╱
██╔═██╗ ██║██║███╗██║██║   ██║██║   ██║██║╚██╔╝██║  █████╱
██║  ██╗██║╚███╔███╔╝╚██████╔╝╚██████╔╝██║ ╚═╝ ██║  ██ ╲██╲
╚═╝  ╚═╝╚═╝ ╚══╝╚══╝  ╚═════╝  ╚═════╝ ╚═╝     ╚═╝  ██  ╲██╲
                                                    ██   ╲██▙"""

_SUBTITLE = "                    키움증권 CLI"


def _use_color() -> bool:
    if "NO_COLOR" in os.environ:
        return False
    if not sys.stdout.isatty():
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    if os.name != "nt":
        return True
    if os.environ.get("WT_SESSION") or os.environ.get("ANSICON"):
        return True
    if os.environ.get("ConEmuANSI", "").upper() == "ON":
        return True
    return _enable_windows_vt()


def _enable_windows_vt() -> bool:
    std_output_handle = -11
    enable_virtual_terminal_processing = 0x0004
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(std_output_handle)
        if handle in (-1, 0):
            return False
        mode = ctypes.c_uint()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        if mode.value & enable_virtual_terminal_processing:
            return True
        return bool(
            kernel32.SetConsoleMode(
                handle,
                mode.value | enable_virtual_terminal_processing,
            )
        )
    except Exception:
        return False


_BOX = set("╗╝═║╔╚")  # 워드마크 외곽선(그림자) 문자


def _colorize_wordmark(segment: str) -> str:
    """워드마크: `█` 블록은 네이비, 외곽선 문자는 #BEBEBE로 대비를 준다."""
    out: list[str] = []
    current: str | None = None
    for char in segment:
        color = _GRAY if char in _BOX else _NAVY
        if color != current:
            out.append(color)
            current = color
        out.append(char)
    return "".join(out)


def _arrow_start(right: str) -> int:
    """오른쪽 조각에서 마지막 공백 뒤(=상단 화살표 시작) 인덱스."""
    index = len(right)
    while index > 0 and right[index - 1] != " ":
        index -= 1
    return index


def print_banner() -> None:
    try:
        current = version("kiwoomcli")
    except PackageNotFoundError:
        current = "dev"
    ver_line = f"                    ver {current}"

    if _use_color():
        for row, line in enumerate(_ART.splitlines()):
            left, right = line[:_SPLIT], line[_SPLIT:]
            if row in _ARROW_ROWS:
                cut = _arrow_start(right)
                if row == 3:
                    cut += 1  # 엘보 맨 왼쪽 한 칸은 기둥이므로 회색 유지
                print(f"{_colorize_wordmark(left)}{_GRAY}{right[:cut]}{_MAGENTA}{right[cut:]}{_RESET}")
            else:
                print(f"{_colorize_wordmark(left)}{_GRAY}{right}{_RESET}")
        print(f"{_WHITE}{_SUBTITLE}{_RESET}")
        print(f"{_WHITE}{ver_line}{_RESET}")
    else:
        print(_ART)
        print(_SUBTITLE)
        print(ver_line)
    print()
