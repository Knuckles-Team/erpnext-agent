"""Governed write-back calls the source guard and replays its durable receipt."""

import json
import time

import pytest
from agent_connector_sdk.http.options import HttpClientOptions
from agent_connector_sdk.http.retry import RetryPolicy
from agent_connector_sdk.testing.http_server import ScriptedHttpServer, ScriptedResponse
from agent_connector_sdk.testing.writeback_audit import InMemoryAuditReservation
from agent_connector_sdk.writeback.connector import DurableWritableConnector
from agent_connector_sdk.writeback.durable_ledger import FileWriteBackLedger
from epistemic_graph.generated.write_back import (
    SourceChangeSet,
    WriteBackAuthorizationDecision,
    WriteBackAuthorizationMode,
    WriteBackEffectStatus,
)
from scion_erp_guard.bindings import _request

from erpnext_agent.invoice_guard_client import InvoiceGuardClient
from erpnext_agent.invoice_writeback import (
    UNOBSERVED_CLAIM_VERSION,
    ERPNextInvoiceTransport,
    ReservableWriteBackTransport,
)


def change_set():
    invoice = {
        "company": "Company",
        "customer": "Customer",
        "currency": "USD",
        "items": [{"item_code": "item", "qty": 1, "rate": 5}],
    }
    patch = {"operation": "create_invoice", "company_id": "Company", "invoice": invoice}
    decision = WriteBackAuthorizationDecision(
        mode=WriteBackAuthorizationMode.STANDING_POLICY,
        authorization_ref="policy:invoice",
        decision_digest="2" * 64,
        input_digest="3" * 64,
        output_digest="4" * 64,
        authorized=True,
    )
    change = SourceChangeSet(
        schema_version=1,
        change_set_id="change",
        change_set_digest="0" * 64,
        tenant_id="tenant",
        actor="principal",
        purpose="invoice",
        connector_id="erpnext",
        source_instance_id="source",
        entity_id="new-invoice",
        base_source_version=UNOBSERVED_CLAIM_VERSION,
        desired_patch=patch,
        field_scope=list(patch),
        field_provenance={key: "fixture" for key in patch},
        required_capability="invoice.create",
        policy_digest="1" * 64,
        authorization=decision,
        idempotency_key="key",
        expires_at_ms=time.time_ns() // 1_000_000 + 60_000,
        reconciliation_procedure="query guard",
        source_of_truth_rule="provider invoice",
    )
    return change.model_copy(update={"change_set_digest": change.canonical_digest()})


@pytest.mark.skipif(
    ReservableWriteBackTransport is None,
    reason="SDK approval preflight not yet released",
)
@pytest.mark.asyncio
async def test_governed_source_create_and_replay_use_exact_receipt(tmp_path):
    change = change_set()
    claim, _, digest, _ = _request(
        change.tenant_id,
        "Company",
        change.idempotency_key,
        change.desired_patch["invoice"],
    )
    receipt = {
        "message": {
            "outcome": "applied",
            "claim_id": claim,
            "invoice": "invoice-1",
            "version": "v1",
            "request_digest": digest,
        }
    }
    unknown = ScriptedResponse(body=b'{"message":{"outcome":"unknown"}}')
    reserved = ScriptedResponse(
        body=json.dumps(
            {
                "message": {
                    "outcome": "reserved",
                    "claim_id": claim,
                    "request_digest": digest,
                }
            }
        ).encode()
    )
    with ScriptedHttpServer(
        unknown,
        reserved,
        reserved,
        reserved,
        ScriptedResponse(body=json.dumps(receipt).encode()),
        ScriptedResponse(body=json.dumps(receipt).encode()),
    ) as upstream:
        options = HttpClientOptions(
            base_url=upstream.base_url,
            pin_egress=True,
            allow_loopback=True,
            retry=RetryPolicy(max_attempts=1),
        )
        transport = ERPNextInvoiceTransport(
            InvoiceGuardClient(options),
            connector="erpnext",
            source_instance="source",
            company="Company",
        )
        ledger = FileWriteBackLedger(tmp_path / "ledger")
        writer = DurableWritableConnector(
            "erpnext", transport, ledger, audit=InMemoryAuditReservation()
        )
        await writer.register(change)
        first = await writer.apply(change)
        replay = await writer.apply(change)
        assert first == replay
        assert first.effect_status is WriteBackEffectStatus.APPLIED
        creates = [
            item
            for item in upstream.requests
            if item.path.endswith("create_invoice_once")
        ]
        assert len(creates) == 1
        assert len(upstream.requests) == 6


@pytest.mark.skipif(
    ReservableWriteBackTransport is None,
    reason="SDK approval preflight not yet released",
)
@pytest.mark.asyncio
async def test_reconciliation_unknown_never_authorizes_retry():
    change = change_set()
    with ScriptedHttpServer(
        ScriptedResponse(body=b'{"message":{"outcome":"unknown"}}')
    ) as upstream:
        options = HttpClientOptions(
            base_url=upstream.base_url,
            pin_egress=True,
            allow_loopback=True,
            retry=RetryPolicy(max_attempts=1),
        )
        transport = ERPNextInvoiceTransport(
            InvoiceGuardClient(options),
            connector="erpnext",
            source_instance="source",
            company="Company",
        )
        result = await transport.reconcile(change)
        assert result.effect_status is WriteBackEffectStatus.OUTCOME_UNCERTAIN
        assert result.retry_allowed is False


@pytest.mark.skipif(
    ReservableWriteBackTransport is None,
    reason="SDK approval preflight not yet released",
)
@pytest.mark.asyncio
async def test_wrong_company_or_operation_is_refused_before_source():
    from agent_connector_sdk.writeback.errors import ChangeSetValidationError

    change = change_set()
    with ScriptedHttpServer() as upstream:
        options = HttpClientOptions(
            base_url=upstream.base_url,
            pin_egress=True,
            allow_loopback=True,
            retry=RetryPolicy(max_attempts=1),
        )
        transport = ERPNextInvoiceTransport(
            InvoiceGuardClient(options),
            connector="erpnext",
            source_instance="source",
            company="Company",
        )
        for patch in (
            {**change.desired_patch, "company_id": "Other"},
            {**change.desired_patch, "operation": "update"},
        ):
            forged = change.model_copy(update={"desired_patch": patch})
            forged = forged.model_copy(
                update={"change_set_digest": forged.canonical_digest()}
            )
            with pytest.raises(ChangeSetValidationError):
                await transport.apply(forged, UNOBSERVED_CLAIM_VERSION)
        assert not upstream.requests


@pytest.mark.asyncio
async def test_missing_sdk_preflight_refuses_before_source(monkeypatch):
    from agent_connector_sdk.writeback.errors import ChangeSetValidationError

    import erpnext_agent.invoice_writeback as module

    monkeypatch.setattr(module, "ReservableWriteBackTransport", None)
    change = change_set()
    with ScriptedHttpServer() as upstream:
        options = HttpClientOptions(
            base_url=upstream.base_url,
            pin_egress=True,
            allow_loopback=True,
            retry=RetryPolicy(max_attempts=1),
        )
        transport = ERPNextInvoiceTransport(
            InvoiceGuardClient(options),
            connector="erpnext",
            source_instance="source",
            company="Company",
        )
        with pytest.raises(ChangeSetValidationError):
            await transport.prior_effect(change)
        assert not upstream.requests


@pytest.mark.skipif(
    ReservableWriteBackTransport is None,
    reason="SDK approval preflight not yet released",
)
@pytest.mark.asyncio
async def test_denied_approval_makes_no_source_request(tmp_path):
    from agent_connector_sdk.writeback.errors import AuthorizationDeniedError

    change = change_set()
    denied = change.model_copy(
        update={
            "authorization": change.authorization.model_copy(
                update={"authorized": False}
            )
        }
    )
    denied = denied.model_copy(update={"change_set_digest": denied.canonical_digest()})
    with ScriptedHttpServer() as upstream:
        options = HttpClientOptions(
            base_url=upstream.base_url,
            pin_egress=True,
            allow_loopback=True,
            retry=RetryPolicy(max_attempts=1),
        )
        transport = ERPNextInvoiceTransport(
            InvoiceGuardClient(options),
            connector="erpnext",
            source_instance="source",
            company="Company",
        )
        ledger = FileWriteBackLedger(tmp_path / "denied-ledger")
        writer = DurableWritableConnector(
            "erpnext", transport, ledger, audit=InMemoryAuditReservation()
        )
        await writer.register(denied)
        with pytest.raises(AuthorizationDeniedError):
            await writer.apply(denied)
        assert not upstream.requests


@pytest.mark.skipif(
    ReservableWriteBackTransport is None,
    reason="SDK enterprise dispatch not yet released",
)
@pytest.mark.asyncio
async def test_served_enterprise_write_uses_guard_and_durable_receipt(tmp_path):
    from agent_connector_sdk.identity import ActorContext, ActorType, use_actor
    from agent_connector_sdk.mcp.server import create_mcp_server
    from agent_connector_sdk.vendor_extractors.enterprise_contract import (
        CreateInvoice,
        EnterpriseCapability,
        EnterpriseOperation,
    )
    from agent_connector_sdk.vendor_extractors.enterprise_dispatch import (
        EnterpriseDispatcher,
        EnterpriseWriteTarget,
        enterprise_schema_binding,
    )
    from fastmcp import Client

    change = change_set()
    claim, _, digest, _ = _request(
        change.tenant_id,
        "Company",
        change.idempotency_key,
        change.desired_patch["invoice"],
    )
    applied = ScriptedResponse(
        body=json.dumps(
            {
                "message": {
                    "outcome": "applied",
                    "claim_id": claim,
                    "invoice": "invoice-1",
                    "version": "v1",
                    "request_digest": digest,
                }
            }
        ).encode()
    )
    reserved = ScriptedResponse(
        body=json.dumps(
            {
                "message": {
                    "outcome": "reserved",
                    "claim_id": claim,
                    "request_digest": digest,
                }
            }
        ).encode()
    )
    unknown = ScriptedResponse(body=b'{"message":{"outcome":"unknown"}}')
    with ScriptedHttpServer(unknown, reserved, reserved, reserved, applied) as upstream:
        options = HttpClientOptions(
            base_url=upstream.base_url,
            pin_egress=True,
            allow_loopback=True,
            retry=RetryPolicy(max_attempts=1),
        )
        source = ERPNextInvoiceTransport(
            InvoiceGuardClient(options),
            connector="erpnext",
            source_instance="source",
            company="Company",
        )
        ledger = FileWriteBackLedger(tmp_path / "ledger")
        writer = DurableWritableConnector(
            "erpnext", source, ledger, audit=InMemoryAuditReservation()
        )
        await writer.register(change)

        class Authority:
            async def authorize(self, actor, request):
                return True

        class Admission:
            async def admit(self, actor, request, capability):
                return EnterpriseWriteTarget(writer, ledger)

        class Reader:
            async def read(self, request):
                raise AssertionError("write reached read path")

        capability = EnterpriseCapability(
            connector="erpnext",
            connector_version="1",
            contract_revision="v1",
            company_ids=("Company",),
            operations=(enterprise_schema_binding("create_invoice"),),
        )
        handler = EnterpriseDispatcher(
            capability,
            authority=Authority(),
            reader=Reader(),
            write_admission=Admission(),
        )
        _, server, _ = create_mcp_server(
            "erpnext", version="1", command_args=[], enterprise_dispatcher=handler
        )
        req = EnterpriseOperation(
            request_id="request",
            tenant="tenant",
            company_id="Company",
            contract_revision="v1",
            authority="principal",
            parameters=CreateInvoice(change_set=change),
        )
        actor = ActorContext(
            actor_id="principal",
            actor_type=ActorType.HUMAN,
            tenant_id="tenant",
            authenticated=True,
        )
        with use_actor(actor):
            async with Client(server) as client:
                result = await client.call_tool(
                    "enterprise_operation", {"request": req.model_dump(mode="json")}
                )
        assert result.data["outcome"] == "ok"
        assert (
            result.data["effect_receipt"]["change_set_digest"]
            == change.change_set_digest
        )
        assert (
            sum(item.path.endswith("create_invoice_once") for item in upstream.requests)
            == 1
        )


@pytest.mark.skipif(
    ReservableWriteBackTransport is None,
    reason="SDK approval preflight not yet released",
)
@pytest.mark.asyncio
async def test_locked_reservation_proves_no_effect_and_permits_reconciliation_retry():
    change = change_set()
    claim, _, digest, _ = _request(
        change.tenant_id,
        "Company",
        change.idempotency_key,
        change.desired_patch["invoice"],
    )
    reserved = {
        "message": {"outcome": "reserved", "claim_id": claim, "request_digest": digest}
    }
    with ScriptedHttpServer(
        ScriptedResponse(body=json.dumps(reserved).encode())
    ) as upstream:
        options = HttpClientOptions(
            base_url=upstream.base_url,
            pin_egress=True,
            allow_loopback=True,
            retry=RetryPolicy(max_attempts=1),
        )
        transport = ERPNextInvoiceTransport(
            InvoiceGuardClient(options),
            connector="erpnext",
            source_instance="source",
            company="Company",
        )
        result = await transport.reconcile(change)
        assert result.effect_status is WriteBackEffectStatus.NO_EFFECT
        assert result.retry_allowed is True
