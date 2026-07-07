import json
from importlib.resources import files
from pathlib import Path
from typing import Any


DEFAULT_SPEC_PATH = files("kiwoom").joinpath("_data", "kiwoom_api_spec.json")


def load_api_specs(spec_path: Path | None = None) -> dict[str, dict[str, Any]]:
    resolved_path = spec_path or DEFAULT_SPEC_PATH
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    return {
        str(api_payload.get("meta", {}).get("API ID", "")).strip(): api_payload
        for api_payload in payload.get("apis", {}).values()
        if str(api_payload.get("meta", {}).get("API ID", "")).strip()
    }


def load_search_entries(spec_path: Path | None = None) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []

    for api_payload in load_api_specs(spec_path).values():
        meta = api_payload.get("meta", {})
        request = api_payload.get("request", {})
        request_terms: list[str] = []

        for item in request.get("header", []):
            request_terms.extend(_collect_item_terms(item))

        for item in request.get("body", []):
            request_terms.extend(_collect_item_terms(item))

        response = api_payload.get("response", {})
        response_terms: list[str] = []

        for item in response.get("body", []):
            if str(item.get("element", "")).strip() in _COMMON_RESPONSE_FIELDS:
                continue
            response_terms.extend(_collect_item_terms(item))

        entries.append(
            {
                "api_id": str(meta.get("API ID", "")).strip(),
                "api_name": str(meta.get("API 명", "")).strip(),
                "menu_path": str(meta.get("메뉴 위치", "")).strip(),
                "url": str(meta.get("URL", "")).strip(),
                "method": str(meta.get("Method", "")).strip(),
                "request_terms": list(dict.fromkeys(term for term in request_terms if term)),
                "response_terms": list(dict.fromkeys(term for term in response_terms if term)),
            }
        )

    return entries


def get_api_spec(api_id: str, *, spec_path: Path | None = None) -> dict[str, Any]:
    normalized_api_id = api_id.strip()
    specs = load_api_specs(spec_path)
    try:
        return specs[normalized_api_id]
    except KeyError as exc:
        raise ValueError(f"알 수 없는 Kiwoom API ID입니다: {normalized_api_id}") from exc


def list_api_groups(*, spec_path: Path | None = None) -> list[dict[str, object]]:
    counts: dict[tuple[str, str], int] = {}
    for api_payload in load_api_specs(spec_path).values():
        major, subcategory = _split_menu_path(str(api_payload.get("meta", {}).get("메뉴 위치", "")))
        key = (major, subcategory)
        counts[key] = counts.get(key, 0) + 1
    return [
        {"major_category": major, "subcategory": subcategory, "count": count}
        for (major, subcategory), count in sorted(counts.items())
    ]


def list_api_summaries(
    *,
    group: str | None = None,
    spec_path: Path | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    normalized_group = group.strip().casefold() if group else None
    summaries: list[dict[str, object]] = []
    for api_payload in load_api_specs(spec_path).values():
        meta = api_payload.get("meta", {})
        menu_path = str(meta.get("메뉴 위치", "")).strip()
        if normalized_group and normalized_group not in menu_path.casefold():
            continue
        summaries.append(
            {
                "api_id": str(meta.get("API ID", "")).strip(),
                "api_name": str(meta.get("API 명", "")).strip(),
                "menu_path": menu_path,
                "method": str(meta.get("Method", "")).strip(),
                "url": str(meta.get("URL", "")).strip(),
            }
        )
    summaries.sort(key=lambda item: str(item["api_id"]))
    if limit is not None:
        return summaries[:limit]
    return summaries


def search_api_specs(query: str, *, spec_path: Path | None = None, limit: int = 10) -> list[dict[str, object]]:
    return search_entries(load_search_entries(spec_path), query=query, limit=limit)


def search_entries(entries: list[dict[str, object]], *, query: str, limit: int = 10) -> list[dict[str, object]]:
    if limit <= 0:
        raise ValueError("limit 값은 0보다 커야 합니다.")

    normalized_query = query.strip().casefold()
    if not normalized_query:
        return []

    query_tokens = [token for token in normalized_query.split() if token]
    scored: list[tuple[int, dict[str, object]]] = []

    for entry in entries:
        score = _score_entry(entry, normalized_query, query_tokens)
        if score <= 0:
            continue
        scored.append((score, entry))

    scored.sort(key=lambda item: (-item[0], str(item[1]["api_id"])))
    return [entry for _, entry in scored[:limit]]


def format_search_results(results: list[dict[str, object]]) -> str:
    if not results:
        return "검색 결과가 없습니다."

    lines: list[str] = []
    for entry in results:
        request_terms = ", ".join(str(term) for term in entry["request_terms"][:6])
        response_terms = ", ".join(str(term) for term in entry.get("response_terms", [])[:6])
        lines.extend(
            [
                f'{entry["api_id"]} | {entry["api_name"]}',
                f'  메뉴: {entry["menu_path"]}',
                f'  호출: {entry["method"]} {entry["url"]}',
                f"  요청 키워드: {request_terms or '-'}",
                f"  응답 키워드: {response_terms or '-'}",
            ]
        )
    return "\n".join(lines)


def format_api_groups(groups: list[dict[str, object]]) -> str:
    if not groups:
        return "API 그룹이 없습니다."
    return "\n".join(
        f'{group["major_category"]} > {group["subcategory"]}: {group["count"]}'
        for group in groups
    )


def format_api_summaries(summaries: list[dict[str, object]]) -> str:
    if not summaries:
        return "API 목록이 없습니다."
    return "\n".join(
        f'{entry["api_id"]} | {entry["api_name"]} | {entry["method"]} {entry["url"]} | {entry["menu_path"]}'
        for entry in summaries
    )


def format_api_spec(api_payload: dict[str, Any]) -> str:
    meta = api_payload.get("meta", {})
    request = api_payload.get("request", {})
    response = api_payload.get("response", {})
    lines = [
        f'{str(meta.get("API ID", "")).strip()} | {str(meta.get("API 명", "")).strip()}',
        f'  메뉴: {str(meta.get("메뉴 위치", "")).strip()}',
        f'  호출: {str(meta.get("Method", "")).strip()} {str(meta.get("URL", "")).strip()}',
        f"  요청 헤더 필수: {_format_fields(_required_items(request.get('header')))}",
        f"  요청 바디 필수: {_format_fields(_required_items(request.get('body')))}",
        f"  요청 바디 선택: {_format_fields(_optional_items(request.get('body')))}",
        f"  응답 바디: {_format_fields(response.get('body', []))}",
    ]
    return "\n".join(lines)


_COMMON_HEADER_FIELDS = frozenset({"api-id", "authorization", "cont-yn", "next-key"})
_COMMON_RESPONSE_FIELDS = frozenset({"return_code", "return_msg", "trnm", "data", "type", "name", "item", "values"})


def _split_menu_path(menu_path: str) -> tuple[str, str]:
    parts = [part.strip() for part in menu_path.split(">") if part.strip()]
    if not parts:
        return ("미분류", "미분류")
    if len(parts) == 1:
        return (parts[0], "미분류")
    return (parts[0], parts[1])


def _required_items(items: list[dict] | None) -> list[dict]:
    return [item for item in items or [] if item.get("required") == "Y"]


def _optional_items(items: list[dict] | None) -> list[dict]:
    return [item for item in items or [] if item.get("required") != "Y"]


def _format_fields(items: list[dict]) -> str:
    fields = []
    for item in items:
        element = str(item.get("element", "")).strip()
        if not element:
            continue
        korean_name = str(item.get("한글명", "")).strip()
        field_type = str(item.get("type", "")).strip()
        label = element
        if korean_name:
            label = f"{label}({korean_name})"
        if field_type:
            label = f"{label}:{field_type}"
        fields.append(label)
    return ", ".join(fields) if fields else "-"


def _collect_item_terms(item: dict) -> list[str]:
    element = str(item.get("element", "")).strip()
    if element in _COMMON_HEADER_FIELDS:
        return []
    terms = [element, str(item.get("한글명", "")).strip()]
    description = _normalize_description(str(item.get("description", "")).strip())
    if description and len(description) <= 30:
        terms.append(description)
    return terms


def _score_entry(entry: dict[str, object], normalized_query: str, query_tokens: list[str]) -> int:
    api_id = str(entry["api_id"])
    api_name = str(entry["api_name"])
    menu_path = str(entry["menu_path"])
    url = str(entry["url"])
    request_terms = [str(term) for term in entry["request_terms"]]
    response_terms = [str(term) for term in entry.get("response_terms", [])]

    score = 0
    if api_id.casefold() == normalized_query:
        score += 1000
    if normalized_query in api_id.casefold():
        score += 250
    if normalized_query in api_name.casefold():
        score += 180
    if normalized_query in menu_path.casefold():
        score += 120
    if normalized_query in url.casefold():
        score += 80

    for term in request_terms:
        if normalized_query in term.casefold():
            score += 40

    for term in response_terms:
        if normalized_query in term.casefold():
            score += 30

    searchable_text = " ".join([api_id, api_name, menu_path, url, *request_terms, *response_terms]).casefold()
    if query_tokens and all(token in searchable_text for token in query_tokens):
        score += 60

    return score


def _normalize_description(description: str) -> str:
    if not description:
        return ""
    return " ".join(part.strip() for part in description.splitlines() if part.strip())
