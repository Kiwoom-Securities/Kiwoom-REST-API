# 수동 생성 필요: CNSRREQ 실시간은 같은 WebSocket 연결에서 CNSRLST 선행 호출 후 요청해야 안정적으로 응답합니다.
# generator marker: MANUAL_REQUIRED_API_IDS
# ---
# api_id: ka10173
# api_name: 조건검색 요청 실시간
# category: 국내주식
# sub_category: 조건검색
# template: websocket_realtime
# api_url: /api/dostk/websocket
# menu_path: 국내주식 > 조건검색 > 조건검색 요청 실시간(ka10173)
# ---

import asyncio
import logging
import os
from collections import defaultdict
from typing import Any

from kiwoom import get_ws_client

# WebSocket 클라이언트가 LOGIN 패킷과 PING 응답을 자동 처리합니다.
# 이 예제는 asyncio.Queue 기반 in-process Pub/Sub 구조를 보여줍니다.
# 조건검색 실시간은 같은 WebSocket 연결에서 CNSRLST를 먼저 호출한 뒤 CNSRREQ를 보내야 합니다.
# 예제는 실시간 등록 후 CNSRCLR로 해제하고 종료합니다.

API_ID = "ka10173"
API_URL = "/api/dostk/websocket"
LIST_TRNM = "CNSRLST"
CLEAR_TRNM = "CNSRCLR"


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
    if trnm == "CNSRLST":
        return "kiwoom.condition.list"
    if trnm == "CNSRREQ":
        return "kiwoom.condition.request"
    if trnm == "CNSRCLR":
        return "kiwoom.condition.clear"
    if trnm == "SYSTEM":
        return "kiwoom.system"
    if trnm:
        return f"kiwoom.system.{trnm.lower()}"
    return "kiwoom.raw"


async def _publish(pubsub: AsyncPubSub, message: Any) -> None:
    topic = resolve_topic(message)
    await pubsub.publish(topic, message)
    await pubsub.publish("kiwoom.all", message)


async def websocket_publisher(
    *,
    pubsub: AsyncPubSub,
    trnm: str = "CNSRREQ",
    seq: str | None = None,
    search_type: str = "1",
    stex_tp: str = "K",
    max_messages: int = 1,
    max_wait_seconds: float = 15.0,
) -> None:
    """조건검색 실시간 WebSocket 수신 메시지를 Pub/Sub topic으로 발행합니다."""
    if max_messages < 0:
        raise ValueError("max_messages must be greater than or equal to 0")
    if max_wait_seconds <= 0:
        raise ValueError("max_wait_seconds must be greater than 0")
    if not trnm:
        raise ValueError("trnm is required.")
    if not search_type:
        raise ValueError("search_type is required.")
    if not stex_tp:
        raise ValueError("stex_tp is required.")

    client = get_ws_client()
    selected_seq: str | None = None

    try:
        await client.connect(api_url=API_URL)

        list_response = await _send_and_receive(client, {"trnm": LIST_TRNM})
        await _publish(pubsub, list_response)
        selected_seq = _select_condition_seq(list_response.get("data"), preferred_seq=seq)

        request_body = {
            "trnm": trnm,
            "seq": selected_seq,
            "search_type": search_type,
            "stex_tp": stex_tp,
        }
        initial_response = await _send_and_receive(client, request_body)
        await _publish(pubsub, initial_response)

        initial_return_code = initial_response.get("return_code")
        if initial_return_code in (None, 0, "0") and max_messages > 0:
            await _publish_realtime_messages(
                client,
                pubsub=pubsub,
                max_messages=max_messages,
                max_wait_seconds=max_wait_seconds,
            )

        clear_response = await _try_clear_condition(client, selected_seq)
        await _publish(pubsub, clear_response)
    finally:
        await client.close()


async def _send_and_receive(client: Any, body: dict[str, Any]) -> dict[str, Any]:
    await client._send_packet(body)
    response = await asyncio.wait_for(client._receive_message(), timeout=client.timeout_seconds)
    if not isinstance(response, dict):
        raise RuntimeError(f"unexpected websocket response type: {type(response).__name__}")
    return response


async def _publish_realtime_messages(
    client: Any,
    *,
    pubsub: AsyncPubSub,
    max_messages: int,
    max_wait_seconds: float,
) -> None:
    published = 0
    loop = asyncio.get_running_loop()
    deadline = loop.time() + max_wait_seconds

    while published < max_messages:
        remaining = deadline - loop.time()
        if remaining <= 0:
            break
        try:
            message = await asyncio.wait_for(client._receive_message(), timeout=remaining)
        except TimeoutError:
            break
        if not isinstance(message, dict):
            continue
        await _publish(pubsub, message)

        trnm = str(message.get("trnm", "")).upper()
        if trnm == "REAL":
            published += 1
            continue
        return_code = message.get("return_code")
        if trnm == "SYSTEM" or return_code not in (None, 0, "0"):
            break


async def _try_clear_condition(client: Any, seq: str) -> dict[str, Any]:
    try:
        return await _send_and_receive(client, {"trnm": CLEAR_TRNM, "seq": seq})
    except TimeoutError as exc:
        return {
            "trnm": CLEAR_TRNM,
            "seq": seq,
            "return_code": "TIMEOUT",
            "return_msg": str(exc),
        }


def _select_condition_seq(raw_rows: object, *, preferred_seq: str | None) -> str:
    rows = _condition_rows(raw_rows)
    if not rows:
        raise RuntimeError("저장된 조건검색식이 없습니다. 영웅문4에서 조건검색식을 먼저 저장해 주세요.")

    if preferred_seq is not None:
        normalized = preferred_seq.strip()
        available = [row["seq"] for row in rows]
        if normalized not in available:
            raise ValueError(f"조건검색식 일련번호를 찾을 수 없습니다: {normalized}. available={available}")
        return normalized

    return rows[0]["seq"]


def _condition_rows(raw_rows: object) -> list[dict[str, str]]:
    if not isinstance(raw_rows, list):
        return []

    rows: list[dict[str, str]] = []
    for row in raw_rows:
        if isinstance(row, dict):
            seq = str(row.get("seq", "")).strip()
            name = str(row.get("name", "")).strip()
        elif isinstance(row, (list, tuple)) and len(row) >= 2:
            seq = str(row[0]).strip()
            name = str(row[1]).strip()
        else:
            continue
        if seq:
            rows.append({"seq": seq, "name": name})
    return rows


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
    seq: str | None = None,
    max_messages: int = 1,
    max_wait_seconds: float = 15.0,
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
            seq=seq,
            max_messages=max_messages,
            max_wait_seconds=max_wait_seconds,
        )
        await asyncio.sleep(0.1)
    finally:
        for task in subscriber_tasks:
            task.cancel()
        await asyncio.gather(*subscriber_tasks, return_exceptions=True)


async def request_domestic_realtime_condition_search_pubsub(
    trnm: str = "CNSRREQ",
    seq: str | None = None,
    search_type: str = "1",
    stex_tp: str = "K",
    max_messages: int = 1,
    max_wait_seconds: float = 15.0,
) -> None:
    """
    조건검색 요청 실시간[ka10173] WebSocket 메시지를 Pub/Sub로 분배합니다.

    같은 WebSocket 연결에서 CNSRLST를 먼저 호출한 뒤 CNSRREQ(search_type=1)를 보냅니다.
    """
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
            trnm=trnm,
            seq=seq,
            search_type=search_type,
            stex_tp=stex_tp,
            max_messages=max_messages,
            max_wait_seconds=max_wait_seconds,
        )
        await asyncio.sleep(0.1)
    finally:
        for task in subscriber_tasks:
            task.cancel()
        await asyncio.gather(*subscriber_tasks, return_exceptions=True)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    await request_domestic_realtime_condition_search_pubsub(
        seq=os.getenv("KIWOOM_CONDITION_SEQ") or None,
        max_messages=1,
        max_wait_seconds=15.0,
    )


if __name__ == "__main__":
    asyncio.run(main())
