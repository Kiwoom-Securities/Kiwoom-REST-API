# Kiwoom CLI Docs

These docs describe the intended customer-facing `kiwoomcli` command surface and
the agent-facing command contracts that should be generated from curated command
maps plus `kiwoom_api_spec.json`.

The docs are part of the CLI design contract. When a command is implemented,
the implementation, maps, help output, and docs must agree.

## Documents

- [Feature Matrix](feature-matrix.md): command groups, command status, API
  candidates, auth requirements, safety policy, and feature notes.
- [Command System](command-system.md): top-level command tree, naming rules,
  safety posture, help/output policy, and CLI change process.
- [API Coverage Analysis](api-coverage.md): current local API counts, coverage
  status, API families, and full-coverage taxonomy.
- [Command Contracts](command-contracts.md): command-by-command argument tables,
  Kiwoom field mappings, output shape, and examples.
- [Types](types.md): shared CLI argument types, formats, validation rules,
  sensitive-field handling, and planned enum sources.
- [Positional Argument Policy](positional-arguments.md): command-by-command
  canonical option form, approved positional shorthand, and deferred/candidate
  shorthand decisions.
- [Implementation Status](implementation-status.md): current implementation
  status, verification evidence, and blocked real-call items.

## Evidence

- [Parameter Naming Audit Evidence](parameter-naming-audit.md): non-authoritative
  audit evidence for CLI option naming. `command-system.md` is the SSOT when the
  two documents differ.

## Documentation Rules

- Public docs describe the installed command as `kiwoomcli`.
- Do not document `uv run kiwoom` as a customer-facing invocation.
- Do not document generated examples as stable public imports.
- Do not document commands that bypass package runtime facades.
- Do not document deposit/withdraw execution commands until the local spec and a
  reviewed safety policy prove support.
- APIs with unclear user semantics or account impact must be documented as
  `Review`, not `Planned`.
- Every documented planned command must name its implementation status.
- Every implemented command must be backed by executable help output and static
  validation.

## Drift Checks

```sh
.venv/bin/python -m kiwoom_cli.validate_maps
.venv/bin/python -m kiwoom_cli.audit_implementation
env PYTHONPYCACHEPREFIX=.pycache-check .venv/bin/python -m compileall -q kiwoom kiwoom_cli Examples
! rg -n "unittest\\.mock|MagicMock|\\bMock\\b|\\bpatch\\b|fake|stub|monkeypatch|cassette|replay" kiwoom kiwoom_cli Examples utils -g '!**/*.md' -g '!**/*.csv'
git diff --check
uv build
.venv/bin/python -m kiwoom_cli.audit_wheel
.venv/bin/python -m kiwoom_cli.verify_real_calls --mode demo || true
.venv/bin/python -m kiwoom_cli.generate_agent_reference --target all
```

## Status Labels

| Status | Meaning |
| --- | --- |
| Implemented | The command exists in `kiwoom_cli/main.py` or a registered CLI module. |
| Partial | At least one command in the resource group is implemented, but the full mapped family is not complete. |
| Planned | The command is part of the intended resource surface, but is not implemented yet. |
| Review | The API is covered in maps/docs, but command semantics or safety policy still need review. |
| Blocked | The command is intentionally withheld until spec support, safety policy, or credentials are available. |
| Internal | The function is for repo maintenance only and is not a customer-facing CLI command. |
