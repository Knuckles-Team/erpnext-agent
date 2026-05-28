from unittest.mock import patch

import pytest

from erpnext_agent.api_client import Api


@pytest.mark.concept("ERPN-001")
def test_api_client_basic_mock(mock_ctx):
    """CONCEPT:ERPN-001 Test basic mock initialization of client facade."""
    assert mock_ctx is not None
    assert hasattr(mock_ctx, "info")


@pytest.mark.concept("ERPN-001")
def test_api_client_endpoints(mock_ctx):
    """CONCEPT:ERPN-001 Verify endpoint configuration on dynamic client."""
    from erpnext_agent.auth import get_client

    client = get_client()
    assert client is not None
    assert hasattr(client, "request")


@pytest.mark.concept("ERPN-001")
def test_base_url_normalization():
    """Verify that trailing slashes and /api prefix are stripped from base_url."""
    c1 = Api(base_url="https://demo.erpnext.com/api")
    assert c1.base_url == "https://demo.erpnext.com"

    c2 = Api(base_url="https://demo.erpnext.com/api/")
    assert c2.base_url == "https://demo.erpnext.com"

    c3 = Api(base_url="https://demo.erpnext.com")
    assert c3.base_url == "https://demo.erpnext.com"


@pytest.mark.concept("ERPN-001")
def test_token_authorization_formats():
    """Verify that different token formats are correctly formatted in authorization headers."""
    # Colon key:secret should format as 'token key:secret'
    c1 = Api(base_url="http://localhost", token="api_key:api_secret")
    assert c1._session.headers.get("Authorization") == "token api_key:api_secret"

    # Already prefixed with Bearer
    c2 = Api(base_url="http://localhost", token="Bearer some_jwt_token")
    assert c2._session.headers.get("Authorization") == "Bearer some_jwt_token"

    # Already prefixed with token
    c3 = Api(base_url="http://localhost", token="token key:secret")
    assert c3._session.headers.get("Authorization") == "token key:secret"

    # Plain string defaults to Bearer
    c4 = Api(base_url="http://localhost", token="simpletoken")
    assert c4._session.headers.get("Authorization") == "Bearer simpletoken"


@pytest.mark.concept("ERPN-001")
def test_list_documents_parameter_serialization():
    """Verify list_documents properly serializes fields, filters, and pagination."""
    client = Api(base_url="http://localhost")

    with patch.object(client, "request") as mock_request:
        client.list_documents(
            doctype="Customer",
            filters=[["Customer", "country", "=", "India"]],
            fields=["name", "country"],
            limit_page_length=50,
            limit_start=100,
        )
        mock_request.assert_called_once_with(
            "GET",
            "/api/resource/Customer",
            params={
                "limit_page_length": 50,
                "limit_start": 100,
                "filters": '[["Customer", "country", "=", "India"]]',
                "fields": '["name", "country"]',
            },
        )


@pytest.mark.concept("ERPN-001")
def test_auth_and_version_methods():
    """Verify all Naive Authentication endpoints are mapped correctly."""
    client = Api(base_url="http://localhost")

    with patch.object(client, "request") as mock_request:
        client.login(usr="admin", pwd="pwd")
        mock_request.assert_called_with(
            "POST", "/api/method/login", data={"usr": "admin", "pwd": "pwd"}
        )

        client.logout()
        mock_request.assert_called_with("GET", "/api/method/logout")

        client.get_logged_user()
        mock_request.assert_called_with(
            "GET", "/api/method/frappe.auth.get_logged_user"
        )

        client.authGetLoggedUser()
        mock_request.assert_called_with(
            "GET", "/api/method/frappe.auth.get_logged_user"
        )

        client.auth_get_logged_user()
        mock_request.assert_called_with(
            "GET", "/api/method/frappe.auth.get_logged_user"
        )

        client.get_version()
        mock_request.assert_called_with("GET", "/api/method/version")

        client.version()
        mock_request.assert_called_with("GET", "/api/method/version")
