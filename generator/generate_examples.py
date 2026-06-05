"""Generate runnable Kiwoom examples directly from the official workbook.

This v2 generator is intentionally self-contained. It does not import the
legacy ``generator`` package and does not require intermediate ``api_list.csv`` or
``kiwoom_api_spec.json`` files.
"""

from __future__ import annotations

import argparse
import csv
import json
import keyword
import math
import re
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Literal

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
for _path in (ROOT, SRC_ROOT):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

DEFAULT_XLSX = ROOT / "키움 REST API 문서.xlsx"
DEFAULT_OUTPUT_DIR = ROOT / "examples"
DEFAULT_MAPPING_PATH = ROOT / "generator" / "function_name_map.csv"
DEFAULT_REPORT_PATH = ROOT / "generator" / "examples_generation_report.json"

SECTION_KEYS = ("Request", "Response", "Request Example", "Response Example")
TEMPLATE_KINDS = frozenset({"rest", "oauth", "websocket_request_once", "websocket_realtime"})
MAPPING_COLUMNS = (
    "api_id",
    "api_name",
    "function_name",
    "template_kind",
    "category",
    "sub_category",
    "url",
    "enabled",
)
FUNCTION_NAME_OVERRIDE_COLUMNS = ("함수이름", "API ID")
INVALID_PATH_CHARS = re.compile(r'[\\/:*?"<>|]')
COMMON_RESPONSE_FIELDS = frozenset({"return_code", "return_msg", "trnm"})
MESSAGE_KEY = "메시지"
MESSAGE_COLUMNS = {"return_code": "응답코드", "return_msg": "응답메시지"}
SUMMARY_KEY = "요약"


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
    request_headers: list[dict[str, Any]]
    request_body: list[dict[str, Any]]
    request_example: str
    response_body: list[dict[str, Any]]
    menu_path: str


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


def parse_workbook(xlsx_path: Path) -> tuple[list[ApiListRow], dict[str, dict[str, Any]]]:
    workbook = pd.ExcelFile(xlsx_path)
    api_rows = _parse_api_list(workbook)
    apis: dict[str, dict[str, Any]] = {}
    for sheet_name in workbook.sheet_names[1:]:
        if sheet_name == "오류코드":
            continue
        api_payload = _parse_api_sheet(workbook, sheet_name)
        api_id = str(api_payload.get("meta", {}).get("API ID", "")).strip()
        if api_id:
            apis[api_id] = api_payload

    listed_ids = {row.api_id for row in api_rows}
    parsed_ids = set(apis)
    missing = sorted(listed_ids - parsed_ids)
    extra = sorted(parsed_ids - listed_ids)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing detail sheets: {', '.join(missing)}")
        if extra:
            details.append(f"extra detail sheets: {', '.join(extra)}")
        raise ValueError("; ".join(details))
    return api_rows, apis


def _parse_api_list(workbook: pd.ExcelFile) -> list[ApiListRow]:
    frame = workbook.parse("API 리스트", header=None)
    header_row: int | None = None
    column_map: dict[str, int] = {}
    for row_index in range(len(frame)):
        values = [_cell_text(frame.iat[row_index, col]) for col in range(frame.shape[1])]
        if "API ID" not in values:
            continue
        header_row = row_index
        column_map = {value: index for index, value in enumerate(values) if value}
        break
    if header_row is None:
        raise ValueError("API 리스트 시트에서 API ID 헤더를 찾을 수 없습니다.")

    def value(row_index: int, column: str) -> str:
        col = column_map[column]
        return _cell_text(frame.iat[row_index, col]) if col < frame.shape[1] else ""

    rows: list[ApiListRow] = []
    for row_index in range(header_row + 1, len(frame)):
        api_id = value(row_index, "API ID")
        url = value(row_index, "URL")
        if not api_id or api_id == "공통" or not url:
            continue
        rows.append(
            ApiListRow(
                api_id=api_id,
                api_name=value(row_index, "API 명"),
                top_category=value(row_index, "대분류"),
                sub_category=value(row_index, "중분류"),
                url=url,
            )
        )
    return rows


def _parse_api_sheet(workbook: pd.ExcelFile, sheet_name: str) -> dict[str, Any]:
    frame = workbook.parse(sheet_name, header=None)
    sections = _find_sections(frame)
    total_rows = len(frame)
    request_start = sections.get("Request", total_rows)
    payload: dict[str, Any] = {"meta": _parse_api_meta(frame, request_start)}
    for section_name in ("Request", "Response"):
        if section_name not in sections:
            continue
        start, end = _section_range(section_name, sections, total_rows)
        payload[section_name.lower()] = _parse_request_response_block(frame, start, end)
    for section_name in ("Request Example", "Response Example"):
        if section_name not in sections:
            continue
        start, end = _section_range(section_name, sections, total_rows)
        key = "request_example" if section_name == "Request Example" else "response_example"
        payload[key] = _parse_example_block(frame, start, end)
    return payload


def _find_sections(frame: pd.DataFrame) -> dict[str, int]:
    found: dict[str, int] = {}
    for row_index in range(len(frame)):
        for col in range(min(4, frame.shape[1])):
            value = _cell_text(frame.iat[row_index, col])
            if value in SECTION_KEYS and value not in found:
                found[value] = row_index
                break
        if len(found) == len(SECTION_KEYS):
            break
    return found


def _section_range(name: str, sections: dict[str, int], total_rows: int) -> tuple[int, int]:
    start = sections[name]
    end = total_rows
    for _, index in sorted(sections.items(), key=lambda item: item[1]):
        if index > start:
            end = index
            break
    return start, end


def _parse_request_response_block(frame: pd.DataFrame, start: int, end: int) -> dict[str, list[dict[str, Any]]]:
    column_map: dict[str, int] = {}
    data_start = start + 1
    for row_index in range(start + 1, end):
        for col in range(frame.shape[1]):
            if _cell_text(frame.iat[row_index, col]) != "구분":
                continue
            column_map = {
                _cell_text(frame.iat[row_index, header_col]): header_col
                for header_col in range(frame.shape[1])
                if _cell_text(frame.iat[row_index, header_col])
            }
            data_start = row_index + 1
            break
        if column_map:
            break
    if not column_map:
        column_map = {
            "구분": 0,
            "Element": 1,
            "한글명": 2,
            "Type": 3,
            "Required": 4,
            "Length": 5,
            "Description": 6,
        }

    def value(row_index: int, column: str, fallback_col: int) -> str:
        col = column_map.get(column, fallback_col)
        return _cell_text(frame.iat[row_index, col]) if col < frame.shape[1] else ""

    header_items: list[dict[str, Any]] = []
    body_items: list[dict[str, Any]] = []
    current_group: str | None = None
    for row_index in range(data_start, end):
        group = value(row_index, "구분", 0)
        if group in {"Header", "Body"}:
            current_group = group

        raw_element = value(row_index, "Element", 1)
        if not raw_element:
            continue
        depth, element = _parse_element_depth(raw_element)
        if not element:
            continue

        label = value(row_index, "한글명", 2)
        item_type = value(row_index, "Type", 3)
        required = value(row_index, "Required", 4)
        item = {
            "element": element,
            "depth": depth,
            "is_section": bool(not label and not item_type and not required),
            "한글명": label,
            "type": item_type,
            "required": required,
            "length": value(row_index, "Length", 5),
            "description": value(row_index, "Description", 6),
        }
        if current_group == "Header":
            header_items.append(item)
        elif current_group == "Body":
            body_items.append(item)
    return {"header": header_items, "body": body_items}


def _parse_api_meta(frame: pd.DataFrame, request_start: int) -> dict[str, str]:
    meta: dict[str, str] = {}
    for row_index in range(request_start):
        key = _cell_text(frame.iat[row_index, 0])
        if not key:
            continue
        value = ""
        for col in range(1, frame.shape[1]):
            candidate = _cell_text(frame.iat[row_index, col])
            if candidate:
                value = candidate
                break
        meta[key] = value
    return meta


def _parse_example_block(frame: pd.DataFrame, start: int, end: int) -> str:
    for row_index in range(start + 1, end):
        for col in range(frame.shape[1]):
            value = _cell_text(frame.iat[row_index, col])
            if value:
                return value
    return ""


def _parse_element_depth(raw: str) -> tuple[int, str | None]:
    value = raw.strip()
    depth = 0
    while value.startswith("-"):
        depth += 1
        value = value[1:].lstrip()
    return depth, value.strip() or None


def _cell_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    try:
        if math.isnan(float(value)):
            return ""
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def build_api_specs(api_rows: list[ApiListRow], api_payloads: dict[str, dict[str, Any]]) -> list[ApiSpec]:
    specs: list[ApiSpec] = []
    for row in api_rows:
        payload = api_payloads[row.api_id]
        meta = payload.get("meta", {})
        request = payload.get("request", {})
        response = payload.get("response", {})
        specs.append(
            ApiSpec(
                api_id=row.api_id,
                api_name=row.api_name,
                top_category=row.top_category,
                sub_category=row.sub_category,
                url=row.url,
                method=str(meta.get("Method") or "POST"),
                content_type=str(meta.get("Content-Type") or "application/json;charset=UTF-8"),
                request_headers=list(request.get("header", [])),
                request_body=list(request.get("body", [])),
                request_example=str(payload.get("request_example") or ""),
                response_body=list(response.get("body", [])),
                menu_path=str(meta.get("메뉴 위치") or ""),
            )
        )
    return specs


def load_mapping(path: Path | None, api_specs: list[ApiSpec]) -> dict[str, FunctionNameMapEntry]:
    if path is None:
        return {api_spec.api_id: default_mapping_entry(api_spec) for api_spec in api_specs}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in MAPPING_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"mapping table missing columns: {', '.join(missing)}")
        entries: dict[str, FunctionNameMapEntry] = {}
        for row in reader:
            api_id = row["api_id"].strip()
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


def apply_function_name_overrides(
    entries: dict[str, FunctionNameMapEntry],
    path: Path | None,
) -> dict[str, FunctionNameMapEntry]:
    if path is None or not path.exists():
        return entries
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in FUNCTION_NAME_OVERRIDE_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"function name override table missing columns: {', '.join(missing)}")
        overrides: dict[str, str] = {}
        for row in reader:
            api_id = row["API ID"].strip()
            function_name = row["함수이름"].strip()
            if not api_id and not function_name:
                continue
            if not api_id or not function_name:
                raise ValueError("function name override rows must include both 함수이름 and API ID")
            if not _is_valid_function_name(function_name):
                raise ValueError(f"invalid function name override for {api_id}: {function_name}")
            overrides[api_id] = function_name
    unknown = sorted(set(overrides) - set(entries))
    if unknown:
        raise ValueError(f"unknown API ID in function name override table: {', '.join(unknown)}")
    return {
        api_id: replace(entry, function_name=overrides.get(api_id, entry.function_name))
        for api_id, entry in entries.items()
    }


def validate_mapping(api_specs: list[ApiSpec], entries: dict[str, FunctionNameMapEntry]) -> None:
    errors: list[str] = []
    spec_ids = {api_spec.api_id for api_spec in api_specs}
    entry_ids = set(entries)
    for api_id in sorted(spec_ids - entry_ids):
        errors.append(f"missing mapping for api_id: {api_id}")
    for api_id in sorted(entry_ids - spec_ids):
        errors.append(f"unknown api_id in mapping table: {api_id}")
    function_names: dict[str, str] = {}
    for entry in entries.values():
        if entry.template_kind not in TEMPLATE_KINDS:
            errors.append(f"unknown template_kind for {entry.api_id}: {entry.template_kind}")
        if not _is_valid_function_name(entry.function_name):
            errors.append(f"invalid function_name for {entry.api_id}: {entry.function_name}")
        if not entry.enabled:
            continue
        previous = function_names.get(entry.function_name)
        if previous is not None:
            errors.append(f"duplicate enabled function_name {entry.function_name}: {previous}, {entry.api_id}")
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


def generate_examples(
    *,
    xlsx_path: Path,
    output_dir: Path,
    mapping_path: Path | None,
    function_name_overrides_path: Path | None,
    report_path: Path | None,
    template_kinds: set[str] | None,
) -> list[Path]:
    api_rows, api_payloads = parse_workbook(xlsx_path)
    api_specs = build_api_specs(api_rows, api_payloads)
    mapping = load_mapping(mapping_path, api_specs)
    mapping = apply_function_name_overrides(mapping, function_name_overrides_path)
    validate_mapping(api_specs, mapping)
    if template_kinds is not None:
        unknown = template_kinds - TEMPLATE_KINDS
        if unknown:
            raise ValueError(f"unknown template kind(s): {', '.join(sorted(unknown))}")

    spec_by_id = {api_spec.api_id: api_spec for api_spec in api_specs}
    enabled_specs = [
        spec_by_id[entry.api_id]
        for entry in mapping.values()
        if entry.enabled and (template_kinds is None or entry.template_kind in template_kinds)
    ]
    filename_map = _build_filename_map(enabled_specs)
    written_paths: list[Path] = []
    counts_by_template_kind = dict.fromkeys(sorted(TEMPLATE_KINDS), 0)

    for api_spec in enabled_specs:
        entry = mapping[api_spec.api_id]
        output_path_dir = output_dir / _safe_path(api_spec.top_category) / _safe_path(api_spec.sub_category)
        output_path_dir.mkdir(parents=True, exist_ok=True)

        if entry.template_kind == "websocket_realtime":
            variants = [
                (output_path_dir / f"{entry.function_name}_async.py", render_websocket_realtime_async(api_spec, entry)),
                (output_path_dir / f"{entry.function_name}_pubsub.py", render_websocket_realtime_pubsub(api_spec, entry)),
            ]
            for path, content in variants:
                path.write_text(content, encoding="utf-8")
                written_paths.append(path)
            counts_by_template_kind[entry.template_kind] += len(variants)
            continue

        rendered = render_example(api_spec, entry)
        output_path = output_path_dir / f"{filename_map[api_spec.api_id]}.py"
        output_path.write_text(rendered, encoding="utf-8")
        if filename_map[api_spec.api_id] != entry.function_name:
            (output_path_dir / f"{entry.function_name}.py").write_text(rendered, encoding="utf-8")
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


def _build_filename_map(api_specs: list[ApiSpec]) -> dict[str, str]:
    return build_filename_map(api_specs)


def _safe_path(value: str) -> str:
    return sanitize_path_part(value)


def sanitize_path_part(value: str) -> str:
    cleaned = INVALID_PATH_CHARS.sub("_", value.strip())
    return cleaned.rstrip(" .")


def api_filename(api_spec: ApiSpec) -> str:
    return api_spec.api_id


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


def render_example(api_spec: ApiSpec, entry: FunctionNameMapEntry) -> str:
    generated = GeneratedApiSpec(api_spec=api_spec, mapping=entry)
    if entry.template_kind == "oauth":
        return render_oauth_example(generated)
    if entry.template_kind == "websocket_request_once":
        return render_websocket_request_once_example(generated)
    if entry.template_kind == "websocket_realtime":
        return render_websocket_realtime_example(generated)
    return render_rest_example(generated)


def render_websocket_realtime_async(api_spec: ApiSpec, entry: FunctionNameMapEntry) -> str:
    return render_websocket_realtime_async_example(api_spec, entry)


def render_websocket_realtime_pubsub(api_spec: ApiSpec, entry: FunctionNameMapEntry) -> str:
    return render_websocket_realtime_pubsub_example(api_spec, entry)


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
    lines.extend(_render_oauth_main_block(entry.function_name))
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
            '        "mode": mode,',
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


def _render_oauth_main_block(function_name: str) -> list[str]:
    return [
        "",
        "if __name__ == \"__main__\":",
        "    # 로깅 설정",
        "    logging.basicConfig(level=logging.INFO)",
        "    # 출력 옵션 설정",
        *_display_option_lines(indent="    "),
        "",
        "    # API 호출",
        f"    result = {function_name}(",
        "    )",
        "    # 결과 출력",
        "    print(result)",
    ]


def render_rest_example(generated: GeneratedApiSpec) -> str:
    return _render_rest_example(generated)


def render_oauth_example(generated: GeneratedApiSpec) -> str:
    return _render_oauth_example(generated)


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
    is_reg_realtime = _is_realtime_reg_spec(api_spec)
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
            "from kiwoom.realtime.decoders import decode_values",
        ],
        constants=[
            f'API_ID = "{api_spec.api_id}"',
            f'API_URL = "{api_spec.url}"',
        ],
        extra_comments=[
            "# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.",
        ],
    )
    if is_reg_realtime:
        lines.extend(_render_realtime_reg_packet_builder())
        lines.extend(_render_fid_realtime_function(api_spec, entry))
    else:
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
        lines.extend(_render_websocket_realtime_receive_loop())
        lines.extend(_render_realtime_main_block(entry.function_name, parameters))
    return "\n".join(lines).rstrip() + "\n"


def render_websocket_realtime_async_example(
    api_spec: ApiSpec,
    entry: FunctionNameMapEntry,
) -> str:
    async_entry = replace(entry, function_name=f"{entry.function_name}_async")
    return _render_websocket_realtime_example(GeneratedApiSpec(api_spec=api_spec, mapping=async_entry))


def render_websocket_realtime_pubsub_example(
    api_spec: ApiSpec,
    entry: FunctionNameMapEntry,
) -> str:
    pubsub_entry = replace(entry, function_name=f"{entry.function_name}_pubsub")
    parameters = _request_parameters(api_spec)
    is_reg_realtime = _is_realtime_reg_spec(api_spec)
    lines = _base_module_lines(
        api_spec,
        template_kind=entry.template_kind,
        imports=[
            "import asyncio",
            "import logging",
            "from collections import defaultdict",
            "from typing import Any",
            "",
            "from kiwoom import get_ws_client",
        ],
        constants=[
            f'API_ID = "{api_spec.api_id}"',
            f'API_URL = "{api_spec.url}"',
        ],
        extra_comments=[
            "# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.",
            "# 이 예제는 asyncio.Queue 기반 in-process Pub/Sub 구조를 보여줍니다.",
        ],
    )
    lines.extend(_render_pubsub_helpers())
    if is_reg_realtime:
        lines.extend(_render_realtime_reg_packet_builder())
        lines.extend(_render_fid_pubsub_function(api_spec, pubsub_entry))
        lines.extend(_render_fid_pubsub_main(api_spec, pubsub_entry.function_name))
    else:
        lines.extend(_render_parameter_pubsub_function(api_spec, pubsub_entry, parameters))
        lines.extend(_render_parameter_pubsub_main(pubsub_entry.function_name, parameters))
    return "\n".join(lines).rstrip() + "\n"


def _render_realtime_main_block(function_name: str, parameters: list[RequestParameter]) -> list[str]:
    return [
        "",
        "async def main() -> None:",
        "    # 로깅 설정",
        "    logging.basicConfig(level=logging.INFO)",
        "",
        "    # API 호출",
        f"    result = await {function_name}(",
        *_render_main_call_arguments(parameters),
        "    )",
        "    # 결과 출력",
        '    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):',
        "        print(k, v.head() if isinstance(v, pd.DataFrame) else v)",
        "",
        "",
        "if __name__ == \"__main__\":",
        "    asyncio.run(main())",
    ]


def _render_pubsub_helpers() -> list[str]:
    return [
        "",
        "class AsyncPubSub:",
        "    \"\"\"예제용 in-process Pub/Sub입니다.",
        "",
        "    Redis/Kafka 같은 외부 인프라 없이 asyncio.Queue만 사용합니다.",
        "    WebSocket 수신 데이터 1개를 여러 소비자에게 분기하는 구조를 보여주기 위한",
        "    예제 전용 클래스입니다.",
        "    \"\"\"",
        "",
        "    def __init__(self) -> None:",
        "        self._subscribers: dict[str, list[asyncio.Queue[Any]]] = defaultdict(list)",
        "",
        "    def subscribe(self, topic: str) -> asyncio.Queue[Any]:",
        "        queue: asyncio.Queue[Any] = asyncio.Queue()",
        "        self._subscribers[topic].append(queue)",
        "        return queue",
        "",
        "    async def publish(self, topic: str, message: Any) -> None:",
        "        for queue in self._subscribers.get(topic, []):",
        "            await queue.put(message)",
        "",
        "",
        "def resolve_topic(message: Any) -> str:",
        "    \"\"\"수신 메시지를 발행할 topic을 결정합니다.\"\"\"",
        "    if not isinstance(message, dict):",
        "        return \"kiwoom.raw\"",
        "",
        "    trnm = str(message.get(\"trnm\", \"\")).upper()",
        "    if trnm == \"REAL\":",
        "        data = message.get(\"data\", [])",
        "        if isinstance(data, list) and data and isinstance(data[0], dict):",
        "            realtime_type = str(data[0].get(\"type\", \"\")).strip()",
        "            if realtime_type:",
        "                return f\"kiwoom.realtime.{realtime_type}\"",
        "        return \"kiwoom.realtime\"",
        "    if trnm == \"REG\":",
        "        return \"kiwoom.system.reg\"",
        "    if trnm == \"SYSTEM\":",
        "        return \"kiwoom.system\"",
        "    if trnm:",
        "        return f\"kiwoom.system.{trnm.lower()}\"",
        "    return \"kiwoom.raw\"",
        "",
        "",
        "async def websocket_publisher(",
        "    *,",
        "    pubsub: AsyncPubSub,",
        "    body: dict[str, Any],",
        "    max_messages: int | None = None,",
        ") -> None:",
        "    \"\"\"키움 WebSocket 수신 메시지를 Pub/Sub topic으로 발행합니다.\"\"\"",
        "    if max_messages is not None and max_messages < 1:",
        "        raise ValueError(\"max_messages must be greater than 0\")",
        "",
        "    client = get_ws_client()",
        "    published = 0",
        "",
        "    try:",
        "        await client.subscribe(api_url=API_URL, body=body)",
        "",
        "        async for message in client.iter_messages():",
        "            topic = resolve_topic(message)",
        "            await pubsub.publish(topic, message)",
        "            await pubsub.publish(\"kiwoom.all\", message)",
        "",
        "            published += 1",
        "            if max_messages is not None and published >= max_messages:",
        "                break",
        "",
        "            if isinstance(message, dict):",
        "                trnm = str(message.get(\"trnm\", \"\")).upper()",
        "                return_code = message.get(\"return_code\")",
        "                if trnm == \"SYSTEM\" or return_code not in (None, 0, \"0\"):",
        "                    break",
        "    finally:",
        "        await client.close()",
        "",
        "",
        "async def strategy_subscriber(queue: asyncio.Queue[Any]) -> None:",
        "    \"\"\"전략 로직 소비자 예시입니다.\"\"\"",
        "    while True:",
        "        message = await queue.get()",
        "        print(\"[strategy]\", message, flush=True)",
        "",
        "",
        "async def logger_subscriber(queue: asyncio.Queue[Any]) -> None:",
        "    \"\"\"로그/저장 로직 소비자 예시입니다.\"\"\"",
        "    while True:",
        "        message = await queue.get()",
        "        print(\"[logger]\", message, flush=True)",
        "",
        "",
        "async def run_pubsub(",
        "    *,",
        "    body: dict[str, Any],",
        "    max_messages: int | None = None,",
        ") -> None:",
        "    \"\"\"publisher 1개와 subscriber 2개를 실행합니다.\"\"\"",
        "    pubsub = AsyncPubSub()",
        "    strategy_queue = pubsub.subscribe(\"kiwoom.all\")",
        "    logger_queue = pubsub.subscribe(\"kiwoom.all\")",
        "",
        "    subscriber_tasks = [",
        "        asyncio.create_task(strategy_subscriber(strategy_queue)),",
        "        asyncio.create_task(logger_subscriber(logger_queue)),",
        "    ]",
        "    try:",
        "        await websocket_publisher(",
        "            pubsub=pubsub,",
        "            body=body,",
        "            max_messages=max_messages,",
        "        )",
        "    finally:",
        "        for task in subscriber_tasks:",
        "            task.cancel()",
        "        await asyncio.gather(*subscriber_tasks, return_exceptions=True)",
        "",
    ]


def _render_fid_pubsub_function(api_spec: ApiSpec, entry: FunctionNameMapEntry) -> list[str]:
    return [
        f"async def {entry.function_name}(",
        "    items: list[str],",
        "    types: list[str] | None = None,",
        '    group_no: str = "1",',
        '    refresh: str = "1",',
        "    max_messages: int | None = None,",
        ") -> None:",
        '    """',
        f"    {api_spec.api_name}[{api_spec.api_id}] 실시간 데이터를 Pub/Sub로 분배합니다.",
        "",
        "    공통 WebSocket 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.",
        '    """',
        "    if not items:",
        '        raise ValueError("items is required.")',
        "",
        "    body = build_realtime_reg_packet(",
        "        items=items,",
        "        types=types or [API_ID],",
        "        group_no=group_no,",
        "        refresh=refresh,",
        "    )",
        "    await run_pubsub(body=body, max_messages=max_messages)",
        "",
    ]


def _render_parameter_pubsub_function(
    api_spec: ApiSpec,
    entry: FunctionNameMapEntry,
    parameters: list[RequestParameter],
) -> list[str]:
    lines = _render_pubsub_signature(entry.function_name, parameters)
    lines.extend(
        [
            '    """',
            f"    {api_spec.api_name}[{api_spec.api_id}] WebSocket 메시지를 Pub/Sub로 분배합니다.",
            "",
            "    공통 WebSocket 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.",
            '    """',
            "    if max_messages is not None and max_messages < 1:",
            '        raise ValueError("max_messages must be greater than 0")',
        ]
    )
    lines.extend(_render_required_parameter_checks(parameters))
    lines.extend(_render_params_block(parameters))
    lines.extend(
        [
            "",
            "    await run_pubsub(body=body, max_messages=max_messages)",
            "",
        ]
    )
    return lines


def _render_pubsub_signature(function_name: str, parameters: list[RequestParameter]) -> list[str]:
    lines = [f"async def {function_name}("]
    for parameter in parameters:
        if parameter.required:
            lines.append(f"    {parameter.parameter_name}: {parameter.annotation},")
        else:
            default_literal = _signature_default_literal(parameter)
            lines.append(f"    {parameter.parameter_name}: {parameter.annotation} | None = {default_literal},")
    lines.append("    max_messages: int | None = None,")
    lines.append(") -> None:")
    return lines


def _render_fid_pubsub_main(api_spec: ApiSpec, function_name: str) -> list[str]:
    example_items = _example_realtime_items(api_spec)
    example_types = _example_realtime_types(api_spec)
    return [
        "",
        "async def main() -> None:",
        "    logging.basicConfig(level=logging.INFO)",
        f"    await {function_name}(",
        f"        items={example_items!r},",
        f"        types={example_types!r},",
        "        max_messages=None,",
        "    )",
        "",
        "",
        "if __name__ == \"__main__\":",
        "    asyncio.run(main())",
    ]


def _render_parameter_pubsub_main(function_name: str, parameters: list[RequestParameter]) -> list[str]:
    return [
        "",
        "async def main() -> None:",
        "    logging.basicConfig(level=logging.INFO)",
        f"    await {function_name}(",
        *_render_main_call_arguments(parameters),
        "        max_messages=None,",
        "    )",
        "",
        "",
        "if __name__ == \"__main__\":",
        "    asyncio.run(main())",
    ]


def _render_realtime_reg_packet_builder() -> list[str]:
    return [
        "",
        "def build_realtime_reg_packet(",
        "    *,",
        "    items: list[str],",
        "    types: list[str],",
        '    group_no: str = "1",',
        '    refresh: str = "1",',
        ") -> dict[str, Any]:",
        '    """키움 실시간 항목 등록(REG) 패킷을 생성합니다."""',
        "    if not types:",
        '        raise ValueError("types is required.")',
        "    return {",
        '        "trnm": "REG",',
        '        "grp_no": group_no,',
        '        "refresh": refresh,',
        '        "data": [',
        "            {",
        '                "item": items,',
        '                "type": types,',
        "            }",
        "        ],",
        "    }",
        "",
    ]


def _render_fid_realtime_function(api_spec: ApiSpec, entry: FunctionNameMapEntry) -> list[str]:
    example_items = _example_realtime_items(api_spec)
    example_types = _example_realtime_types(api_spec)
    lines = [
        f"async def {entry.function_name}(",
        "    items: list[str],",
        "    types: list[str] | None = None,",
        '    group_no: str = "1",',
        '    refresh: str = "1",',
        '    output: Literal["dataframe", "json"] = "dataframe",',
        "    max_messages: int = 10,",
        ") -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:",
        '    """',
        f"    {api_spec.api_name}[{api_spec.api_id}] 실시간 데이터를 수신합니다.",
        "",
        "    공통 WebSocket 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.",
        "",
        "    Args:",
        "        items: 실시간 등록 종목 또는 요소 목록.",
        "        types: 실시간 항목 타입 목록. 생략하면 이 예제의 API_ID를 사용합니다.",
        "        group_no: 그룹번호.",
        "        refresh: 기존 등록 유지 여부. \"1\"은 기존 등록을 유지합니다.",
        "        output: \"dataframe\" 또는 \"json\".",
        "        max_messages: 수집할 최대 실시간 메시지 수.",
        "",
        "    Returns:",
        "        실시간 수신 데이터를 반환합니다.",
        "",
        "    Example:",
        f"        >>> result = await {entry.function_name}(",
        f"        ...     items={example_items!r},",
        f"        ...     types={example_types!r},",
        "        ... )",
        "        >>> for k, v in (result.items() if isinstance(result, dict) else [(\"data\", result)]):",
        "        ...     print(k, v.head() if isinstance(v, pd.DataFrame) else v)",
        '    """',
        "    if max_messages < 1:",
        '        raise ValueError("max_messages must be greater than 0")',
        "    if not items:",
        '        raise ValueError("items is required.")',
        "",
        "    body = build_realtime_reg_packet(",
        "        items=items,",
        "        types=types or [API_ID],",
        "        group_no=group_no,",
        "        refresh=refresh,",
        "    )",
    ]
    lines.extend(_render_websocket_realtime_receive_loop())
    lines.extend(
        [
            "",
            "async def main() -> None:",
            "    # 로깅 설정",
            "    logging.basicConfig(level=logging.INFO)",
            "    # API 호출",
            f"    result = await {entry.function_name}(",
            f"        items={example_items!r},",
            f"        types={example_types!r},",
            "    )",
            "    # 결과 출력",
            '    for k, v in (result.items() if isinstance(result, dict) else [("data", result)]):',
            "        print(k, v.head() if isinstance(v, pd.DataFrame) else v)",
            "",
            "",
            "if __name__ == \"__main__\":",
            "    asyncio.run(main())",
        ]
    )
    return lines


def _render_websocket_realtime_receive_loop() -> list[str]:
    return [
        "",
        "    client = get_ws_client()",
        "    rows: list[dict[str, Any]] = []",
        "    system_rows: list[dict[str, Any]] = []",
        "    try:",
        "        await client.subscribe(api_url=API_URL, body=body)",
        "",
        "        async for message in client.iter_messages():",
        "            if not isinstance(message, dict):",
        "                continue",
        "            trnm = str(message.get(\"trnm\", \"\")).upper()",
        "            if trnm in {\"REG\", \"SYSTEM\"}:",
        "                system_rows.append(message)",
        "                print(f\"[{trnm}]\", message, flush=True)",
        "                return_code = message.get(\"return_code\")",
        "                if trnm == \"SYSTEM\" or return_code not in (None, 0, \"0\"):",
        "                    if output == \"json\":",
        "                        return {\"system\": system_rows, \"data\": rows} if rows else system_rows",
        "                    result: dict[str, pd.DataFrame] = {\"system\": pd.DataFrame(system_rows)}",
        "                    if rows:",
        "                        result[\"data\"] = pd.DataFrame(rows)",
        "                    return result",
        "                continue",
        "            if trnm != \"REAL\":",
        "                system_rows.append(message)",
        "                print(f\"[{trnm or 'MESSAGE'}]\", message, flush=True)",
        "                continue",
        "            for entry in message.get(\"data\", []):",
        "                if not isinstance(entry, dict):",
        "                    continue",
        "                values = decode_values(str(entry.get(\"type\", \"\")), entry.get(\"values\", {}))",
        "                rows.append({\"item\": entry.get(\"item\", \"\"), \"type\": entry.get(\"type\", \"\"), **values})",
        "                if len(rows) >= max_messages:",
        "                    if output == \"json\":",
        "                        return {\"system\": system_rows, \"data\": rows} if system_rows else rows",
        "                    result: dict[str, pd.DataFrame] = {\"data\": pd.DataFrame(rows)}",
        "                    if system_rows:",
        "                        result[\"system\"] = pd.DataFrame(system_rows)",
        "                    return result",
        "    finally:",
        "        await client.close()",
        "",
        "    if output == \"json\":",
        "        return {\"system\": system_rows, \"data\": rows} if system_rows else rows",
        "    result: dict[str, pd.DataFrame] = {\"data\": pd.DataFrame(rows)}",
        "    if system_rows:",
        "        result[\"system\"] = pd.DataFrame(system_rows)",
        "    return result",
        "",
    ]


def _example_realtime_items(api_spec: ApiSpec) -> list[str]:
    payload = _request_body_example(api_spec)
    value = _find_example_value(payload, "item")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    if isinstance(value, str):
        return [value]
    return [""]


def _example_realtime_types(api_spec: ApiSpec) -> list[str]:
    payload = _request_body_example(api_spec)
    value = _find_example_value(payload, "type")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    if isinstance(value, str):
        return [value]
    return [api_spec.api_id]


def render_websocket_request_once_example(generated: GeneratedApiSpec) -> str:
    return _render_websocket_request_once_example(generated)


def render_websocket_realtime_example(generated: GeneratedApiSpec) -> str:
    return _render_websocket_realtime_example(generated)


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
    return _display_helper_lines_for_labels([*response_table.scalar_columns.values(), *response_table.columns.values()])


def _display_helper_lines_for_labels(labels: list[str]) -> list[str]:
    numeric_columns = {
        label
        for label in labels
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
        "잔고",
        "율",
        "자산",
        "총액",
        "PER",
        "PBR",
        "ROE",
        "ROA",
        "EPS",
        "BPS",
        "비율",
        "거래량",
        "거래대금",
        "거래회전율",
        "비중",
        "등락률"
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


def _is_realtime_reg_spec(api_spec: ApiSpec) -> bool:
    payload = _request_body_example(api_spec)
    trnm = _find_example_value(payload, "trnm")
    has_items = _find_example_value(payload, "item") is not None
    has_types = _find_example_value(payload, "type") is not None
    return str(trnm).upper() == "REG" and has_items and has_types


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

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate runnable Kiwoom examples from a workbook.")
    parser.add_argument("xlsx", type=Path, help="Path to the Kiwoom REST API workbook")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR, help="Output examples directory")
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING_PATH, help="Optional function_name_map.csv path")
    parser.add_argument(
        "--function-name-overrides",
        type=Path,
        help="Optional CSV with columns '함수이름,API ID'",
    )
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="Output generation report path")
    parser.add_argument("--no-report", action="store_true", help="Do not write a generation report")
    parser.add_argument(
        "--kind",
        action="append",
        choices=sorted(TEMPLATE_KINDS),
        help="Template kind to generate. Repeat to select multiple kinds.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    start = time.perf_counter()
    args = _parse_args(argv)
    written = generate_examples(
        xlsx_path=args.xlsx,
        output_dir=args.out,
        mapping_path=args.mapping,
        function_name_overrides_path=args.function_name_overrides,
        report_path=None if args.no_report else args.report,
        template_kinds=set(args.kind) if args.kind else None,
    )
    elapsed = time.perf_counter() - start
    print(f"wrote {len(written)} examples in {elapsed:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
