"""Candle/chart resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command


CANDLE_COMMANDS = (
    ("daily", "종목 일봉 차트를 조회합니다."),
    ("by-stock", "종목별 투자자/기관 차트를 조회합니다."),
    ("lookup", "장중 투자자별 매매 차트를 조회합니다."),
    ("stock-tick", "주식 틱 차트를 조회합니다."),
    ("stock-minute", "주식 분봉 차트를 조회합니다."),
    ("stock-weekly", "주식 주봉 차트를 조회합니다."),
    ("stock-monthly", "주식 월봉 차트를 조회합니다."),
    ("stock-yearly", "주식 년봉 차트를 조회합니다."),
    ("sector-tick", "업종 틱 차트를 조회합니다."),
    ("sector-minute", "업종 분봉 차트를 조회합니다."),
    ("sector-daily", "업종 일봉 차트를 조회합니다."),
    ("sector-weekly", "업종 주봉 차트를 조회합니다."),
    ("sector-monthly", "업종 월봉 차트를 조회합니다."),
    ("sector-yearly", "업종 년봉 차트를 조회합니다."),
    ("gold-tick", "금현물 틱 차트를 조회합니다."),
    ("gold-minute", "금현물 분봉 차트를 조회합니다."),
    ("gold-daily", "금현물 일봉 차트를 조회합니다."),
    ("gold-weekly", "금현물 주봉 차트를 조회합니다."),
    ("gold-monthly", "금현물 월봉 차트를 조회합니다."),
    ("gold-today-tick", "금현물 당일 틱 차트를 조회합니다."),
    ("gold-today-minute", "금현물 당일 분봉 차트를 조회합니다."),
)


def add_candles_parser(subparsers: argparse._SubParsersAction) -> None:
    candles_parser = subparsers.add_parser("candles", help="차트/캔들 조회 명령입니다.")
    candles_subparsers = candles_parser.add_subparsers(dest="candles_command", required=True)
    add_mapped_command_parsers(
        candles_subparsers,
        group="candles",
        commands=CANDLE_COMMANDS,
        handler=handle_candles_mapped,
    )


def handle_candles_mapped(args: argparse.Namespace) -> None:
    _execute(args.candles_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    execute_mapped_rest_command(group="candles", command=command, args=args)
