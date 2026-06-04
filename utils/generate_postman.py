"""Generate a Postman collection directly from the official Kiwoom workbook.

This v2 generator is a standalone implementation. It does not import legacy
``utils`` modules and does not require ``api_list.csv`` or
``kiwoom_api_spec.json`` as intermediate inputs.
"""

from __future__ import annotations

import argparse
from collections import OrderedDict
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import sys
import time
from typing import Any
from urllib.parse import quote

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
for _path in (ROOT, SRC_ROOT):
    path_text = str(_path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

DEFAULT_OUTPUT_PATH = ROOT / "postman" / "kiwoom-openapi.postman_collection.json"
DEFAULT_CONFIG_PATH = ROOT / "utils_v2" / "postman_collection_config.json"
DEFAULT_REPORT_PATH = ROOT / "utils_v2" / "generate_postman_report.json"
POSTMAN_SCHEMA = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
SECTION_KEYS = ("Request", "Response", "Request Example", "Response Example")
REQUIRED_STATIC_VARIABLES = (
    "PRD",
    "MOCK",
    "APP_KEY",
    "APP_SECRET",
    "APP_KEY_MOCK",
    "APP_SECRET_MOCK",
)
SUPPORTED_WEBSOCKET_STRATEGIES = frozenset({"skip"})
SUPPORTED_BODY_PARAMETER_MODES = frozenset(
    {
        "inline_examples",
        "postman_variables",
        "query_params_to_body",
        "query_params",
        "query_params_and_body",
    }
)


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
class PostmanEnvironmentConfig:
    name: str
    folder_name: str
    base_variable: str
    app_key_variable: str
    app_secret_variable: str
    access_token_variable: str


@dataclass(frozen=True)
class PostmanConfig:
    collection_name: str
    schema: str
    static_variables: OrderedDict[str, str]
    environments: tuple[PostmanEnvironmentConfig, ...]
    websocket_strategy: str
    websocket_reason: str
    body_parameter_mode: str
    body_variable_name_template: str
    request_value_overrides_by_field: OrderedDict[str, str]


@dataclass(frozen=True)
class BodyVariable:
    name: str
    field_path: str
    default_value: Any
    description: str


@dataclass(frozen=True)
class SkippedApi:
    api_id: str
    api_name: str
    category: str
    sub_category: str
    url: str
    reason: str

    def to_json(self) -> dict[str, str]:
        return {
            "api_id": self.api_id,
            "api_name": self.api_name,
            "category": self.category,
            "sub_category": self.sub_category,
            "url": self.url,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class PostmanGenerationReport:
    total_specs: int
    environments: list[str]
    generated_requests: int
    generated_api_ids: list[str]
    skipped_apis: list[SkippedApi]
    counts_by_kind: dict[str, int]
    counts_by_environment: dict[str, int]
    variables: list[str]
    websocket_strategy: str

    def to_json(self) -> dict[str, object]:
        return {
            "total_specs": self.total_specs,
            "environments": self.environments,
            "generated_requests": self.generated_requests,
            "generated_api_ids": self.generated_api_ids,
            "skipped_apis": [skipped.to_json() for skipped in self.skipped_apis],
            "counts_by_kind": self.counts_by_kind,
            "counts_by_environment": self.counts_by_environment,
            "variables": self.variables,
            "websocket_strategy": self.websocket_strategy,
        }


def default_postman_config() -> PostmanConfig:
    static_variables = OrderedDict(
        [
            ("PRD", "https://api.kiwoom.com"),
            ("MOCK", "https://mockapi.kiwoom.com"),
            ("APP_KEY", ""),
            ("APP_SECRET", ""),
            ("APP_KEY_MOCK", ""),
            ("APP_SECRET_MOCK", ""),
        ]
    )
    return PostmanConfig(
        collection_name="Kiwoom OpenAPI",
        schema=POSTMAN_SCHEMA,
        static_variables=static_variables,
        environments=(
            PostmanEnvironmentConfig(
                name="production",
                folder_name="운영",
                base_variable="PRD",
                app_key_variable="APP_KEY",
                app_secret_variable="APP_SECRET",
                access_token_variable="ACCESS_TOKEN",
            ),
            PostmanEnvironmentConfig(
                name="mock",
                folder_name="모의투자",
                base_variable="MOCK",
                app_key_variable="APP_KEY_MOCK",
                app_secret_variable="APP_SECRET_MOCK",
                access_token_variable="ACCESS_TOKEN_MOCK",
            ),
        ),
        websocket_strategy="skip",
        websocket_reason="WebSocket specs are not generated into HTTP requests.",
        body_parameter_mode="query_params_and_body",
        body_variable_name_template="{api_id}_{field_path}",
        request_value_overrides_by_field=OrderedDict(
            [
                ("date", "20260507"),
                ("base_dt", "20260507"),
                ("qry_dt", "20260507"),
                ("ord_dt", "20260507"),
                ("rqst_dt", "20260507"),
                ("rsrv_dt", "20260507"),
                ("frcs_dt", "20260507"),
                ("deal_dt", "20260507"),
                ("cntr_dt", "20260507"),
                ("abnd_dt", "20260507"),
                ("ord_send_dt", "20260507"),
                ("strt_dt", "20260101"),
                ("start_dt", "20260101"),
                ("fr_dt", "20260101"),
                ("exmn_strt_dt", "20260101"),
                ("rsrv_strt_dt", "20260101"),
                ("fr_rsrv_dt", "20260101"),
                ("wi_from", "20260101"),
                ("end_dt", "20260507"),
                ("to_dt", "20260507"),
                ("exmn_end_dt", "20260507"),
                ("rsrv_end_dt", "20260507"),
                ("to_rsrv_dt", "20260507"),
                ("wi_to", "20260507"),
            ]
        ),
    )


def parse_workbook(xlsx_path: Path) -> list[ApiSpec]:
    workbook = pd.ExcelFile(xlsx_path)
    api_rows = _parse_api_list(workbook)
    api_payloads: dict[str, dict[str, Any]] = {}
    for sheet_name in workbook.sheet_names[1:]:
        if sheet_name == "오류코드":
            continue
        payload = _parse_api_sheet(workbook, sheet_name)
        api_id = str(payload.get("meta", {}).get("API ID", "")).strip()
        if api_id:
            api_payloads[api_id] = payload

    listed_ids = {row.api_id for row in api_rows}
    parsed_ids = set(api_payloads)
    missing = sorted(listed_ids - parsed_ids)
    extra = sorted(parsed_ids - listed_ids)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing detail sheets: {', '.join(missing)}")
        if extra:
            details.append(f"extra detail sheets: {', '.join(extra)}")
        raise ValueError("; ".join(details))

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


def load_postman_config(path: Path | None) -> PostmanConfig:
    if path is None:
        return default_postman_config()
    payload = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
    if not isinstance(payload, dict):
        raise ValueError("postman config must be a JSON object")

    base = default_postman_config()
    collection_name = _optional_string(payload, "collection_name", base.collection_name)
    schema = _optional_string(payload, "schema", base.schema)
    static_variables = _load_static_variables(payload.get("static_variables"), base.static_variables)
    environments = _load_environment_configs(payload.get("environments"), static_variables, base.environments)

    websocket = payload.get("websocket") or {}
    if not isinstance(websocket, dict):
        raise ValueError("websocket config must be a JSON object")
    websocket_strategy = str(websocket.get("strategy") or base.websocket_strategy)
    if websocket_strategy not in SUPPORTED_WEBSOCKET_STRATEGIES:
        allowed = ", ".join(sorted(SUPPORTED_WEBSOCKET_STRATEGIES))
        raise ValueError(f"unsupported websocket strategy: {websocket_strategy}; allowed: {allowed}")
    websocket_reason = str(websocket.get("reason") or base.websocket_reason)

    body_parameters = payload.get("body_parameters") or {}
    if not isinstance(body_parameters, dict):
        raise ValueError("body_parameters config must be a JSON object")
    body_parameter_mode = str(body_parameters.get("mode") or base.body_parameter_mode)
    if body_parameter_mode not in SUPPORTED_BODY_PARAMETER_MODES:
        allowed = ", ".join(sorted(SUPPORTED_BODY_PARAMETER_MODES))
        raise ValueError(f"unsupported body parameter mode: {body_parameter_mode}; allowed: {allowed}")
    body_variable_name_template = str(
        body_parameters.get("variable_name_template") or base.body_variable_name_template
    )
    if "{api_id}" not in body_variable_name_template or "{field_path}" not in body_variable_name_template:
        raise ValueError("body parameter variable_name_template must contain {api_id} and {field_path}")

    overrides = OrderedDict(base.request_value_overrides_by_field)
    overrides.update(_load_request_value_overrides(payload.get("request_value_overrides")))
    return PostmanConfig(
        collection_name=collection_name,
        schema=schema,
        static_variables=static_variables,
        environments=tuple(environments),
        websocket_strategy=websocket_strategy,
        websocket_reason=websocket_reason,
        body_parameter_mode=body_parameter_mode,
        body_variable_name_template=body_variable_name_template,
        request_value_overrides_by_field=overrides,
    )


def _load_static_variables(
    raw_variables: object,
    default_variables: OrderedDict[str, str],
) -> OrderedDict[str, str]:
    if raw_variables is None:
        return OrderedDict(default_variables)
    if not isinstance(raw_variables, dict):
        raise ValueError("static_variables must be a JSON object")
    actual_names = tuple(raw_variables)
    missing = [name for name in REQUIRED_STATIC_VARIABLES if name not in raw_variables]
    extra = [name for name in actual_names if name not in REQUIRED_STATIC_VARIABLES]
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing: {', '.join(missing)}")
        if extra:
            details.append(f"extra: {', '.join(extra)}")
        raise ValueError(f"static_variables must contain exactly the required variables ({'; '.join(details)})")
    ordered: OrderedDict[str, str] = OrderedDict()
    for name in REQUIRED_STATIC_VARIABLES:
        value = raw_variables[name]
        if not isinstance(value, str):
            raise ValueError(f"static variable value must be a string: {name}")
        ordered[name] = value
    return ordered


def _load_environment_configs(
    raw_environments: object,
    static_variables: OrderedDict[str, str],
    default_environments: tuple[PostmanEnvironmentConfig, ...],
) -> list[PostmanEnvironmentConfig]:
    if raw_environments is None:
        return list(default_environments)
    if not isinstance(raw_environments, dict) or not raw_environments:
        raise ValueError("environments must be a non-empty JSON object")
    environments: list[PostmanEnvironmentConfig] = []
    folder_names: set[str] = set()
    token_variables: set[str] = set()
    for name, raw_environment in raw_environments.items():
        if not isinstance(raw_environment, dict):
            raise ValueError(f"environment config must be a JSON object: {name}")
        environment = PostmanEnvironmentConfig(
            name=str(name),
            folder_name=_required_string(raw_environment, "folder_name"),
            base_variable=_required_string(raw_environment, "base_variable"),
            app_key_variable=_required_string(raw_environment, "app_key_variable"),
            app_secret_variable=_required_string(raw_environment, "app_secret_variable"),
            access_token_variable=_required_string(raw_environment, "access_token_variable"),
        )
        for variable_name in (environment.base_variable, environment.app_key_variable, environment.app_secret_variable):
            if variable_name not in static_variables:
                raise ValueError(f"environment {environment.name} references unknown static variable: {variable_name}")
        if environment.folder_name in folder_names:
            raise ValueError(f"duplicate environment folder name: {environment.folder_name}")
        if environment.access_token_variable in token_variables:
            raise ValueError(f"duplicate access token variable: {environment.access_token_variable}")
        folder_names.add(environment.folder_name)
        token_variables.add(environment.access_token_variable)
        environments.append(environment)
    return environments


def _load_request_value_overrides(raw_overrides: object) -> OrderedDict[str, str]:
    if raw_overrides is None:
        return OrderedDict()
    if not isinstance(raw_overrides, dict):
        raise ValueError("request_value_overrides must be a JSON object")
    by_field = raw_overrides.get("by_field") or {}
    if not isinstance(by_field, dict):
        raise ValueError("request_value_overrides.by_field must be a JSON object")
    overrides: OrderedDict[str, str] = OrderedDict()
    for field_name, value in by_field.items():
        if not isinstance(field_name, str) or not field_name.strip():
            raise ValueError("request_value_overrides.by_field keys must be non-empty strings")
        if not isinstance(value, str):
            raise ValueError(f"request_value_overrides.by_field value must be a string: {field_name}")
        overrides[field_name.strip()] = value
    return overrides


def build_postman_collection(
    api_specs: list[ApiSpec],
    config: PostmanConfig,
) -> tuple[dict[str, Any], PostmanGenerationReport]:
    generated_api_ids: OrderedDict[str, None] = OrderedDict()
    skipped_apis: OrderedDict[str, SkippedApi] = OrderedDict()
    counts_by_kind = {"oauth": 0, "rest": 0, "websocket": 0}
    counts_by_environment = {environment.name: 0 for environment in config.environments}
    request_paths: set[tuple[str, ...]] = set()
    top_items: list[dict[str, Any]] = []

    for environment in config.environments:
        category_items: OrderedDict[str, OrderedDict[str, list[dict[str, Any]]]] = OrderedDict()
        for api_spec in api_specs:
            kind = _api_kind(api_spec)
            if kind == "websocket" and config.websocket_strategy == "skip":
                skipped_apis.setdefault(
                    api_spec.api_id,
                    SkippedApi(
                        api_id=api_spec.api_id,
                        api_name=api_spec.api_name,
                        category=api_spec.top_category,
                        sub_category=api_spec.sub_category,
                        url=api_spec.url,
                        reason=config.websocket_reason,
                    ),
                )
                continue

            request_item = _build_request_item(api_spec, environment, config, kind)
            request_path = (
                environment.folder_name,
                api_spec.top_category,
                api_spec.sub_category,
                request_item["name"],
            )
            if request_path in request_paths:
                raise ValueError(f"duplicate Postman request path: {' > '.join(request_path)}")
            request_paths.add(request_path)
            category_items.setdefault(api_spec.top_category, OrderedDict()).setdefault(
                api_spec.sub_category,
                [],
            ).append(request_item)
            generated_api_ids.setdefault(api_spec.api_id, None)
            counts_by_kind[kind] += 1
            counts_by_environment[environment.name] += 1
        top_items.append(_environment_folder(environment, category_items))

    collection = {
        "info": {
            "name": config.collection_name,
            "schema": config.schema,
        },
        "item": top_items,
        "variable": [
            {"key": key, "value": value, "type": "string"}
            for key, value in config.static_variables.items()
        ],
    }
    report = PostmanGenerationReport(
        total_specs=len(api_specs),
        environments=[environment.name for environment in config.environments],
        generated_requests=sum(counts_by_environment.values()),
        generated_api_ids=list(generated_api_ids),
        skipped_apis=list(skipped_apis.values()),
        counts_by_kind=counts_by_kind,
        counts_by_environment=counts_by_environment,
        variables=list(config.static_variables),
        websocket_strategy=config.websocket_strategy,
    )
    return collection, report


def write_postman_collection(
    *,
    xlsx_path: Path,
    config_path: Path | None,
    output_path: Path,
    report_path: Path | None,
) -> tuple[Path, PostmanGenerationReport]:
    api_specs = parse_workbook(xlsx_path)
    config = load_postman_config(config_path)
    collection, report = build_postman_collection(api_specs, config)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_json_dump(collection), encoding="utf-8")
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(_json_dump(report.to_json()), encoding="utf-8")
    return output_path, report


def _build_request_item(
    api_spec: ApiSpec,
    environment: PostmanEnvironmentConfig,
    config: PostmanConfig,
    kind: str,
) -> dict[str, Any]:
    if kind == "rest" and config.body_parameter_mode in {"query_params", "query_params_and_body"}:
        body_variables: list[BodyVariable] = []
        query_parameters = _request_query_parameters(api_spec, environment, config)
        body: dict[str, Any] = {}
        if config.body_parameter_mode == "query_params_and_body" and _requires_raw_json_body(api_spec):
            body = {parameter["key"]: parameter.get("value", "") for parameter in query_parameters}
    else:
        body, body_variables = _request_body(api_spec, environment, config, kind)
        query_parameters = _query_parameters(config, kind, body_variables)

    raw_url = _raw_url(environment.base_variable, api_spec.url, query_parameters)
    request: dict[str, Any] = {
        "method": api_spec.method,
        "header": _request_headers(api_spec, environment, kind),
        "url": _postman_url(raw_url, environment.base_variable, api_spec.url, query_parameters),
        "description": _request_description(api_spec, kind),
    }
    if body or _requires_raw_json_body(api_spec):
        request["body"] = {
            "mode": "raw",
            "raw": _json_dump(body),
            "options": {"raw": {"language": "json"}},
        }

    events = _request_events(api_spec, environment, config, kind, body_variables)
    if kind == "rest" and config.body_parameter_mode == "query_params_and_body" and query_parameters:
        events.insert(0, _query_params_to_body_event())
    item: dict[str, Any] = {"name": f"{api_spec.api_name}({api_spec.api_id})", "request": request}
    if events:
        item["event"] = events
    return item


def _request_headers(api_spec: ApiSpec, environment: PostmanEnvironmentConfig, kind: str) -> list[dict[str, Any]]:
    headers: list[dict[str, Any]] = [
        {"key": "Content-Type", "value": api_spec.content_type, "type": "text"}
    ]
    if kind == "oauth":
        return headers
    headers.extend(
        [
            {"key": "api-id", "value": api_spec.api_id, "type": "text"},
            {
                "key": "authorization",
                "value": f"Bearer {{{{{environment.access_token_variable}}}}}",
                "type": "text",
            },
        ]
    )
    header_elements = {str(item.get("element", "")).strip().lower() for item in api_spec.request_headers}
    if "cont-yn" in header_elements:
        headers.append(
            {
                "key": "cont-yn",
                "value": "",
                "type": "text",
                "disabled": True,
                "description": "연속조회 시 응답 header의 cont-yn 값을 입력합니다.",
            }
        )
    if "next-key" in header_elements:
        headers.append(
            {
                "key": "next-key",
                "value": "",
                "type": "text",
                "disabled": True,
                "description": "연속조회 시 응답 header의 next-key 값을 입력합니다.",
            }
        )
    return headers


def _request_body(
    api_spec: ApiSpec,
    environment: PostmanEnvironmentConfig,
    config: PostmanConfig,
    kind: str,
) -> tuple[dict[str, Any], list[BodyVariable]]:
    body = _request_body_example(api_spec)
    sanitized = _replace_sensitive_values(body, environment)
    if kind != "rest" or config.body_parameter_mode == "inline_examples":
        return sanitized, []
    return _replace_body_values_with_postman_variables(api_spec, sanitized, config)


def _request_query_parameters(
    api_spec: ApiSpec,
    environment: PostmanEnvironmentConfig,
    config: PostmanConfig,
) -> list[dict[str, Any]]:
    body = _replace_sensitive_values(_request_body_example(api_spec), environment)
    descriptions = _request_body_descriptions(api_spec)
    parameters: list[dict[str, Any]] = []
    for item in api_spec.request_body:
        if item.get("is_section") or int(item.get("depth", 0) or 0) != 0:
            continue
        key = str(item.get("element", "")).strip()
        if not key:
            continue
        value = config.request_value_overrides_by_field.get(key, body.get(key, ""))
        parameter = {
            "key": key,
            "value": _query_value(value),
            "description": descriptions.get(key, ""),
        }
        if not _is_required_field(item):
            parameter["disabled"] = True
        parameters.append(parameter)
    return parameters


def _replace_body_values_with_postman_variables(
    api_spec: ApiSpec,
    value: dict[str, Any],
    config: PostmanConfig,
) -> tuple[dict[str, Any], list[BodyVariable]]:
    variables: list[BodyVariable] = []
    descriptions = _request_body_descriptions(api_spec)

    def replace(current: Any, path: tuple[str, ...]) -> Any:
        if isinstance(current, dict):
            return {key: replace(child, path + (str(key),)) for key, child in current.items()}
        if isinstance(current, list):
            return [replace(child, path + (str(index),)) for index, child in enumerate(current)]
        if not path or _is_existing_postman_variable(current):
            return current
        variable_name = _body_variable_name(api_spec, path, config)
        variables.append(
            BodyVariable(
                name=variable_name,
                field_path=".".join(path),
                default_value="" if current is None else current,
                description=descriptions.get(".".join(path), ""),
            )
        )
        return f"{{{{{variable_name}}}}}"

    replaced = replace(value, ())
    if not isinstance(replaced, dict):
        return value, []
    return replaced, variables


def _request_events(
    api_spec: ApiSpec,
    environment: PostmanEnvironmentConfig,
    config: PostmanConfig,
    kind: str,
    body_variables: list[BodyVariable],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    if body_variables:
        events.append(
            _body_variable_defaults_event(
                body_variables,
                mirror_query_to_body=kind == "rest" and config.body_parameter_mode == "query_params_to_body",
            )
        )
    if kind == "oauth" and api_spec.url.endswith("/token"):
        events.append(_token_save_event(environment))
    elif kind == "oauth" and api_spec.url.endswith("/revoke"):
        events.append(_revoke_token_cleanup_event(environment))
    return events


def _token_save_event(environment: PostmanEnvironmentConfig) -> dict[str, Any]:
    return _script_event(
        "test",
        [
            "const body = pm.response.json();",
            "if (body && body.token) {",
            f"  pm.collectionVariables.set('{environment.access_token_variable}', body.token);",
            "  try {",
            f"    pm.environment.set('{environment.access_token_variable}', body.token);",
            "  } catch (error) {",
            "    // No active environment; collection variable is still set.",
            "  }",
            "}",
        ],
    )


def _revoke_token_cleanup_event(environment: PostmanEnvironmentConfig) -> dict[str, Any]:
    return _script_event(
        "test",
        [
            "const body = pm.response.json();",
            "if (!body || body.return_code === 0 || body.return_code === '0') {",
            f"  pm.collectionVariables.unset('{environment.access_token_variable}');",
            "  try {",
            f"    pm.environment.unset('{environment.access_token_variable}');",
            "  } catch (error) {",
            "    // No active environment; collection variable cleanup is still applied.",
            "  }",
            "}",
        ],
    )


def _body_variable_defaults_event(body_variables: list[BodyVariable], *, mirror_query_to_body: bool) -> dict[str, Any]:
    defaults = {variable.name: variable.default_value for variable in body_variables}
    script = [
        f"const bodyVariableDefaults = {_json_dump(defaults)};",
        "for (const [key, value] of Object.entries(bodyVariableDefaults)) {",
        "  if (pm.variables.get(key) === undefined) {",
        "    pm.collectionVariables.set(key, value);",
        "  }",
        "}",
    ]
    if mirror_query_to_body:
        script.extend(_query_params_to_body_script())
    return _script_event("prerequest", script)


def _query_params_to_body_event() -> dict[str, Any]:
    return _script_event("prerequest", _query_params_to_body_script())


def _query_params_to_body_script() -> list[str]:
    return [
        "let jsonBodyFromParams = {};",
        "try {",
        "  const currentRawBody = pm.request.body && pm.request.body.raw ? pm.request.body.raw : '{}';",
        "  const parsedBody = JSON.parse(pm.variables.replaceIn(currentRawBody || '{}'));",
        "  if (parsedBody && typeof parsedBody === 'object' && !Array.isArray(parsedBody)) {",
        "    jsonBodyFromParams = parsedBody;",
        "  }",
        "} catch (error) {",
        "  jsonBodyFromParams = {};",
        "}",
        "for (const queryParam of pm.request.url.query.all()) {",
        "  if (!queryParam.key || queryParam.disabled === true) {",
        "    continue;",
        "  }",
        "  const rawValue = queryParam.value === undefined ? '' : String(queryParam.value);",
        "  jsonBodyFromParams[queryParam.key] = pm.variables.replaceIn(rawValue);",
        "}",
        "pm.request.body.update(JSON.stringify(jsonBodyFromParams, null, 2));",
    ]


def _script_event(listen: str, script: list[str]) -> dict[str, Any]:
    return {"listen": listen, "script": {"type": "text/javascript", "exec": script}}


def _query_parameters(
    config: PostmanConfig,
    kind: str,
    body_variables: list[BodyVariable],
) -> list[dict[str, Any]]:
    if kind != "rest" or config.body_parameter_mode != "query_params_to_body":
        return []
    return [
        {
            "key": variable.field_path,
            "value": f"{{{{{variable.name}}}}}",
            "description": variable.description,
            "disabled": True,
        }
        for variable in body_variables
    ]


def _request_body_example(api_spec: ApiSpec) -> dict[str, Any]:
    parsed = _jsonish(api_spec.request_example)
    if isinstance(parsed, dict):
        return {str(key): value for key, value in parsed.items()}
    body: dict[str, Any] = {}
    for item in api_spec.request_body:
        if item.get("is_section") or int(item.get("depth", 0) or 0) != 0:
            continue
        key = str(item.get("element", "")).strip()
        if key:
            body[key] = [] if _is_list_container(item) else f"TODO_{key}"
    return body


def _request_body_descriptions(api_spec: ApiSpec) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    for item in api_spec.request_body:
        if item.get("is_section"):
            continue
        element = str(item.get("element", "")).strip()
        if not element:
            continue
        label = str(item.get("한글명", "")).strip()
        description = str(item.get("description", "")).strip()
        descriptions[element] = " / ".join(part for part in (label, description) if part)
    return descriptions


def _replace_sensitive_values(value: Any, environment: PostmanEnvironmentConfig, key: str = "") -> Any:
    role = _sensitive_field_role(key)
    if role == "app_key":
        return f"{{{{{environment.app_key_variable}}}}}"
    if role == "app_secret":
        return f"{{{{{environment.app_secret_variable}}}}}"
    if role == "access_token":
        return f"{{{{{environment.access_token_variable}}}}}"
    if role == "authorization":
        return f"Bearer {{{{{environment.access_token_variable}}}}}"
    if isinstance(value, dict):
        return {child_key: _replace_sensitive_values(child, environment, str(child_key)) for child_key, child in value.items()}
    if isinstance(value, list):
        return [_replace_sensitive_values(child, environment, key) for child in value]
    return value


def _sensitive_field_role(key: str) -> str | None:
    normalized = key.lower().replace("-", "").replace("_", "")
    if normalized == "appkey":
        return "app_key"
    if normalized in {"secretkey", "appsecret"}:
        return "app_secret"
    if normalized == "token":
        return "access_token"
    if normalized == "authorization":
        return "authorization"
    return None


def _request_description(api_spec: ApiSpec, kind: str) -> str:
    lines = [
        f"## {api_spec.api_name}({api_spec.api_id})",
        "",
        f"- 종류: {kind}",
        f"- 메뉴 위치: {api_spec.menu_path or '-'}",
        f"- Method: {api_spec.method}",
        f"- URL: {api_spec.url}",
        "",
        "### 요청 Header",
        _field_table(api_spec.request_headers),
        "",
        "### 요청 Body",
        _field_table(api_spec.request_body),
        "",
        "### 응답 Body",
        _field_table(api_spec.response_body),
    ]
    header_elements = {str(item.get("element", "")).strip().lower() for item in api_spec.request_headers}
    if header_elements & {"cont-yn", "next-key"}:
        lines.extend(
            [
                "",
                "### 연속조회",
                "응답 header의 `cont-yn`이 `Y`이면 다음 요청의 disabled header 값을 채워서 이어서 조회합니다.",
            ]
        )
    return "\n".join(lines)


def _field_table(items: list[dict[str, Any]]) -> str:
    rows = [item for item in items if not item.get("is_section") and str(item.get("element", "")).strip()]
    if not rows:
        return "- 없음"
    lines = ["| element | 한글명 | required | type | length | description |", "| --- | --- | --- | --- | --- | --- |"]
    for item in rows:
        cells = [
            _markdown_cell(str(item.get(key, "")).strip())
            for key in ("element", "한글명", "required", "type", "length", "description")
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _environment_folder(
    environment: PostmanEnvironmentConfig,
    category_items: OrderedDict[str, OrderedDict[str, list[dict[str, Any]]]],
) -> dict[str, Any]:
    return {
        "name": environment.folder_name,
        "item": [
            {
                "name": category,
                "item": [
                    {"name": sub_category, "item": requests}
                    for sub_category, requests in sub_categories.items()
                ],
            }
            for category, sub_categories in category_items.items()
        ],
    }


def _api_kind(api_spec: ApiSpec) -> str:
    if api_spec.top_category == "OAuth 인증" or api_spec.url.startswith("/oauth2"):
        return "oauth"
    if "/websocket" in api_spec.url:
        return "websocket"
    return "rest"


def _body_variable_name(api_spec: ApiSpec, path: tuple[str, ...], config: PostmanConfig) -> str:
    field_path = "_".join(path)
    raw_name = config.body_variable_name_template.format(api_id=api_spec.api_id, field_path=field_path)
    normalized = re.sub(r"[^0-9A-Za-z_]+", "_", raw_name).strip("_").upper()
    return normalized or f"{api_spec.api_id.upper()}_PARAM"


def _raw_url(base_variable: str, path: str, query_parameters: list[dict[str, Any]]) -> str:
    base = f"{{{{{base_variable}}}}}{path}"
    enabled_parameters = [parameter for parameter in query_parameters if not parameter.get("disabled")]
    if not enabled_parameters:
        return base
    query = "&".join(
        f"{_raw_query_component(parameter['key'])}={_raw_query_component(parameter.get('value', ''))}"
        for parameter in enabled_parameters
    )
    return f"{base}?{query}"


def _postman_url(
    raw_url: str,
    base_variable: str,
    path: str,
    query_parameters: list[dict[str, Any]],
) -> dict[str, Any]:
    url = {
        "raw": raw_url,
        "host": [f"{{{{{base_variable}}}}}"],
        "path": [part for part in path.strip("/").split("/") if part],
    }
    if query_parameters:
        url["query"] = query_parameters
    return url


def _query_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def _raw_query_component(value: Any) -> str:
    return quote(_query_value(value), safe="{}")


def _jsonish(raw: str) -> object | None:
    text = raw.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _is_required_field(item: dict[str, Any]) -> bool:
    return str(item.get("required", "")).strip().upper() == "Y"


def _requires_raw_json_body(api_spec: ApiSpec) -> bool:
    return api_spec.method.upper() not in {"GET", "HEAD"}


def _is_list_container(item: dict[str, Any]) -> bool:
    return str(item.get("type", "")).strip().upper() == "LIST" and int(item.get("depth", 0) or 0) == 0


def _is_existing_postman_variable(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("{{") and value.endswith("}}")


def _markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _optional_string(payload: dict[str, Any], key: str, default: str) -> str:
    value = payload.get(key)
    if value is None:
        return default
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Kiwoom Postman collection from a workbook.")
    parser.add_argument("xlsx", type=Path, help="Path to the Kiwoom REST API workbook")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="Optional Postman generator config JSON")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_PATH, help="Output Postman collection path")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="Output generation report path")
    parser.add_argument("--no-report", action="store_true", help="Do not write a generation report")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    start = time.perf_counter()
    args = _parse_args(argv)
    output_path, report = write_postman_collection(
        xlsx_path=args.xlsx,
        config_path=args.config,
        output_path=args.out,
        report_path=None if args.no_report else args.report,
    )
    elapsed = time.perf_counter() - start
    print(f"Wrote {output_path}")
    print(
        "Generated "
        f"{report.generated_requests} requests across {len(report.environments)} environments; "
        f"skipped {len(report.skipped_apis)} WebSocket specs in {elapsed:.2f}s."
    )
    if not args.no_report:
        print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
