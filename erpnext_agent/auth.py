import os
from agent_utilities.base_utilities import get_logger, to_boolean
from erpnext_agent.api_client import Api

logger = get_logger(__name__)

def get_client() -> Api:
    """Get authenticated client for erpnext_agent."""
    base_url = os.getenv("ERPNEXT_URL") or os.getenv("ERPNEXT_AGENT_BASE_URL", "")
    token = os.getenv("ERPNEXT_TOKEN", "")
    username = os.getenv("ERPNEXT_AGENT_USERNAME", "")
    password = os.getenv("ERPNEXT_AGENT_PASSWORD", "")
    verify = to_boolean(os.getenv("ERPNEXT_AGENT_SSL_VERIFY", "True"))

    if not base_url:
        # Default fallback for testing
        base_url = "http://localhost"

    return Api(base_url=base_url, token=token, username=username, password=password, verify=verify)
