from typing import Any

from erpnext_agent.api.api_client_base import ApiClientBase


class Api(ApiClientBase):
    def login(self, usr: str | None = None, pwd: str | None = None) -> dict:
        """Authenticate yourself."""
        data = {}
        if usr:
            data["usr"] = usr
        if pwd:
            data["pwd"] = pwd
        return self.request("POST", "/api/method/login", data=data)

    def logout(self) -> dict:
        """Logout from current session."""
        return self.request("GET", "/api/method/logout")

    def get_logged_user(self) -> dict:
        """Get the user that is logged in."""
        return self.request("GET", "/api/method/frappe.auth.get_logged_user")

    def authGetLoggedUser(self) -> dict:
        """Alias for get_logged_user matching OpenAPI operationId."""
        return self.get_logged_user()

    def auth_get_logged_user(self) -> dict:
        """Snake-case alias for get_logged_user."""
        return self.get_logged_user()

    def get_version(self) -> dict:
        """Get the version of the app."""
        return self.request("GET", "/api/method/version")

    def version(self) -> dict:
        """Alias for get_version."""
        return self.get_version()

    def get_document(self, doctype: str, name: str) -> dict:
        """Get a document resource by name."""
        return self.request("GET", f"/api/resource/{doctype}/{name}")

    def create_document(self, doctype: str, data: dict) -> dict:
        """Create a new document resource."""
        return self.request("POST", f"/api/resource/{doctype}", data=data)

    def update_document(self, doctype: str, name: str, data: dict) -> dict:
        """Update a specific document resource."""
        return self.request("PUT", f"/api/resource/{doctype}/{name}", data=data)

    def delete_document(self, doctype: str, name: str) -> dict:
        """Delete a specific document resource."""
        return self.request("DELETE", f"/api/resource/{doctype}/{name}")

    def list_documents(
        self,
        doctype: str,
        filters: list | None = None,
        fields: list | None = None,
        limit_page_length: int = 20,
        limit_start: int = 0,
        limit: int | None = None,
    ) -> list:
        """List document resources with pagination, filters, and selected fields."""
        import json

        page_length = limit if limit is not None else limit_page_length
        params: dict[str, Any] = {
            "limit_page_length": page_length,
            "limit_start": limit_start,
        }
        if filters:
            if isinstance(filters, (list, dict, tuple)):
                params["filters"] = json.dumps(filters)
            else:
                params["filters"] = str(filters)
        if fields:
            if isinstance(fields, (list, dict, tuple)):
                params["fields"] = json.dumps(fields)
            else:
                params["fields"] = str(fields)
        return self.request("GET", f"/api/resource/{doctype}", params=params)

    def call_method(self, method: str, params: dict | None = None) -> dict:
        """Execute dotted path whitelisted RPC methods (covers 100% of custom functions)."""
        return self.request("POST", f"/api/method/{method}", data=params)
