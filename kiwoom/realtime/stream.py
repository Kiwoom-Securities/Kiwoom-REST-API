"""In-process pub/sub and collection helpers for Kiwoom realtime streams.

These utilities are API-agnostic. Callers provide the realtime client, the
control packet(s) to send, and an optional ``{fid: label}`` column map. Message
decoding and topic routing reuse :mod:`kiwoom.realtime.events`, so examples only
need to declare their column map and the consumers/topics they care about.

Two delivery models are provided:

* :func:`collect_realtime` - await a bounded number of events and return them as
  DataFrames or JSON (one-shot collection).
* :func:`run_pubsub` - fan a single live stream out to multiple topic consumers
  via an in-process :class:`AsyncPubSub`.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

import pandas as pd

from kiwoom.realtime.events import (
    is_terminal_event,
    normalize_message_events,
    resolve_topic,
    topic_fanout,
)

Consumer = Callable[["asyncio.Queue[Any]"], Awaitable[None]]


class AsyncPubSub:
    """Minimal in-process pub/sub built on ``asyncio.Queue``.

    No external broker (Redis/Kafka) is involved: one received message can be
    fanned out to several consumers, each reading from its own queue.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[Any]]] = defaultdict(list)

    def subscribe(self, topic: str) -> "asyncio.Queue[Any]":
        """Register interest in *topic* and return the queue to read from."""
        queue: asyncio.Queue[Any] = asyncio.Queue()
        self._subscribers[topic].append(queue)
        return queue

    async def publish(self, topic: str, message: Any) -> None:
        """Deliver *message* to every queue subscribed to *topic*."""
        for queue in self._subscribers.get(topic, []):
            await queue.put(message)


def event_to_dataframe(event: dict[str, Any]) -> pd.DataFrame:
    """Convert one decoded event into a single-row DataFrame."""
    return pd.DataFrame([event])


async def _publish_stream(
    client: Any,
    *,
    api_url: str,
    bodies: dict[str, Any] | list[dict[str, Any]],
    columns: dict[str, str],
    pubsub: AsyncPubSub,
    max_messages: int | None,
    close_client: bool,
) -> None:
    body_list = [bodies] if isinstance(bodies, dict) else list(bodies)
    published_realtime = 0
    try:
        if not client.is_connected:
            await client.connect(api_url=api_url)
        for body in body_list:
            await client.send(body)

        async for message in client.iter_messages():
            for event in normalize_message_events(message, columns):
                for topic in topic_fanout(resolve_topic(event)):
                    await pubsub.publish(topic, event)

                if str(event.get("trnm", "")).upper() == "REAL":
                    published_realtime += 1
                    if max_messages is not None and published_realtime >= max_messages:
                        return

                if is_terminal_event(event):
                    return
    finally:
        if close_client:
            await client.close()


async def run_pubsub(
    client: Any,
    *,
    api_url: str,
    bodies: dict[str, Any] | list[dict[str, Any]],
    consumers: Mapping[str, Consumer],
    columns: Mapping[str, str] | None = None,
    pubsub: AsyncPubSub | None = None,
    max_messages: int | None = None,
    close_client: bool = True,
) -> None:
    """Fan a live Kiwoom realtime stream out to topic *consumers*.

    Each ``{topic: consumer}`` pair gets its own queue; the publisher decodes
    every received message, routes it to the matching topics (plus the shared
    ``kiwoom.realtime`` / ``kiwoom.all`` fan-out), and the consumers run as
    background tasks until the stream ends.

    Args:
        client: A connected-or-connectable realtime WebSocket client.
        api_url: Realtime WebSocket API path.
        bodies: One ``REG`` packet, or a list to combine several on one
            connection.
        consumers: ``{topic: async consumer(queue)}`` mapping.
        columns: Optional ``{fid: label}`` map applied to realtime values.
        pubsub: Optional shared bus (inject to combine with other streams).
        max_messages: Stop after this many ``REAL`` events (None = unlimited).
        close_client: Close *client* when the stream ends.
    """
    bus = pubsub or AsyncPubSub()
    tasks = [
        asyncio.create_task(consumer(bus.subscribe(topic)))
        for topic, consumer in consumers.items()
    ]
    try:
        await _publish_stream(
            client,
            api_url=api_url,
            bodies=bodies,
            columns=dict(columns or {}),
            pubsub=bus,
            max_messages=max_messages,
            close_client=close_client,
        )
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def _format_collected(
    rows: list[dict[str, Any]],
    system_rows: list[dict[str, Any]],
    output: str,
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    if output == "json":
        if rows and system_rows:
            return {"system": system_rows, "data": rows}
        return rows or system_rows
    result: dict[str, pd.DataFrame] = {"data": pd.DataFrame(rows)}
    if system_rows:
        result["system"] = pd.DataFrame(system_rows)
    return result


async def collect_realtime(
    client: Any,
    *,
    api_url: str,
    body: dict[str, Any],
    columns: Mapping[str, str] | None = None,
    output: str = "dataframe",
    max_messages: int = 10,
) -> pd.DataFrame | dict[str, Any] | list[dict[str, Any]]:
    """Collect up to *max_messages* realtime events, then return them.

    REAL events are decoded through *columns* and collected as data rows; other
    frames (REG/SYSTEM/...) are printed and collected separately. Collection
    stops at *max_messages* data rows or on a terminal frame.

    Args:
        client: A connectable realtime WebSocket client.
        api_url: Realtime WebSocket API path.
        body: The ``REG`` packet to send.
        columns: Optional ``{fid: label}`` map applied to realtime values.
        output: ``"dataframe"`` or ``"json"``.
        max_messages: Maximum number of REAL events to collect.

    Returns:
        ``{"data": ..., "system": ...}`` (DataFrames) or the JSON equivalent.
    """
    if max_messages < 1:
        raise ValueError("max_messages must be greater than 0")
    column_map = dict(columns or {})
    rows: list[dict[str, Any]] = []
    system_rows: list[dict[str, Any]] = []
    try:
        await client.subscribe(api_url=api_url, body=body)

        async for message in client.iter_messages():
            for event in normalize_message_events(message, column_map):
                if str(event.get("trnm", "")).upper() == "REAL":
                    rows.append(
                        {key: value for key, value in event.items() if key != "trnm"}
                    )
                    if len(rows) >= max_messages:
                        return _format_collected(rows, system_rows, output)
                    continue

                system_rows.append(event)
                print(f"[{event.get('trnm') or 'MESSAGE'}]", event, flush=True)
                if is_terminal_event(event):
                    return _format_collected(rows, system_rows, output)
    finally:
        await client.close()

    return _format_collected(rows, system_rows, output)
