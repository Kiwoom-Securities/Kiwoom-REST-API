"""Quote resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command


QUOTE_COMMANDS = (
    ("price", "종목 현재가 시세를 조회합니다."),
    ("balance", "프로그램매매 차익잔고 추이를 조회합니다."),
    ("by-stock", "종목별 기관 매매 추이를 조회합니다."),
    ("list", "신주인수권 전체 시세를 조회합니다."),
    ("gold-price", "금현물 시세를 조회합니다."),
    ("gold-fills", "금현물 체결 추이를 조회합니다."),
    ("gold-daily", "금현물 일별 추이를 조회합니다."),
    ("gold-expected", "금현물 예상체결을 조회합니다."),
    ("multi-period", "주식 일/주/월/시/분 요약 시세를 조회합니다."),
    ("intraday-minute", "주식 시분 시세를 조회합니다."),
    ("institution-daily", "일별 기관 매매 종목을 조회합니다."),
    ("strength-time", "체결강도 시간별 추이를 조회합니다."),
    ("strength-daily", "체결강도 일별 추이를 조회합니다."),
    ("investor-intraday", "장중 투자자별 매매를 조회합니다."),
    ("investor-after-close", "장마감 후 투자자별 매매를 조회합니다."),
    ("broker-trend", "증권사별 종목 매매 동향을 조회합니다."),
    ("daily-price", "일별 주가를 조회합니다."),
    ("after-hours", "시간외 단일가를 조회합니다."),
    ("program-time", "프로그램매매 시간대별 추이를 조회합니다."),
    ("program-cumulative", "프로그램매매 누적 추이를 조회합니다."),
    ("program-by-stock", "종목 시간별 프로그램매매 추이를 조회합니다."),
    ("program-daily", "프로그램매매 일자별 추이를 조회합니다."),
    ("stock-program-daily", "종목 일별 프로그램매매 추이를 조회합니다."),
)


def add_quotes_parser(subparsers: argparse._SubParsersAction) -> None:
    quotes_parser = subparsers.add_parser("quotes", help="현재가와 시세 조회 명령입니다.")
    quotes_subparsers = quotes_parser.add_subparsers(dest="quotes_command", required=True)
    add_mapped_command_parsers(
        quotes_subparsers,
        group="quotes",
        commands=QUOTE_COMMANDS,
        handler=handle_quotes_mapped,
    )


def handle_quotes_mapped(args: argparse.Namespace) -> None:
    _execute(args.quotes_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    execute_mapped_rest_command(group="quotes", command=command, args=args)
