import asyncio
import json
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

from kiwoom.core.auth import KiwoomAuth, get_ws_base_url
from kiwoom.core.errors import auth_retry_code, normalize_return_code

logger = logging.getLogger(__name__)

try:
    from websockets.asyncio.client import connect as _ws_connect
except ImportError:  # pragma: no cover - compatibility fallback
    try:
        from websockets.client import connect as _ws_connect
    except ImportError:  # pragma: no cover - dependency installed later in the flow
        _ws_connect = None


type ConnectFactory = Callable[..., Any]


class WebSocketLoginError(RuntimeError):
    def __init__(self, return_code: int, return_msg: str) -> None:
        super().__init__(f"websocket login failed: {return_msg}")
        self.return_code = return_code
        self.return_msg = return_msg


class KiwoomWebSocketClient:
    def __init__(
        self,
        auth: KiwoomAuth,
        *,
        timeout_seconds: int = 30,
        connect_factory: ConnectFactory | None = None,
    ) -> None:
        self.auth = auth
        self.timeout_seconds = timeout_seconds
        self._connect_factory = connect_factory or _default_connect
        self._websocket: Any | None = None

    @property
    def is_connected(self) -> bool:
        """Whether a live WebSocket connection is currently open."""
        return self._websocket is not None

    async def connect(self, *, api_url: str, retry_on_auth_failure: bool = True) -> None:
        if self._websocket is not None:
            await self.close()

        path = _parse_api_url(api_url)
        uri = f"{get_ws_base_url(self.auth.mode)}{path}"
        try:
            await self._connect_and_login(uri)
        except WebSocketLoginError as exc:
            if not retry_on_auth_failure or not _is_auth_retry_login_error(exc):
                raise RuntimeError(f"websocket login failed: {exc.return_msg}") from exc
            logger.info("websocket auth failed; refreshing token and retrying login")
            await self.close()
            self.auth.recover_from_auth_failure()
            try:
                await self._connect_and_login(uri)
            except WebSocketLoginError as retry_exc:
                raise RuntimeError(f"websocket login failed: {retry_exc.return_msg}") from retry_exc

    async def request_once(
        self,
        *,
        api_url: str,
        body: dict[str, Any],
    ) -> Any:
        await self.connect(api_url=api_url)
        try:
            logger.info("websocket sent request")
            await self.send(body)
            try:
                message = await asyncio.wait_for(self._receive_message(), timeout=self.timeout_seconds)
            except TimeoutError as exc:
                raise TimeoutError(f"websocket response timed out after {self.timeout_seconds}s") from exc
            logger.info("websocket received response")
            return message
        finally:
            await self.close()

    async def subscribe(
        self,
        *,
        api_url: str,
        body: dict[str, Any],
    ) -> None:
        await self.connect(api_url=api_url)
        logger.info("websocket sent subscribe request")
        await self.send(body)

    async def send(self, payload: Any) -> None:
        """Send a packet over the current WebSocket connection."""
        await self._send_packet(payload)

    async def recv(self) -> Any:
        """Receive the next non-ping, non-login message over the current connection."""
        return await self._receive_message()

    async def iter_messages(self) -> AsyncIterator[Any]:
        if self._websocket is None:
            raise RuntimeError("websocket is not connected")

        while True:
            try:
                yield await self._receive_message()
            except Exception as exc:  # pragma: no cover - exercised with real websocket client
                if _is_connection_closed_exception(exc):
                    logger.info("websocket connection closed by remote")
                    break
                raise

    async def close(self) -> None:
        if self._websocket is None:
            return

        await self._websocket.close()
        self._websocket = None
        logger.info("websocket closed")

    async def _connect_and_login(self, uri: str) -> None:
        logger.info("websocket connecting: %s", uri)
        self._websocket = await self._connect_factory(
            uri,
            self.timeout_seconds,
        )
        logger.info("websocket connected")
        await self._login()

    async def _receive_message(self) -> Any:
        while True:
            parsed = await self._receive_non_ping_message()
            if _is_login_message(parsed):
                return_code = normalize_return_code(parsed.get("return_code")) or 0
                if return_code != 0:
                    raise WebSocketLoginError(
                        return_code,
                        str(parsed.get("return_msg", "unknown error")),
                    )
                logger.info("websocket login acknowledged")
                continue

            logger.info("websocket received message")
            return parsed

    async def _login(self) -> None:
        if self._websocket is None:
            raise RuntimeError("websocket is not connected")

        login_packet = {
            "trnm": "LOGIN",
            "token": self.auth.get_access_token(),
        }
        logger.info("websocket sending LOGIN packet")
        await self._send_packet(login_packet)
        await self._await_login_ack()

    async def _send_packet(self, payload: Any) -> None:
        if self._websocket is None:
            raise RuntimeError("websocket is not connected")
        await self._websocket.send(_serialize_message(payload))

    async def _await_login_ack(self) -> None:
        while True:
            parsed = await self._receive_non_ping_message()
            if not _is_login_message(parsed):
                raise RuntimeError("websocket login ack was not received before other messages")
            return_code = normalize_return_code(parsed.get("return_code")) or 0
            if return_code != 0:
                raise WebSocketLoginError(
                    return_code,
                    str(parsed.get("return_msg", "unknown error")),
                )
            logger.info("websocket login acknowledged")
            return

    async def _receive_non_ping_message(self) -> Any:
        if self._websocket is None:
            raise RuntimeError("websocket is not connected")

        while True:
            message = await self._websocket.recv()
            parsed = _parse_message(message)
            if not _is_ping_message(parsed):
                return parsed
            logger.info("websocket received ping; echoing back")
            await self._send_packet(parsed)
            logger.info("websocket sent ping echo")


def _is_auth_retry_login_error(exc: WebSocketLoginError) -> bool:
    return auth_retry_code(exc.return_code, exc.return_msg) is not None


async def _default_connect(uri: str, timeout_seconds: int) -> Any:
    if _ws_connect is None:
        raise RuntimeError("websockets dependency is not installed")
    return await _ws_connect(
        uri,
        open_timeout=timeout_seconds,
        ping_interval=None,
    )


def _parse_api_url(api_url: str) -> str:
    normalized = api_url.strip()
    if not normalized.startswith("/"):
        raise ValueError("api_url must be an API path starting with '/'")
    if normalized.endswith("/websocket"):
        return normalized

    path, _, api_id = normalized.rpartition("/")
    if not path or not api_id:
        raise ValueError("api_url must be an API path starting with '/'")

    return path


def _parse_message(message: Any) -> Any:
    if isinstance(message, bytes):
        message = message.decode("utf-8")

    if isinstance(message, str):
        stripped = message.strip()
        if not stripped:
            return message
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return message

    return message


def _is_login_message(message: Any) -> bool:
    return isinstance(message, dict) and str(message.get("trnm", "")).upper() == "LOGIN"


def _is_ping_message(message: Any) -> bool:
    if isinstance(message, str):
        return message.strip().upper() == "PING"
    if isinstance(message, dict):
        return str(message.get("trnm", "")).upper() == "PING"
    return False


def _serialize_message(message: Any) -> str:
    if isinstance(message, str):
        return message
    return json.dumps(message, ensure_ascii=False)


def _is_connection_closed_exception(exc: Exception) -> bool:
    name = exc.__class__.__name__
    return "ConnectionClosed" in name or name.endswith("ClosedOK") or name.endswith("ClosedError")
