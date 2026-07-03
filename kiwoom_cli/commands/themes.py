"""Theme resource commands."""

from __future__ import annotations

import argparse

from kiwoom_cli.commands.common import add_mapped_command_parsers, execute_mapped_rest_command


THEME_COMMANDS = (
    ("by-stock", "테마 구성 종목을 조회합니다."),
    ("lookup", "테마 그룹을 조회합니다."),
)


def add_themes_parser(subparsers: argparse._SubParsersAction) -> None:
    themes_parser = subparsers.add_parser("themes", help="테마 조회 명령입니다.")
    themes_subparsers = themes_parser.add_subparsers(dest="themes_command", required=True)
    add_mapped_command_parsers(
        themes_subparsers,
        group="themes",
        commands=THEME_COMMANDS,
        handler=handle_themes_mapped,
    )


def handle_themes_mapped(args: argparse.Namespace) -> None:
    _execute(args.themes_command, args)


def _execute(command: str, args: argparse.Namespace) -> None:
    execute_mapped_rest_command(group="themes", command=command, args=args)
