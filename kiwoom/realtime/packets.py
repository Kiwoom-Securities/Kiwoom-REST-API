"""Builders for Kiwoom realtime WebSocket control packets.

These helpers only encode the Kiwoom realtime request contract (``REG`` to
register, ``REMOVE`` to unregister). They are API-agnostic: callers pass the
items and realtime types they want, so a single builder serves every realtime
example without per-API logic.
"""

from __future__ import annotations

from typing import Any


def build_reg_packet(
    items: list[str],
    types: list[str],
    *,
    group_no: str = "1",
    refresh: str = "1",
) -> dict[str, Any]:
    """Build a Kiwoom realtime registration (``REG``) packet.

    Args:
        items: Symbols or elements to register (e.g. ``["005930"]``).
        types: Realtime type codes to register (e.g. ``["0B"]``).
        group_no: Group number.
        refresh: ``"1"`` keeps existing registrations, ``"0"`` replaces them.

    Returns:
        A packet dict ready to send over the realtime WebSocket.
    """
    if not types:
        raise ValueError("types is required.")
    return {
        "trnm": "REG",
        "grp_no": group_no,
        "refresh": refresh,
        "data": [
            {
                "item": items,
                "type": types,
            }
        ],
    }


def build_remove_packet(
    items: list[str],
    types: list[str],
    *,
    group_no: str = "1",
) -> dict[str, Any]:
    """Build a Kiwoom realtime unregistration (``REMOVE``) packet."""
    if not types:
        raise ValueError("types is required.")
    return {
        "trnm": "REMOVE",
        "grp_no": group_no,
        "data": [
            {
                "item": items,
                "type": types,
            }
        ],
    }
