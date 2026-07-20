from typing import Any
from urllib.parse import urljoin

import requests
from agent_utilities.core.transport_security import (
    ResolvedTLSProfile,
    resolve_configured_tls_profile,
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
        self.tls_profile = tls_profile or resolve_configured_tls_profile(
            "erpnext_agent"
        )
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
    ) -> Any:
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = urljoin(self.base_url, endpoint)

        headers = {"Content-Type": "application/json"}
        response = self._session.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=data,
        )

        if response.status_code >= 400:
            raise Exception(f"API error: {response.status_code}")

        if response.status_code == 204 or not response.text.strip():
            return {"status": "success"}

        try:
            return response.json()
        except Exception:
            return {"status": "success", "text": response.text}
