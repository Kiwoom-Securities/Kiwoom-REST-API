"""Schema registry for Kiwoom realtime WebSocket values.

The packaged Kiwoom API spec is the source of truth. This module exposes the
spec rows under ``REAL``/``data[*].values`` as a registry that decoders can read
without embedding FID-specific branching in decode logic.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any


RealtimeField = dict[str, str]
RealtimeSchema = dict[str, Any]


@lru_cache(maxsize=1)
def realtime_schemas() -> dict[str, RealtimeSchema]:
    """Return built-in realtime schemas keyed by realtime type/API ID."""
    from kiwoom.specs import load_api_specs

    schemas: dict[str, RealtimeSchema] = {}
    for api_id, payload in load_api_specs().items():
        fields = _extract_value_fields(payload)
        if not fields:
            continue
        meta = payload.get("meta", {})
        api_name = str(meta.get("API 명", "")).strip()
        schemas[api_id] = {
            "event": api_id,
            "name": api_name,
            "fields": fields,
        }
    return schemas


def get_realtime_schema(real_type: str) -> RealtimeSchema | None:
    """Return a realtime schema for *real_type*, or ``None`` if unknown."""
    return realtime_schemas().get(str(real_type).strip())


def _extract_value_fields(payload: dict[str, Any]) -> dict[str, RealtimeField]:
    fields: dict[str, RealtimeField] = {}
    seen_names: set[str] = set()
    in_values = False
    for row in payload.get("response", {}).get("body", []):
        element = str(row.get("element", "")).strip()
        depth = row.get("depth")
        if element == "values" and depth == 1:
            in_values = True
            continue
        if not in_values:
            continue
        if depth == 2 and element:
            korean_name = str(row.get("한글명", "")).strip()
            if korean_name:
                field_name = (
                    korean_name
                    if korean_name not in seen_names
                    else f"{korean_name}_{element}"
                )
                seen_names.add(field_name)
                fields[element] = {
                    # The current official spec provides Korean display names,
                    # not English field identifiers. Keep the explicit spec name
                    # as the stable v1 named key instead of guessing. When the
                    # spec repeats a display name in one schema, suffix the FID
                    # so named decoding cannot overwrite a previous value.
                    "name": field_name,
                    "ko": korean_name,
                    "type": str(row.get("type", "")).strip() or "String",
                }
        elif isinstance(depth, int) and depth <= 1:
            in_values = False
    return fields
