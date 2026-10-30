"""The connector transport uses one governed HTTP attempt and binds receipts."""

import json

import pytest
from scion_erp_guard.bindings import _request
from scion_sdk.http.options import HttpClientOptions
from scion_sdk.http.retry import RetryPolicy
from scion_sdk.testing.http_server import ScriptedHttpServer, ScriptedResponse
from scion_sdk.writeback.errors import OutcomeUncertainError

from erpnext_agent.invoice_guard_client import InvoiceGuardClient


def invoice():
    return {
        "company": "Company",
        "customer": "Customer",
        "currency": "USD",
        "items": [{"item_code": "item", "qty": 1, "rate": 5}],
    }


def options(base):
    return HttpClientOptions(
        base_url=base,
        pin_egress=True,
        allow_loopback=True,
        retry=RetryPolicy(max_attempts=1),
    )


@pytest.mark.asyncio
async def test_one_attempt_validates_receipt_and_keeps_missing_outcome_unknown():
    claim, _, digest, _ = _request("tenant", "Company", "key", invoice())
    receipt = {
        "message": {
            "outcome": "applied",
            "claim_id": claim,
            "invoice": "invoice-1",
            "version": "v1",
            "request_digest": digest,
        }
    }
    with ScriptedHttpServer(
        ScriptedResponse(body=json.dumps(receipt).encode()),
        ScriptedResponse(body=b'{"message":{"outcome":"unknown"}}'),
    ) as upstream:
        client = InvoiceGuardClient(options(upstream.base_url))
        result = await client.create("tenant", "Company", "key", invoice())
        assert result.outcome == "applied" and result.claim_id == claim
        missing = await client.reconcile("tenant", "Company", "key", invoice())
        assert missing.outcome == "unknown"
        assert len(upstream.requests) == 2
        assert all(item.method == "POST" for item in upstream.requests)


@pytest.mark.asyncio
async def test_untrusted_or_missing_receipt_is_uncertain_and_never_retried():
    claim, _, digest, _ = _request("tenant", "Company", "key", invoice())
    receipt = {
        "message": {
            "outcome": "applied",
            "claim_id": claim,
            "invoice": "invoice-1",
            "version": "v1",
            "request_digest": "0" * 64,
        }
    }
    with ScriptedHttpServer(
        ScriptedResponse(body=json.dumps(receipt).encode()),
        ScriptedResponse(status=503),
    ) as upstream:
        client = InvoiceGuardClient(options(upstream.base_url))
        with pytest.raises(OutcomeUncertainError):
            await client.create("tenant", "Company", "key", invoice())
        with pytest.raises(OutcomeUncertainError):
            await client.create("tenant", "Company", "key", invoice())
        assert len(upstream.requests) == 2
    assert digest != "0" * 64


def test_transport_refuses_unpinned_or_retrying_client():
    with pytest.raises(ValueError):
        InvoiceGuardClient(HttpClientOptions(base_url="https://example.com"))
    with pytest.raises(ValueError):
        InvoiceGuardClient(
            HttpClientOptions(
                base_url="https://example.com",
                pin_egress=True,
                retry=RetryPolicy(max_attempts=2),
            )
        )
    with pytest.raises(ValueError):
        InvoiceGuardClient(
            HttpClientOptions(
                base_url="https://example.com", pin_egress=True, timeout=31
            )
        )


@pytest.mark.asyncio
async def test_reservation_and_reconciliation_are_bound_to_exact_payload():
    claim, _, digest, _ = _request("tenant", "Company", "key", invoice())
    reserved = {
        "message": {"outcome": "reserved", "claim_id": claim, "request_digest": digest}
    }
    with ScriptedHttpServer(
        ScriptedResponse(body=json.dumps(reserved).encode()),
        ScriptedResponse(body=json.dumps(reserved).encode()),
    ) as upstream:
        client = InvoiceGuardClient(options(upstream.base_url))
        assert (
            await client.reserve("tenant", "Company", "key", invoice())
        ).outcome == "reserved"
        assert (
            await client.reconcile("tenant", "Company", "key", invoice())
        ).outcome == "reserved"
        assert len(upstream.requests) == 2
