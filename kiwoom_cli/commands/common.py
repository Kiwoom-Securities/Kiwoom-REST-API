"""Shared helpers for mapped resource command modules."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Iterable
from typing import Any

from kiwoom_cli.argument_maps import add_mapped_arguments, build_body
from kiwoom_cli.arguments import add_output_format_arg, add_runtime_args
from kiwoom_cli.executor import execute_rest_command
from kiwoom_cli.output import format_response
from kiwoom_cli.registry import get_implemented_command


CommandHelp = tuple[str, str]


def add_mapped_command_parser(
    subparsers: argparse._SubParsersAction,
    *,
    group: str,
    command: str,
    help_text: str,
    handler: Callable[[argparse.Namespace], None],
    parser_kwargs: dict[str, Any] | None = None,
) -> argparse.ArgumentParser:
    definition = get_implemented_command(group, command)
    kwargs = {"help": help_text}
    if parser_kwargs:
        kwargs.update(parser_kwargs)
    command_parser = subparsers.add_parser(command, **kwargs)
    add_mapped_arguments(command_parser, definition.command_path)
    add_output_format_arg(command_parser)
    add_runtime_args(command_parser)
    command_parser.set_defaults(handler=handler)
    return command_parser


def add_mapped_command_parsers(
    subparsers: argparse._SubParsersAction,
    *,
    group: str,
    commands: Iterable[CommandHelp],
    handler: Callable[[argparse.Namespace], None],
) -> None:
    for command, help_text in commands:
        add_mapped_command_parser(
            subparsers,
            group=group,
            command=command,
            help_text=help_text,
            handler=handler,
        )


def execute_mapped_rest_command(
    *,
    group: str,
    command: str,
    args: argparse.Namespace,
    redact_fields: Iterable[str] = (),
) -> None:
    definition = get_implemented_command(group, command)
    body = build_body(definition.command_path, args)
    response = execute_rest_command(
        definition,
        body=body,
        mode=args.mode,
        profile=args.profile,
    )
    print(format_response(response, output_format=args.format, redact_fields=redact_fields))
