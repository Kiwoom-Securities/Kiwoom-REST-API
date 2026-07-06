import argparse
import re
import sys

import requests

from kiwoom import describe_selection
from kiwoom.core.errors import CredentialsNotFoundError, KiwoomError
from kiwoom.core.secrets import env_var_names
from kiwoom_cli.errors import CliInputError, CliInternalError
from kiwoom_cli.commands.accounts import add_accounts_parser
from kiwoom_cli.commands.auth import add_auth_parser
from kiwoom_cli.commands.candles import add_candles_parser
from kiwoom_cli.commands.elws import add_elws_parser
from kiwoom_cli.commands.etfs import add_etfs_parser
from kiwoom_cli.commands.investors import add_investors_parser
# TODO(overseas): keep disabled until overseas Kiwoom API execution is verified.
# from kiwoom_cli.commands.investment_info import add_investment_info_parser
from kiwoom_cli.commands.orderbooks import add_orderbooks_parser
# TODO(overseas): keep disabled until overseas Kiwoom API execution is verified.
# from kiwoom_cli.commands.overseas import add_overseas_parser
from kiwoom_cli.commands.orders import add_orders_parser
from kiwoom_cli.commands.quotes import add_quotes_parser
from kiwoom_cli.commands.rankings import add_rankings_parser
from kiwoom_cli.commands.sectors import add_sectors_parser
from kiwoom_cli.commands.securities_lending import add_securities_lending_parser
from kiwoom_cli.commands.short_selling import add_short_selling_parser
from kiwoom_cli.commands.spec import add_spec_parser
from kiwoom_cli.commands.stocks import add_stocks_parser
from kiwoom_cli.commands.streams import add_streams_parser
from kiwoom_cli.commands.themes import add_themes_parser
from kiwoom_cli.doctor import add_doctor_parser
from kiwoom_cli.setup import add_setup_parser


class KiwoomArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("allow_abbrev", False)
        kwargs.setdefault("formatter_class", argparse.RawDescriptionHelpFormatter)
        super().__init__(*args, **kwargs)

    def add_subparsers(self, *args, **kwargs):
        kwargs.setdefault("parser_class", type(self))
        return super().add_subparsers(*args, **kwargs)

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)
        translated = _translate_argparse_error(message)
        self.exit(2, f"{self.prog}: 오류: {translated}\n")


def _translate_argparse_error(message: str) -> str:
    required = re.fullmatch(r"the following arguments are required: (.+)", message)
    if required:
        return f"필수 인자가 빠졌습니다: {required.group(1)}"

    argument_error = re.fullmatch(r"argument ([^:]+): (.+)", message)
    if argument_error:
        argument, reason = argument_error.groups()
        return f"{argument} 값 오류: {_translate_argparse_error(reason)}"

    unrecognized = re.fullmatch(r"unrecognized arguments: (.+)", message)
    if unrecognized:
        return f"알 수 없는 인자입니다: {unrecognized.group(1)}"

    invalid_choice = re.fullmatch(
        r"invalid choice: (.+) \(choose from (.+)\)", message
    )
    if invalid_choice:
        value, choices = invalid_choice.groups()
        return f"지원하지 않는 값입니다: {value}. 가능한 값: {choices}"

    expected_one = re.fullmatch(r"expected one argument", message)
    if expected_one:
        return "값 하나가 필요합니다."

    ignored_explicit = re.fullmatch(r"ignored explicit argument (.+)", message)
    if ignored_explicit:
        return f"예상하지 못한 값입니다: {ignored_explicit.group(1)}"

    return message


def build_parser() -> argparse.ArgumentParser:
    parser = KiwoomArgumentParser(prog="kiwoomcli", description="키움 REST API 도우미 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 전역(시장 무관) 명령
    add_setup_parser(subparsers)
    add_auth_parser(subparsers)
    add_doctor_parser(subparsers)
    add_spec_parser(subparsers)

    # 국내 시장(OpenAPI) 명령: `kiwoomcli domestic <group> <command>`
    domestic_parser = subparsers.add_parser(
        "domestic", help="국내 시장(OpenAPI) 명령입니다."
    )
    domestic = domestic_parser.add_subparsers(dest="domestic_command", required=True)
    add_stocks_parser(domestic)
    add_quotes_parser(domestic)
    add_orderbooks_parser(domestic)
    add_candles_parser(domestic)
    add_etfs_parser(domestic)
    add_elws_parser(domestic)
    add_investors_parser(domestic)
    # TODO(overseas): planned only; do not expose until runtime is verified.
    # add_investment_info_parser(domestic)
    add_rankings_parser(domestic)
    add_sectors_parser(domestic)
    add_short_selling_parser(domestic)
    add_securities_lending_parser(domestic)
    add_themes_parser(domestic)
    add_streams_parser(domestic)
    # TODO(overseas): planned only; 향후 `kiwoomcli overseas ...`로 노출.
    # add_overseas_parser(subparsers)
    add_accounts_parser(domestic)
    add_orders_parser(domestic)

    return parser


def _normalize_console_encoding() -> None:
    """표준 출력 스트림을 UTF-8로 맞춘다.

    한글 Windows 콘솔의 기본 코덱(cp949)은 배너의 박스 문자나 일부 한글
    출력을 인코딩하지 못해 UnicodeEncodeError로 죽는다. 시작 시 한 번
    UTF-8로 정규화해 CLI 전체 출력을 일관되게 만든다.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass


def main() -> None:
    _normalize_console_encoding()
    parser = build_parser()
    args = parser.parse_args()

    try:
        args.handler(args)
    except KeyboardInterrupt:
        print("사용자에 의해 작업이 취소되었습니다.", file=sys.stderr)
        raise SystemExit(130)
    except EOFError:
        print("입력이 중단되었습니다.", file=sys.stderr)
        raise SystemExit(1)
    except CliInputError as exc:
        # 사용자 입력/정책 위반: 한글 한 줄, usage 오류 코드(2)로 종료.
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
    except CliInternalError as exc:
        # 정상 사용으로는 도달 불가한 단언: 버그로 취급해 traceback과 함께 노출.
        print(f"내부 오류: {exc}", file=sys.stderr)
        raise
    except CredentialsNotFoundError as exc:
        print(_format_credentials_error(args, exc), file=sys.stderr)
        raise SystemExit(1)
    except (KiwoomError, OSError, requests.RequestException, ValueError) as exc:
        # API/서버 오류와 라이브러리 ValueError(예: mode 불일치)는 원형 통과.
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        # 예기치 못한 오류 = 버그: 내부 오류로 표시하고 traceback을 남긴다.
        print(f"내부 오류: {exc}", file=sys.stderr)
        raise


def _format_credentials_error(args: argparse.Namespace, exc: CredentialsNotFoundError) -> str:
    """Render a credentials error tailored to how the target was selected.

    `CredentialsNotFoundError` only carries `mode`, so reconstruct the entry
    path from args/env via `describe_selection`. The `--mode` failure and the
    `--profile` failure are genuinely different problems and get different fixes.
    """
    mode_arg = getattr(args, "mode", None)
    profile_arg = getattr(args, "profile", None)
    try:
        selection = describe_selection(mode_arg, profile=profile_arg)
    except KiwoomError:
        return str(exc)

    if selection.uses_profile:
        return "\n".join(
            [
                f"계좌 별칭 '{selection.profile}'의 키/시크릿을 찾을 수 없습니다.",
                "",
                "해결:",
                f"  kiwoomcli setup {selection.profile}",
            ]
        )

    appkey_var, secretkey_var = env_var_names(selection.mode)
    return "\n".join(
        [
            f"{selection.mode} mode 키/시크릿을 찾을 수 없습니다.",
            "",
            "현재 인증 컨텍스트:",
            f"  선택 방식: {selection.selection_source}",
            f"  선택 대상: {selection.target_label}",
            "  계좌 별칭: 사용 안 함",
            "",
            "왜 발생했나요?",
            f"  {selection.selection_source}은(는) 저장된 계좌 별칭을 사용하지 않습니다.",
            "  mode 방식은 APP_KEY / APP_SECRET 환경변수 또는 mode용 자격 증명이 필요합니다.",
            "",
            "해결:",
            "  저장된 별칭을 쓰려면:  kiwoomcli <명령> --profile <별칭>",
            f"  환경변수 방식으로 쓰려면:  {appkey_var} / {secretkey_var} 를 설정하세요.",
        ]
    )


if __name__ == "__main__":
    main()
