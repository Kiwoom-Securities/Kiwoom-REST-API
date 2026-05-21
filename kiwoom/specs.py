import json
from pathlib import Path


DEFAULT_SPEC_PATH = Path(__file__).resolve().parents[1] / "kiwoom_api_spec.json"


def load_search_entries(spec_path: Path | None = None) -> list[dict[str, object]]:
    resolved_path = spec_path or DEFAULT_SPEC_PATH
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    entries: list[dict[str, object]] = []

    for api_payload in payload.get("apis", {}).values():
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


def search_api_specs(query: str, *, spec_path: Path | None = None, limit: int = 10) -> list[dict[str, object]]:
    return search_entries(load_search_entries(spec_path), query=query, limit=limit)


def search_entries(entries: list[dict[str, object]], *, query: str, limit: int = 10) -> list[dict[str, object]]:
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

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


def load_response_column_map(api_id: str, *, spec_path: Path | None = None) -> dict[str, str]:
    """응답 필드의 영문 element → 한글명 매핑 딕셔너리를 반환합니다."""
    resolved_path = spec_path or DEFAULT_SPEC_PATH
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    for api_payload in payload.get("apis", {}).values():
        if str(api_payload.get("meta", {}).get("API ID", "")).strip() == api_id:
            return {
                str(item["element"]).strip(): str(item["한글명"]).strip()
                for item in api_payload.get("response", {}).get("body", [])
                if item.get("element") and item.get("한글명")
            }
    return {}


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


_COMMON_HEADER_FIELDS = frozenset({"api-id", "authorization", "cont-yn", "next-key"})
_COMMON_RESPONSE_FIELDS = frozenset({"return_code", "return_msg", "trnm", "data", "type", "name", "item", "values"})


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
