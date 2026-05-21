from __future__ import annotations

import argparse
import csv
import json
import keyword
import re
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from kiwoom.core.fid import FID_MAP

INVALID_PATH_CHARS = re.compile(r'[\\/:*?"<>|]')
TEMPLATE_KINDS = frozenset({"rest", "oauth", "websocket_request_once", "websocket_realtime"})
COMMON_RESPONSE_FIELDS = frozenset({"return_code", "return_msg", "trnm"})
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {"return_code": "응답코드", "return_msg": "응답메시지"}
SUMMARY_KEY = "요약"
MAPPING_COLUMNS = [
    "api_id",
    "api_name",
    "function_name",
    "template_kind",
    "category",
    "sub_category",
    "url",
    "enabled",
]
FUNCTION_NAME_OVERRIDE_COLUMNS = ("함수이름", "API ID")


@dataclass(frozen=True)
class ApiListRow:
    api_id: str
    api_name: str
    top_category: str
    sub_category: str
    url: str


@dataclass(frozen=True)
class ApiSpec:
    api_id: str
    api_name: str
    top_category: str
    sub_category: str
    url: str
    method: str
    content_type: str
    request_headers: list[dict]
    request_body: list[dict]
    request_example: str
    response_body: list[dict] = field(default_factory=list)
    menu_path: str = ""


@dataclass(frozen=True)
class FunctionNameMapEntry:
    api_id: str
    api_name: str
    function_name: str
    template_kind: Literal["rest", "oauth", "websocket_request_once", "websocket_realtime"]
    category: str
    sub_category: str
    url: str
    enabled: bool = True


@dataclass(frozen=True)
class GeneratedApiSpec:
    api_spec: ApiSpec
    mapping: FunctionNameMapEntry


@dataclass(frozen=True)
class RequestParameter:
    body_key: str
    parameter_name: str
    required: bool
    annotation: str
    default_value: object | None
    label: str
    description: str


@dataclass(frozen=True)
class ResponseTableSpec:
    table_keys: list[str]
    table_labels: dict[str, str]
    columns: dict[str, str]
    scalar_columns: dict[str, str]


@dataclass(frozen=True)
class GenerationReport:
    total_specs: int
    enabled_specs: int
    written_files: int
    disabled_api_ids: list[str]
    counts_by_template_kind: dict[str, int]
    output_files: list[str]

    def to_json(self) -> dict[str, object]:
        return {
            "total_specs": self.total_specs,
            "enabled_specs": self.enabled_specs,
            "written_files": self.written_files,
            "disabled_api_ids": self.disabled_api_ids,
            "counts_by_template_kind": self.counts_by_template_kind,
            "output_files": self.output_files,
        }


def load_api_list(csv_path: Path) -> list[ApiListRow]:
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            ApiListRow(
                api_id=row["API ID"].strip(),
                api_name=row["API 명"].strip(),
                top_category=row["대분류"].strip(),
                sub_category=row["중분류"].strip(),
                url=row["URL"].strip(),
            )
            for row in reader
        ]


def load_api_spec(spec_path: Path) -> dict[str, dict]:
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    return {
        info["meta"]["API ID"]: payload
        for payload in data["apis"].values()
        if (info := payload).get("meta", {}).get("API ID")
    }


def build_api_spec(row: ApiListRow, payload: dict) -> ApiSpec:
    meta = payload["meta"]
    request = payload.get("request", {})
    response = payload.get("response", {})
    return ApiSpec(
        api_id=row.api_id,
        api_name=row.api_name,
        top_category=row.top_category,
        sub_category=row.sub_category,
        url=row.url,
        method=meta.get("Method", "POST"),
        content_type=meta.get("Content-Type", "application/json;charset=UTF-8"),
        request_headers=request.get("header", []),
        request_body=request.get("body", []),
        request_example=payload.get("request_example", ""),
        response_body=response.get("body", []),
        menu_path=meta.get("메뉴 위치", ""),
    )


def load_api_specs(csv_path: Path, spec_path: Path) -> list[ApiSpec]:
    api_rows = load_api_list(csv_path)
    spec_map = load_api_spec(spec_path)
    api_specs: list[ApiSpec] = []
    for row in api_rows:
        payload = spec_map.get(row.api_id)
        if payload is None:
            raise KeyError(f"Missing spec entry for API ID {row.api_id}")
        api_specs.append(build_api_spec(row, payload))
    return api_specs


def sanitize_path_part(value: str) -> str:
    cleaned = INVALID_PATH_CHARS.sub("_", value.strip())
    return cleaned.rstrip(" .")


def api_filename(api_spec: ApiSpec) -> str:
    return api_spec.api_id


def example_path(examples_root: Path, api_spec: ApiSpec) -> Path:
    return (
        examples_root
        / sanitize_path_part(api_spec.top_category)
        / sanitize_path_part(api_spec.sub_category)
        / f"{api_filename(api_spec)}.py"
    )


def build_filename_map(api_specs: list[ApiSpec]) -> dict[str, str]:
    base_keys: dict[str, list[ApiSpec]] = {}
    for api_spec in api_specs:
        key = _casefold_relative_key(
            api_spec.top_category,
            api_spec.sub_category,
            api_filename(api_spec),
        )
        base_keys.setdefault(key, []).append(api_spec)

    filename_map: dict[str, str] = {}
    for group in base_keys.values():
        if len(group) == 1:
            filename_map[group[0].api_id] = api_filename(group[0])
            continue
        for api_spec in group:
            disambiguated = f"{api_spec.api_id}__{sanitize_path_part(api_spec.api_name)}"
            filename_map[api_spec.api_id] = disambiguated
    return filename_map


def bootstrap_function_name_map(
    csv_path: Path,
    spec_path: Path,
    output_path: Path,
    *,
    overwrite: bool = False,
) -> Path:
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"mapping table already exists: {output_path}")

    api_specs = load_api_specs(csv_path, spec_path)
    entries = [default_mapping_entry(api_spec) for api_spec in api_specs]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_function_name_map(entries, output_path)
    return output_path


def write_function_name_map(entries: list[FunctionNameMapEntry], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MAPPING_COLUMNS)
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "api_id": entry.api_id,
                    "api_name": entry.api_name,
                    "function_name": entry.function_name,
                    "template_kind": entry.template_kind,
                    "category": entry.category,
                    "sub_category": entry.sub_category,
                    "url": entry.url,
                    "enabled": "Y" if entry.enabled else "N",
                }
            )


def load_function_name_map(path: Path) -> dict[str, FunctionNameMapEntry]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [column for column in MAPPING_COLUMNS if column not in (reader.fieldnames or [])]
        if missing_columns:
            raise ValueError(f"mapping table missing columns: {', '.join(missing_columns)}")
        entries: dict[str, FunctionNameMapEntry] = {}
        for row in reader:
            api_id = row["api_id"].strip()
            if api_id in entries:
                raise ValueError(f"duplicate api_id in mapping table: {api_id}")
            entries[api_id] = FunctionNameMapEntry(
                api_id=api_id,
                api_name=row["api_name"].strip(),
                function_name=row["function_name"].strip(),
                template_kind=row["template_kind"].strip(),  # type: ignore[arg-type]
                category=row["category"].strip(),
                sub_category=row["sub_category"].strip(),
                url=row["url"].strip(),
                enabled=row["enabled"].strip().upper() not in {"", "0", "N", "NO", "FALSE"},
            )
        return entries


def load_function_name_overrides(path: Path) -> dict[str, str]:
    """Load a compact editable API ID -> function name override table."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing_columns = [
            column
            for column in FUNCTION_NAME_OVERRIDE_COLUMNS
            if column not in (reader.fieldnames or [])
        ]
        if missing_columns:
            raise ValueError(f"function name override table missing columns: {', '.join(missing_columns)}")

        overrides: dict[str, str] = {}
        for row in reader:
            api_id = row["API ID"].strip()
            function_name = row["함수이름"].strip()
            if not api_id and not function_name:
                continue
            if not api_id or not function_name:
                raise ValueError("function name override rows must include both 함수이름 and API ID")
            if api_id in overrides:
                raise ValueError(f"duplicate API ID in function name override table: {api_id}")
            if not _is_valid_function_name(function_name):
                raise ValueError(f"invalid function name override for {api_id}: {function_name}")
            overrides[api_id] = function_name
        return overrides


def apply_function_name_overrides(
    entries: dict[str, FunctionNameMapEntry],
    overrides: dict[str, str],
) -> dict[str, FunctionNameMapEntry]:
    unknown_ids = sorted(set(overrides) - set(entries))
    if unknown_ids:
        raise ValueError(f"unknown API ID in function name override table: {', '.join(unknown_ids)}")
    return {
        api_id: replace(entry, function_name=overrides.get(api_id, entry.function_name))
        for api_id, entry in entries.items()
    }


def validate_function_name_map(
    api_specs: list[ApiSpec],
    entries: dict[str, FunctionNameMapEntry],
) -> None:
    errors: list[str] = []
    spec_ids = {api_spec.api_id for api_spec in api_specs}
    entry_ids = set(entries)

    for missing_id in sorted(spec_ids - entry_ids):
        errors.append(f"missing mapping for api_id: {missing_id}")
    for unknown_id in sorted(entry_ids - spec_ids):
        errors.append(f"unknown api_id in mapping table: {unknown_id}")

    function_names: dict[str, str] = {}
    for entry in entries.values():
        if entry.template_kind not in TEMPLATE_KINDS:
            errors.append(f"unknown template_kind for {entry.api_id}: {entry.template_kind}")
        if not _is_valid_function_name(entry.function_name):
            errors.append(f"invalid function_name for {entry.api_id}: {entry.function_name}")
        if not entry.enabled:
            continue
        previous_api_id = function_names.get(entry.function_name)
        if previous_api_id is not None:
            errors.append(
                f"duplicate enabled function_name {entry.function_name}: "
                f"{previous_api_id}, {entry.api_id}"
            )
        function_names[entry.function_name] = entry.api_id

    if errors:
        raise ValueError("\n".join(errors))


def default_mapping_entry(api_spec: ApiSpec) -> FunctionNameMapEntry:
    return FunctionNameMapEntry(
        api_id=api_spec.api_id,
        api_name=api_spec.api_name,
        function_name=_default_function_name(api_spec.api_id),
        template_kind=_default_template_kind(api_spec),
        category=api_spec.top_category,
        sub_category=api_spec.sub_category,
        url=api_spec.url,
        enabled=True,
    )


def scaffold_examples(
    csv_path: Path,
    spec_path: Path,
    examples_root: Path,
    *,
    mapping_path: Path | None = None,
    function_name_overrides_path: Path | None = None,
    report_path: Path | None = None,
) -> list[Path]:
    api_specs = load_api_specs(csv_path, spec_path)
    mapping = (
        load_function_name_map(mapping_path)
        if mapping_path is not None
        else {api_spec.api_id: default_mapping_entry(api_spec) for api_spec in api_specs}
    )
    if function_name_overrides_path is not None and function_name_overrides_path.exists():
        mapping = apply_function_name_overrides(
            mapping,
            load_function_name_overrides(function_name_overrides_path),
        )
    validate_function_name_map(api_specs, mapping)

    spec_by_id = {api_spec.api_id: api_spec for api_spec in api_specs}
    enabled_specs = [spec_by_id[entry.api_id] for entry in mapping.values() if entry.enabled]
    filename_map = build_filename_map(enabled_specs)
    written_paths: list[Path] = []
    counts_by_template_kind = dict.fromkeys(sorted(TEMPLATE_KINDS), 0)

    for api_spec in enabled_specs:
        entry = mapping[api_spec.api_id]
        output_path = (
            examples_root
            / sanitize_path_part(api_spec.top_category)
            / sanitize_path_part(api_spec.sub_category)
            / f"{filename_map[api_spec.api_id]}.py"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_example(api_spec, entry), encoding="utf-8")
        written_paths.append(output_path)
        counts_by_template_kind[entry.template_kind] += 1

    if report_path is not None:
        report = GenerationReport(
            total_specs=len(api_specs),
            enabled_specs=len(enabled_specs),
            written_files=len(written_paths),
            disabled_api_ids=sorted(entry.api_id for entry in mapping.values() if not entry.enabled),
            counts_by_template_kind=counts_by_template_kind,
            output_files=[str(path) for path in written_paths],
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report.to_json(), ensure_ascii=False, indent=2), encoding="utf-8")

    return written_paths


def render_example(api_spec: ApiSpec, mapping_entry: FunctionNameMapEntry | None = None) -> str:
    entry = mapping_entry or default_mapping_entry(api_spec)
    generated = GeneratedApiSpec(api_spec=api_spec, mapping=entry)
    if entry.template_kind == "oauth":
        return _render_oauth_example(generated)
    if entry.template_kind == "websocket_request_once":
        return _render_websocket_request_once_example(generated)
    if entry.template_kind == "websocket_realtime":
        return _render_websocket_realtime_example(generated)
    return _render_rest_example(generated)


def _render_rest_example(generated: GeneratedApiSpec) -> str:
    api_spec = generated.api_spec
    entry = generated.mapping
    parameters = _request_parameters(api_spec)
    response_table = _response_table_spec(api_spec.response_body)
    lines = _base_module_lines(
        api_spec,
        template_kind=entry.template_kind,
        imports=[
            "import logging",
            "import time",
            "",
            "import pandas as pd",
            "",
            "from kiwoom import get_client",
        ],
        constants=[
            f'API_ID = "{api_spec.api_id}"',
            f'API_URL = "{api_spec.url}"',
            "MAX_PAGES = 10 # 최대 조회 페이지 수",
            "REQUEST_DELAY_SECONDS = 0.2 # 요청 간격 (초)",
            f'MESSAGE_KEY = "{MESSAGE_KEY}"',
            f"MESSAGE_COLUMNS = {_json_literal(MESSAGE_COLUMNS)}",
            _table_keys_constant_line(response_table),
            _columns_constant_line(response_table),
            *_summary_constant_lines(response_table),
        ],
    )
    lines.extend(_display_helper_lines(response_table))
    lines.append(_render_signature(entry.function_name, parameters, kind="rest", response_table=response_table))
    lines.extend(
        _render_docstring(
            api_spec,
            parameters,
            function_name=entry.function_name,
            kind="rest",
            response_table=response_table,
        )
    )
    lines.extend(_render_required_parameter_checks(parameters))
    lines.extend(_render_params_block(parameters))
    lines.extend(
        [
            "",
            "    # 3. 인증 클라이언트",
            "    client = get_client()",
            "",
            "    # 4. 응답 데이터 저장소",
            "    message_rows = []",
        ]
    )
    if response_table.table_keys:
        if response_table.scalar_columns:
            lines.append("    summary_rows = []")
        lines.extend(_render_table_rows_initializer(response_table, indent="    ", rows_var="rows"))
    else:
        lines.append("    rows = []")
    lines.extend(
        [
            "    # 5. API 호출 및 연속조회",
            "    next_cont_yn = None",
            "    next_key = None",
            "",
            "    for page in range(MAX_PAGES):",
            "        response = client.fetch_page(",
            "            api_id=API_ID,",
            "            path=API_URL,",
            "            body=body,",
            "            cont_yn=next_cont_yn,",
            "            next_key=next_key,",
            "        )",
            "        response_body = response.body",
            '        if response_body.get("return_code") not in (None, 0):',
            "            message_rows.append({",
            "                key: response_body.get(key)",
            "                for key in MESSAGE_COLUMNS",
            "            })",
        ]
    )
    if response_table.table_keys and response_table.scalar_columns:
        lines.extend(_render_summary_rows_append(response_table, body_var="response_body", rows_var="summary_rows", indent="        "))
    lines.extend(_render_dataframe_rows_extend(response_table, body_var="response_body", rows_var="rows", indent="        "))
    lines.extend(
        [
            "",
            "        next_cont_yn = response.continuation.cont_yn",
            "        next_key = response.continuation.next_key",
            "",
            "        if next_cont_yn != \"Y\":",
            "            break",
            "",
            "        if page + 1 >= MAX_PAGES:",
            "            break",
            "",
            "        time.sleep(REQUEST_DELAY_SECONDS)",
        ]
    )
    if response_table.table_keys:
        dataframe_return_lines = [
            "    result = {",
            "        TABLE_KEYS.get(key, key): pd.DataFrame(records).rename(columns=COLUMNS)",
            "        for key, records in rows.items()",
            "    }",
        ]
        if response_table.scalar_columns:
            dataframe_return_lines.extend(
                [
                    "    result = {",
                    "        SUMMARY_KEY: pd.DataFrame(summary_rows).rename(columns=SUMMARY_COLUMNS),",
                    "        **result,",
                    "    }",
                ]
            )
        dataframe_return_lines.extend(
            [
                "    if message_rows:",
                "        result = {",
                "            MESSAGE_KEY: pd.DataFrame(message_rows).rename(columns=MESSAGE_COLUMNS),",
                "            **result,",
                "        }",
            ]
        )
        dataframe_return_lines.append("    return result")
    else:
        dataframe_return_lines = [
            "    result = pd.DataFrame(rows).rename(columns=COLUMNS)",
            "    if message_rows:",
            "        message_df = pd.DataFrame(message_rows).rename(columns=MESSAGE_COLUMNS)",
            "        result = pd.concat([message_df, result], axis=1)",
            "    return result",
        ]
    lines.extend(
        [
            "",
            "    # 6. DataFrame 변환",
            *dataframe_return_lines,
            "",
        ]
    )
    result_shape = "dataframe_dict" if response_table.table_keys else "dataframe"
    lines.extend(_render_main_block(entry.function_name, parameters, async_call=False, result_shape=result_shape))
    return "\n".join(lines).rstrip() + "\n"


def _render_oauth_example(generated: GeneratedApiSpec) -> str:
    api_spec = generated.api_spec
    entry = generated.mapping
    parameters: list[RequestParameter] = []
    response_table = _response_table_spec(api_spec.response_body)
    lines = _base_module_lines(
        api_spec,
        template_kind=entry.template_kind,
        imports=[
            "import logging",
            "from typing import Any, Literal",
            "",
            "import pandas as pd",
            "",
            "from kiwoom import get_auth",
        ],
        constants=[
            f'API_ID = "{api_spec.api_id}"',
            f'API_PATH = "{api_spec.url}"',
            _columns_constant_line(response_table),
        ],
    )
    lines.extend(_display_helper_lines(response_table))
    lines.append(_render_signature(entry.function_name, parameters, kind="oauth"))
    lines.extend(_render_docstring(api_spec, parameters, function_name=entry.function_name, kind="oauth"))
    lines.extend(_render_oauth_common_auth_call(api_spec))
    lines.extend(_render_dataframe_conversion(response_table, body_var="response_body", result_var="current_data", indent="    "))
    lines.extend(
        [
            "    return current_data",
            "",
        ]
    )
    lines.extend(_render_main_block(entry.function_name, parameters, async_call=False, oauth=True))
    return "\n".join(lines).rstrip() + "\n"


def _render_oauth_common_auth_call(api_spec: ApiSpec) -> list[str]:
    if api_spec.url == "/oauth2/token":
        return [
            "",
            "    auth = get_auth(mode=mode)",
            "    auth.refresh_access_token()",
            "    status = auth.status()",
            "    response_body = {",
            '        "mode": status.mode,',
            '        "issued": True,',
            '        "token_saved_at": status.token_saved_at.isoformat() if status.token_saved_at else None,',
            '        "expires_dt": status.token_expires_at.isoformat() if status.token_expires_at else None,',
            '        "token_valid": status.token_valid,',
            "    }",
            "",
            '    if output == "json":',
            "        return response_body",
        ]
    if api_spec.url == "/oauth2/revoke":
        return [
            "",
            "    auth = get_auth(mode=mode)",
            "    auth.revoke_access_token()",
            "    response_body = {",
            '        "mode": auth.mode,',
            '        "revoked": True,',
            '        "return_code": 0,',
            '        "return_msg": "토큰 폐기 완료",',
            "    }",
            "",
            '    if output == "json":',
            "        return response_body",
        ]
    return [
        "",
        f'    raise NotImplementedError("공통 인증 예제 템플릿이 지원하지 않는 OAuth 경로입니다: {api_spec.url}")',
    ]


def _render_websocket_request_once_example(generated: GeneratedApiSpec) -> str:
    api_spec = generated.api_spec
    entry = generated.mapping
    parameters = _request_parameters(api_spec)
    response_table = _response_table_spec(api_spec.response_body)
    lines = _base_module_lines(
        api_spec,
        template_kind=entry.template_kind,
        imports=[
            "import asyncio",
            "import logging",
            "from typing import Any, Literal",
            "",
            "import pandas as pd",
            "",
            "from kiwoom import get_ws_client",
        ],
        constants=[
            f'API_ID = "{api_spec.api_id}"',
            f'API_URL = "{api_spec.url}"',
            _table_keys_constant_line(response_table),
            _columns_constant_line(response_table),
        ],
        extra_comments=["# WebSocket 클라이언트가 LOGIN 패킷을 자동 처리합니다."],
    )
    lines.extend(_display_helper_lines(response_table))
    lines.append(_render_signature(entry.function_name, parameters, kind="websocket_request_once"))
    lines.extend(_render_docstring(api_spec, parameters, function_name=entry.function_name, kind="websocket_request_once"))
    lines.extend(_render_required_parameter_checks(parameters))
    lines.extend(_render_params_block(parameters))
    lines.extend(
        [
            "",
            "    response_body = await get_ws_client().request_once(api_url=API_URL, body=body)",
            "",
            "    if output == \"json\":",
            "        return response_body",
        ]
    )
    lines.extend(_render_dataframe_conversion(response_table, body_var="response_body", result_var="current_data", indent="    "))
    lines.extend(
        [
            "    return current_data",
            "",
        ]
    )
    lines.extend(_render_main_block(entry.function_name, parameters, async_call=True))
    return "\n".join(lines).rstrip() + "\n"


def _render_websocket_realtime_example(generated: GeneratedApiSpec) -> str:
    api_spec = generated.api_spec
    entry = generated.mapping
    parameters = _request_parameters(api_spec)
    fields_block = _realtime_fields_block(api_spec.api_id)
    lines = _base_module_lines(
        api_spec,
        template_kind=entry.template_kind,
        imports=[
            "import asyncio",
            "import logging",
            "from typing import Any, Literal",
            "",
            "import pandas as pd",
            "",
            "from kiwoom import get_ws_client",
            "from kiwoom.domain.realtime.decoders import decode_values",
        ],
        constants=[
            f'API_ID = "{api_spec.api_id}"',
            f'API_URL = "{api_spec.url}"',
            fields_block.strip(),
        ],
        extra_comments=[
            "# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.",
        ],
    )
    lines.extend(_display_helper_lines(_response_table_spec(api_spec.response_body)))
    lines.append(_render_signature(entry.function_name, parameters, kind="websocket_realtime"))
    lines.extend(_render_docstring(api_spec, parameters, function_name=entry.function_name, kind="websocket_realtime"))
    lines.extend(
        [
            "    if max_messages < 1:",
            "        raise ValueError(\"max_messages must be greater than 0\")",
        ]
    )
    lines.extend(_render_required_parameter_checks(parameters))
    lines.extend(_render_params_block(parameters))
    lines.extend(
        [
            "",
            "    client = get_ws_client()",
            "    await client.subscribe(api_url=API_URL, body=body)",
            "",
            "    rows: list[dict[str, Any]] = []",
            "    try:",
            "        async for message in client.iter_messages():",
            "            if not isinstance(message, dict):",
            "                continue",
            "            if str(message.get(\"trnm\", \"\")).upper() != \"REAL\":",
            "                continue",
            "            for entry in message.get(\"data\", []):",
            "                if not isinstance(entry, dict):",
            "                    continue",
            "                values = decode_values(str(entry.get(\"type\", \"\")), entry.get(\"values\", {}))",
            "                row = {field: values[field] for field in FIELDS if field in values} if FIELDS else values",
            "                rows.append({\"item\": entry.get(\"item\", \"\"), **row})",
            "                if len(rows) >= max_messages:",
            "                    if output == \"json\":",
            "                        return rows",
            "                    return {\"data\": pd.DataFrame(rows)}",
            "    finally:",
            "        await client.close()",
            "",
            "    if output == \"json\":",
            "        return rows",
            "    return {\"data\": pd.DataFrame(rows)}",
            "",
        ]
    )
    lines.extend(_render_main_block(entry.function_name, parameters, async_call=True))
    return "\n".join(lines).rstrip() + "\n"


def _base_module_lines(
    api_spec: ApiSpec,
    *,
    template_kind: str,
    imports: list[str],
    constants: list[str],
    extra_comments: list[str] | None = None,
) -> list[str]:
    lines = [
        "# ---",
        f"# api_id: {api_spec.api_id}",
        f"# api_name: {api_spec.api_name}",
        f"# category: {api_spec.top_category}",
        f"# sub_category: {api_spec.sub_category}",
        f"# template: {template_kind}",
        f"# api_url: {api_spec.url}",
    ]
    if api_spec.menu_path:
        lines.extend(_front_matter_value("menu_path", api_spec.menu_path))
    lines.append("# ---")
    lines.extend(["", *imports, ""])
    if extra_comments:
        lines.extend(extra_comments)
        lines.append("")
    lines.extend(
        [
            *constants,
            "",
        ]
    )
    return lines


def _front_matter_value(key: str, value: str) -> list[str]:
    lines = value.splitlines() or [""]
    first, *rest = lines
    comments = [f"# {key}: {first}"]
    comments.extend(f"#   {line}" for line in rest)
    return comments


def _render_signature(
    function_name: str,
    parameters: list[RequestParameter],
    *,
    kind: Literal["rest", "oauth", "websocket_request_once", "websocket_realtime"],
    response_table: ResponseTableSpec | None = None,
) -> str:
    prefix = "async def" if kind.startswith("websocket") else "def"
    lines = [f"{prefix} {function_name}("]
    for parameter in parameters:
        if parameter.required:
            lines.append(f"    {parameter.parameter_name}: {parameter.annotation},")
        else:
            default_literal = _signature_default_literal(parameter)
            lines.append(f"    {parameter.parameter_name}: {parameter.annotation} | None = {default_literal},")
    if kind == "rest":
        return_type = "dict[str, pd.DataFrame]" if response_table and response_table.table_keys else "pd.DataFrame"
        lines.append(f") -> {return_type}:")
        return "\n".join(lines)

    lines.append('    output: Literal["dataframe", "json"] = "dataframe",')
    if kind == "oauth":
        lines.append('    mode: Literal["real", "demo"] | None = None,')
    elif kind == "websocket_request_once":
        pass
    else:
        lines.append("    max_messages: int = 10,")
    lines.append(") -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:")
    return "\n".join(lines)


def _render_docstring(
    api_spec: ApiSpec,
    parameters: list[RequestParameter],
    *,
    function_name: str,
    kind: Literal["rest", "oauth", "websocket_request_once", "websocket_realtime"],
    response_table: ResponseTableSpec | None = None,
) -> list[str]:
    return_description = _return_description(kind)
    lines = [
        '    """',
        f"    {api_spec.api_name}[{api_spec.api_id}] API를 호출합니다.",
    ]
    auth_note = _auth_runtime_docstring_note(kind, api_spec.url)
    if auth_note:
        lines.extend(["", f"    {auth_note}"])
    lines.extend(
        [
            "",
            "    Args:",
        ]
    )
    for parameter in parameters:
        description_lines = _parameter_description_lines(parameter)
        lines.append(f"        {parameter.parameter_name}: {description_lines[0]}")
        for extra_line in description_lines[1:]:
            lines.append(f"            {extra_line}")
    if kind != "rest":
        lines.append('        output: "dataframe" 또는 "json".')
    if kind == "oauth":
        lines.append('        mode: "real" 또는 "demo". 생략하면 current auth profile을 사용합니다.')
    elif kind == "websocket_realtime":
        lines.append("        max_messages: 수집할 최대 실시간 메시지 수.")
    lines.extend(
        [
            "",
            "    Returns:",
            f"        {return_description}",
            "",
            "    Example:",
        ]
    )
    if kind == "rest" and not (response_table and response_table.table_keys):
        lines.append(f"        >>> df = {function_name}(")
        lines.extend(_render_docstring_example_arguments(parameters))
        lines.extend(
            [
                "        ... )",
                "        >>> print(df)",
                '    """',
            ]
        )
        return lines

    lines.append(f"        >>> result = {'await ' if kind.startswith('websocket') else ''}{function_name}(")
    lines.extend(_render_docstring_example_arguments(parameters))
    lines.append("        ... )")
    if kind == "rest":
        lines.extend(
            [
                "        >>> for key, df in result.items():",
                "        ...     print(key, df)",
            ]
        )
    else:
        lines.extend(
            [
                '        >>> for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):',
                "        ...     print(k, v.head() if isinstance(v, pd.DataFrame) else v)",
            ]
        )
    lines.append('    """')
    return lines


def _auth_runtime_docstring_note(
    kind: Literal["rest", "oauth", "websocket_request_once", "websocket_realtime"],
    url: str,
) -> str | None:
    if kind == "rest":
        return "공통 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다."
    if kind.startswith("websocket"):
        return "공통 WebSocket 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다."
    if url == "/oauth2/token":
        return "발급된 토큰은 공통 토큰 저장소에 저장되며 토큰 값은 출력하지 않습니다."
    if url == "/oauth2/revoke":
        return "공통 토큰 저장소의 현재 토큰을 서버에서 폐기하고 로컬 캐시도 삭제합니다."
    return None


def _return_description(kind: str) -> str:
    if kind == "websocket_realtime":
        return "실시간 수신 데이터를 반환합니다."
    if kind.startswith("websocket"):
        return "WebSocket 응답 데이터를 반환합니다."
    return "API 응답 데이터입니다."


def _parameter_description_lines(parameter: RequestParameter) -> list[str]:
    description = parameter.description or parameter.label or parameter.body_key
    lines = [line.strip() for line in description.splitlines() if line.strip()]
    return lines or [parameter.body_key]


def _render_docstring_example_arguments(parameters: list[RequestParameter]) -> list[str]:
    lines: list[str] = []
    for parameter in parameters:
        value = _example_argument_value(parameter)
        if value is None and not parameter.required:
            continue
        lines.append(f"        ...     {parameter.parameter_name}={_python_literal(value)},")
    return lines


def _render_required_parameter_checks(parameters: list[RequestParameter]) -> list[str]:
    required_parameters = [parameter for parameter in parameters if parameter.required]
    lines = ["", "    # 1. 필수 파라미터 검증"]
    if not required_parameters:
        return lines
    for parameter in required_parameters:
        message = f"{parameter.parameter_name} is required."
        lines.extend(
            [
                f"    if not {parameter.parameter_name}:",
                f"        raise ValueError({_python_literal(message)})",
            ]
        )
    return lines


def _render_params_block(parameters: list[RequestParameter]) -> list[str]:
    lines = ["", "    # 2. 요청 파라미터 바디", "    body = {"]
    for parameter in parameters:
        if parameter.required:
            lines.append(f'        "{parameter.body_key}": {parameter.parameter_name},')
    lines.append("    }")
    for parameter in parameters:
        if parameter.required:
            continue
        lines.extend(
            [
                f"    if {parameter.parameter_name} is not None:",
                f'        body["{parameter.body_key}"] = {parameter.parameter_name}',
            ]
        )
    return lines


def _render_table_rows_initializer(
    response_table: ResponseTableSpec,
    *,
    indent: str,
    rows_var: str = "table_rows",
) -> list[str]:
    lines = [f"{indent}{rows_var} = {{"]
    for records_key in response_table.table_keys:
        lines.append(f"{indent}    {_json_string_literal(records_key)}: [],")
    lines.append(f"{indent}}}")
    return lines


def _render_dataframe_conversion(
    response_table: ResponseTableSpec,
    *,
    body_var: str,
    result_var: str,
    indent: str,
) -> list[str]:
    lines: list[str] = []
    if response_table.table_keys:
        lines.extend(_render_table_rows_initializer(response_table, indent=indent))
        lines.extend(_render_dataframe_rows_extend(response_table, body_var=body_var, rows_var="table_rows", indent=indent))
        lines.extend(
            [
                f"{indent}{result_var} = {{",
                f"{indent}    TABLE_KEYS.get(key, key): pd.DataFrame(records).rename(columns=COLUMNS)",
                f"{indent}    for key, records in table_rows.items()",
                f"{indent}}}",
            ]
        )
        if response_table.scalar_columns:
            lines.extend(
                [
                    f"{indent}summary_row = {{",
                    f"{indent}    key: {body_var}.get(key)",
                    f"{indent}    for key in SUMMARY_COLUMNS",
                    f"{indent}}}",
                    f"{indent}{result_var} = {{",
                    f"{indent}    SUMMARY_KEY: pd.DataFrame([summary_row]).rename(columns=SUMMARY_COLUMNS),",
                    f"{indent}    **{result_var},",
                    f"{indent}}}",
                ]
            )
        return lines

    lines.extend(
        [
            f"{indent}scalar_values = {{",
            f"{indent}    key: value",
            f"{indent}    for key, value in {body_var}.items()",
            f'{indent}    if key not in {{"return_code", "return_msg", "trnm"}} and not isinstance(value, (dict, list))',
            f"{indent}}}",
            f"{indent}{result_var} = pd.DataFrame([scalar_values]) if scalar_values else pd.DataFrame()",
        ]
    )
    lines.append(f"{indent}{result_var} = {result_var}.rename(columns=COLUMNS)")
    return lines


def _render_dataframe_rows_extend(
    response_table: ResponseTableSpec,
    *,
    body_var: str,
    rows_var: str,
    indent: str,
) -> list[str]:
    lines: list[str] = []
    if response_table.table_keys:
        lines.extend(
            [
                f"{indent}for key in {rows_var}:",
                f"{indent}    records = {body_var}.get(key, [])",
                f"{indent}    if isinstance(records, list):",
                f"{indent}        {rows_var}[key].extend(",
                f"{indent}            record for record in records if isinstance(record, dict)",
                f"{indent}        )",
            ]
        )
        return lines
    lines.extend(
        [
            f"{indent}row = {{",
            f"{indent}    key: {body_var}.get(key)",
            f"{indent}    for key in COLUMNS",
            f"{indent}}}",
            f"{indent}if row:",
            f"{indent}    {rows_var}.append(row)",
        ]
    )
    return lines


def _render_summary_rows_append(
    response_table: ResponseTableSpec,
    *,
    body_var: str,
    rows_var: str,
    indent: str,
) -> list[str]:
    if not response_table.scalar_columns:
        return []
    return [
        f"{indent}{rows_var}.append({{",
        f"{indent}    key: {body_var}.get(key)",
        f"{indent}    for key in SUMMARY_COLUMNS",
        f"{indent}}})",
    ]


def _render_main_block(
    function_name: str,
    parameters: list[RequestParameter],
    *,
    async_call: bool,
    oauth: bool = False,
    result_shape: Literal["generic", "dataframe", "dataframe_dict"] = "generic",
) -> list[str]:
    call_arguments = _render_main_call_arguments(parameters)
    if async_call:
        lines = [
            "",
            "async def main() -> None:",
            "    # 로깅 설정",
            "    logging.basicConfig(level=logging.INFO)",
            "    # 출력 옵션 설정",
            *_display_option_lines(indent="    "),
            "",
            "    # API 호출",
            f"    result = await {function_name}(",
            *call_arguments,
            "    )",
            "    # 결과 출력",
            '    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):',
            "        print(k, _format_display(v).head() if isinstance(v, pd.DataFrame) else v)",
            "",
            "",
            "if __name__ == \"__main__\":",
            "    asyncio.run(main())",
        ]
        return lines
    if result_shape == "dataframe":
        lines = [
            "",
            "if __name__ == \"__main__\":",
            "    # 로깅 설정",
            "    logging.basicConfig(level=logging.INFO)",
            "    # 출력 옵션 설정",
            *_display_option_lines(indent="    "),
            "",
            "    # API 호출",
            f"    df = {function_name}(",
            *call_arguments,
            "    )",
            "    # 결과 출력",
            "    print(_format_display(df))",
        ]
        return lines
    if result_shape == "dataframe_dict":
        lines = [
            "",
            "if __name__ == \"__main__\":",
            "    # 로깅 설정",
            "    logging.basicConfig(level=logging.INFO)",
            "    # 출력 옵션 설정",
            *_display_option_lines(indent="    "),
            "",
            "    # API 호출",
            f"    result = {function_name}(",
            *call_arguments,
            "    )",
            "    # 결과 출력",
            "    for key, df in result.items():",
            '        print(f"\\n[{key}]")',
            "        print(_format_display(df))",
        ]
        return lines
    lines = [
        "",
        "if __name__ == \"__main__\":",
        "    # 로깅 설정",
        "    logging.basicConfig(level=logging.INFO)",
        "    # 출력 옵션 설정",
        *_display_option_lines(indent="    "),
        "",
        "    # API 호출",
        f"    result = {function_name}(",
        *call_arguments,
    ]
    lines.extend(
        [
            "    )",
            "    # 결과 출력",
            '    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):',
            "        print(k, _format_display(v).head() if isinstance(v, pd.DataFrame) else v)",
        ]
    )
    return lines


def _display_helper_lines(response_table: ResponseTableSpec) -> list[str]:
    numeric_columns = {
        label
        for label in [*response_table.scalar_columns.values(), *response_table.columns.values()]
        if _is_default_numeric_display_column(label)
    }
    return [
        "",
        f"NUMERIC_COLUMNS = {_tuple_literal(sorted(numeric_columns))}",
        "",
        "def _format_display(df: pd.DataFrame) -> pd.DataFrame:",
        "    display = df.copy()",
        "    for column in tuple(NUMERIC_COLUMNS):",
        "        if column in display.columns:",
        "            display[column] = display[column].map(_format_display_value)",
        "    return display",
        "",
        "",
        "def _format_display_value(value: object) -> object:",
        "    if value is None or isinstance(value, (dict, list, tuple, set)):",
        "        return value",
        "    try:",
        "        if pd.isna(value):",
        "            return value",
        "    except (TypeError, ValueError):",
        "        return value",
        "    text = str(value).strip()",
        "    sign = \"-\" if text.startswith(\"-\") else \"\"",
        "    unsigned = text[1:] if sign else text",
        "    if \".\" in unsigned:",
        "        integer, fraction = unsigned.split(\".\", 1)",
        "        if integer.isdigit() and fraction.isdigit():",
        "            return f\"{sign}{int(integer or '0'):,}.{fraction}\"",
        "        return value",
        "    if unsigned.isdigit() and len(unsigned) >= 6:",
        "        return f\"{sign}{int(unsigned or '0'):,}\"",
        "    return value",
        "",
    ]


def _is_default_numeric_display_column(label: str) -> bool:
    text_markers = ("코드", "번호", "명", "구분", "일자", "일시", "시간", "대출일")
    numeric_markers = (
        "금액",
        "금",
        "대금",
        "가격",
        "가",
        "수량",
        "수수료",
        "세금",
        "손익",
        "평가",
        "매입",
        "현재가",
        "종가",
        "예수금",
        "자산",
        "대출",
        "담보",
        "%",
        "신용이자",
        "이용료",
        "잔고"
    )
    return not any(marker in label for marker in text_markers) and any(
        marker in label for marker in numeric_markers
    )


def _tuple_literal(values: list[str]) -> str:
    if not values:
        return "()"
    if len(values) == 1:
        return f"({_python_literal(values[0])},)"
    items = "\n".join(f"    {_python_literal(value)}," for value in values)
    return f"(\n{items}\n)"


def _display_option_lines(*, indent: str) -> list[str]:
    return [
        f'{indent}pd.set_option("display.max_columns", None)',
        f'{indent}pd.set_option("display.width", 160)',
    ]


def _render_main_call_arguments(parameters: list[RequestParameter]) -> list[str]:
    lines: list[str] = []
    for parameter in parameters:
        value = _example_argument_value(parameter)
        if value is None and not parameter.required:
            continue
        lines.append(f"        {parameter.parameter_name}={_python_literal(value)},")
    return lines


def _signature_default_literal(parameter: RequestParameter) -> str:
    value = parameter.default_value
    if value is None or isinstance(value, (list, dict)):
        return "None"
    return _python_literal(value)


def _example_argument_value(parameter: RequestParameter) -> object | None:
    if parameter.default_value is not None:
        return parameter.default_value
    if parameter.annotation == "list[Any]":
        return []
    if parameter.annotation == "dict[str, Any]":
        return {}
    return ""


def _python_literal(value: object) -> str:
    return repr(value)


def _request_parameters(api_spec: ApiSpec) -> list[RequestParameter]:
    body_values = _request_body_example(api_spec)
    parameters: list[RequestParameter] = []
    used_names: dict[str, str] = {}
    for item in api_spec.request_body:
        if item.get("is_section") or int(item.get("depth", 0) or 0) != 0:
            continue
        body_key = str(item.get("element", "")).strip()
        if not body_key:
            continue
        parameter_name = _sanitize_identifier(body_key)
        previous_key = used_names.get(parameter_name)
        if previous_key is not None and previous_key != body_key:
            raise ValueError(f"duplicate parameter name {parameter_name}: {previous_key}, {body_key}")
        used_names[parameter_name] = body_key
        required = str(item.get("required", "")).strip().upper() == "Y" or _is_list_container(item)
        parameters.append(
            RequestParameter(
                body_key=body_key,
                parameter_name=parameter_name,
                required=required,
                annotation=_parameter_annotation(item),
                default_value=_find_example_value(body_values, body_key),
                label=str(item.get("한글명", "")).strip(),
                description=str(item.get("description", "")).strip(),
            )
        )
    return sorted(parameters, key=lambda parameter: not parameter.required)


def _parameter_annotation(item: dict) -> str:
    item_type = str(item.get("type", "")).strip().upper()
    if item_type == "LIST":
        return "list[Any]"
    if item_type in {"OBJECT", "DICT", "MAP"}:
        return "dict[str, Any]"
    return "str"


def _parameter_mappings(parameters: list[RequestParameter]) -> dict[str, list[str]]:
    return {parameter.parameter_name: [parameter.body_key] for parameter in parameters}


def _request_body_example(api_spec: ApiSpec) -> dict[str, object]:
    parsed = _parse_jsonish(api_spec.request_example)
    if isinstance(parsed, dict):
        return _sanitize_request_example(parsed)

    skeleton: dict[str, object] = {}
    for item in api_spec.request_body:
        if item.get("is_section") or int(item.get("depth", 0) or 0) != 0:
            continue
        key = str(item.get("element", "")).strip()
        if not key:
            continue
        skeleton[key] = [] if _is_list_container(item) else _placeholder_value(item)
    return skeleton


def _request_body_comment(body_items: list[dict]) -> str:
    if not body_items:
        return "- 없음"
    lines = []
    for item in body_items:
        if item.get("is_section"):
            continue
        element = item.get("element", "")
        required = item.get("required", "")
        name = item.get("한글명", "")
        depth = int(item.get("depth", 0) or 0)
        indent = "  " * depth
        item_type = str(item.get("type", "")).strip().upper()
        type_label = " [LIST]" if item_type == "LIST" else ""
        lines.append(f"{indent}- {element} ({name}, required={required}){type_label}")
    return "\n".join(lines)


def _comment_block(label: str, value: str) -> list[str]:
    lines = value.splitlines() or [""]
    first, *rest = lines
    comments = [f"# {label}: {first}"]
    comments.extend(f"# {line}" for line in rest)
    return comments


def _response_table_spec(response_body: list[dict]) -> ResponseTableSpec:
    table_keys = _top_level_list_keys(response_body)
    scalar_columns = _scalar_response_columns(response_body)
    table_labels = _table_key_labels(response_body, table_keys)
    if not table_keys:
        return ResponseTableSpec(
            table_keys=[],
            table_labels={},
            columns=scalar_columns,
            scalar_columns={},
        )
    return ResponseTableSpec(
        table_keys=table_keys,
        table_labels=table_labels,
        columns=_list_child_columns(response_body, table_keys),
        scalar_columns=scalar_columns,
    )


def _top_level_list_keys(response_body: list[dict]) -> list[str]:
    records_keys: list[str] = []
    for item in response_body:
        if item.get("is_section"):
            continue
        if not _is_list_container(item):
            continue
        element = str(item.get("element", "")).strip()
        if element and element not in records_keys:
            records_keys.append(element)
    return records_keys


def _table_key_labels(response_body: list[dict], table_keys: list[str]) -> dict[str, str]:
    labels: dict[str, str] = {}
    for item in response_body:
        if item.get("is_section"):
            continue
        element = str(item.get("element", "")).strip()
        label = str(item.get("한글명", "")).strip()
        if element in table_keys and label:
            labels[element] = label
    return labels


def _scalar_response_columns(response_body: list[dict]) -> dict[str, str]:
    mappings: dict[str, str] = {}
    for item in response_body:
        if item.get("is_section"):
            continue
        if int(item.get("depth", 0) or 0) != 0:
            continue
        if _is_list_container(item):
            continue
        element = str(item.get("element", "")).strip()
        label = str(item.get("한글명", "")).strip()
        if element and label and element not in COMMON_RESPONSE_FIELDS:
            mappings[element] = label
    return mappings


def _list_child_columns(response_body: list[dict], records_keys: list[str]) -> dict[str, str]:
    mappings: dict[str, str] = {}
    collecting = False
    for item in response_body:
        depth = int(item.get("depth", 0) or 0)
        element = str(item.get("element", "")).strip()
        if depth == 0:
            collecting = element in records_keys and _is_list_container(item)
            continue
        if not collecting or depth != 1 or item.get("is_section") or _is_list_item(item):
            continue
        label = str(item.get("한글명", "")).strip()
        if element and label and element not in COMMON_RESPONSE_FIELDS:
            mappings[element] = label
    return mappings


def _table_keys_constant_line(response_table: ResponseTableSpec) -> str:
    return f"TABLE_KEYS = {_json_literal(response_table.table_labels)}"


def _columns_constant_line(response_table: ResponseTableSpec) -> str:
    return f"COLUMNS = {_json_literal(response_table.columns)}"


def _summary_constant_lines(response_table: ResponseTableSpec) -> list[str]:
    if not response_table.scalar_columns:
        return []
    return [
        f'SUMMARY_KEY = "{SUMMARY_KEY}"',
        f"SUMMARY_COLUMNS = {_json_literal(response_table.scalar_columns)}",
    ]


def _parse_jsonish(raw: str):
    text = raw.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _sanitize_request_example(parsed: dict) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in parsed.items():
        if _is_sensitive_example_field(key):
            sanitized[key] = f"TODO_{key}"
            continue
        sanitized[key] = value
    return sanitized


def _is_sensitive_example_field(key: str) -> bool:
    lowered = key.lower()
    sensitive_markers = ("appkey", "secretkey", "token", "authorization")
    return any(marker in lowered for marker in sensitive_markers)


def _placeholder_value(item: dict) -> str:
    key = str(item.get("element", "")).strip()
    return f"TODO_{key}" if key else "TODO"


def _find_example_value(payload: object, key: str) -> object | None:
    if isinstance(payload, dict):
        if key in payload:
            return payload[key]
        for nested_value in payload.values():
            found = _find_example_value(nested_value, key)
            if found is not None:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = _find_example_value(item, key)
            if found is not None:
                return found
    return None


def _is_list_container(item: dict) -> bool:
    return _is_list_item(item) and int(item.get("depth", 0) or 0) == 0


def _is_list_item(item: dict) -> bool:
    return str(item.get("type", "")).strip().upper() == "LIST"


def _default_function_name(api_id: str) -> str:
    normalized = re.sub(r"\W+", "_", api_id.strip()).strip("_")
    if not normalized:
        normalized = "api"
    if normalized[0].isdigit():
        normalized = f"api_{normalized}"
    if keyword.iskeyword(normalized):
        normalized = f"{normalized}_value"
    return normalized


def _sanitize_identifier(value: str) -> str:
    normalized = re.sub(r"\W+", "_", value.strip().lower()).strip("_")
    if not normalized:
        normalized = "value"
    if normalized[0].isdigit():
        normalized = f"field_{normalized}"
    if keyword.iskeyword(normalized):
        normalized = f"{normalized}_value"
    return normalized


def _is_valid_function_name(value: str) -> bool:
    return value.isidentifier() and not keyword.iskeyword(value)


def _default_template_kind(api_spec: ApiSpec):
    if api_spec.top_category == "OAuth 인증" or api_spec.url.startswith("/oauth2"):
        return "oauth"
    if "/websocket" in api_spec.url:
        return "websocket_realtime" if _is_realtime_stream_spec(api_spec) else "websocket_request_once"
    return "rest"


def _is_realtime_stream_spec(api_spec: ApiSpec) -> bool:
    response_elements = {str(item.get("element", "")).strip() for item in api_spec.response_body}
    section_names = {
        str(item.get("element", "")).strip() or str(item.get("한글명", "")).strip()
        for item in api_spec.response_body
        if item.get("is_section")
    }
    return "values" in response_elements or "실시간 데이터" in section_names


def _realtime_fields_block(api_id: str) -> str:
    names = list(FID_MAP.get(api_id, {}).values())
    if not names:
        return "\nFIELDS: list[str] = []"
    items = "\n".join(f'    "{name}",' for name in names)
    return f"\nFIELDS: list[str] = [\n{items}\n]"


def _json_literal(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=4)


def _json_string_literal(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _casefold_relative_key(top_category: str, sub_category: str, filename: str) -> str:
    return "/".join(
        [
            sanitize_path_part(top_category).casefold(),
            sanitize_path_part(sub_category).casefold(),
            f"{filename}.py".casefold(),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate runnable Kiwoom examples from local specs.")
    parser.add_argument("--api-list", type=Path, default=Path("api_list.csv"))
    parser.add_argument("--spec", type=Path, default=Path("kiwoom_api_spec.json"))
    parser.add_argument("--out", type=Path, default=Path("examples"))
    parser.add_argument("--mapping", type=Path, default=Path("utils/function_name_map.csv"))
    parser.add_argument(
        "--function-name-overrides",
        type=Path,
        default=Path("func_name_temp.csv"),
        help="Optional compact CSV with columns '함수이름,API ID' applied over --mapping when present.",
    )
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    written = scaffold_examples(
        args.api_list,
        args.spec,
        args.out,
        mapping_path=args.mapping,
        function_name_overrides_path=args.function_name_overrides,
        report_path=args.report,
    )
    print(f"wrote {len(written)} examples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
