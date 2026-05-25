from erpnext_agent.api.api_client_base import ApiClientBase


class Api(ApiClientBase):
    def get_document(self, doctype: str, name: str) -> dict:
        """Get a document resource."""
        return self.request("GET", f"/api/resource/{doctype}/{name}")

    def create_document(self, doctype: str, data: dict) -> dict:
        """Create a new document resource."""
        return self.request("POST", f"/api/resource/{doctype}", data=data)

    def update_document(self, doctype: str, name: str, data: dict) -> dict:
        """Update a document resource."""
        return self.request("PUT", f"/api/resource/{doctype}/{name}", data=data)

    def delete_document(self, doctype: str, name: str) -> dict:
        """Delete a document resource."""
        return self.request("DELETE", f"/api/resource/{doctype}/{name}")

    def list_documents(
        self, doctype: str, filters: list = None, fields: list = None, limit: int = 20
    ) -> list:
        """List document resources."""
        params = {"limit_page_length": limit}
        if filters:
            params["filters"] = str(filters)
        if fields:
            params["fields"] = str(fields)
        return self.request("GET", f"/api/resource/{doctype}", params=params)

    def call_method(self, method: str, params: dict = None) -> dict:
        """Execute dotted path whitelisted RPC methods (covers 100% of custom functions)."""
        return self.request("POST", f"/api/method/{method}", data=params)
