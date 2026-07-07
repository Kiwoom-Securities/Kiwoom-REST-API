"""Sector resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command


SECTOR_COMMANDS = (
    ("program", "종목 기준 업종 프로그램 매매를 조회합니다."),
    ("investor-flows", "업종별 투자자 순매수를 조회합니다."),
    ("price", "업종 현재가를 조회합니다."),
    ("stocks", "업종별 주가를 조회합니다."),
    ("indices", "전업종 지수를 조회합니다."),
    ("daily", "업종 현재가 일별 데이터를 조회합니다."),
)


def add_sectors_parser(subparsers: argparse._SubParsersAction) -> None:
    sectors_parser = subparsers.add_parser("sectors", help="업종 조회 명령입니다.")
    sectors_subparsers = sectors_parser.add_subparsers(dest="sectors_command", required=True)
    add_mapped_command_parsers(
        sectors_subparsers,
        group="sectors",
        commands=SECTOR_COMMANDS,
        handler=handle_sectors_mapped,
    )


def handle_sectors_mapped(args: argparse.Namespace) -> None:
    _execute(args.sectors_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    execute_mapped_rest_command(group="sectors", command=command, args=args)
