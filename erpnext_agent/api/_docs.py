"""Small helpers shared by the typed operation mixins."""

from typing import Any


def data_of(response: Any) -> Any:
    """The document inside a ``{"data": ...}`` resource response."""
    if isinstance(response, dict) and "data" in response:
        return response["data"]
    return response


def message_of(response: Any) -> dict[str, Any]:
    """The ``message`` payload of a whitelisted-method response, as a dict copy."""
    if isinstance(response, dict):
        inner = response.get("message", response)
        if isinstance(inner, dict):
            return dict(inner)
    return {}


def compact(doc: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """``doc`` without ``None`` values, then any caller-supplied extra fields."""
    merged = {key: value for key, value in doc.items() if value is not None}
    merged.update(extra or {})
    return merged
