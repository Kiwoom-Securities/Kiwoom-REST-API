"""Run safe credentialed Kiwoom checks and report sanitized evidence."""

from __future__ import annotations

import argparse
import json
from types import SimpleNamespace
from typing import Any

from kiwoom.core.errors import CredentialsNotFoundError, KiwoomError
from kiwoom.core.runtime import get_auth
from kiwoom.core.profiles import get_current_profile, load_profiles
from kiwoom_cli.argument_maps import build_body
from kiwoom_cli.errors import CliError
from kiwoom_cli.executor import execute_rest_command
from kiwoom_cli.registry import get_implemented_command


SAFE_READ_COMMAND = "kiwoomcli domestic stocks info"
SAFE_READ_API_GROUP = "stocks"
SAFE_READ_API_COMMAND = "info"
SAFE_READ_CODE = "005930"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run safe Kiwoom real-call verification and print sanitized JSON evidence."
    )
    parser.add_argument("--mode", choices=("demo", "real"), default="demo")
    parser.add_argument("--profile")
    parser.add_argument("--code", default=SAFE_READ_CODE)
    args = parser.parse_args(argv)

    evidence = run_safe_public_read(
        mode=args.mode,
        profile=args.profile,
        code=args.code,
    )
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    return 0 if evidence["status"] == "passed" else 1


def run_safe_public_read(
    *,
    mode: str,
    profile: str | None,
    code: str,
) -> dict[str, Any]:
    resolved_profile = profile or _single_credentialed_profile_for_mode(mode)
    definition = get_implemented_command(SAFE_READ_API_GROUP, SAFE_READ_API_COMMAND)
    body = build_body(definition.command_path, SimpleNamespace(code=code))
    target_args = f"--profile {resolved_profile}" if resolved_profile else f"--mode {mode}"
    evidence: dict[str, Any] = {
        "check": "safe-public-read",
        "command": f"{SAFE_READ_COMMAND} --code {code} {target_args} --format json",
        "api_id": definition.api_id,
        "method": definition.method,
        "endpoint": definition.path,
        "mode": mode,
        "profile": resolved_profile or "",
        "output_mode": "json",
        "status": "blocked",
        "row_count": None,
        "response_keys": [],
        "secret_values": "not-recorded",
    }
    try:
        response = execute_rest_command(
            definition,
            body=body,
            mode=mode,
            profile=resolved_profile,
        )
    except CredentialsNotFoundError as exc:
        evidence["reason"] = "credentials-not-configured"
        evidence["message"] = str(exc)
        return evidence
    except (CliError, ValueError) as exc:
        evidence["reason"] = "invalid-target"
        evidence["message"] = str(exc)
        return evidence
    except KiwoomError as exc:
        evidence["reason"] = exc.__class__.__name__
        evidence["message"] = str(exc)
        return evidence

    payload = response.body
    evidence["status"] = "passed"
    evidence["reason"] = ""
    evidence["message"] = ""
    evidence["response_keys"] = sorted(payload.keys()) if isinstance(payload, dict) else []
    evidence["row_count"] = _row_count(payload)
    return evidence


def _single_credentialed_profile_for_mode(mode: str) -> str | None:
    """Pick a saved profile for mode when it has credentials.

    `--mode demo` uses mode-level environment/keyring credentials in the runtime.
    Users who configured aliases through `kiwoomcli auth login` usually have
    profile-scoped keyring entries instead. For the reusable real-call checker,
    selecting the current matching profile, or the single matching credentialed
    profile, avoids reporting a false "credentials missing" result when
    `kiwoomcli auth list` clearly shows a saved demo alias.
    """

    candidates: list[str] = []
    try:
        profiles = load_profiles()
        current = get_current_profile()
    except KiwoomError:
        return None
    if current is not None and current.mode == mode:
        try:
            if get_auth(profile=current.alias).status().has_credentials:
                return current.alias
        except KiwoomError:
            pass
    for alias, profile in profiles.items():
        if profile.mode != mode:
            continue
        try:
            if get_auth(profile=alias).status().has_credentials:
                candidates.append(alias)
        except KiwoomError:
            continue
    if len(candidates) == 1:
        return candidates[0]
    return None


def _row_count(payload: Any) -> int | None:
    if isinstance(payload, list):
        return len(payload)
    if not isinstance(payload, dict):
        return None
    list_lengths = [len(value) for value in payload.values() if isinstance(value, list)]
    if list_lengths:
        return max(list_lengths)
    return None


if __name__ == "__main__":
    raise SystemExit(main())
