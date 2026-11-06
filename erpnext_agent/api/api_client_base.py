import json
from typing import Any
from urllib.parse import urljoin

import requests
from scion_sdk.tls.profile import ResolvedTLSProfile
from scion_sdk.tls.resolve import resolve_tls_profile


class ErpNextApiError(Exception):
    """A Frappe REST call failed; carries the server's own reason.

    Frappe answers a refused write with an HTTP 4xx/5xx body holding
    ``exc_type`` and ``_server_messages`` (a JSON list of JSON-encoded
    message objects). The reason ("Could not find Gender: X", "Customer is
    mandatory") is what an agent needs to correct the call, so it is kept;
    the server traceback (``exc``) is never copied.
    """

    def __init__(self, status: int, exc_type: str | None, messages: list[str]):
        self.status = status
        self.exc_type = exc_type
        self.messages = messages
        reason = "; ".join(messages) if messages else "no server message"
        kind = f" {exc_type}" if exc_type else ""
        super().__init__(f"API error: {status}{kind}: {reason}")


def _strip_html(text: str) -> str:
    import re

    return re.sub(r"<[^>]+>", "", text).strip()


def frappe_error(status: int, body: str) -> ErpNextApiError:
    """Build an :class:`ErpNextApiError` from a Frappe error response body."""
    try:
        payload = json.loads(body)
    except ValueError:
        return ErpNextApiError(status, None, [])
    if not isinstance(payload, dict):
        return ErpNextApiError(status, None, [])
    messages: list[str] = []
    raw = payload.get("_server_messages")
    if isinstance(raw, str):
        try:
            for item in json.loads(raw):
                try:
                    entry = json.loads(item) if isinstance(item, str) else item
                except ValueError:
                    entry = {"message": item}
                text = entry.get("message") if isinstance(entry, dict) else entry
                if text:
                    messages.append(_strip_html(str(text)))
        except ValueError:
            pass
    if not messages:
        exception = payload.get("exception") or payload.get("message")
        if isinstance(exception, str) and exception:
            messages.append(_strip_html(exception.splitlines()[-1]))
    exc_type = payload.get("exc_type")
    return ErpNextApiError(
        status, exc_type if isinstance(exc_type, str) else None, messages
    )


class ApiClientBase:
    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        username: str | None = None,
        password: str | None = None,
        tls_profile: ResolvedTLSProfile | None = None,
    ):
        base_url = base_url.rstrip("/")
        if base_url.endswith("/api"):
            base_url = base_url[:-4].rstrip("/")
        self.base_url = base_url
        self.token = token
        self.username = username
        self.password = password
        self.tls_profile = tls_profile or resolve_tls_profile("erpnext_agent")
        self._session = self.tls_profile.configure_requests_session(requests.Session())

        if token:
            if not token.startswith("Bearer ") and not token.startswith("token "):
                if ":" in token:
                    self._session.headers.update({"Authorization": f"token {token}"})
                else:
                    self._session.headers.update({"Authorization": f"Bearer {token}"})
            else:
                self._session.headers.update({"Authorization": token})
        elif username and password:
            self._session.auth = (username, password)

    def close(self) -> None:
        """Release transport resources and runtime-only TLS material."""
        self._session.close()
        self.tls_profile.cleanup()

    def request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: Any | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = urljoin(self.base_url, endpoint)

        if files is None:
            headers = {"Content-Type": "application/json"}
            response = self._session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
            )
        else:
            response = self._session.request(
                method=method, url=url, params=params, data=data, files=files
            )

        if response.status_code >= 400:
            raise frappe_error(response.status_code, response.text)

        if response.status_code == 204 or not response.text.strip():
            return {"status": "success"}

        try:
            return response.json()
        except Exception:
            return {"status": "success", "text": response.text}
