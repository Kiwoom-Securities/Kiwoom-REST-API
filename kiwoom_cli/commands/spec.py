"""Spec search commands."""

from __future__ import annotations

import argparse

from kiwoom.specs import (
    format_api_groups,
    format_api_spec,
    format_api_summaries,
    format_search_results,
    get_api_spec,
    list_api_groups,
    list_api_summaries,
    search_api_specs,
)
from kiwoom_cli.output import format_payload


def add_spec_parser(subparsers: argparse._SubParsersAction) -> None:
    spec_parser = subparsers.add_parser("spec", help="API 스펙을 검색합니다.")
    spec_subparsers = spec_parser.add_subparsers(dest="spec_command", required=True)

    search_parser = spec_subparsers.add_parser(
        "search", help="API ID, 이름, 요청 필드로 스펙을 검색합니다."
    )
    search_parser.add_argument("query", help="검색어")
    search_parser.add_argument("--limit", type=_positive_int, default=10, help="최대 결과 수")
    search_parser.set_defaults(handler=handle_spec_search)

    show_parser = spec_subparsers.add_parser("show", help="API ID로 스펙 상세를 표시합니다.")
    show_parser.add_argument("api_id", help="API ID")
    show_parser.add_argument(
        "--format", choices=("pretty", "json", "yaml"), default="pretty", help="출력 형식"
    )
    show_parser.set_defaults(handler=handle_spec_show)

    groups_parser = spec_subparsers.add_parser("groups", help="API 그룹과 API 수를 표시합니다.")
    groups_parser.add_argument(
        "--format", choices=("pretty", "json", "yaml"), default="pretty", help="출력 형식"
    )
    groups_parser.set_defaults(handler=handle_spec_groups)

    apis_parser = spec_subparsers.add_parser("apis", help="API 목록을 표시합니다.")
    apis_parser.add_argument("--group", help="메뉴 경로에 포함될 그룹명")
    apis_parser.add_argument("--limit", type=_positive_int, help="최대 결과 수")
    apis_parser.add_argument(
        "--format", choices=("pretty", "json", "yaml"), default="pretty", help="출력 형식"
    )
    apis_parser.set_defaults(handler=handle_spec_apis)


def handle_spec_search(args: argparse.Namespace) -> None:
    results = search_api_specs(args.query, limit=args.limit)
    print(format_search_results(results))


def handle_spec_show(args: argparse.Namespace) -> None:
    api_payload = get_api_spec(args.api_id)
    print(
        _format_spec_payload(
            api_payload, output_format=args.format, pretty_formatter=format_api_spec
        )
    )


def handle_spec_groups(args: argparse.Namespace) -> None:
    groups = list_api_groups()
    print(
        _format_spec_payload(
            groups, output_format=args.format, pretty_formatter=format_api_groups
        )
    )


def handle_spec_apis(args: argparse.Namespace) -> None:
    apis = list_api_summaries(group=args.group, limit=args.limit)
    print(
        _format_spec_payload(
            apis, output_format=args.format, pretty_formatter=format_api_summaries
        )
    )


def _format_spec_payload(payload, *, output_format: str, pretty_formatter) -> str:
    if output_format == "pretty":
        return pretty_formatter(payload)
    return format_payload(payload, output_format=output_format)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--limit 값은 정수여야 합니다.") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("--limit 값은 0보다 커야 합니다.")
    return parsed
