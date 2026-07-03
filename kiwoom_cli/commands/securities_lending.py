"""Securities lending resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command


def add_securities_lending_parser(subparsers: argparse._SubParsersAction) -> None:
    lending_parser = subparsers.add_parser("securities-lending", help="대차거래 조회 명령입니다.")
    lending_subparsers = lending_parser.add_subparsers(
        dest="securities_lending_command",
        required=True,
    )

    add_mapped_command_parsers(
        lending_subparsers,
        group="securities-lending",
        commands=(
            ("by-stock", "종목별 대차거래 추이를 조회합니다."),
            ("trend", "대차거래 추이를 조회합니다."),
            ("list", "대차거래 상위 종목을 조회합니다."),
            ("lookup", "대차거래 내역을 조회합니다."),
        ),
        handler=handle_securities_lending_mapped,
    )


def handle_securities_lending_mapped(args: argparse.Namespace) -> None:
    _execute(args.securities_lending_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    execute_mapped_rest_command(group="securities-lending", command=command, args=args)
