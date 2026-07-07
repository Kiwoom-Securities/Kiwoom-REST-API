"""Decoder for Kiwoom WebSocket REAL messages.

Translates numeric FID keys in ``values`` dicts to Korean field names. The
``{fid: 한글명}`` mapping is derived from the Kiwoom WebSocket spec
(``kiwoom_api_spec.json``): each realtime type's REAL ``values`` fields are the
depth-2 rows nested under ``values`` in the response body. The spec is the single
source of truth and names are returned verbatim; unknown FID keys pass through
unchanged so no data is lost.

Typical REAL message shape::

    {
        "trnm": "REAL",
        "data": [
            {
                "type": "0B",
                "name": "주식체결",
                "item": "005930",
                "values": {"10": "-82000", "15": "+12345", ...}
            }
        ]
    }
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from kiwoom.realtime.schemas import get_realtime_schema


@lru_cache(maxsize=None)
def _fid_map(real_type: str) -> dict[str, str]:
    """Extract ``{fid: 한글명}`` from the spec's REAL ``values`` rows (depth 2)."""
    from kiwoom.specs import get_api_spec

    try:
        payload = get_api_spec(real_type)
    except ValueError:
        return {}

    fid_map: dict[str, str] = {}
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
            fid_map[element] = str(row.get("한글명", "")).strip()
        elif isinstance(depth, int) and depth <= 1:
            in_values = False
    return fid_map


def fid_display_map(real_type: str) -> dict[str, str]:
    """Return the spec-defined FID -> display name mapping for a realtime type."""
    return dict(_fid_map(real_type))


def decode_values(real_type: str, values: dict[str, str]) -> dict[str, str]:
    """Translate FID-keyed *values* dict to Korean field names.

    Unknown FID keys are passed through unchanged so no data is lost.

    Args:
        real_type: REAL type ID, e.g. ``"0B"``.
        values: Raw ``{"fid": "value"}`` dict from the server message.

    Returns:
        ``{"field_name": "value"}`` dict with human-readable keys.
    """
    fid_map = fid_display_map(real_type)
    return {fid_map.get(k, k): v for k, v in values.items()}


def decode_realtime_message(message: dict[str, Any]) -> dict[str, Any]:
    """Decode FID keys in all ``data[*].values`` entries of a REAL message.

    Non-REAL messages (e.g. ACK, LOGIN) are returned unchanged.

    Args:
        message: Parsed WebSocket message dict.

    Returns:
        Copy of *message* with ``values`` dicts translated to field names.
    """
    if not isinstance(message, dict):
        return message

    if str(message.get("trnm", "")).upper() != "REAL":
        return message

    data = message.get("data")
    if not isinstance(data, list):
        return message

    decoded_data = []
    for entry in data:
        if not isinstance(entry, dict):
            decoded_data.append(entry)
            continue

        real_type = entry.get("type", "")
        values = entry.get("values")

        if isinstance(values, dict) and real_type:
            decoded_data.append({**entry, "values": decode_values(real_type, values)})
        else:
            decoded_data.append(entry)

    return {**message, "data": decoded_data}


def decode_realtime_message_named(message: dict[str, Any]) -> dict[str, Any]:
    """Convert REAL message entries into named data objects.

    Only ``trnm == "REAL"`` messages are decoded. Control frames such as ``REG``
    and ``SYSTEM`` are returned unchanged. Values keep their original string
    representation; this function changes keys/shape only and preserves unknown
    FIDs under ``unknown``.
    """
    if not isinstance(message, dict):
        return message

    if str(message.get("trnm", "")).upper() != "REAL":
        return message

    data = message.get("data")
    if not isinstance(data, list):
        return message

    named_data = []
    for entry in data:
        if not isinstance(entry, dict):
            named_data.append(entry)
            continue

        real_type = str(entry.get("type", "")).strip()
        values = entry.get("values")
        schema = get_realtime_schema(real_type)
        if not isinstance(values, dict) or schema is None:
            named_data.append(entry)
            continue

        fields = schema.get("fields", {})
        named_values: dict[str, Any] = {}
        unknown: dict[str, Any] = {}
        for fid, value in values.items():
            field = fields.get(str(fid))
            if field is None:
                unknown[str(fid)] = value
                continue
            named_values[str(field["name"])] = value

        named_entry: dict[str, Any] = {
            "event": schema.get("event", real_type),
            "type": real_type,
            "name": entry.get("name") or schema.get("name", ""),
            "code": entry.get("item", ""),
            "data": named_values,
        }
        if unknown:
            named_entry["unknown"] = unknown
        named_data.append(named_entry)

    return {**message, "data": named_data}
