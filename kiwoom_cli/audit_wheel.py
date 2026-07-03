"""Audit the built wheel for packaged CLI resources."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"

REQUIRED_WHEEL_MEMBERS = {
    "kiwoom/__init__.py",
    "kiwoom/core/runtime.py",
    "kiwoom_cli/README.md",
    "kiwoom_cli/main.py",
    "kiwoom_cli/registry.py",
    "kiwoom_cli/verify_real_calls.py",
    "kiwoom_cli/argument_maps.py",
    "kiwoom_cli/executor.py",
    "kiwoom_cli/generate_agent_reference.py",
    "kiwoom_cli/output.py",
    "kiwoom_cli/safety.py",
    "kiwoom_cli/commands/__init__.py",
    "kiwoom_cli/commands/accounts.py",
    "kiwoom_cli/commands/candles.py",
    "kiwoom_cli/commands/elws.py",
    "kiwoom_cli/commands/etfs.py",
    "kiwoom_cli/commands/investment_info.py",
    "kiwoom_cli/commands/investors.py",
    "kiwoom_cli/commands/orderbooks.py",
    "kiwoom_cli/commands/overseas.py",
    "kiwoom_cli/commands/quotes.py",
    "kiwoom_cli/commands/rankings.py",
    "kiwoom_cli/commands/securities_lending.py",
    "kiwoom_cli/commands/short_selling.py",
    "kiwoom_cli/commands/stocks.py",
    "kiwoom_cli/commands/orders.py",
    "kiwoom_cli/commands/sectors.py",
    "kiwoom_cli/commands/streams.py",
    "kiwoom_cli/commands/themes.py",
    "kiwoom_cli/maps/README.md",
    "kiwoom_cli/maps/api_commands.csv",
    "kiwoom_cli/maps/arguments.csv",
    "kiwoom_cli/maps/positional_arguments.csv",
    "kiwoom_cli/docs/README.md",
    "kiwoom_cli/docs/api-coverage.md",
    "kiwoom_cli/docs/command-system.md",
    "kiwoom_cli/docs/command-contracts.md",
    "kiwoom_cli/docs/feature-matrix.md",
    "kiwoom_cli/docs/implementation-status.md",
    "kiwoom_cli/docs/positional-arguments.md",
    "kiwoom_cli/docs/types.md",
    "kiwoom/_data/kiwoom_api_spec.json",
    "api_list.csv",
}

REQUIRED_ENTRY_POINT = "kiwoom = kiwoom_cli.main:main"


def audit() -> None:
    wheels = sorted(DIST.glob("*.whl"), key=lambda path: path.stat().st_mtime)
    if not wheels:
        raise SystemExit("wheel audit failed: no wheel files found in dist/")

    wheel = wheels[-1]
    with ZipFile(wheel) as archive:
        members = set(archive.namelist())
        missing = sorted(REQUIRED_WHEEL_MEMBERS - members)
        entry_points_name = _find_entry_points_name(members)
        entry_points_text = (
            archive.read(entry_points_name).decode("utf-8")
            if entry_points_name is not None
            else ""
        )

    if missing:
        joined = "\n".join(f"- {member}" for member in missing)
        raise SystemExit(f"wheel audit failed: missing required members in {wheel.name}\n{joined}")
    if entry_points_name is None:
        raise SystemExit(f"wheel audit failed: missing dist-info/entry_points.txt in {wheel.name}")
    if REQUIRED_ENTRY_POINT not in entry_points_text:
        raise SystemExit(
            "wheel audit failed: missing console script entry point "
            f"{REQUIRED_ENTRY_POINT!r} in {entry_points_name}"
        )

    print(
        "wheel audit passed: "
        f"{wheel.name} includes {len(REQUIRED_WHEEL_MEMBERS)} required CLI resources "
        "and the kiwoom console script"
    )


def _find_entry_points_name(members: set[str]) -> str | None:
    for member in members:
        if member.endswith(".dist-info/entry_points.txt"):
            return member
    return None


if __name__ == "__main__":
    audit()
