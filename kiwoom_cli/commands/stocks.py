"""Stock resource commands."""

from __future__ import annotations

import argparse
from typing import Any

from kiwoom_cli.argument_maps import build_body
from kiwoom_cli.commands.common import add_mapped_command_parsers
from kiwoom_cli.executor import execute_rest_command
from kiwoom_cli.output import format_payload, format_response
from kiwoom_cli.registry import get_implemented_command


STOCK_COMMANDS = (
    ("info", "종목 기본정보를 조회합니다."),
    ("trend", "종목 신용매매 동향을 조회합니다."),
    ("realtime-rank", "실시간 종목 조회 순위를 조회합니다."),
    ("brokers", "주식 거래원을 조회합니다."),
    ("fills", "체결 정보를 조회합니다."),
    ("daily-trades", "일별 거래 상세를 조회합니다."),
    ("new-high-low", "신고가/신저가 종목을 조회합니다."),
    ("limit-move", "상하한가/상승하락 종목을 조회합니다."),
    ("high-low-near", "고저가 근접 종목을 조회합니다."),
    ("price-spike", "가격 급등락 종목을 조회합니다."),
    ("volume-renewal", "거래량 갱신 종목을 조회합니다."),
    ("volume-zone", "매물대 집중 종목을 조회합니다."),
    ("valuation-rank", "고저 PER/PBR/ROE 순위를 조회합니다."),
    ("open-change", "시가 대비 등락률을 조회합니다."),
    ("broker-volume-zone", "거래원 매물대 분석을 조회합니다."),
    ("broker-instant-volume", "거래원 순간 거래량을 조회합니다."),
    ("vi-triggered", "변동성완화장치 발동 종목을 조회합니다."),
    ("today-previous-fills", "당일/전일 체결량을 조회합니다."),
    ("investor-daily", "투자자별 일별 매매 종목을 조회합니다."),
    ("investor-by-stock", "종목별 투자자/기관 매매를 조회합니다."),
    ("investor-by-stock-total", "종목별 투자자/기관 매매 합계를 조회합니다."),
    ("today-previous-trades", "당일/전일 체결을 조회합니다."),
    ("watchlist-info", "관심종목 정보를 조회합니다."),
    ("info-list", "종목정보 리스트를 조회합니다."),
    ("info-detail", "종목정보를 조회합니다."),
    ("sector-codes", "업종코드 리스트를 조회합니다."),
    ("member-firms", "회원사 리스트를 조회합니다."),
    ("program-net-top", "프로그램 순매수 상위 50을 조회합니다."),
    ("program-by-stock", "종목별 프로그램매매 현황을 조회합니다."),
    ("credit-loanable", "신용융자 가능 종목을 조회합니다."),
    ("credit-loanable-check", "신용융자 가능 여부를 조회합니다."),
)


def add_stocks_parser(subparsers: argparse._SubParsersAction) -> None:
    stocks_parser = subparsers.add_parser("stocks", help="종목 정보 조회 명령입니다.")
    stocks_subparsers = stocks_parser.add_subparsers(dest="stocks_command", required=True)
    add_mapped_command_parsers(
        stocks_subparsers,
        group="stocks",
        commands=STOCK_COMMANDS,
        handler=handle_stocks_mapped,
    )


def handle_stocks_mapped(args: argparse.Namespace) -> None:
    _execute(args.stocks_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    definition = get_implemented_command("stocks", command)
    body = build_body(definition.command_path, args)
    response = execute_rest_command(
        definition,
        body=body,
        mode=args.mode,
        profile=args.profile,
    )
    if command == "credit-loanable-check":
        payload = _with_credit_loanable_status(response.body)
        print(format_payload(payload, output_format=args.format))
        return
    print(format_response(response, output_format=args.format))


def _with_credit_loanable_status(payload: Any) -> Any:
    if not isinstance(payload, dict):
        return payload
    normalized = dict(payload)
    normalized["loanable"] = _derive_loanable(payload.get("crd_alow_yn"))
    return normalized


def _derive_loanable(value: Any) -> bool | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if "불가능" in text:
        return False
    if "가능" in text:
        return True
    return None
