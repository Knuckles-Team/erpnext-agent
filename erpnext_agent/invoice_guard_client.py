"""One-attempt governed transport for the optional source-side invoice guard.

The host must authorize a change set before calling this client. It does not
prove that the source app is installed or that an outcome is safe to retry.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any, Literal

from scion_erp_guard.bindings import _identity, _request
from scion_sdk.http.bodies import aread_bounded
from scion_sdk.http.client import create_async_http_client
from scion_sdk.http.options import HttpClientOptions
from scion_sdk.writeback.errors import OutcomeUncertainError

_RECEIPT_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_MAX_REPLY_BYTES = 4096


@dataclass(frozen=True)
class InvoiceGuardOutcome:
    """A source receipt or an explicitly unresolved source outcome."""

    outcome: Literal["applied", "reserved", "unknown"]
    claim_id: str = ""
    invoice: str = ""
    version: str = ""
    request_digest: str = ""


class InvoiceGuardClient:
    """Call the installed guard without retries or redirect forwarding."""

    def __init__(self, options: HttpClientOptions) -> None:
        if (
            not options.pin_egress
            or options.retry.max_attempts != 1
            or isinstance(options.timeout, bool)
            or not isinstance(options.timeout, (int, float))
            or not math.isfinite(options.timeout)
            or not 0 < options.timeout <= 30
        ):
            raise ValueError(
                "invoice guard requires pinned egress, one attempt and a bounded timeout"
            )
        self._options = replace(
            options,
            headers=MappingProxyType(dict(options.headers)),
            allowed_private_hosts=tuple(options.allowed_private_hosts),
        )

    async def create(
        self, tenant: str, company: str, idempotency_key: str, invoice: dict[str, Any]
    ) -> InvoiceGuardOutcome:
        """Create once; an ambiguous provider response must be reconciled."""
        claim_id, _, digest, payload = _request(
            tenant, company, idempotency_key, invoice
        )
        payload = json.loads(json.dumps(payload, allow_nan=False))
        data = {
            "tenant": tenant,
            "company": company,
            "idempotency_key": idempotency_key,
            "invoice": payload,
        }
        reply = await self._post("create_invoice_once", data)
        return self._receipt(
            reply, claim_id, digest, allow_unknown=False, allow_reserved=False
        )

    async def reconcile(
        self, tenant: str, company: str, idempotency_key: str, invoice: dict[str, Any]
    ) -> InvoiceGuardOutcome:
        """Read the exact prior receipt; unknown never authorizes a retry."""
        claim_id, _, digest, _ = _request(tenant, company, idempotency_key, invoice)
        data = {
            "tenant": tenant,
            "company": company,
            "idempotency_key": idempotency_key,
        }
        reply = await self._post("reconcile_invoice", data)
        return self._receipt(
            reply, claim_id, digest, allow_unknown=True, allow_reserved=True
        )

    async def _post(self, method: str, data: dict[str, Any]) -> object:
        try:
            async with create_async_http_client(self._options) as client:
                async with client.stream(
                    "POST",
                    f"/api/method/scion_erp_guard.api.{method}",
                    json=data,
                    follow_redirects=False,
                ) as response:
                    if response.status_code != 200:
                        raise OutcomeUncertainError(
                            "invoice source outcome unavailable"
                        )
                    raw = await aread_bounded(response, _MAX_REPLY_BYTES)
            result = json.loads(raw)
            if not isinstance(result, dict) or set(result) != {"message"}:
                raise ValueError("invalid source envelope")
            return result["message"]
        except Exception:
            raise OutcomeUncertainError("invoice source outcome unavailable") from None

    @staticmethod
    def _receipt(
        reply: object,
        claim_id: str,
        digest: str,
        *,
        allow_unknown: bool,
        allow_reserved: bool,
    ) -> InvoiceGuardOutcome:
        if (
            isinstance(reply, dict)
            and reply == {"outcome": "unknown"}
            and allow_unknown
        ):
            return InvoiceGuardOutcome("unknown")
        if (
            allow_reserved
            and isinstance(reply, dict)
            and reply
            == {"outcome": "reserved", "claim_id": claim_id, "request_digest": digest}
        ):
            return InvoiceGuardOutcome(
                "reserved", claim_id=claim_id, request_digest=digest
            )
        if not isinstance(reply, dict) or set(reply) != {
            "outcome",
            "claim_id",
            "invoice",
            "version",
            "request_digest",
        }:
            raise OutcomeUncertainError("invoice source receipt unavailable")
        try:
            name, version = _identity(reply["invoice"]), _identity(reply["version"])
            if (
                reply["outcome"] != "applied"
                or reply["claim_id"] != claim_id
                or reply["request_digest"] != digest
                or not _RECEIPT_DIGEST.fullmatch(digest)
            ):
                raise ValueError("invalid receipt binding")
        except (TypeError, ValueError):
            raise OutcomeUncertainError("invoice source receipt unavailable") from None
        return InvoiceGuardOutcome("applied", claim_id, name, version, digest)

    async def reserve(
        self, tenant: str, company: str, idempotency_key: str, invoice: dict[str, Any]
    ) -> InvoiceGuardOutcome:
        """Reserve an exact no-effect claim; ambiguity never grants a create."""
        claim_id, _, digest, payload = _request(
            tenant, company, idempotency_key, invoice
        )
        payload = json.loads(json.dumps(payload, allow_nan=False))
        data = {
            "tenant": tenant,
            "company": company,
            "idempotency_key": idempotency_key,
            "invoice": payload,
        }
        reply = await self._post("reserve_invoice", data)
        return self._receipt(
            reply, claim_id, digest, allow_unknown=False, allow_reserved=True
        )
