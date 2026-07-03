"""Account resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command
from kiwoom_cli.output import ACCOUNT_REDACT_FIELDS


def add_accounts_parser(subparsers: argparse._SubParsersAction) -> None:
    accounts_parser = subparsers.add_parser("accounts", help="계좌 조회 명령입니다.")
    accounts_subparsers = accounts_parser.add_subparsers(dest="accounts_command", required=True)

    add_mapped_command_parsers(
        accounts_subparsers,
        group="accounts",
        commands=(
            ("list", "계좌번호 목록을 조회합니다."),
            ("daily-balance-return", "일별잔고수익률을 조회합니다."),
            ("realized-profit-stock-daily", "일자별 종목별 실현손익을 일자 기준으로 조회합니다."),
            ("realized-profit-period-stock", "일자별 종목별 실현손익을 기간 기준으로 조회합니다."),
            ("realized-profit-daily", "일자별 실현손익을 조회합니다."),
            ("realized-profit-today-detail", "당일 실현손익 상세를 조회합니다."),
            ("return-rate", "계좌수익률을 조회합니다."),
            ("day-trading-log", "당일매매일지를 조회합니다."),
            ("cash", "예수금 상세 현황을 조회합니다."),
            ("estimated-assets-daily", "일별 추정예탁자산 현황을 조회합니다."),
            ("assets", "추정자산을 조회합니다."),
            ("valuation", "계좌평가 현황을 조회합니다."),
            ("fill-balance", "체결잔고를 조회합니다."),
            ("order-fill-detail", "계좌별 주문체결내역 상세를 조회합니다."),
            ("next-settlement", "계좌별 익일결제 예정내역을 조회합니다."),
            ("order-fill-status", "계좌별 주문체결 현황을 조회합니다."),
            ("credit-margin", "신용보증금율별 주문가능수량을 조회합니다."),
            ("margin-details", "증거금 세부내역을 조회합니다."),
            ("transaction-history", "위탁종합 거래내역을 조회합니다."),
            ("daily-return-detail", "일별 계좌수익률 상세현황을 조회합니다."),
            ("today-status", "계좌별 당일현황을 조회합니다."),
            ("holdings", "계좌평가 잔고내역을 조회합니다."),
            ("gold-balance", "금현물 잔고를 조회합니다."),
            ("gold-cash", "금현물 예수금을 조회합니다."),
            ("gold-all-order-fills", "금현물 주문체결 전체를 조회합니다."),
            ("gold-order-fills", "금현물 주문체결을 조회합니다."),
            ("gold-transactions", "금현물 거래내역을 조회합니다."),
            ("gold-open-orders", "금현물 미체결을 조회합니다."),
        ),
        handler=handle_accounts_mapped,
    )


def handle_accounts_mapped(args: argparse.Namespace) -> None:
    _execute(args.accounts_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    execute_mapped_rest_command(
        group="accounts",
        command=command,
        args=args,
        redact_fields=ACCOUNT_REDACT_FIELDS,
    )
