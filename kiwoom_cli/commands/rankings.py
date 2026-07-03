"""Ranking resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command


def add_rankings_parser(subparsers: argparse._SubParsersAction) -> None:
    rankings_parser = subparsers.add_parser("rankings", help="순위 정보 조회 명령입니다.")
    rankings_subparsers = rankings_parser.add_subparsers(dest="rankings_command", required=True)

    add_mapped_command_parsers(
        rankings_subparsers,
        group="rankings",
        commands=(
            ("orderbook-balance", "호가잔량 상위를 조회합니다."),
            ("orderbook-balance-spike", "호가잔량 급증을 조회합니다."),
            ("balance-rate-spike", "잔량율 급증을 조회합니다."),
            ("volume-spike", "거래량 급증을 조회합니다."),
            ("previous-change-rate", "전일대비 등락률 상위를 조회합니다."),
            ("list-fills", "예상체결 등락률 상위를 조회합니다."),
            ("today-volume", "당일 거래량 상위를 조회합니다."),
            ("previous-volume", "전일 거래량 상위를 조회합니다."),
            ("amount", "거래대금 상위를 조회합니다."),
            ("credit-ratio", "신용비율 상위를 조회합니다."),
            ("foreign-period-trades", "외인 기간별 매매 상위를 조회합니다."),
            ("foreign-continuous-net", "외인 연속 순매매 상위를 조회합니다."),
            ("foreign-limit-usage", "외인 한도소진율 증가 상위를 조회합니다."),
            ("foreign-broker-trades", "외국계 창구 매매 상위를 조회합니다."),
            ("broker-by-stock", "종목별 증권사 순위를 조회합니다."),
            ("broker-trades", "증권사별 매매 상위를 조회합니다."),
            ("stock-main-brokers", "당일 주요 거래원을 조회합니다."),
            ("net-buy-brokers", "순매수 거래원 순위를 조회합니다."),
            ("top-exit-brokers", "당일 상위 이탈원을 조회합니다."),
            ("same-net-trades", "동일 순매매 순위를 조회합니다."),
            ("investor-intraday", "장중 투자자별 매매 상위를 조회합니다."),
            ("after-hours-change-rate", "시간외 단일가 등락율 순위를 조회합니다."),
            ("foreign-institution-trades", "외국인기관 매매 상위를 조회합니다."),
        ),
        handler=handle_rankings_mapped,
    )


def handle_rankings_mapped(args: argparse.Namespace) -> None:
    execute_mapped_rest_command(group="rankings", command=args.rankings_command, args=args)
