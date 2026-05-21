"""Decoder for Kiwoom WebSocket REAL messages.

Translates numeric FID keys in ``values`` dicts to Korean field names
using the mapping tables in :mod:`kiwoom.core.fid`.

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

from typing import Any

from kiwoom.core.fid import FID_MAP


def decode_values(real_type: str, values: dict[str, str]) -> dict[str, str]:
    """Translate FID-keyed *values* dict to Korean field names.

    Unknown FID keys are passed through unchanged so no data is lost.

    Args:
        real_type: REAL type ID, e.g. ``"0B"``.
        values: Raw ``{"fid": "value"}`` dict from the server message.

    Returns:
        ``{"field_name": "value"}`` dict with human-readable keys.
    """
    fid_map = FID_MAP.get(real_type, {})
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
