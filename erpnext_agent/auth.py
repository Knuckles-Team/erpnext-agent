"""CONCEPT:EN-OS.identity.erpn Identity credentials loader and session manager."""

from agent_utilities.base_utilities import get_logger
from agent_utilities.core.config import setting
from agent_utilities.core.transport_security import (
    ResolvedTLSProfile,
    resolve_configured_tls_profile,
)

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
        tls_profile=tls_profile or resolve_configured_tls_profile("erpnext_agent"),
    )
