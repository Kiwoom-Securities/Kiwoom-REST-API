"""Common command execution through the package runtime facade."""

from __future__ import annotations

from collections.abc import AsyncIterator
import asyncio
import time
from typing import Any

from kiwoom import get_client, get_ws_client
from kiwoom.core.types import KiwoomResponse
from kiwoom_cli.registry import CommandDefinition
from kiwoom_cli.errors import CliInputError, CliInternalError
from kiwoom_cli.safety import enforce_before_preview, enforce_before_request


CONDITION_LIST_TRNM = "CNSRLST"
CONDITION_REQUEST_TRNM = "CNSRREQ"
CONDITION_CLEAR_TRNM = "CNSRCLR"
DEFAULT_CONDITION_MAX_WAIT_SECONDS = 15.0
DEFAULT_STREAM_MAX_WAIT_SECONDS = 15.0


def execute_rest_command(
    definition: CommandDefinition,
    *,
    body: dict[str, Any],
    mode: str | None = None,
    profile: str | None = None,
    confirm: bool = False,
) -> KiwoomResponse:
    validate_request_body(definition, body)
    enforce_before_request(definition, confirm=confirm)
    client = get_client(mode=mode, profile=profile)
    return client.fetch_page(
        api_id=definition.api_id,
        path=definition.path,
        method=definition.method,
        body=body,
    )


def preview_rest_command(definition: CommandDefinition, *, body: dict[str, Any]) -> dict[str, Any]:
    validate_request_body(definition, body)
    enforce_before_preview(definition)
    validation_errors = validate_preview_request(definition, body)
    return {
        "command": definition.command_path,
        "api_id": definition.api_id,
        "method": definition.method,
        "path": definition.path,
        "coverage_status": definition.coverage_status,
        "safety_policy": definition.safety_policy,
        "network": "not-submitted",
        "validation": {
            "status": "invalid" if validation_errors else "valid",
            "errors": validation_errors,
        },
        "body": body,
    }


def validate_preview_request(definition: CommandDefinition, body: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if definition.safety_policy not in {"order_preview", "order_write"}:
        return errors
    for field in ("orig_ord_no", "ord_no", "fr_ord_no", "rsrv_ord_no"):
        value = body.get(field)
        if value in (None, ""):
            continue
        if not str(value).isdigit() or len(str(value)) != 7:
            errors.append(
                {
                    "field": field,
                    "code": "invalid_order_id",
                    "message": "주문번호는 네트워크 전송 전에 키움 7자리 주문번호여야 합니다.",
                }
            )
    return errors


async def execute_websocket_request_once(
    definition: CommandDefinition,
    *,
    body: dict[str, Any],
    mode: str | None = None,
    profile: str | None = None,
) -> Any:
    validate_request_body(definition, body)
    enforce_before_request(definition, confirm=False)
    client = get_ws_client(mode=mode, profile=profile)
    return await client.request_once(api_url=definition.path, body=body)


async def execute_websocket_stream(
    definition: CommandDefinition,
    *,
    body: dict[str, Any],
    mode: str | None = None,
    profile: str | None = None,
    max_messages: int | str = 1,
    max_wait_seconds: float | int | str = DEFAULT_STREAM_MAX_WAIT_SECONDS,
) -> AsyncIterator[Any]:
    validate_request_body(definition, body)
    enforce_before_request(definition, confirm=False)
    message_limit = _normalize_max_messages(max_messages)
    wait_limit = _normalize_stream_max_wait_seconds(max_wait_seconds)
    data_count = 0
    system_count = 0
    started = time.monotonic()
    client = get_ws_client(mode=mode, profile=profile)
    await client.subscribe(api_url=definition.path, body=body)
    try:
        while message_limit == 0 or data_count < message_limit:
            timeout = _remaining_stream_wait_seconds(wait_limit, started)
            if timeout is not None and timeout <= 0:
                if message_limit == 0:
                    return
                raise TimeoutError(
                    _stream_timeout_message(
                        data_count=data_count,
                        system_count=system_count,
                        max_messages=message_limit,
                        max_wait_seconds=wait_limit,
                    )
                )
            try:
                if timeout is None:
                    message = await client.recv()
                else:
                    message = await asyncio.wait_for(client.recv(), timeout=timeout)
            except TimeoutError as exc:
                if message_limit == 0:
                    return
                raise TimeoutError(
                    _stream_timeout_message(
                        data_count=data_count,
                        system_count=system_count,
                        max_messages=message_limit,
                        max_wait_seconds=wait_limit,
                    )
                ) from exc

            if _is_realtime_message(message):
                data_count += 1
            else:
                system_count += 1

            yield message

            if _is_error_control_message(message):
                raise ValueError(_stream_error_message(message))
    finally:
        await client.close()


async def execute_condition_command(
    command: str,
    definition: CommandDefinition,
    *,
    body: dict[str, Any],
    mode: str | None = None,
    profile: str | None = None,
    max_messages: int | str = 1,
    max_wait_seconds: float | int | str = DEFAULT_CONDITION_MAX_WAIT_SECONDS,
    exchange: str | None = None,
) -> dict[str, Any]:
    if command == "conditions-search":
        return await _execute_condition_search(definition, body=body, mode=mode, profile=profile)
    if command == "conditions-subscribe":
        return await _execute_condition_subscribe(
            definition,
            body=body,
            mode=mode,
            profile=profile,
            max_messages=max_messages,
            max_wait_seconds=max_wait_seconds,
        )
    if command == "conditions-unsubscribe":
        return await _execute_condition_unsubscribe(
            definition,
            body=body,
            mode=mode,
            profile=profile,
            exchange=exchange,
        )
    raise CliInternalError(f"지원하지 않는 조건검색 명령입니다: {command}")


async def _execute_condition_search(
    definition: CommandDefinition,
    *,
    body: dict[str, Any],
    mode: str | None,
    profile: str | None,
) -> dict[str, Any]:
    enforce_before_request(definition, confirm=False)
    client = get_ws_client(mode=mode, profile=profile)
    try:
        await client.connect(api_url=definition.path)
        list_response = await _condition_send_and_receive(client, {"trnm": CONDITION_LIST_TRNM})
        condition_rows = _condition_rows(list_response.get("data"))
        selected_condition = _select_condition(condition_rows, preferred_seq=body.get("seq"))
        if selected_condition is None:
            return _condition_blocked_payload(
                conditions=condition_rows,
                list_response=list_response,
                preferred_seq=body.get("seq"),
                mode=mode,
                profile=profile,
            )

        request_body = {
            "trnm": body.get("trnm") or CONDITION_REQUEST_TRNM,
            "seq": selected_condition["seq"],
            "search_type": body.get("search_type") or "0",
            "stex_tp": body.get("stex_tp") or "K",
        }
        for optional_field in ("cont_yn", "next_key"):
            if optional_field in body:
                request_body[optional_field] = body[optional_field]
        validate_request_body(definition, request_body)
        response = await _condition_send_and_receive(client, request_body)
        return {
            "conditions": condition_rows,
            "selected_condition": selected_condition,
            "initial": response,
        }
    finally:
        await client.close()


async def _execute_condition_subscribe(
    definition: CommandDefinition,
    *,
    body: dict[str, Any],
    mode: str | None,
    profile: str | None,
    max_messages: int | str,
    max_wait_seconds: float | int | str,
) -> dict[str, Any]:
    enforce_before_request(definition, confirm=False)
    client = get_ws_client(mode=mode, profile=profile)
    selected_condition: dict[str, str] | None = None
    clear_done = False
    registered = False
    try:
        await client.connect(api_url=definition.path)
        list_response = await _condition_send_and_receive(client, {"trnm": CONDITION_LIST_TRNM})
        condition_rows = _condition_rows(list_response.get("data"))
        selected_condition = _select_condition(condition_rows, preferred_seq=body.get("seq"))
        if selected_condition is None:
            return _condition_blocked_payload(
                conditions=condition_rows,
                list_response=list_response,
                preferred_seq=body.get("seq"),
                mode=mode,
                profile=profile,
            )

        request_body = {
            "trnm": body.get("trnm") or CONDITION_REQUEST_TRNM,
            "seq": selected_condition["seq"],
            "search_type": body.get("search_type") or "1",
            "stex_tp": body.get("stex_tp") or "K",
        }
        validate_request_body(definition, request_body)
        initial_response = await _condition_send_and_receive(client, request_body)
        registered = True
        message_limit = _normalize_max_messages(max_messages)
        wait_limit = _normalize_max_wait_seconds(max_wait_seconds)
        realtime_messages, system_messages = await _collect_condition_realtime_messages(
            client,
            max_messages=message_limit,
            max_wait_seconds=wait_limit,
        )
        clear_response = await _try_clear_condition(client, selected_condition["seq"])
        clear_done = True
        if message_limit > 0 and len(realtime_messages) < message_limit:
            raise TimeoutError(
                _stream_timeout_message(
                    data_count=len(realtime_messages),
                    system_count=len(system_messages),
                    max_messages=message_limit,
                    max_wait_seconds=wait_limit,
                )
            )
        return {
            "conditions": condition_rows,
            "selected_condition": selected_condition,
            "initial": initial_response,
            "realtime": realtime_messages,
            "system": system_messages,
            "clear": clear_response,
        }
    finally:
        if selected_condition is not None and registered and not clear_done and client.is_connected:
            await _try_clear_condition(client, selected_condition["seq"])
        await client.close()


async def _execute_condition_unsubscribe(
    definition: CommandDefinition,
    *,
    body: dict[str, Any],
    mode: str | None,
    profile: str | None,
    exchange: str | None,
) -> dict[str, Any]:
    enforce_before_request(definition, confirm=False)
    client = get_ws_client(mode=mode, profile=profile)
    try:
        await client.connect(api_url=definition.path)
        list_response = await _condition_send_and_receive(client, {"trnm": CONDITION_LIST_TRNM})
        condition_rows = _condition_rows(list_response.get("data"))
        selected_condition = _select_condition(condition_rows, preferred_seq=body.get("seq"))
        if selected_condition is None:
            return _condition_blocked_payload(
                conditions=condition_rows,
                list_response=list_response,
                preferred_seq=body.get("seq"),
                mode=mode,
                profile=profile,
            )

        setup_request = {
            "trnm": CONDITION_REQUEST_TRNM,
            "seq": selected_condition["seq"],
            "search_type": "1",
            "stex_tp": _exchange_to_stex_tp(exchange),
        }
        setup_response = await _condition_send_and_receive(client, setup_request)
        clear_body = {
            "trnm": body.get("trnm") or CONDITION_CLEAR_TRNM,
            "seq": selected_condition["seq"],
        }
        validate_request_body(definition, clear_body)
        clear_response = await _condition_send_and_receive(client, clear_body)
        return {
            "conditions": condition_rows,
            "selected_condition": selected_condition,
            "setup_request": setup_response,
            "clear": clear_response,
        }
    finally:
        await client.close()


def validate_request_body(definition: CommandDefinition, body: dict[str, Any]) -> None:
    missing = [
        field
        for field in definition.required_body_fields
        if not _has_required_field(body, field)
    ]
    if missing:
        fields = ", ".join(missing)
        raise CliInputError(f"{definition.command_path}: 필수 요청 필드가 빠졌습니다: {fields}")


def _has_required_field(body: dict[str, Any], field: str) -> bool:
    if field in body and body[field] not in (None, ""):
        return True
    for row in body.get("data", []):
        if not isinstance(row, dict):
            continue
        if field not in row:
            continue
        value = row[field]
        if isinstance(value, list):
            if any(item not in (None, "") for item in value):
                return True
        elif value not in (None, ""):
            return True
    return False


async def _condition_send_and_receive(client: Any, body: dict[str, Any]) -> dict[str, Any]:
    await client.send(body)
    response = await asyncio.wait_for(client.recv(), timeout=client.timeout_seconds)
    if not isinstance(response, dict):
        raise RuntimeError(f"예상하지 못한 WebSocket 응답 형식입니다: {type(response).__name__}")
    return response


async def _collect_condition_realtime_messages(
    client: Any,
    *,
    max_messages: int,
    max_wait_seconds: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    realtime_messages: list[dict[str, Any]] = []
    system_messages: list[dict[str, Any]] = []
    loop = asyncio.get_running_loop()
    deadline = loop.time() + max_wait_seconds

    while max_messages == 0 or len(realtime_messages) < max_messages:
        remaining = deadline - loop.time()
        if remaining <= 0:
            break
        try:
            message = await asyncio.wait_for(client.recv(), timeout=remaining)
        except TimeoutError:
            break
        if not isinstance(message, dict):
            continue
        if str(message.get("trnm", "")).upper() == "REAL":
            realtime_messages.append(message)
            continue
        system_messages.append(message)
        return_code = message.get("return_code")
        if str(message.get("trnm", "")).upper() == "SYSTEM" or return_code not in (None, 0, "0"):
            break

    return realtime_messages, system_messages


async def _try_clear_condition(client: Any, seq: str) -> dict[str, Any]:
    try:
        return await _condition_send_and_receive(
            client,
            {
                "trnm": CONDITION_CLEAR_TRNM,
                "seq": seq,
            },
        )
    except TimeoutError as exc:
        return {
            "trnm": CONDITION_CLEAR_TRNM,
            "seq": seq,
            "return_code": "TIMEOUT",
            "return_msg": str(exc),
        }


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


def _select_condition(
    rows: list[dict[str, str]],
    *,
    preferred_seq: object,
) -> dict[str, str] | None:
    normalized = str(preferred_seq).strip() if preferred_seq not in (None, "") else ""
    if normalized:
        for row in rows:
            if row["seq"] == normalized:
                return row
        return None
    if not rows:
        return None
    return rows[0]


def _condition_blocked_payload(
    *,
    conditions: list[dict[str, str]],
    list_response: dict[str, Any],
    preferred_seq: object,
    mode: str | None,
    profile: str | None,
) -> dict[str, Any]:
    reason = "condition-seq-not-found" if preferred_seq not in (None, "") else "condition-list-empty"
    return {
        "status": "blocked",
        "blocked_reason": reason,
        "message": (
            "저장된 조건검색식을 찾을 수 없습니다. 영웅문에서 조건검색식을 저장한 뒤 "
            "다시 실행하거나, conditions-list 결과에 있는 --seq 값을 지정해 주세요."
        ),
        "mode": mode,
        "profile": profile,
        "preferred_seq": preferred_seq,
        "conditions": conditions,
        "conditions_count": len(conditions),
        "list_response": list_response,
    }


def _normalize_max_messages(value: int | str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise CliInputError("stream 메시지 수는 정수여야 합니다.") from exc
    if parsed < 0:
        raise CliInputError("stream 메시지 수는 0 이상이어야 합니다.")
    return parsed


def _normalize_stream_max_wait_seconds(value: float | int | str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise CliInputError("stream 대기 시간은 숫자여야 합니다.") from exc
    if parsed < 0:
        raise CliInputError("stream 대기 시간은 0초 이상이어야 합니다.")
    return parsed


def _remaining_stream_wait_seconds(wait_limit: float, started: float) -> float | None:
    if wait_limit == 0:
        return None
    return wait_limit - (time.monotonic() - started)


def _is_realtime_message(message: Any) -> bool:
    return isinstance(message, dict) and str(message.get("trnm", "")).upper() == "REAL"


def _is_error_control_message(message: Any) -> bool:
    if not isinstance(message, dict):
        return False
    return_code = message.get("return_code")
    if return_code in (None, "", 0, "0", "0000"):
        return False
    return True


def _stream_error_message(message: dict[str, Any]) -> str:
    code = message.get("return_code")
    text = str(message.get("return_msg") or message.get("message") or "").strip()
    if text:
        return f"실시간 등록/제어 응답 오류(return_code={code}): {text}"
    return f"실시간 등록/제어 응답 오류(return_code={code})"


def _stream_timeout_message(
    *,
    data_count: int,
    system_count: int,
    max_messages: int,
    max_wait_seconds: float,
) -> str:
    target = "무제한" if max_messages == 0 else str(max_messages)
    return (
        "실시간 REAL 데이터가 제한 시간 안에 충분히 수신되지 않았습니다. "
        f"REAL={data_count}/{target}, control={system_count}, wait={max_wait_seconds:g}s"
    )


def _normalize_max_wait_seconds(value: float | int | str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise CliInputError("stream 대기 시간은 숫자여야 합니다.") from exc
    if parsed <= 0:
        raise CliInputError("stream 대기 시간은 0초보다 커야 합니다.")
    return parsed


def _exchange_to_stex_tp(value: object) -> str:
    return {
        "KRX": "K",
        "NXT": "N",
        "ALL": "A",
        None: "K",
        "": "K",
    }.get(value, str(value))
