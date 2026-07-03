"""Short-selling resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parser, execute_mapped_rest_command


def add_short_selling_parser(subparsers: argparse._SubParsersAction) -> None:
    short_parser = subparsers.add_parser("short-selling", help="공매도 조회 명령입니다.")
    short_subparsers = short_parser.add_subparsers(dest="short_selling_command", required=True)

    add_mapped_command_parser(
        short_subparsers,
        group="short-selling",
        command="trend",
        help_text="종목별 공매도 추이를 조회합니다.",
        handler=handle_short_selling_mapped,
    )


def handle_short_selling_mapped(args: argparse.Namespace) -> None:
    execute_mapped_rest_command(
        group="short-selling", command=args.short_selling_command, args=args
    )
