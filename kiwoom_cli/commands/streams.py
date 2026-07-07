"""WebSocket stream commands."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Any

from kiwoom.realtime import decode_realtime_message_named
from kiwoom_cli.argument_maps import (
    TYPE_PARSERS,
    add_mapped_arguments,
    build_body,
    get_argument_definitions,
)
from kiwoom_cli.arguments import add_output_format_arg, add_runtime_args
from kiwoom_cli.errors import CliInputError
from kiwoom_cli.executor import (
    execute_condition_command,
    execute_websocket_request_once,
    execute_websocket_stream,
)
from kiwoom_cli.output import format_payload
from kiwoom_cli.registry import get_implemented_command


CONDITION_COMMANDS = {
    "conditions-search",
    "conditions-subscribe",
    "conditions-unsubscribe",
}
DEFAULT_CONDITION_MAX_WAIT_SECONDS = 15.0
DEFAULT_STREAM_MAX_WAIT_SECONDS = 15.0
CONDITION_HTS_NOTE = (
    "조건검색식 생성/수정은 영웅문 HTS에서 해야 합니다. "
    "CLI는 HTS에 저장된 조건식을 목록 조회, 선택, 조회, 구독, 해제만 합니다."
)

# Account numbers stay redacted; order numbers are operational identifiers the
# user needs and are not redacted.
STREAM_REDACT_FIELDS = (
    "acctNo",
    "acnt_no",
    "acntNo",
)


def add_streams_parser(subparsers: argparse._SubParsersAction) -> None:
    streams_parser = subparsers.add_parser("streams", help="WebSocket 실시간/조건검색 명령입니다.")
    streams_subparsers = streams_parser.add_subparsers(dest="streams_command", required=True)

    for command, help_text in (
        ("conditions-list", "조건검색식 목록을 조회합니다."),
        ("conditions-search", "조건검색 결과를 1회 조회합니다."),
        ("conditions-subscribe", "조건검색 실시간 결과를 구독합니다."),
        ("conditions-unsubscribe", "조건검색 실시간 구독을 해제합니다."),
        ("order-fills", "주문체결 실시간 이벤트를 구독합니다."),
        ("balance", "잔고 실시간 이벤트를 구독합니다."),
        ("momentum", "주식기세 실시간 데이터를 구독합니다."),
        ("trades", "주식체결 실시간 데이터를 구독합니다."),
        ("best-quotes", "주식우선호가 실시간 데이터를 구독합니다."),
        ("orderbook", "주식호가잔량 실시간 데이터를 구독합니다."),
        ("after-hours-orderbook", "주식시간외호가 실시간 데이터를 구독합니다."),
        ("brokers", "주식당일거래원 실시간 데이터를 구독합니다."),
        ("etf-nav", "ETF NAV 실시간 데이터를 구독합니다."),
        ("expected-fills", "주식예상체결 실시간 데이터를 구독합니다."),
        ("gold-conversion", "국제금환산가격 실시간 데이터를 구독합니다."),
        ("sector-index", "업종지수 실시간 데이터를 구독합니다."),
        ("sector-change", "업종등락 실시간 데이터를 구독합니다."),
        ("stock-info", "주식종목정보 실시간 데이터를 구독합니다."),
        ("elw-theory", "ELW 이론가 실시간 데이터를 구독합니다."),
        ("market-open", "장시작시간 실시간 데이터를 구독합니다."),
        ("elw-indicator", "ELW 지표 실시간 데이터를 구독합니다."),
        ("program-trades", "종목프로그램매매 실시간 데이터를 구독합니다."),
        ("vi", "VI발동/해제 실시간 데이터를 구독합니다."),
    ):
        definition = get_implemented_command("streams", command)
        parser_kwargs: dict[str, Any] = {"help": help_text}
        if command.startswith("conditions-"):
            parser_kwargs.update(
                {
                    "description": f"{help_text} {CONDITION_HTS_NOTE}",
                    "epilog": CONDITION_HTS_NOTE,
                }
            )
        command_parser = streams_subparsers.add_parser(command, **parser_kwargs)
        code_action_overrides = (
            {"code": "append"}
            if _command_has_code_argument(definition.command_path)
            else {}
        )
        code_required_overrides = {"code": False} if code_action_overrides else {}
        add_mapped_arguments(
            command_parser,
            definition.command_path,
            required_overrides=code_required_overrides,
            action_overrides=code_action_overrides,
        )
        if command == "conditions-subscribe":
            _add_count_duration_args(
                command_parser,
                duration_type=_positive_duration,
                duration_help="조건검색 REAL 데이터를 기다릴 최대 시간(초)",
            )
            command_parser.add_argument(
                "--check",
                action="store_true",
                help="등록 확인용으로 2초 동안 수집 후 REAL 수신 여부와 관계없이 종료합니다.",
            )
        if _supports_foreground_stream_options(command) and code_action_overrides:
            command_parser.add_argument(
                "--codes",
                dest="codes",
                help="쉼표로 구분한 복수 등록 요소/종목코드입니다. --code 반복 입력과 함께 사용할 수 있습니다.",
            )
        if _supports_foreground_stream_options(command):
            _add_count_duration_args(command_parser)
            command_parser.add_argument(
                "--watch",
                action="store_true",
                help="시간/건수 제한 없이 계속 수신합니다.",
            )
            command_parser.add_argument(
                "--check",
                action="store_true",
                help="등록 확인용으로 2초 동안 수신 후 종료합니다.",
            )
            command_parser.add_argument(
                "--named",
                action="store_true",
                help="REAL values FID를 스키마 기반 이름으로 변환해 출력합니다.",
            )
            command_parser.add_argument(
                "--output",
                type=Path,
                help="이벤트를 stdout 대신 이 JSONL 파일에 씁니다.",
            )
        add_output_format_arg(command_parser)
        add_runtime_args(command_parser)
        command_parser.set_defaults(handler=handle_streams_mapped)


def handle_streams_mapped(args: argparse.Namespace) -> None:
    asyncio.run(_run_streams_command(args))


async def _run_streams_command(args: argparse.Namespace) -> None:
    definition = get_implemented_command("streams", args.streams_command)
    body = _build_websocket_body(definition.command_path, args)
    redact_fields = STREAM_REDACT_FIELDS if definition.safety_policy == "account_read" else ()

    if args.streams_command in CONDITION_COMMANDS:
        condition_max_messages, condition_max_wait_seconds = _resolve_condition_limits(args)
        response = await execute_condition_command(
            args.streams_command,
            definition,
            body=body,
            mode=args.mode,
            profile=args.profile,
            max_messages=condition_max_messages,
            max_wait_seconds=condition_max_wait_seconds,
            exchange=getattr(args, "exchange", None),
        )
        print(format_payload(response, output_format=args.format, redact_fields=redact_fields))
        return

    if _is_subscription_command(args.streams_command):
        if body.get("trnm") == "REMOVE":
            response = await execute_websocket_request_once(
                definition,
                body=body,
                mode=args.mode,
                profile=args.profile,
            )
            print(format_payload(response, output_format=args.format, redact_fields=redact_fields))
            return

        max_messages, max_wait_seconds = _resolve_stream_limits(args)
        line_mode = _use_line_mode(args.format, max_messages=max_messages, max_wait_seconds=max_wait_seconds)
        messages: list[Any] = []
        try:
            async for message in execute_websocket_stream(
                definition,
                body=body,
                mode=args.mode,
                profile=args.profile,
                max_messages=max_messages,
                max_wait_seconds=max_wait_seconds,
            ):
                if getattr(args, "named", False):
                    message = decode_realtime_message_named(message)
                if line_mode:
                    _emit_stream_payload(
                        message,
                        args=args,
                        redact_fields=redact_fields,
                        append=True,
                    )
                else:
                    messages.append(message)
        except Exception:
            if not line_mode and messages:
                _emit_stream_payload(
                    messages,
                    args=args,
                    redact_fields=redact_fields,
                    append=False,
                )
            raise
        if not line_mode:
            _emit_stream_payload(
                messages,
                args=args,
                redact_fields=redact_fields,
                append=False,
            )
        return

    response = await execute_websocket_request_once(
        definition,
        body=body,
        mode=args.mode,
        profile=args.profile,
    )
    print(format_payload(response, output_format=args.format, redact_fields=redact_fields))


def _build_websocket_body(command_path: str, args: argparse.Namespace) -> dict[str, Any]:
    _merge_stream_code_args(command_path, args)
    body = build_body(command_path, args)
    if "type" not in body:
        return body

    stream_type = body.pop("type")
    item_value = body.pop("item", "")
    if isinstance(item_value, list):
        raw_items = item_value
    else:
        raw_items = str(item_value).split(",")
    items = [str(item).strip() for item in raw_items if str(item).strip()]
    if not items:
        items = [""]
    body["data"] = [{"item": items, "type": [stream_type]}]
    return body


def _command_has_code_argument(command_path: str) -> bool:
    return any(
        definition.dest == "code" and definition.option == "--code"
        for definition in get_argument_definitions(command_path)
    )


def _supports_foreground_stream_options(command: str) -> bool:
    return command not in {
        "conditions-list",
        "conditions-search",
        "conditions-subscribe",
        "conditions-unsubscribe",
    }


def _emit_stream_payload(
    payload: Any,
    *,
    args: argparse.Namespace,
    redact_fields: tuple[str, ...],
    append: bool,
) -> None:
    rendered = format_payload(payload, output_format=args.format, redact_fields=redact_fields)
    output_path = getattr(args, "output", None)
    if output_path is None:
        print(rendered, flush=True)
        return
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if append else "w"
    with path.open(mode, encoding="utf-8") as file:
        file.write(rendered)
        file.write("\n")


def _merge_stream_code_args(command_path: str, args: argparse.Namespace) -> None:
    code_definition = next(
        (
            definition
            for definition in get_argument_definitions(command_path)
            if definition.dest == "code"
        ),
        None,
    )
    if code_definition is None:
        return

    values: list[str] = []
    code_value = getattr(args, "code", None)
    if isinstance(code_value, list):
        values.extend(str(item) for item in code_value if str(item).strip())
    elif code_value not in (None, ""):
        values.extend(str(code_value).split(","))

    codes_value = getattr(args, "codes", None)
    if codes_value not in (None, ""):
        for item in str(codes_value).split(","):
            stripped = item.strip()
            if stripped:
                values.append(_validate_stream_code_item(code_definition, stripped, source="--codes"))

    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        stripped = str(value).strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        deduped.append(stripped)
    if deduped:
        setattr(args, "code", ",".join(deduped))
    elif code_definition.required:
        raise CliInputError(f"{command_path}: --code 또는 --codes 옵션이 필요합니다.")


def _validate_stream_code_item(definition: Any, value: str, *, source: str) -> str:
    parser = TYPE_PARSERS.get(definition.type_name)
    try:
        parsed = parser(value) if parser is not None else value
    except argparse.ArgumentTypeError as exc:
        raise CliInputError(f"{source} 값 오류: {exc}") from exc
    if definition.choices and parsed not in definition.choices:
        choices = ", ".join(definition.choices)
        raise CliInputError(f"{source} 값 오류: {parsed!r} 값은 다음 중 하나여야 합니다: {choices}")
    return str(parsed)


def _resolve_stream_limits(args: argparse.Namespace) -> tuple[int, float | str]:
    count = getattr(args, "count", None)
    duration = getattr(args, "duration", None)
    watch = bool(getattr(args, "watch", False))
    check = bool(getattr(args, "check", False))

    if check and (watch or count is not None or duration is not None):
        raise CliInputError("--check는 --watch, --count, --duration과 함께 사용할 수 없습니다.")
    if watch and count is not None:
        raise CliInputError("--watch는 --count와 함께 사용할 수 없습니다.")

    if check:
        return 0, 2.0
    if watch:
        if getattr(args, "format", "pretty") in {"json", "yaml"}:
            raise CliInputError(
                "--watch에는 --format jsonl 또는 pretty를 사용해야 합니다. "
                "--format json/yaml은 --count 또는 --duration으로 종료 조건을 지정해 주세요."
            )
        return 0, 0.0

    max_messages = count if count is not None else 1
    max_wait_seconds = duration if duration is not None else DEFAULT_STREAM_MAX_WAIT_SECONDS
    return _normalize_max_messages(max_messages), max_wait_seconds


def _resolve_condition_limits(args: argparse.Namespace) -> tuple[int, float]:
    count = getattr(args, "count", None)
    duration = getattr(args, "duration", None)
    check = bool(getattr(args, "check", False))

    if check and (count is not None or duration is not None):
        raise CliInputError("--check는 --count 또는 --duration과 함께 사용할 수 없습니다.")
    if check:
        return 0, 2.0
    return count if count is not None else 1, duration or DEFAULT_CONDITION_MAX_WAIT_SECONDS


def _add_count_duration_args(
    parser: argparse.ArgumentParser,
    *,
    duration_type: Any = None,
    duration_help: str = "REAL 데이터를 기다릴 최대 시간(초)",
) -> None:
    resolved_duration_type = duration_type or _nonnegative_duration
    parser.add_argument(
        "--count",
        type=_positive_count,
        help="수신 후 종료할 REAL 데이터 수",
    )
    parser.add_argument(
        "--duration",
        type=resolved_duration_type,
        help=duration_help,
    )


def _positive_count(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--count 값은 정수여야 합니다.") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("--count 값은 0보다 커야 합니다.")
    return parsed


def _nonnegative_duration(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--duration 값은 숫자여야 합니다.") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("--duration 값은 0 이상이어야 합니다.")
    return parsed


def _positive_duration(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--duration 값은 숫자여야 합니다.") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("--duration 값은 0보다 커야 합니다.")
    return parsed


def _is_subscription_command(command: str) -> bool:
    return command not in {"conditions-list", "conditions-search", "conditions-unsubscribe"}


def _normalize_max_messages(value: int | str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise CliInputError("stream 메시지 수는 정수여야 합니다.") from exc
    if parsed < 0:
        raise CliInputError("stream 메시지 수는 0 이상이어야 합니다.")
    return parsed


def _use_line_mode(
    output_format: str,
    *,
    max_messages: int,
    max_wait_seconds: float | int | str,
) -> bool:
    if output_format == "jsonl":
        return True
    try:
        wait_limit = float(max_wait_seconds)
    except (TypeError, ValueError):
        wait_limit = DEFAULT_STREAM_MAX_WAIT_SECONDS
    return max_messages == 0 and wait_limit == 0
