from collections.abc import Iterator
import time
from typing import Any

import requests

from kiwoom.core.auth import KiwoomAuth, get_base_url
from kiwoom.core.errors import AuthenticationError, HTTPRequestError
from kiwoom.core.types import Continuation, KiwoomResponse

RESERVED_REQUEST_HEADERS = {"content-type", "api-id", "authorization"}


class KiwoomClient:
    def __init__(self, auth: KiwoomAuth, *, timeout_seconds: int = 30) -> None:
        self.auth = auth
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def request(
        self,
        *,
        api_url: str | None = None,
        api: str | None = None,
        api_id: str | None = None,
        path: str | None = None,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        extra_headers: dict[str, str] | None = None,
        retry_on_auth_failure: bool = True,
    ) -> KiwoomResponse:
        resolved_api_id, resolved_path = _resolve_api_target(
            api_url=api_url,
            api=api,
            api_id=api_id,
            path=path,
        )
        _validate_extra_headers(extra_headers)
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "api-id": resolved_api_id,
            "authorization": self.auth.authorization_header(),
        }
        if extra_headers:
            headers.update(extra_headers)

        response = self.session.request(
            method=method,
            url=f"{get_base_url(self.auth.mode)}{resolved_path}",
            headers=headers,
            json=body or {},
            timeout=self.timeout_seconds,
        )

        if response.status_code == 401 and retry_on_auth_failure:
            self.auth.recover_from_auth_failure()
            return self.request(
                api_id=resolved_api_id,
                path=resolved_path,
                body=body,
                method=method,
                extra_headers=extra_headers,
                retry_on_auth_failure=False,
            )
        if response.status_code == 401:
            raise AuthenticationError("인증 정보를 갱신한 뒤 다시 시도했지만 요청에 실패했습니다.")

        try:
            data = response.json()
        except ValueError as exc:
            if response.status_code >= 400:
                raise HTTPRequestError(response.status_code, "API 응답이 JSON 형식이 아닙니다.") from exc
            data = {
                "return_msg": "API 응답이 JSON 형식이 아닙니다.",
                "raw_text": response.text,
            }

        if data.get("return_code") in (8005, 8031, 8103) and retry_on_auth_failure:
            self.auth.recover_from_auth_failure()
            return self.request(
                api_id=resolved_api_id,
                path=resolved_path,
                body=body,
                method=method,
                extra_headers=extra_headers,
                retry_on_auth_failure=False,
            )

        if response.status_code >= 400:
            message = str(data.get("return_msg", "API 요청에 실패했습니다."))
            if data.get("return_code") not in (None, 0):
                message = f"{message} (return_code={data['return_code']})"
            raise HTTPRequestError(response.status_code, message)
        return _build_response(data, response.headers)

    def fetch_page(
        self,
        *,
        api_url: str | None = None,
        api: str | None = None,
        api_id: str | None = None,
        path: str | None = None,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        cont_yn: str | None = None,
        next_key: str | None = None,
    ) -> KiwoomResponse:
        """단일 페이지를 조회하고, 연속조회 cursor가 있으면 요청 헤더에 반영합니다."""
        extra_headers: dict[str, str] = {}
        if cont_yn is not None:
            extra_headers["cont-yn"] = cont_yn
        if next_key is not None:
            extra_headers["next-key"] = next_key

        return self.request(
            api_url=api_url,
            api=api,
            api_id=api_id,
            path=path,
            body=body,
            method=method,
            extra_headers=extra_headers or None,
        )

    def paginate(
        self,
        *,
        api_url: str | None = None,
        api: str | None = None,
        api_id: str | None = None,
        path: str | None = None,
        body: dict[str, Any] | None = None,
        method: str = "POST",
        max_pages: int | None = None,
        request_delay_seconds: float = 0,
    ) -> Iterator[KiwoomResponse]:
        """연속조회가 끝날 때까지 페이지를 순서대로 yield합니다."""
        if max_pages is not None and max_pages < 1:
            raise ValueError("max_pages must be greater than 0")
        if request_delay_seconds < 0:
            raise ValueError("request_delay_seconds must be greater than or equal to 0")

        cont_yn: str | None = None
        next_key: str | None = None
        page_count = 0
        while True:
            response = self.fetch_page(
                api_url=api_url,
                api=api,
                api_id=api_id,
                path=path,
                body=body,
                method=method,
                cont_yn=cont_yn,
                next_key=next_key,
            )
            yield response
            page_count += 1
            if not response.continuation.has_next:
                break
            if max_pages is not None and page_count >= max_pages:
                break
            cont_yn = response.continuation.cont_yn or "Y"
            next_key = response.continuation.next_key or ""
            if request_delay_seconds > 0:
                time.sleep(request_delay_seconds)

def _validate_extra_headers(extra_headers: dict[str, str] | None) -> None:
    if not extra_headers:
        return

    for header_name in extra_headers:
        if header_name.lower() in RESERVED_REQUEST_HEADERS:
            raise ValueError(f"extra_headers cannot override reserved header: {header_name}")


def _resolve_api_target(
    *,
    api_url: str | None,
    api: str | None,
    api_id: str | None,
    path: str | None,
) -> tuple[str, str]:
    if api_url is not None:
        if api is not None or api_id is not None or path is not None:
            raise ValueError("use only one of api_url, api, or api_id/path")
        return _parse_api_url_target(api_url)

    if api is not None:
        if api_id is not None or path is not None:
            raise ValueError("use only one of api_url, api, or api_id/path")
        return _parse_api_target(api)

    if not api_id or not path:
        raise ValueError("api_id and path are required when api is not provided")
    return api_id, path


def _parse_api_url_target(api_url: str) -> tuple[str, str]:
    normalized = api_url.strip()
    if not normalized.startswith("/"):
        raise ValueError("api_url must be in the format '<path>/<api_id>'")

    path, _, api_id = normalized.rpartition("/")
    if not path or not api_id:
        raise ValueError("api_url must be in the format '<path>/<api_id>'")

    return api_id, path


def _parse_api_target(api: str) -> tuple[str, str]:
    api_spec = api.strip()
    parts = api_spec.split(maxsplit=1)
    if len(parts) != 2:
        raise ValueError("api must be in the format '<api_id> <path>'")

    api_id, path = parts[0].strip(), parts[1].strip()
    if not api_id or not path.startswith("/"):
        raise ValueError("api must be in the format '<api_id> <path>'")
    return api_id, path


def _build_response(data: dict[str, Any], response_headers: Any) -> KiwoomResponse:
    cont_yn = response_headers.get("cont-yn") or response_headers.get("Cont-Yn")
    next_key = response_headers.get("next-key") or response_headers.get("Next-Key")
    continuation = Continuation(
        has_next=cont_yn == "Y",
        next_key=next_key or None,
        cont_yn=cont_yn or None,
    )
    return KiwoomResponse(
        body=data,
        continuation=continuation,
        headers=dict(response_headers),
    )
