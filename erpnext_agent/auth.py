"""CONCEPT:EN-OS.identity.erpn Identity credentials loader and session manager."""

from agent_connector_sdk.config import setting
from agent_connector_sdk.tls.profile import ResolvedTLSProfile
from agent_connector_sdk.tls.resolve import resolve_tls_profile
from agent_connector_sdk.utilities import get_logger

from erpnext_agent.api_client import Api

logger = get_logger(__name__)


def get_client(tls_profile: ResolvedTLSProfile | None = None) -> Api:
    """Get authenticated client for erpnext_agent."""
    base_url = setting("ERPNEXT_URL", "")
    token = setting("ERPNEXT_TOKEN", "")
    username = setting("ERPNEXT_AGENT_USERNAME", "")
    password = setting("ERPNEXT_AGENT_PASSWORD", "")
    if not base_url:
        raise RuntimeError("ERPNEXT_URL is required")

    return Api(
        base_url=base_url,
        token=token,
        username=username,
        password=password,
        tls_profile=tls_profile or resolve_tls_profile("erpnext_agent"),
    )
