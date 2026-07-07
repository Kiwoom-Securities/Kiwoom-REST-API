"""Orderbook resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command


ORDERBOOK_COMMANDS = (
    ("list", "종목 호가를 조회합니다."),
    ("gold", "금현물 호가를 조회합니다."),
)


def add_orderbooks_parser(subparsers: argparse._SubParsersAction) -> None:
    orderbooks_parser = subparsers.add_parser("orderbooks", help="호가 조회 명령입니다.")
    orderbooks_subparsers = orderbooks_parser.add_subparsers(dest="orderbooks_command", required=True)
    add_mapped_command_parsers(
        orderbooks_subparsers,
        group="orderbooks",
        commands=ORDERBOOK_COMMANDS,
        handler=handle_orderbooks_mapped,
    )


def handle_orderbooks_mapped(args: argparse.Namespace) -> None:
    _execute(args.orderbooks_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    execute_mapped_rest_command(group="orderbooks", command=command, args=args)
