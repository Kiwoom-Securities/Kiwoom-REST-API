"""ELW resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command


ELW_COMMANDS = (
    ("daily", "ELW 일별 민감도 지표를 조회합니다."),
    ("balance", "ELW LP 보유 일별 추이를 조회합니다."),
    ("conditions", "ELW 조건검색 결과를 조회합니다."),
    ("sensitivity", "ELW 민감도 지표를 조회합니다."),
    ("price-move", "ELW 가격 급등락을 조회합니다."),
    ("broker-net", "거래원별 ELW 순매매 상위를 조회합니다."),
    ("divergence", "ELW 괴리율을 조회합니다."),
    ("change-rank", "ELW 등락율 순위를 조회합니다."),
    ("balance-rank", "ELW 잔량 순위를 조회합니다."),
    ("proximity", "ELW 근접율을 조회합니다."),
    ("details", "ELW 종목 상세정보를 조회합니다."),
)


def add_elws_parser(subparsers: argparse._SubParsersAction) -> None:
    elws_parser = subparsers.add_parser("elws", help="ELW 조회 명령입니다.")
    elws_subparsers = elws_parser.add_subparsers(dest="elws_command", required=True)
    add_mapped_command_parsers(
        elws_subparsers,
        group="elws",
        commands=ELW_COMMANDS,
        handler=handle_elws_mapped,
    )


def handle_elws_mapped(args: argparse.Namespace) -> None:
    _execute(args.elws_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    execute_mapped_rest_command(group="elws", command=command, args=args)
