"""Institution/foreign investor resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command


INVESTOR_COMMANDS = (
    ("by-stock", "종목별 외국인 매매동향을 조회합니다."),
    ("lookup", "종목별 기관 정보를 조회합니다."),
    ("trend", "기관/외국인 연속매매 현황을 조회합니다."),
    ("gold-status", "금현물 투자자 현황을 조회합니다."),
)


def add_investors_parser(subparsers: argparse._SubParsersAction) -> None:
    investors_parser = subparsers.add_parser("investors", help="기관/외국인 조회 명령입니다.")
    investors_subparsers = investors_parser.add_subparsers(dest="investors_command", required=True)
    add_mapped_command_parsers(
        investors_subparsers,
        group="investors",
        commands=INVESTOR_COMMANDS,
        handler=handle_investors_mapped,
    )


def handle_investors_mapped(args: argparse.Namespace) -> None:
    _execute(args.investors_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    execute_mapped_rest_command(group="investors", command=command, args=args)
