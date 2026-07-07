"""Generic helpers for turning Kiwoom WebSocket messages into pub/sub events.

These utilities are intentionally API-agnostic: they only depend on the shape of
Kiwoom WebSocket frames (``trnm`` / ``data`` / ``values``), not on any specific
realtime type. Examples keep their own field label table (``COLUMNS``) inline and
pass it in, so a single example still shows which fields it produces while the
routing/normalization plumbing lives here.
"""

from __future__ import annotations

from typing import Any


def normalize_message_events(
    message: Any,
    columns: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Convert a received WebSocket message into a list of consumer events.

    A ``REAL`` frame is expanded into one event per ``data`` entry, with FID keys
    in ``values`` translated through *columns* (unknown keys pass through). Any
    other frame (REG/SYSTEM/CNSR*/...) is returned unchanged as a single event.

    Args:
        message: Parsed WebSocket message.
        columns: Optional ``{fid: label}`` map applied to ``values``.

    Returns:
        A list of event dicts ready to publish.
    """
    if not isinstance(message, dict):
        return [{"trnm": "RAW", "message": message}]

    trnm = str(message.get("trnm", "")).upper()
    if trnm != "REAL":
        return [{**message, "trnm": trnm or message.get("trnm", "")}]

    column_map = columns or {}
    events: list[dict[str, Any]] = []
    data = message.get("data", [])
    if not isinstance(data, list):
        return [{"trnm": "REAL", "message": message}]

    for entry in data:
        if not isinstance(entry, dict):
            continue
        raw_values = entry.get("values")
        raw_values = raw_values if isinstance(raw_values, dict) else {}
        values = {column_map.get(key, key): value for key, value in raw_values.items()}
        event: dict[str, Any] = {
            "trnm": "REAL",
            "item": entry.get("item", ""),
            "type": str(entry.get("type", "")),
        }
        if "name" in entry:
            event["name"] = entry.get("name", "")
        event.update(values)
        events.append(event)
    return events


def resolve_topic(event: dict[str, Any]) -> str:
    """Decide the representative topic for a normalized *event*."""
    if not isinstance(event, dict):
        return "kiwoom.raw"

    trnm = str(event.get("trnm", "")).upper()
    if trnm == "REAL":
        realtime_type = str(event.get("type", "")).strip()
        if realtime_type:
            return f"kiwoom.realtime.{realtime_type}"
        return "kiwoom.realtime"
    if trnm == "REG":
        return "kiwoom.system.reg"
    if trnm == "SYSTEM":
        return "kiwoom.system"
    if trnm:
        return f"kiwoom.system.{trnm.lower()}"
    return "kiwoom.raw"


def topic_fanout(topic: str) -> list[str]:
    """Expand a representative topic to the shared topics it also publishes to."""
    topics = [topic]
    if topic.startswith("kiwoom.realtime."):
        topics.append("kiwoom.realtime")
    if topic.startswith("kiwoom.system."):
        topics.append("kiwoom.system")
    topics.append("kiwoom.all")
    return list(dict.fromkeys(topics))


def is_terminal_event(event: dict[str, Any]) -> bool:
    """Whether *event* should stop the receive loop (SYSTEM or error return_code)."""
    trnm = str(event.get("trnm", "")).upper()
    return_code = event.get("return_code")
    return trnm == "SYSTEM" or return_code not in (None, 0, "0")
