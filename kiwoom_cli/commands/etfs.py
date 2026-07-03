"""ETF resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command


ETF_COMMANDS = (
    ("info", "ETF 종목정보를 조회합니다."),
    ("daily", "ETF 일별추이를 조회합니다."),
    ("profit", "ETF 수익률을 조회합니다."),
    ("list", "ETF 전체 시세를 조회합니다."),
    ("intraday-trend", "ETF 시간대별 추이를 조회합니다."),
    ("intraday-fills", "ETF 시간대별 체결을 조회합니다."),
    ("daily-fills", "ETF 일자별 체결을 조회합니다."),
    ("nav", "ETF NAV 관련 정보를 조회합니다."),
    ("foreign-trend", "ETF 외국인 순매수 추이를 조회합니다."),
)


def add_etfs_parser(subparsers: argparse._SubParsersAction) -> None:
    etfs_parser = subparsers.add_parser("etfs", help="ETF 조회 명령입니다.")
    etfs_subparsers = etfs_parser.add_subparsers(dest="etfs_command", required=True)
    add_mapped_command_parsers(
        etfs_subparsers,
        group="etfs",
        commands=ETF_COMMANDS,
        handler=handle_etfs_mapped,
    )


def handle_etfs_mapped(args: argparse.Namespace) -> None:
    _execute(args.etfs_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    execute_mapped_rest_command(group="etfs", command=command, args=args)
