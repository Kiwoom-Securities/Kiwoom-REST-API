# ---
# api_id: 0A
# api_name: 주식기세
# category: 국내주식
# sub_category: 실시간시세
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 실시간시세 > 주식기세(0A)
# ---

import asyncio
import logging
from collections import defaultdict
from typing import Any

from kiwoom import get_ws_client

# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.
# 이 예제는 asyncio.Queue 기반 in-process Pub/Sub 구조를 보여줍니다.

API_ID = "0A"
API_URL = "/api/dostk/websocket"


class AsyncPubSub:
    """예제용 in-process Pub/Sub입니다.

    Redis/Kafka 같은 외부 인프라 없이 asyncio.Queue만 사용합니다.
    WebSocket 수신 데이터 1개를 여러 소비자에게 분기하는 구조를 보여주기 위한
    예제 전용 클래스입니다.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue[Any]]] = defaultdict(list)

    def subscribe(self, topic: str) -> asyncio.Queue[Any]:
        queue: asyncio.Queue[Any] = asyncio.Queue()
        self._subscribers[topic].append(queue)
        return queue

    async def publish(self, topic: str, message: Any) -> None:
        for queue in self._subscribers.get(topic, []):
            await queue.put(message)


def resolve_topic(message: Any) -> str:
    """수신 메시지를 발행할 topic을 결정합니다."""
    if not isinstance(message, dict):
        return "kiwoom.raw"

    trnm = str(message.get("trnm", "")).upper()
    if trnm == "REAL":
        data = message.get("data", [])
        if isinstance(data, list) and data and isinstance(data[0], dict):
            realtime_type = str(data[0].get("type", "")).strip()
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


async def websocket_publisher(
    *,
    pubsub: AsyncPubSub,
    body: dict[str, Any],
    max_messages: int | None = None,
) -> None:
    """키움 WebSocket 수신 메시지를 Pub/Sub topic으로 발행합니다."""
    if max_messages is not None and max_messages < 1:
        raise ValueError("max_messages must be greater than 0")

    client = get_ws_client()
    published = 0

    try:
        await client.subscribe(api_url=API_URL, body=body)

        async for message in client.iter_messages():
            topic = resolve_topic(message)
            await pubsub.publish(topic, message)
            await pubsub.publish("kiwoom.all", message)

            published += 1
            if max_messages is not None and published >= max_messages:
                break

            if isinstance(message, dict):
                trnm = str(message.get("trnm", "")).upper()
                return_code = message.get("return_code")
                if trnm == "SYSTEM" or return_code not in (None, 0, "0"):
                    break
    finally:
        await client.close()


async def strategy_subscriber(queue: asyncio.Queue[Any]) -> None:
    """전략 로직 소비자 예시입니다."""
    while True:
        message = await queue.get()
        print("[strategy]", message, flush=True)


async def logger_subscriber(queue: asyncio.Queue[Any]) -> None:
    """로그/저장 로직 소비자 예시입니다."""
    while True:
        message = await queue.get()
        print("[logger]", message, flush=True)


async def run_pubsub(
    *,
    body: dict[str, Any],
    max_messages: int | None = None,
) -> None:
    """publisher 1개와 subscriber 2개를 실행합니다."""
    pubsub = AsyncPubSub()
    strategy_queue = pubsub.subscribe("kiwoom.all")
    logger_queue = pubsub.subscribe("kiwoom.all")

    subscriber_tasks = [
        asyncio.create_task(strategy_subscriber(strategy_queue)),
        asyncio.create_task(logger_subscriber(logger_queue)),
    ]
    try:
        await websocket_publisher(
            pubsub=pubsub,
            body=body,
            max_messages=max_messages,
        )
    finally:
        for task in subscriber_tasks:
            task.cancel()
        await asyncio.gather(*subscriber_tasks, return_exceptions=True)


def build_realtime_reg_packet(
    *,
    items: list[str],
    types: list[str],
    group_no: str = "1",
    refresh: str = "1",
) -> dict[str, Any]:
    """키움 실시간 항목 등록(REG) 패킷을 생성합니다."""
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

async def subscribe_domestic_stock_surge_pubsub(
    items: list[str],
    types: list[str] | None = None,
    group_no: str = "1",
    refresh: str = "1",
    max_messages: int | None = None,
) -> None:
    """
    주식기세[0A] 실시간 데이터를 Pub/Sub로 분배합니다.

    공통 WebSocket 클라이언트가 유효한 캐시 토큰을 사용하거나 필요 시 자동으로 발급합니다.
    """
    if not items:
        raise ValueError("items is required.")

    body = build_realtime_reg_packet(
        items=items,
        types=types or [API_ID],
        group_no=group_no,
        refresh=refresh,
    )
    await run_pubsub(body=body, max_messages=max_messages)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await subscribe_domestic_stock_surge_pubsub(
        items=['005930'],
        types=['0A'],
        max_messages=None,
    )


if __name__ == "__main__":
    asyncio.run(main())
