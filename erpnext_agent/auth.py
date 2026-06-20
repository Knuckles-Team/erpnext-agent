"""CONCEPT:ERPN-003 Identity credentials loader and session manager."""

from agent_utilities.base_utilities import get_logger
from agent_utilities.core.config import setting

from erpnext_agent.api_client import Api

logger = get_logger(__name__)


def get_client() -> Api:
    """Get authenticated client for erpnext_agent."""
    base_url = setting("ERPNEXT_URL", None) or setting("ERPNEXT_AGENT_BASE_URL", "")
    token = setting("ERPNEXT_TOKEN", "")
    username = setting("ERPNEXT_AGENT_USERNAME", "")
    password = setting("ERPNEXT_AGENT_PASSWORD", "")
    verify = setting("ERPNEXT_AGENT_SSL_VERIFY", True)

    if not base_url:
        # Default fallback for testing
        base_url = "http://localhost"

    return Api(
        base_url=base_url,
        token=token,
        username=username,
        password=password,
        verify=verify,
    )
