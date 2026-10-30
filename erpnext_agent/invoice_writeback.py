"""ERPNext source transport for the installed transactional invoice guard.

This transport never grants authority. Use it through the SDK's durable
write-back composition, after the operator qualifies the installed source app.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any

from epistemic_graph.generated.write_back import (
    ReconciliationObservation,
    SourceChangeSet,
    WriteBackAttempt,
    WriteBackAttemptKind,
    WriteBackEffectStatus,
    WriteBackOutcome,
)
from scion_erp_guard.bindings import _request
from scion_sdk.writeback.errors import (
    ChangeSetValidationError,
    OutcomeUncertainError,
)
from scion_sdk.writeback.models import DryRunObservation, SourceSnapshot

from erpnext_agent.invoice_guard_client import InvoiceGuardClient, InvoiceGuardOutcome

try:
    from scion_sdk.ports.writeback_transport import (
        ReservableWriteBackTransport,
    )
except ImportError:
    ReservableWriteBackTransport = None

UNOBSERVED_CLAIM_VERSION = "claim-reserved"


def _digest(value: object) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()
    return hashlib.sha256(raw).hexdigest()


class ERPNextInvoiceTransport:
    """Map a company-bound approved invoice change to the source transaction."""

    def __init__(
        self,
        client: InvoiceGuardClient,
        *,
        connector: str,
        source_instance: str,
        company: str,
    ) -> None:
        if not connector or not source_instance or not company:
            raise ValueError("source binding is required")
        self._client = client
        self._connector = connector
        self._source_instance = source_instance
        self._company = company

    def _invoice(self, change: SourceChangeSet) -> dict[str, Any]:
        if ReservableWriteBackTransport is None:
            raise ChangeSetValidationError("SDK approval preflight is unavailable")
        patch = change.desired_patch
        if (
            change.connector_id != self._connector
            or change.source_instance_id != self._source_instance
            or change.base_source_version != UNOBSERVED_CLAIM_VERSION
            or set(patch) != {"operation", "company_id", "invoice"}
            or patch["operation"] != "create_invoice"
            or patch["company_id"] != self._company
            or not isinstance(patch["invoice"], dict)
            or change.change_set_digest != change.canonical_digest()
        ):
            raise ChangeSetValidationError("invoice source binding mismatch")
        try:
            _, _, _, invoice = _request(
                change.tenant_id,
                self._company,
                change.idempotency_key,
                patch["invoice"],
            )
        except (TypeError, ValueError):
            raise ChangeSetValidationError("invalid invoice source payload") from None
        return invoice

    async def read_current(self, change: SourceChangeSet) -> SourceSnapshot:
        """Observe the idempotency claim without asserting that it is absent."""
        invoice = self._invoice(change)
        outcome = await self._client.reconcile(
            change.tenant_id, self._company, change.idempotency_key, invoice
        )
        if outcome.outcome == "unknown":
            raise OutcomeUncertainError("invoice reservation is unavailable")
        version = (
            outcome.version
            if outcome.outcome == "applied"
            else UNOBSERVED_CLAIM_VERSION
        )
        return SourceSnapshot(source_version=version, fields={})

    async def preview(
        self, change: SourceChangeSet, current: SourceSnapshot
    ) -> DryRunObservation:
        self._invoice(change)
        before = {name: current.fields.get(name) for name in change.field_scope}
        after = dict(change.desired_patch)
        return DryRunObservation(
            change_set_digest=change.change_set_digest,
            source_version=current.source_version,
            desired_patch_digest=change.patch_digest(),
            changed_fields=tuple(
                name for name in change.field_scope if before[name] != after[name]
            ),
            before=before,
            after=after,
        )

    async def prepare_writeback(self, change: SourceChangeSet) -> None:
        """Create a source reservation after the SDK verifies durable approval."""
        invoice = self._invoice(change)
        outcome = await self._client.reconcile(
            change.tenant_id, self._company, change.idempotency_key, invoice
        )
        if outcome.outcome == "unknown":
            await self._client.reserve(
                change.tenant_id, self._company, change.idempotency_key, invoice
            )

    async def prior_effect(self, change: SourceChangeSet) -> WriteBackAttempt | None:
        invoice = self._invoice(change)
        outcome = await self._client.reconcile(
            change.tenant_id, self._company, change.idempotency_key, invoice
        )
        if outcome.outcome == "unknown":
            raise OutcomeUncertainError("invoice reservation is unavailable")
        return self._attempt(change, outcome) if outcome.outcome == "applied" else None

    async def apply(
        self, change: SourceChangeSet, expected_version: str
    ) -> WriteBackAttempt:
        invoice = self._invoice(change)
        if expected_version != UNOBSERVED_CLAIM_VERSION:
            raise ChangeSetValidationError("invoice source version mismatch")
        outcome = await self._client.create(
            change.tenant_id, self._company, change.idempotency_key, invoice
        )
        return self._attempt(change, outcome)

    async def reconcile(self, change: SourceChangeSet) -> ReconciliationObservation:
        invoice = self._invoice(change)
        outcome = await self._client.reconcile(
            change.tenant_id, self._company, change.idempotency_key, invoice
        )
        applied = outcome.outcome == "applied"
        reserved = outcome.outcome == "reserved"
        return ReconciliationObservation(
            tenant_id=change.tenant_id,
            change_set_id=change.change_set_id,
            change_set_digest=change.change_set_digest,
            idempotency_key=change.idempotency_key,
            observed_source_version=outcome.version
            if applied
            else UNOBSERVED_CLAIM_VERSION,
            effect_status=WriteBackEffectStatus.APPLIED
            if applied
            else (
                WriteBackEffectStatus.NO_EFFECT
                if reserved
                else WriteBackEffectStatus.OUTCOME_UNCERTAIN
            ),
            retry_allowed=reserved,
            evidence_digest=_digest(asdict(outcome)),
            connector_observation_digest=_digest(asdict(outcome)),
            provenance_digest=_digest(change.field_provenance),
        )

    @staticmethod
    def _attempt(
        change: SourceChangeSet, outcome: InvoiceGuardOutcome
    ) -> WriteBackAttempt:
        if outcome.outcome != "applied" or outcome.version == UNOBSERVED_CLAIM_VERSION:
            raise ChangeSetValidationError("invoice source receipt is unavailable")
        return WriteBackAttempt(
            tenant_id=change.tenant_id,
            change_set_id=change.change_set_id,
            change_set_digest=change.change_set_digest,
            idempotency_key=change.idempotency_key,
            kind=WriteBackAttemptKind.APPLY,
            input_digest=change.authorization.input_digest,
            output_digest=change.authorization.output_digest,
            pre_source_version=UNOBSERVED_CLAIM_VERSION,
            post_source_version=outcome.version,
            applied_field_digest=change.patch_digest(),
            outcome=WriteBackOutcome.APPLIED,
            effect_status=WriteBackEffectStatus.APPLIED,
            connector_observation_digest=_digest(asdict(outcome)),
            provenance_digest=_digest(change.field_provenance),
        )
