"""Order commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.argument_maps import add_mapped_arguments, build_body
from kiwoom_cli.arguments import add_output_format_arg, add_runtime_args
from kiwoom_cli.commands.common import (
    add_mapped_command_parser,
    execute_mapped_rest_command,
)
from kiwoom_cli.executor import execute_rest_command
from kiwoom_cli.order_confirmation import (
    build_order_confirmation,
    format_order_confirmation,
)
from kiwoom_cli.output import ACCOUNT_REDACT_FIELDS, format_response
from kiwoom_cli.registry import get_implemented_command


def add_orders_parser(subparsers: argparse._SubParsersAction) -> None:
    orders_parser = subparsers.add_parser(
        "orders", help="주문 조회 및 주문 전송(--confirm) 명령입니다."
    )
    orders_subparsers = orders_parser.add_subparsers(
        dest="orders_command", required=True
    )

    for command, help_text in (
        ("chance", "주문 전 주문/인출 가능금액을 조회합니다."),
        ("margin", "증거금율별 주문가능수량을 조회합니다."),
        ("list-open", "미체결 주문을 조회합니다."),
        ("list-fills", "체결 주문을 조회합니다."),
        ("open-detail", "미체결 분할주문 상세를 조회합니다."),
    ):
        command_parser = add_mapped_command_parser(
            orders_subparsers,
            group="orders",
            command=command,
            help_text=help_text,
            handler=handle_order_read,
        )
        command_parser.set_defaults(order_command=command)

    for command, help_text in (
        ("buy", "매수 주문을 전송합니다 (--confirm 없으면 미전송 주문 확인)."),
        ("sell", "매도 주문을 전송합니다 (--confirm 없으면 미전송 주문 확인)."),
        ("modify", "정정 주문을 전송합니다 (--confirm 없으면 미전송 주문 확인)."),
        ("cancel", "취소 주문을 전송합니다 (--confirm 없으면 미전송 주문 확인)."),
        (
            "credit-buy",
            "신용 매수주문을 전송합니다 (--confirm 없으면 미전송 주문 확인).",
        ),
        (
            "credit-sell",
            "신용 매도주문을 전송합니다 (--confirm 없으면 미전송 주문 확인).",
        ),
        (
            "credit-modify",
            "신용 정정주문을 전송합니다 (--confirm 없으면 미전송 주문 확인).",
        ),
        (
            "credit-cancel",
            "신용 취소주문을 전송합니다 (--confirm 없으면 미전송 주문 확인).",
        ),
        (
            "gold-buy",
            "금현물 매수주문을 전송합니다 (--confirm 없으면 미전송 주문 확인).",
        ),
        (
            "gold-sell",
            "금현물 매도주문을 전송합니다 (--confirm 없으면 미전송 주문 확인).",
        ),
        (
            "gold-modify",
            "금현물 정정주문을 전송합니다 (--confirm 없으면 미전송 주문 확인).",
        ),
        (
            "gold-cancel",
            "금현물 취소주문을 전송합니다 (--confirm 없으면 미전송 주문 확인).",
        ),
    ):
        definition = get_implemented_command("orders", command)
        command_parser = orders_subparsers.add_parser(command, help=help_text)
        add_mapped_arguments(command_parser, definition.command_path)
        command_parser.add_argument(
            "--confirm",
            action="store_true",
            help="지정하면 실제 주문을 전송합니다. 미지정 시 미전송 주문 확인을 출력합니다.",
        )
        add_output_format_arg(command_parser)
        add_runtime_args(command_parser)
        command_parser.set_defaults(handler=handle_order_submit, order_command=command)


def handle_order_read(args: argparse.Namespace) -> None:
    execute_mapped_rest_command(
        group="orders",
        command=args.order_command,
        args=args,
        redact_fields=ACCOUNT_REDACT_FIELDS,
    )


def handle_order_submit(args: argparse.Namespace) -> None:
    definition = get_implemented_command("orders", args.order_command)
    body = build_body(definition.command_path, args)
    if not args.confirm:
        payload = build_order_confirmation(definition, args)
        print(format_order_confirmation(payload, output_format=args.format))
        return
    response = execute_rest_command(
        definition,
        body=body,
        mode=args.mode,
        profile=args.profile,
        confirm=True,
    )
    print(
        format_response(
            response, output_format=args.format, redact_fields=ACCOUNT_REDACT_FIELDS
        )
    )
