"""Bounded canonical identity and invoice payload binding."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

_MAX_PAYLOAD_BYTES = 131_072
_MAX_TEXT_BYTES = 256
_INVOICE_FIELDS = frozenset(
    {
        "company",
        "customer",
        "currency",
        "posting_date",
        "due_date",
        "items",
        "remarks",
        "debit_to",
    }
)
_ITEM_FIELDS = frozenset(
    {"item_code", "qty", "rate", "uom", "income_account", "cost_center", "description"}
)


def _scalar(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, str):
        return len(value.encode("utf-8")) <= 8192
    if isinstance(value, int):
        return -(2**63) <= value < 2**63
    return isinstance(value, float) and math.isfinite(value)


def _identity(value: object) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > _MAX_TEXT_BYTES
        or any(ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        raise ValueError("invalid operation binding")
    return value


def _request(
    tenant: object, company: object, key: object, invoice: object
) -> tuple[str, str, str, dict[str, Any]]:
    tenant_id, company_id, effect_key = (
        _identity(item) for item in (tenant, company, key)
    )
    if isinstance(invoice, str):
        if len(invoice.encode("utf-8")) > _MAX_PAYLOAD_BYTES:
            raise ValueError("invoice exceeds the size limit")
        invoice = json.loads(invoice)
    if not isinstance(invoice, dict) or any(
        not isinstance(name, str) or name not in _INVOICE_FIELDS for name in invoice
    ):
        raise ValueError("invalid invoice payload")
    if invoice.get("company") != company_id:
        raise ValueError("invoice company does not match operation")
    if any(not _scalar(value) for name, value in invoice.items() if name != "items"):
        raise ValueError("invalid invoice field")
    items = invoice.get("items")
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise ValueError("invoice item count is invalid")
    if any(
        not isinstance(item, dict)
        or not item
        or any(not isinstance(name, str) or name not in _ITEM_FIELDS for name in item)
        or any(not _scalar(value) for value in item.values())
        for item in items
    ):
        raise ValueError("invalid invoice items")
    raw = json.dumps(
        invoice, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    if len(raw) > _MAX_PAYLOAD_BYTES:
        raise ValueError("invoice exceeds the size limit")
    claim = hashlib.sha256(
        json.dumps([tenant_id, company_id, effect_key], separators=(",", ":")).encode()
    ).hexdigest()
    digest = hashlib.sha256(raw).hexdigest()
    return claim, company_id, digest, dict(invoice)
