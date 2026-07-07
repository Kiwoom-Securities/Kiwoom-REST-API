"""Shared argparse helpers for resource commands."""

from __future__ import annotations

import argparse
from datetime import datetime
import re

from kiwoom.core.types import VALID_MODES
from kiwoom_cli.errors import CliInputError
from kiwoom_cli.output import OUTPUT_FORMATS


STOCK_CODE_PATTERN = re.compile(r"^\d{6}$")
EXCHANGE_STOCK_CODE_PATTERN = re.compile(r"^\d{6}(?:_(?:NX|AL))?$")
INSTRUMENT_CODE_PATTERN = re.compile(r"^[A-Za-z0-9]{6}$")
SECTOR_CODE_PATTERN = re.compile(r"^\d{3}$")
DATE_YYYYMMDD_PATTERN = re.compile(r"^\d{8}$")
INTEGER_PATTERN = re.compile(r"^\d+$")
ORDER_ID_PATTERN = re.compile(r"^\d{7}$")
PREVIEW_ORDER_ID_PATTERN = re.compile(r"^\d+$")


def add_runtime_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--profile",
        help="사용할 계좌 별칭입니다. --mode/KIWOOM_MODE가 없을 때 생략하면 현재 계좌 별칭을 사용합니다.",
    )
    parser.add_argument("--mode", choices=VALID_MODES, help="계좌 별칭 대신 모드를 직접 지정합니다.")


def add_output_format_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=OUTPUT_FORMATS, default="pretty", help="출력 형식")


def resolve_optional_alias(
    positional: str | None, option: str | None, option_name: str
) -> str | None:
    if positional and option and positional != option:
        raise CliInputError(
            "계좌 별칭은 positional 또는 "
            f"{option_name} 중 하나만 지정해 주세요: {positional!r} != {option!r}"
        )
    return option or positional


def stock_code(value: str) -> str:
    if not STOCK_CODE_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("--code는 6자리 국내 종목코드여야 합니다.")
    return value


def exchange_stock_code(value: str) -> str:
    normalized = value.upper()
    if not EXCHANGE_STOCK_CODE_PATTERN.fullmatch(normalized):
        raise argparse.ArgumentTypeError(
            "--code는 6자리 종목코드이거나 _NX/_AL 접미사가 붙은 거래소별 종목코드여야 합니다."
        )
    return normalized


def instrument_code(value: str) -> str:
    if not INSTRUMENT_CODE_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("--code는 6자리 영문/숫자 종목코드여야 합니다.")
    return value.upper()


def sector_code(value: str) -> str:
    if not SECTOR_CODE_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("--code는 3자리 키움 업종코드여야 합니다.")
    return value


def date_yyyymmdd(value: str) -> str:
    if not DATE_YYYYMMDD_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("날짜는 YYYYMMDD 형식이어야 합니다.")
    try:
        datetime.strptime(value, "%Y%m%d")
    except ValueError as exc:
        raise argparse.ArgumentTypeError("날짜가 실제 달력 날짜가 아닙니다.") from exc
    return value


def adjusted_price_flag(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "adjusted"}:
        return "1"
    if normalized in {"0", "false", "no", "n", "raw", "unadjusted"}:
        return "0"
    raise argparse.ArgumentTypeError(
        "--adjusted 값은 0, 1, true, false, adjusted, raw 중 하나여야 합니다."
    )


def positive_int_string(value: str) -> str:
    if not INTEGER_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("값은 양의 정수여야 합니다.")
    if int(value) <= 0:
        raise argparse.ArgumentTypeError("값은 0보다 커야 합니다.")
    return value


def nonnegative_int_string(value: str) -> str:
    if not INTEGER_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("값은 0 이상의 정수여야 합니다.")
    if int(value) < 0:
        raise argparse.ArgumentTypeError("값은 0 이상이어야 합니다.")
    return value


def price_string(value: str) -> str:
    if not INTEGER_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("가격은 정수 문자열이어야 합니다.")
    if int(value) < 0:
        raise argparse.ArgumentTypeError("가격은 0 이상이어야 합니다.")
    return value


def order_id(value: str) -> str:
    if not ORDER_ID_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("주문번호는 키움 7자리 주문번호여야 합니다.")
    return value


def preview_order_id(value: str) -> str:
    if not PREVIEW_ORDER_ID_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("주문번호는 숫자만 입력할 수 있습니다.")
    return value
